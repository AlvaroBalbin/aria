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

# ── Global state ─────────────────────────────────────────────────────────────
active_pendant_ws: WebSocket | None = None
session_task: asyncio.Task | None = None
session_stop_event: asyncio.Event | None = None
ambient_enabled = True


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


# ── Pendant helpers ──────────────────────────────────────────────────────────

_last_pendant_state = ""

async def send_pendant_state(state: str):
    """Send state to pendant + dashboard. Debounces duplicate states."""
    global _last_pendant_state
    if state == _last_pendant_state:
        return
    _last_pendant_state = state
    if active_pendant_ws:
        try:
            await active_pendant_ws.send_text(json.dumps({"state": state}))
        except Exception:
            pass
    await broadcast("pendant_state", {"state": state})


async def send_pendant_text(text: str):
    """Send text to pendant for OLED display."""
    if active_pendant_ws:
        try:
            await active_pendant_ws.send_text(json.dumps({"text": text[:120]}))
        except Exception:
            pass


async def on_realtime_event(event: dict):
    """Handle events from realtime session — broadcast to dashboard + pendant."""
    if event["event"] == "transcript":
        await broadcast("transcript", {
            "speaker": event["speaker"],
            "text": event["text"],
            "ts": time.time(),
        })
        if event["speaker"] == "ARIA":
            await send_pendant_text(event["text"])
    elif event["event"] == "tool_use":
        await broadcast("tool_use", {
            "tool": event["tool"],
            "args": event.get("args", {}),
            "result": event.get("result", ""),
            "ts": time.time(),
        })


async def start_session():
    """Start a realtime session."""
    global session_task, session_stop_event, ambient_enabled
    if session_task and not session_task.done():
        return  # already running

    ambient_enabled = False
    session_stop_event = asyncio.Event()

    async def run():
        global ambient_enabled
        try:
            await realtime_session(
                state_callback=send_pendant_state,
                mic_device="pulse",
                stop_event=session_stop_event,
                on_event=on_realtime_event,
            )
        except Exception as e:
            print(f"Realtime failed: {e} — falling back to Claude pipeline")
            await fallback_pipeline()
        finally:
            ambient_enabled = True
            await send_pendant_state("idle")

    session_task = asyncio.create_task(run())


async def stop_session():
    """Stop the current realtime session."""
    global session_task, session_stop_event, ambient_enabled
    if session_stop_event:
        session_stop_event.set()
    if session_task:
        try:
            await session_task
        except Exception:
            pass
        session_task = None
    ambient_enabled = True


async def fallback_pipeline():
    """Fallback: record → whisper → Claude → TTS when realtime fails."""
    print("Running fallback pipeline...")
    await send_pendant_state("listening")
    loop = asyncio.get_event_loop()
    text = await loop.run_in_executor(None, record_and_transcribe)
    if text and text.strip():
        print(f"Fallback heard: {text}")
        save_transcript(text, speaker="User")
        await broadcast("transcript", {"speaker": "User", "text": text, "ts": time.time()})

        await send_pendant_state("processing")
        response = await loop.run_in_executor(None, ask, text)

        print(f"Fallback ARIA: {response}")
        save_transcript(response, speaker="ARIA")
        await broadcast("transcript", {"speaker": "ARIA", "text": response, "ts": time.time()})
        await send_pendant_text(response)

        await send_pendant_state("speaking")
        await loop.run_in_executor(None, speak, response)
    await send_pendant_state("idle")


# ── Ambient listening (24/7) + wake word ─────────────────────────────────────

async def ambient_listen_loop():
    """Continuously record + transcribe ambient audio in 15s chunks.
    Detects wake word 'ARIA' to auto-start a session."""
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

                # Wake word detection
                if "aria" in text.lower() and not (session_task and not session_task.done()):
                    print("Wake word 'ARIA' detected! Starting session...")
                    await start_session()
        except Exception as e:
            print(f"Ambient listen error: {e}")
            await asyncio.sleep(5)


# ── ESP32 audio WebSocket (legacy — raw audio streaming) ─────────────────────

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


# ── Pendant control WebSocket ────────────────────────────────────────────────

@app.websocket("/ws/pendant")
async def pendant_ws(websocket: WebSocket):
    """
    Pendant connects here. Button press toggles realtime session on/off.
    """
    global active_pendant_ws
    await websocket.accept()
    active_pendant_ws = websocket
    print("Pendant connected on /ws/pendant")

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("event") == "button_press":
                if session_task and not session_task.done():
                    print("Button pressed — stopping Realtime session")
                    await stop_session()
                else:
                    print("Button pressed — starting Realtime session")
                    await start_session()

    except WebSocketDisconnect:
        print("Pendant disconnected")
        active_pendant_ws = None
        await stop_session()
    except Exception as e:
        print(f"Pendant handler crashed: {e}")
        active_pendant_ws = None
        await stop_session()


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
