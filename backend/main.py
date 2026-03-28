"""
ARIA Backend — FastAPI server running on Raspberry Pi 5
Handles: ESP32 audio WebSocket, Claude brain, TTS, dashboard push
"""
import asyncio
import json
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from db import init_db, save_transcript, get_transcript, get_all_memories, save_conversation_turn
from transcriber import transcribe_bytes
from brain import ask
from tts import speak
from memory import memory_extraction_loop

# Connected dashboard browsers (for live push)
dashboard_clients: set[WebSocket] = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("DB initialised")
    # Start background memory extraction loop
    asyncio.create_task(memory_extraction_loop())
    asyncio.create_task(ambient_check_loop())
    yield


app = FastAPI(lifespan=lifespan)


# ── Dashboard broadcast ───────────────────────────────────────────────────────

async def broadcast(event: str, data: dict):
    """Push an event to all connected dashboard browsers."""
    msg = json.dumps({"event": event, **data})
    dead = set()
    for ws in dashboard_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    dashboard_clients -= dead


# ── ESP32 audio WebSocket ─────────────────────────────────────────────────────

@app.websocket("/ws/audio")
async def audio_ws(websocket: WebSocket):
    await websocket.accept()
    print("Pendant connected")
    audio_buffer = bytearray()
    pendant_state = "idle"

    try:
        while True:
            data = await websocket.receive()

            if "bytes" in data:
                # Binary frame: raw PCM audio from ESP32
                audio_buffer.extend(data["bytes"])

            elif "text" in data:
                msg = json.loads(data["text"])

                if msg.get("event") == "end_of_speech":
                    # Button released — process the accumulated audio
                    if audio_buffer:
                        print(f"Processing {len(audio_buffer)} bytes of audio…")
                        await broadcast("pendant_state", {"state": "processing"})
                        await websocket.send_text(json.dumps({"state": "processing"}))

                        # Transcribe in thread (blocks CPU)
                        pcm = bytes(audio_buffer)
                        audio_buffer.clear()
                        loop = asyncio.get_event_loop()
                        text = await loop.run_in_executor(None, transcribe_bytes, pcm)

                        if text.strip():
                            print(f"Heard: {text}")
                            save_transcript(text, speaker="User")
                            await broadcast("transcript", {"speaker": "User", "text": text, "ts": time.time()})

                            # Get Claude response (also in thread)
                            await broadcast("pendant_state", {"state": "processing"})
                            response = await loop.run_in_executor(None, ask, text)

                            print(f"ARIA: {response}")
                            save_transcript(response, speaker="ARIA")
                            await broadcast("transcript", {"speaker": "ARIA", "text": response, "ts": time.time()})
                            await broadcast("pendant_state", {"state": "speaking"})
                            await websocket.send_text(json.dumps({"state": "speaking"}))

                            # Speak (in thread so we don't block)
                            await loop.run_in_executor(None, speak, response)
                        else:
                            print("Nothing intelligible heard.")

                        await broadcast("pendant_state", {"state": "idle"})
                        await websocket.send_text(json.dumps({"state": "idle"}))
                        audio_buffer.clear()

                elif msg.get("pendant_state"):
                    pendant_state = msg["pendant_state"]
                    await broadcast("pendant_state", {"state": pendant_state})

    except WebSocketDisconnect:
        print("Pendant disconnected")


# ── Dashboard WebSocket ───────────────────────────────────────────────────────

@app.websocket("/ws/dashboard")
async def dashboard_ws(websocket: WebSocket):
    await websocket.accept()
    dashboard_clients.add(websocket)
    print(f"Dashboard connected ({len(dashboard_clients)} total)")

    # Send current state on connect
    rows = get_transcript(minutes=60)
    await websocket.send_text(json.dumps({
        "event": "history",
        "transcript": [{"speaker": r["speaker"], "text": r["text"], "ts": r["ts"]} for r in rows],
        "memories": get_all_memories(limit=20),
    }))

    try:
        while True:
            await websocket.receive_text()  # keep alive
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
