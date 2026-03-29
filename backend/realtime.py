"""
OpenAI Realtime API — voice-to-voice with function calling.
Streams mic audio to OpenAI, gets audio response back, plays through AirPods.
"""
import asyncio
import json
import base64
import subprocess
import os
import websockets
from tools import TOOL_MAP
from memory import build_memory_context
from db import save_transcript, get_transcript
from config import OPENAI_API_KEY, USER_NAME

MODEL = "gpt-4o-realtime-preview"
RT_URL = f"wss://api.openai.com/v1/realtime?model={MODEL}"
RT_HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "OpenAI-Beta": "realtime=v1",
}

# Tool schemas for realtime API (slightly different format from chat)
RT_TOOLS = [
    {
        "type": "function",
        "name": "search_web",
        "description": "Search the web for current info, news, or facts.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query"}},
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "save_memory",
        "description": "Permanently save an important fact about the user.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Short label"},
                "value": {"type": "string", "description": "The value to store"},
            },
            "required": ["key", "value"],
        },
    },
    {
        "type": "function",
        "name": "query_memories",
        "description": "Search stored memories about the user.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "What to look for"}},
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "get_transcript",
        "description": "Get recent ambient transcript of nearby conversation.",
        "parameters": {
            "type": "object",
            "properties": {"minutes": {"type": "integer", "description": "Minutes back (default 30)"}},
            "required": [],
        },
    },
    {
        "type": "function",
        "name": "set_reminder",
        "description": "Set a reminder for the user.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "What to remind about"},
                "when_description": {"type": "string", "description": "When (optional)"},
            },
            "required": ["text"],
        },
    },
    {
        "type": "function",
        "name": "get_datetime",
        "description": "Get the current date and time.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "type": "function",
        "name": "search_x",
        "description": "Search X/Twitter for the latest real-time tweets and news.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Topic to search"}},
            "required": ["query"],
        },
    },
]


def _build_instructions() -> str:
    memory_ctx = build_memory_context()
    ambient_rows = get_transcript(minutes=5)
    if ambient_rows:
        lines = [f"[{r['speaker']}]: {r['text']}" for r in ambient_rows[-10:]]
        ambient_ctx = "Recent conversation you overheard:\n" + "\n".join(lines)
    else:
        ambient_ctx = ""

    return f"""You are ARIA — a wearable AI assistant built into a pendant worn by {USER_NAME}.
You hear everything through their AirPods and speak back through them.

## Personality
- You're sharp, witty, and direct. Think Jarvis meets a brilliant best friend.
- Keep responses to 1-3 sentences. You're speaking into someone's ear — be punchy.
- Never say "as an AI". You're ARIA, act like it.
- Match the user's energy.

## Capabilities
- Search the web and X/Twitter for real-time info
- Remember things about {USER_NAME} permanently
- Hear ambient conversation and reference it
- Set reminders, check the time

## Context
You're at the Bath Hackathon 2026. {USER_NAME} built you as their hackathon project.
You run on a Raspberry Pi 5, connected to an ESP32 pendant with a screen and LEDs.

{memory_ctx}

{ambient_ctx}

## Rules
- Use tools WITHOUT asking. Just do it.
- KEEP IT SHORT. Voice assistant, not essay writer.
- Be proactive — if ambient context is relevant, reference it."""


async def realtime_session(state_callback, mic_device="pulse", stop_event: asyncio.Event = None):
    """
    Persistent realtime conversation session.
    Keeps the connection open for multiple back-and-forth turns.
    Set stop_event to signal shutdown from outside.
    """
    all_user = []
    all_assistant = []

    # Start aplay process to stream output audio
    player = subprocess.Popen(
        ["aplay", "-D", "pulse", "-t", "raw", "-f", "S16_LE", "-r", "24000", "-c", "1", "-q"],
        stdin=subprocess.PIPE,
    )

    # Start arecord process to capture mic
    recorder = subprocess.Popen(
        ["arecord", "-D", mic_device, "-f", "S16_LE", "-r", "24000", "-c", "1", "-q"],
        stdout=subprocess.PIPE,
    )

    try:
        async with websockets.connect(RT_URL, extra_headers=RT_HEADERS) as ws:
            # Wait for session.created
            event = json.loads(await ws.recv())
            print(f"Realtime: {event['type']}")

            # Configure session
            await ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "modalities": ["audio", "text"],
                    "instructions": _build_instructions(),
                    "voice": "ash",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 800,
                    },
                    "input_audio_transcription": {"model": "whisper-1"},
                    "tools": RT_TOOLS,
                    "tool_choice": "auto",
                },
            }))

            # Wait for session.updated
            ack = json.loads(await ws.recv())
            print(f"Realtime: {ack['type']}")

            await state_callback("listening")

            # Stream mic audio in background
            async def stream_mic():
                loop = asyncio.get_event_loop()
                while True:
                    try:
                        chunk = await loop.run_in_executor(None, recorder.stdout.read, 4800)
                        if not chunk:
                            break
                        await ws.send(json.dumps({
                            "type": "input_audio_buffer.append",
                            "audio": base64.b64encode(chunk).decode(),
                        }))
                    except Exception:
                        break

            mic_task = asyncio.create_task(stream_mic())

            # Process events — loop forever until stop_event or disconnect
            while True:
                # Check if we should stop
                if stop_event and stop_event.is_set():
                    print("Realtime: stop requested")
                    break

                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=60)
                except asyncio.TimeoutError:
                    # No activity for 60s — still keep alive, just loop
                    continue

                event = json.loads(raw)
                t = event["type"]

                if t == "input_audio_buffer.speech_started":
                    print("Realtime: user speaking...")
                    await state_callback("listening")

                elif t == "input_audio_buffer.speech_stopped":
                    print("Realtime: user stopped")
                    await state_callback("processing")

                elif t == "conversation.item.input_audio_transcription.completed":
                    transcript = event.get("transcript", "")
                    if transcript.strip():
                        print(f"Realtime heard: {transcript}")
                        all_user.append(transcript)
                        save_transcript(transcript, speaker="User")

                elif t in ("response.audio.delta", "response.output_audio.delta"):
                    await state_callback("speaking")
                    chunk = base64.b64decode(event["delta"])
                    try:
                        player.stdin.write(chunk)
                        player.stdin.flush()
                    except Exception:
                        pass

                elif t in ("response.audio_transcript.delta", "response.output_audio_transcript.delta"):
                    # Accumulate current turn's assistant transcript
                    if not hasattr(realtime_session, '_current_turn'):
                        realtime_session._current_turn = ""
                    realtime_session._current_turn += event.get("delta", "")

                elif t == "response.output_item.done":
                    item = event.get("item", {})
                    if item.get("type") == "function_call":
                        fn_name = item.get("name", "")
                        call_id = item.get("call_id", "")
                        fn_args = json.loads(item.get("arguments", "{}"))
                        print(f"[Tool] {fn_name}({fn_args})")

                        try:
                            result = TOOL_MAP[fn_name](fn_args)
                        except Exception as e:
                            result = f"Tool error: {e}"
                        print(f"[Result] {str(result)[:120]}")

                        await ws.send(json.dumps({
                            "type": "conversation.item.create",
                            "item": {
                                "type": "function_call_output",
                                "call_id": call_id,
                                "output": str(result),
                            },
                        }))
                        await ws.send(json.dumps({"type": "response.create"}))

                elif t == "response.done":
                    print("Realtime: response complete")
                    # Save assistant transcript for this turn
                    turn_text = getattr(realtime_session, '_current_turn', "")
                    if turn_text.strip():
                        all_assistant.append(turn_text)
                        save_transcript(turn_text, speaker="ARIA")
                    realtime_session._current_turn = ""
                    # Go back to listening for next turn
                    await state_callback("listening")

                elif t == "error":
                    print(f"Realtime error: {event}")
                    break

            mic_task.cancel()

    except Exception as e:
        print(f"Realtime session error: {e}")
    finally:
        try:
            recorder.terminate()
            recorder.wait(timeout=2)
        except Exception:
            try:
                recorder.kill()
            except Exception:
                pass
        try:
            player.stdin.close()
            player.wait(timeout=2)
        except Exception:
            try:
                player.kill()
            except Exception:
                pass

    await state_callback("idle")
    return {
        "user": " | ".join(all_user),
        "assistant": " | ".join(all_assistant),
    }
