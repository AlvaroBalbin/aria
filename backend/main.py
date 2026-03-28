"""
ARIA Backend — FastAPI server running on Raspberry Pi 5
Handles: ESP32 audio WebSocket, Claude brain, TTS, dashboard push
"""
import asyncio
import base64
import json
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from db import init_db, save_transcript, get_transcript, get_all_memories, save_conversation_turn, get_due_reminders, delete_reminder
from transcriber import transcribe_bytes, transcribe_webm
from brain import ask
from memory import run_extraction_job
from tts import speak, synthesize, clone_voice, get_active_voice_id

# Connected dashboard browsers (for live push)
dashboard_clients: set[WebSocket] = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("DB initialised")
    asyncio.create_task(ambient_check_loop())
    asyncio.create_task(memory_extraction_loop())
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
    dashboard_clients.difference_update(dead)


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

                        try:
                            # Transcribe in thread (blocks CPU)
                            pcm = bytes(audio_buffer)
                            audio_buffer.clear()
                            loop = asyncio.get_event_loop()
                            text = await loop.run_in_executor(None, transcribe_bytes, pcm)

                            if text.strip():
                                import re
                                text = re.sub(r'\barya\b', 'ARIA', text, flags=re.IGNORECASE)
                                print(f"Heard: {text}")
                                save_transcript(text, speaker="User")
                                await broadcast("transcript", {"speaker": "User", "text": text, "ts": time.time()})

                                # Get Claude response (also in thread)
                                await broadcast("pendant_state", {"state": "processing"})
                                result = await loop.run_in_executor(None, ask, text)
                                response = result["response"]

                                print(f"ARIA: {response}")
                                save_transcript(response, speaker="ARIA")
                                await broadcast("transcript", {"speaker": "ARIA", "text": response, "ts": time.time()})
                                await broadcast("pendant_state", {"state": "speaking"})
                                await websocket.send_text(json.dumps({"state": "speaking"}))

                                # Speak (in thread so we don't block)
                                await loop.run_in_executor(None, speak, response)
                            else:
                                print("Nothing intelligible heard.")
                        except Exception as e:
                            import traceback
                            traceback.print_exc()
                            error_text = f"Sorry, I encountered an error: {str(e)}"
                            print(f"[Error] Audio processing failed: {e}")
                            await broadcast("transcript", {"speaker": "System", "text": error_text, "ts": time.time()})
                            await loop.run_in_executor(None, speak, error_text)
                        finally:
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
    import re
    text = re.sub(r'\barya\b', 'ARIA', req.text, flags=re.IGNORECASE)
    save_transcript(text, speaker="User")
    await broadcast("transcript", {"speaker": "User", "text": text, "ts": time.time()})
    await broadcast("pendant_state", {"state": "processing"})

    try:
        result = await loop.run_in_executor(None, ask, text)
        response = result["response"]
        mood = result["mood"]

        save_transcript(response, speaker="ARIA")
        await broadcast("transcript", {"speaker": "ARIA", "text": response, "ts": time.time()})

        # Generate audio for browser playback
        audio_bytes = await loop.run_in_executor(None, synthesize, response)
        audio_b64 = None
        if audio_bytes:
            audio_b64 = "data:audio/mpeg;base64," + base64.b64encode(audio_bytes).decode()

        return {"response": response, "mood": mood, "audio_base64": audio_b64}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"response": f"Sorry, I encountered an error answering your text query: {str(e)}", "mood": "neutral", "audio_base64": None}
    finally:
        await broadcast("pendant_state", {"state": "idle"})


# Wake word state — when ARIA is heard, buffer and wait for the full question
_wake_word_pending = False
_wake_word_time = 0.0


@app.post("/ambient")
async def ambient_endpoint(audio: UploadFile = File(...)):
    """Continuous ambient listening — transcribe and log without querying ARIA."""
    global _wake_word_pending, _wake_word_time
    audio_bytes = await audio.read()
    if len(audio_bytes) < 2000:
        return {"text": ""}
    loop = asyncio.get_event_loop()
    text = await loop.run_in_executor(None, transcribe_webm, audio_bytes)
    if not text.strip():
        # If we were waiting for a follow-up and got silence, fire with what we have
        if _wake_word_pending and (time.time() - _wake_word_time > 10):
            _wake_word_pending = False
            await _respond_from_ambient(loop)
        return {"text": ""}

    import re
    text = re.sub(r'\barya\b', 'ARIA', text, flags=re.IGNORECASE)
    save_transcript(text, speaker="User")
    await broadcast("transcript", {"speaker": "User", "text": text, "ts": time.time()})

    has_wake = bool(re.search(r'\bARIA\b', text))

    if _wake_word_pending:
        # This is the follow-up chunk after the wake word — now respond
        _wake_word_pending = False
        await _respond_from_ambient(loop)
    elif has_wake:
        # Check if the question is complete in this chunk (wake word + more words after it)
        after_wake = re.split(r'\bARIA\b', text, flags=re.IGNORECASE)[-1].strip()
        if len(after_wake.split()) >= 3:
            # Full question in one chunk — respond now
            await _respond_from_ambient(loop)
        else:
            # Just the wake word or a fragment — wait for the next chunk
            _wake_word_pending = True
            _wake_word_time = time.time()
            await broadcast("pendant_state", {"state": "listening"})

    return {"text": text}


async def _respond_from_ambient(loop):
    """Gather recent transcript context and send to ARIA's brain."""
    try:
        # Pull the last 2 minutes of transcript for full context
        recent = get_transcript(minutes=2)
        if not recent:
            return
        # Combine recent user speech into one query
        user_lines = [r["text"] for r in recent if r["speaker"] == "User"]
        combined = " ".join(user_lines[-5:])  # last ~5 entries
        if not combined.strip():
            return

        await broadcast("pendant_state", {"state": "processing"})
        result = await loop.run_in_executor(None, ask, combined)
        response = result["response"]

        save_transcript(response, speaker="ARIA")
        await broadcast("transcript", {"speaker": "ARIA", "text": response, "ts": time.time()})
        await broadcast("pendant_state", {"state": "speaking"})

        await loop.run_in_executor(None, speak, response)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[Error] Ambient response failed: {e}")
    finally:
        await broadcast("pendant_state", {"state": "idle"})


@app.post("/voice-query")
async def voice_query_endpoint(audio: UploadFile = File(...)):
    """Voice query — browser mic audio in, text + audio response out."""
    audio_bytes = await audio.read()
    loop = asyncio.get_event_loop()

    # Transcribe
    text = await loop.run_in_executor(None, transcribe_webm, audio_bytes)
    if not text.strip():
        return {"text": "", "response": "", "audio_base64": None}

    import re
    text = re.sub(r'\barya\b', 'ARIA', text, flags=re.IGNORECASE)

    # Save & broadcast user turn
    save_transcript(text, speaker="User")
    await broadcast("transcript", {"speaker": "User", "text": text, "ts": time.time()})
    await broadcast("pendant_state", {"state": "processing"})

    try:
        # Brain
        result = await loop.run_in_executor(None, ask, text)
        response = result["response"]
        mood = result["mood"]
        save_transcript(response, speaker="ARIA")
        await broadcast("transcript", {"speaker": "ARIA", "text": response, "ts": time.time()})

        # TTS
        audio_bytes_out = await loop.run_in_executor(None, synthesize, response)
        audio_b64 = None
        if audio_bytes_out:
            audio_b64 = "data:audio/mpeg;base64," + base64.b64encode(audio_bytes_out).decode()

        return {"text": text, "response": response, "mood": mood, "audio_base64": audio_b64}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"text": text, "response": f"Sorry, an error occurred during voice query: {str(e)}", "mood": "neutral", "audio_base64": None}
    finally:
        await broadcast("pendant_state", {"state": "idle"})


@app.post("/clone-voice")
async def clone_voice_endpoint(audio: UploadFile = File(...), name: str = Form("ARIA")):
    """Clone a voice from uploaded audio sample."""
    audio_bytes = await audio.read()
    ext = Path(audio.filename).suffix if audio.filename else ".webm"
    loop = asyncio.get_event_loop()
    voice_id = await loop.run_in_executor(None, clone_voice, audio_bytes, name, ext)
    if voice_id:
        return {"success": True, "voice_id": voice_id}
    return {"success": False, "error": "Voice cloning failed. Try a longer or clearer sample."}


@app.get("/voice-status")
async def voice_status_endpoint():
    """Check if a custom voice is configured."""
    vid = get_active_voice_id()
    return {"has_voice": bool(vid), "voice_id": vid or ""}


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
            due = get_due_reminders()
            for r in due:
                msg = f"Reminder: {r['text']}"
                await broadcast("transcript", {"speaker": "ARIA", "text": msg, "ts": time.time()})
                asyncio.get_event_loop().run_in_executor(None, speak, msg)
                delete_reminder(r["id"])
        except Exception as e:
            print(f"Reminder check error: {e}")

async def memory_extraction_loop():
    """Extract memories from transcript every 5 minutes."""
    while True:
        await asyncio.sleep(300)  # 5 minutes
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, run_extraction_job)
        except Exception as e:
            print(f"Memory extraction loop error: {e}")


# ── Serve frontend ────────────────────────────────────────────────────────────

frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    from config import HOST, PORT
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)
