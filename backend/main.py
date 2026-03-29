"""
ARIA Backend — FastAPI server running on Raspberry Pi 5
Handles: pendant WebSocket, Claude brain, TTS, ambient listening, dashboard
"""
import asyncio
import json
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from db import init_db, save_transcript, get_transcript, get_all_memories, save_conversation_turn
from transcriber import transcribe_bytes, record_and_transcribe, record_ambient_chunk
from brain import ask
from tts import speak
from memory import memory_extraction_loop
from realtime import realtime_session

# Connected dashboard browsers (for live push)
dashboard_clients: set[WebSocket] = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("DB initialised")
    asyncio.create_task(memory_extraction_loop())
    asyncio.create_task(ambient_check_loop())
    asyncio.create_task(ambient_listen_loop())
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ── Dashboard broadcast ───────────────────────────────────────────────────────

async def broadcast(event: str, data: dict):
    """Push an event to all connected dashboard browsers."""
    global dashboard_clients
    msg = json.dumps({"event": event, **data})
    dead = set()
    for ws in dashboard_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    dashboard_clients -= dead


# ── Ambient listening (24/7) ─────────────────────────────────────────────────

ambient_enabled = True  # toggle via API if needed

async def ambient_listen_loop():
    """Continuously record + transcribe ambient audio in 15s chunks."""
    print("Ambient listening started — recording environment 24/7")
    loop = asyncio.get_event_loop()
    while True:
        if not ambient_enabled:
            await asyncio.sleep(5)
            continue
        try:
            text = await loop.run_in_executor(None, record_ambient_chunk)
            if text and text.strip() and len(text.strip()) > 5:
                print(f"[Ambient] {text}")
                save_transcript(text, speaker="Ambient")
                await broadcast("transcript", {"speaker": "Ambient", "text": text, "ts": time.time()})
        except Exception as e:
            print(f"Ambient listen error: {e}")
            await asyncio.sleep(5)


# ── ESP32 audio WebSocket ─────────────────────────────────────────────────────

@app.websocket("/ws/audio")
async def audio_ws(websocket: WebSocket):
    await websocket.accept()
    print("Pendant connected")
    audio_buffer = bytearray()

    try:
        while True:
            data = await websocket.receive()

            if "bytes" in data:
                audio_buffer.extend(data["bytes"])

            elif "text" in data:
                msg = json.loads(data["text"])

                if msg.get("event") == "end_of_speech":
                    if audio_buffer:
                        print(f"Processing {len(audio_buffer)} bytes of audio...")
                        await broadcast("pendant_state", {"state": "processing"})
                        await websocket.send_text(json.dumps({"state": "processing"}))

                        pcm = bytes(audio_buffer)
                        audio_buffer.clear()
                        loop = asyncio.get_event_loop()
                        text = await loop.run_in_executor(None, transcribe_bytes, pcm)

                        if text.strip():
                            print(f"Heard: {text}")
                            save_transcript(text, speaker="User")
                            await broadcast("transcript", {"speaker": "User", "text": text, "ts": time.time()})

                            await broadcast("pendant_state", {"state": "processing"})
                            response = await loop.run_in_executor(None, ask, text)

                            print(f"ARIA: {response}")
                            save_transcript(response, speaker="ARIA")
                            await broadcast("transcript", {"speaker": "ARIA", "text": response, "ts": time.time()})
                            await broadcast("pendant_state", {"state": "speaking"})
                            await websocket.send_text(json.dumps({"state": "speaking"}))

                            await loop.run_in_executor(None, speak, response)
                        else:
                            print("Nothing intelligible heard.")

                        await broadcast("pendant_state", {"state": "idle"})
                        await websocket.send_text(json.dumps({"state": "idle"}))
                        audio_buffer.clear()

                elif msg.get("pendant_state"):
                    await broadcast("pendant_state", {"state": msg["pendant_state"]})

    except WebSocketDisconnect:
        print("Pendant disconnected")


# ── Pendant control WebSocket (no audio — button only) ───────────────────────

@app.websocket("/ws/pendant")
async def pendant_ws(websocket: WebSocket):
    """
    Pendant connects here. First button press starts a persistent Realtime session.
    Second button press stops it. Toggle on/off.
    """
    await websocket.accept()
    print("Pendant connected on /ws/pendant")

    session_task = None
    stop_event = None

    async def send_state(state: str):
        try:
            await websocket.send_text(json.dumps({"state": state}))
            await broadcast("pendant_state", {"state": state})
        except Exception:
            pass

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("event") == "button_press":
                if session_task and not session_task.done():
                    # Session running — stop it
                    print("Button pressed — stopping Realtime session")
                    stop_event.set()
                    await session_task
                    session_task = None
                    global ambient_enabled
                    ambient_enabled = True
                else:
                    # No session — start one
                    print("Button pressed — starting Realtime session")
                    ambient_enabled = False
                    stop_event = asyncio.Event()

                    async def run_session():
                        try:
                            await realtime_session(
                                state_callback=send_state,
                                mic_device="pulse",
                                stop_event=stop_event,
                            )
                        except Exception as e:
                            print(f"Realtime session failed: {e}")
                            await send_state("idle")

                    session_task = asyncio.create_task(run_session())

    except WebSocketDisconnect:
        print("Pendant disconnected")
        if stop_event:
            stop_event.set()
        ambient_enabled = True
    except Exception as e:
        print(f"Pendant handler crashed: {e}")
        if stop_event:
            stop_event.set()
        ambient_enabled = True


# ── Dashboard WebSocket ───────────────────────────────────────────────────────

@app.websocket("/ws/dashboard")
async def dashboard_ws(websocket: WebSocket):
    await websocket.accept()
    dashboard_clients.add(websocket)
    print(f"Dashboard connected ({len(dashboard_clients)} total)")

    rows = get_transcript(minutes=60)
    await websocket.send_text(json.dumps({
        "event": "history",
        "transcript": [{"speaker": r["speaker"], "text": r["text"], "ts": r["ts"]} for r in rows],
        "memories": get_all_memories(limit=20),
    }))

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        dashboard_clients.discard(websocket)
        print("Dashboard disconnected")


# ── REST endpoints ────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    text: str


@app.post("/query")
async def query_endpoint(req: QueryRequest):
    """Direct text query — used by dashboard chat box."""
    loop = asyncio.get_event_loop()
    save_transcript(req.text, speaker="User")
    await broadcast("transcript", {"speaker": "User", "text": req.text, "ts": time.time()})
    await broadcast("pendant_state", {"state": "processing"})

    response = await loop.run_in_executor(None, ask, req.text)

    save_transcript(response, speaker="ARIA")
    await broadcast("transcript", {"speaker": "ARIA", "text": response, "ts": time.time()})
    await broadcast("pendant_state", {"state": "idle"})
    loop.run_in_executor(None, speak, response)
    return {"response": response}


@app.get("/transcript")
async def transcript_endpoint(minutes: int = 30):
    return get_transcript(minutes)


@app.get("/memories")
async def memories_endpoint():
    return get_all_memories()


@app.post("/ambient/toggle")
async def toggle_ambient():
    global ambient_enabled
    ambient_enabled = not ambient_enabled
    return {"ambient_enabled": ambient_enabled}


# ── Background: check reminders ───────────────────────────────────────────────

async def ambient_check_loop():
    """Periodically check for due reminders."""
    while True:
        await asyncio.sleep(60)
        try:
            from db import get_conn
            import time as t
            conn = get_conn()
            due = conn.execute(
                "SELECT id, text FROM reminders WHERE due IS NOT NULL AND due <= ?", (t.time(),)
            ).fetchall()
            conn.close()
            for r in due:
                msg = f"Reminder: {r['text']}"
                await broadcast("transcript", {"speaker": "ARIA", "text": msg, "ts": t.time()})
                asyncio.get_event_loop().run_in_executor(None, speak, msg)
        except Exception as e:
            print(f"Reminder check error: {e}")


# ── Serve frontend ────────────────────────────────────────────────────────────

frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    from config import HOST, PORT
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)
