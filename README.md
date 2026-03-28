# ARIA — Wearable AI Personal Assistant

> *The AI you wear. It knows you. It remembers everything. It takes real actions.*

Built at **Bath Hackathon 2026** in 24 hours.

---

## What is it?

A circular pendant you wear around your neck. Hold the button and speak. ARIA responds through your AirPods — powered by Claude, running on a Raspberry Pi 5.

It remembers your day. It searches the web. It learns who you are over time.

**£30 in hardware. No subscription. Your data stays on your own device.**

---

## Demo

1. Wear the pendant
2. Hold the button: *"ARIA, what have I been working on today?"*
3. ARIA answers from your ambient transcript — in your own cloned voice

---

## Tech Stack

| Layer | Tech |
|---|---|
| Pendant MCU | ESP32 + INMP441 I2S mic + SSD1306 OLED + NeoPixel ring |
| Speech-to-text | faster-whisper (tiny.en, runs on Pi 5 CPU) |
| AI Brain | Claude claude-sonnet-4-6 with agentic tool use |
| Memory | SQLite + Claude extraction — grows over time |
| Text-to-speech | Piper (offline) / ElevenLabs voice clone |
| Audio output | Bluetooth AirPods via Pi 5 |
| Dashboard | FastAPI + vanilla JS, served from Pi 5 |

---

## Quick Start

See [docs/setup.md](docs/setup.md) for full setup instructions.

```bash
# Pi 5
cd backend && pip install -r requirements.txt
cp .env.example .env  # add your ANTHROPIC_API_KEY
python main.py

# Dashboard: http://10.42.0.1:8000
```

---

## Why We Built This

Humane AI Pin raised $230M and failed. Rabbit raised $180M. Tab AI, Plaud, Limitless — all funded, none nailed it.

We think we know why: they built hardware looking for a use case. We built the use case first.

ARIA is what all of them were trying to be — open source, private, affordable, and genuinely useful.

---

## Track Submissions

- **Most Technically Impressive** — Distributed edge AI pipeline: ESP32 → Pi 5 Whisper → Claude agentic tool use → ElevenLabs voice clone → Bluetooth AirPods
- **Best Use of AI** — Claude embedded at every layer: transcription, agentic Q&A, memory extraction, tool use
- **Most Commercially Viable** — £30 open-source hardware competing with $230M funded products
- **Embedded (XMOS)** — ESP32 edge compute: I2S audio, wake detection, WiFi streaming, display rendering
- **Hackers' Choice** — It knows your name. It remembers your day. It sounds like you.
