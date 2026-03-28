# ARIA — Claude Context File

**Read this first.** This file gives you instant full context on the ARIA project so you can jump in and help immediately.

---

## What is ARIA?

A wearable AI personal assistant built at Bath Hackathon 2026. A circular pendant (ESP32 + OLED + NeoPixels + microphone) worn around the neck. You hold a button and speak. The response comes back in your AirPods. A Raspberry Pi 5 on the table runs all the AI.

**Elevator pitch:** "Siri, but it actually knows you, remembers your whole day, and takes real actions. Runs on your own hardware for £30."

**Competing for:** Most Technically Impressive, Best AI, Most Commercially Viable, Embedded, Hackers' Choice.

---

## Architecture

```
[PENDANT — ESP32]                    [BASE STATION — Raspberry Pi 5]
  INMP441 I2S mic    ──WiFi WS──>    FastAPI backend (main.py)
  SSD1306 OLED display               faster-whisper STT
  NeoPixel LED ring                  Claude claude-sonnet-4-6 (brain.py)
  Push button (GPIO 0)               SQLite: transcripts + memories
  LiPo battery                       Piper / ElevenLabs TTS
                     <──WiFi WS──    Bluetooth → AirPods
                                     Screen: web dashboard
```

**Data flow:**
1. User holds button → ESP32 streams raw PCM (16kHz mono) over WebSocket
2. Button released → ESP32 sends `{"event":"end_of_speech"}`
3. Pi 5 transcribes with faster-whisper
4. Transcript → Claude with full tool suite + memory context
5. Claude responds (using tools if needed)
6. Piper/ElevenLabs synthesises speech → plays through AirPods

---

## File Map

```
aria/
├── firmware/aria_esp32/
│   ├── aria_esp32.ino     Main firmware: WiFi, WebSocket, button, state machine
│   ├── audio_stream.h     I2S capture (INMP441), PCM streaming
│   ├── display.h          SSD1306 OLED animations (idle/listening/thinking/speaking)
│   └── leds.h             NeoPixel ring state machine (FastLED)
│
├── backend/
│   ├── main.py            FastAPI server, WebSocket handlers, orchestration
│   ├── brain.py           Claude agentic loop with tool use
│   ├── transcriber.py     faster-whisper pipeline (bytes → text)
│   ├── memory.py          Background memory extraction + context builder
│   ├── tools.py           Tool implementations + schemas for Claude
│   ├── tts.py             Piper TTS + ElevenLabs voice clone
│   ├── db.py              SQLite CRUD: transcripts, memories, conversations
│   ├── config.py          All config via env vars
│   └── requirements.txt   Python deps
│
├── frontend/
│   ├── index.html         Dashboard UI (dark, fullscreen on Pi)
│   └── app.js             WebSocket client, live transcript, chat, waveform
│
├── docs/
│   ├── setup.md           Full setup guide (Pi 5 + Arduino + voice clone)
│   ├── hardware.md        Wiring diagrams + parts list
│   └── demo.md            Demo script + judge Q&A
│
├── .env.example           Config template — copy to .env
└── CLAUDE.md              This file
```

---

## Claude Tools Available

| Tool | What it does |
|---|---|
| `search_web` | Brave Search or DuckDuckGo web search |
| `save_memory` | Store a key/value fact about the user permanently |
| `query_memories` | Retrieve relevant memories by text match |
| `get_transcript` | Get last N minutes of ambient transcript |
| `set_reminder` | Store a reminder |
| `get_datetime` | Current date and time |

All implemented in `backend/tools.py`. Schemas in `TOOL_SCHEMAS`. Dispatch map in `TOOL_MAP`.

---

## Key Config (.env)

```
ANTHROPIC_API_KEY=...          # Required
ELEVENLABS_API_KEY=...         # For voice cloning
ELEVENLABS_VOICE_ID=...        # Set after running clone_voice()
BRAVE_API_KEY=...              # Optional better search
USER_NAME=...                  # The wearer's name
WHISPER_MODEL=tiny.en          # tiny.en = fastest on Pi 5 CPU
```

---

## Running It

```bash
# On Pi 5:
cd backend && source .venv/bin/activate && python main.py
# Dashboard: http://localhost:8000

# ESP32: flash firmware/aria_esp32/aria_esp32.ino via Arduino IDE
# Set Pi hotspot first: sudo nmcli device wifi hotspot ssid ARIA-BASE password aria1234
```

---

## Known Gotchas

- **Pi 5 hotspot IP is `10.42.0.1`** — this is hardcoded in `aria_esp32.ino`. Change if needed.
- **NeoPixels need 5V** — power from USB pin, not 3.3V pin
- **INMP441 L/R pin must be pulled to GND** for left channel
- **AirPods Bluetooth**: pair manually once with `bluetoothctl`, then they auto-reconnect
- **Whisper** downloads model on first run — needs internet for that one-time download
- **ElevenLabs voice cloning**: run `from tts import clone_voice; clone_voice('sample.wav')` to get voice_id

---

## Hardware Wiring Quick Reference

```
INMP441 SCK  → ESP32 GPIO 26
INMP441 WS   → ESP32 GPIO 25
INMP441 SD   → ESP32 GPIO 34
INMP441 L/R  → GND
OLED SDA     → ESP32 GPIO 21
OLED SCL     → ESP32 GPIO 22
NeoPixel DIN → ESP32 GPIO 5
Button       → GPIO 0 (boot button — already on board)
```

---

## What Still Needs Doing (as of project start)

- [ ] Flash ESP32 and test I2S audio capture
- [ ] Test WebSocket audio streaming to Pi
- [ ] Confirm faster-whisper transcription quality in noisy room
- [ ] Pair AirPods to Pi 5 Bluetooth
- [ ] Record voice sample + run ElevenLabs clone
- [ ] Set ELEVENLABS_VOICE_ID in .env
- [ ] 3D print / build pendant enclosure
- [ ] Test full end-to-end: button → voice → response in AirPods
- [ ] Load ambient transcript pre-data for demo
- [ ] Rehearse demo script 3x
