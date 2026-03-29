# ARIA - Your Wearable AI That Actually Works

> **Plug it in. Connect to any network. Hold the button and speak. Get answers in your AirPods - in your own cloned voice. Anywhere.**

Built in 24 hours at **Bath Hack 2026**. A wearable AI assistant that knows you, remembers your entire day, searches the web in real time, manages your calendar, and takes real actions - all running on a Raspberry Pi 5 you own.

**Works on any WiFi, any network, anywhere you go. The Pi creates its own hotspot - the wearable auto-connects. Tether your phone, plug into hotel WiFi, use campus ethernet. ARIA just works.**

**Total hardware cost: ~$30. No subscription. All data stays on your device.**

![ARIA Device](https://img.shields.io/badge/ESP32-Wearable-blue) ![Python](https://img.shields.io/badge/Python-3.11-green) ![OpenAI](https://img.shields.io/badge/GPT--5.2-Agentic-orange) ![License](https://img.shields.io/badge/License-MIT-yellow)

---

## The Problem

Humane AI Pin raised **$230M** and failed. Rabbit raised **$180M**. Tab AI, Plaud, Limitless - all funded, none delivered.

They built expensive hardware looking for a use case. We built the use case first - then wrapped it in a $30 box you can 3D-print at home.

**ARIA is what all of them were trying to be: open-source, private, affordable, and genuinely useful.**

---

## How It Works

```
You press the button and speak
             |
   [ESP32 Wearable]                 [Raspberry Pi 5 Base Station]
    Button + LEDs       --WiFi-->    FastAPI orchestration server
    TFT Display         <--WiFi--    OpenAI Realtime voice-to-voice
    State machine                    GPT-5.2 agentic brain (10 tools)
    Auto-connects to                 ElevenLabs voice clone TTS
    Pi's hotspot on                  SQLite: memories, calendar, transcripts
    any network                      Bluetooth --> AirPods
                                            |
                                      You hear ARIA respond
                                      in your own cloned voice
```

> The Pi 5 creates its own WiFi hotspot (`ARIA-BASE`). The wearable auto-connects to it. Give the Pi any internet connection - phone hotspot, campus WiFi, ethernet cable - and the whole system is live in seconds. No setup, no configuration, no router needed.

### The Full Pipeline

1. **Press the button** on the wearable box
2. **Speak naturally** - OpenAI Realtime API streams your voice at 24kHz with server-side VAD
3. **GPT-5.2 reasons** using an agentic tool loop (up to 6 chained tool calls per query)
4. **ARIA responds** through your AirPods in your own cloned voice via ElevenLabs
5. **The display updates** with ARIA's response, LEDs shift color to match state
6. **Memories persist** - ARIA learns about you over time, automatically extracting facts from ambient conversation

---

## What ARIA Can Actually Do

| Capability | How |
|---|---|
| Answer any question | GPT-5.2 agentic reasoning with web search |
| Search the web in real time | Brave Search API + DuckDuckGo fallback |
| Search X/Twitter | Live tweet search via Tweepy API |
| Remember facts about you | Automatic memory extraction from ambient audio every 15 minutes |
| Recall what you said today | Full ambient transcript with retrieval by time range |
| Manage your calendar | Add, list, delete events with natural language |
| Set reminders | Time-based notifications spoken through AirPods |
| Speak in your voice | 60-second voice sample trains an ElevenLabs voice clone |
| Listen 24/7 (opt-in) | Ambient mode with "ARIA" wake word detection |
| Show responses on-device | Word-wrapped text rendering on the TFT display |

### 10 Agentic Tools

The AI doesn't just chat - it **acts**. Each query can trigger up to 6 chained tool calls:

```
You: "What's happening in F1 this weekend and add the race to my calendar?"

ARIA internally:
  1. search_web("F1 race schedule March 2026")
  2. add_calendar_event(title="F1 Australian GP", start="2026-03-29T14:00")
  3. Responds: "The Australian GP is Sunday at 2pm. I've added it to your calendar."
```

Tools: `search_web` | `search_x` | `save_memory` | `query_memories` | `get_transcript` | `set_reminder` | `get_datetime` | `add_calendar_event` | `list_calendar_events` | `delete_calendar_event`

---

## Architecture

### Three-Layer Distributed System

```
Layer 1: WEARABLE (ESP32)          Layer 2: EDGE AI (Raspberry Pi 5)       Layer 3: DASHBOARD (Browser)
+-----------------------+          +--------------------------------+       +------------------------+
| ST7789 TFT Display    |          | FastAPI Server                 |       | Live Transcript Feed   |
| 4x RGB PWM LEDs       |  WiFi   | OpenAI Realtime WebSocket      | WiFi  | Conversation History   |
| Push Button (GPIO 0)  | <-----> | GPT-5.2 Agentic Brain          |<----->| Tool Activity Log      |
| WiFi State Machine    |   WS    | ElevenLabs/OpenAI/espeak TTS   |  WS   | Memory Display         |
| WebSocket Client      |          | Whisper STT (fallback)         |       | Waveform Visualizer    |
+-----------------------+          | SQLite (5 tables)              |       | Voice/Text Chat Input  |
                                   | Bluetooth Audio (AirPods)      |       +------------------------+
                                   +--------------------------------+
```

### 3 WebSocket Channels

| Endpoint | Purpose |
|---|---|
| `/ws/pendant` | Bidirectional state sync + text display with keepalive pings |
| `/ws/audio` | Raw PCM audio streaming from ESP32 mic |
| `/ws/dashboard` | Live broadcast of transcripts, tool use, state changes to all connected browsers |

### 7 External APIs Integrated

1. **OpenAI Realtime API** - Voice-to-voice at 24kHz, server-side VAD, persistent sessions
2. **OpenAI GPT-5.2** - Agentic brain with tool use (6 iteration loop)
3. **OpenAI Whisper** - Speech-to-text (fallback + ambient transcription)
4. **OpenAI TTS** - Text-to-speech (secondary fallback)
5. **ElevenLabs Flash v2.5** - Primary TTS with voice cloning
6. **Brave Search API** - Real-time web search (DuckDuckGo fallback)
7. **Twitter/X API v2** - Real-time social media search via Tweepy

### Graceful Degradation

Every component has fallbacks. If one API goes down, ARIA keeps working:

```
Voice I/O:    OpenAI Realtime --> Whisper + GPT + ElevenLabs --> Whisper + GPT + OpenAI TTS --> espeak
Web Search:   Brave API --> DuckDuckGo (free, no API key needed)
Audio Play:   mpg123 --> ffplay --> espeak direct
Wearable:     WiFi drops --> state/text queued, delivered on reconnect
Network:      Pi hotspot auto-creates local mesh --> any internet source works (phone, ethernet, WiFi)
```

---

## Hardware

### Wearable Device

- **MCU**: ESP32 (WiFi + Bluetooth)
- **Display**: ST7789 240x320 TFT (SPI) - shows ARIA's responses with word-wrapping
- **LEDs**: 4x RGB LEDs with PWM sine-wave animations
  - Blue breathing = Idle
  - Green pulsing = Listening
  - Yellow rapid = Processing
  - Magenta + green = Speaking
- **Button**: GPIO 0 (boot button) - press to start/stop conversation
- **Enclosure**: Custom 3D-printed box (Autodesk Inventor, `.ipt` files included)
- **Audio**: AirPods handle mic input + audio output via Pi 5 Bluetooth

### Base Station

- **Raspberry Pi 5** running Raspberry Pi OS
- **Bluetooth**: Paired to AirPods for audio I/O
- **WiFi**: Self-hosted hotspot (`ARIA-BASE`) - ESP32 auto-connects, works on any network
- **Storage**: SQLite database for memories, transcripts, calendar, reminders

### Bill of Materials

| Part | Cost |
|---|---|
| ESP32 DevKit | ~$5 |
| ST7789 TFT Display | ~$5 |
| 4x RGB LEDs + resistors | ~$2 |
| Push button + wiring | ~$1 |
| 3D-printed enclosure | ~$3 |
| Raspberry Pi 5 (base station) | ~$60 (one-time, shared) |
| **Wearable total** | **~$16** |

---

## The Dashboard

Real-time web interface served from the Pi 5 at `http://<pi-ip>:8000`.

**Features:**
- Live animated waveform that changes color/amplitude by state
- Real-time transcript feed (User, ARIA, Ambient speakers)
- Full conversation history with tool use activity log
- Memory viewer showing what ARIA has learned about you
- Text and voice chat input (Web Speech API)
- All updates pushed via WebSocket - zero polling

---

## Memory System

ARIA doesn't just answer questions - it **learns who you are**.

### How It Works

1. **Ambient listening** captures continuous 5-second audio chunks
2. Every **15 minutes**, GPT-5.2 extracts 3-5 key facts from the ambient transcript
3. Facts stored as key-value pairs in SQLite (`"favorite_drink" -> "oat milk latte"`)
4. Top 25 memories injected into every system prompt
5. ARIA's responses become increasingly personalized over time

### Example

```
Day 1: "What's my name?"        --> "I don't know yet!"
Day 1: (ambient) "...yeah I'm Alvaro, studying CS at Bath..."
Day 2: "What's my name?"        --> "You're Alvaro! How's the CS coursework going?"
```

---

## Commercial Viability

### Market Validation

- **60+ people** on our waitlist within 24 hours of announcing
- **100+ B2B prospects** reached via LinkedIn outreach
- Direct interest from professionals wanting ambient AI for meetings, sales calls, and note-taking

### The Market

| Competitor | Funding | Status | Our Advantage |
|---|---|---|---|
| Humane AI Pin | $230M | Failed, recalled | We cost $30, not $700 |
| Rabbit R1 | $180M | Underwhelming reviews | We use real AI, not scripted demos |
| Tab AI | $2M | Early stage | We're open-source, they're closed |
| Limitless | $25M | $99 device, $19/mo | We have no subscription |

### Business Model

| Revenue Stream | Price Point |
|---|---|
| ARIA Kit (ESP32 + enclosure + Pi setup guide) | $149 one-time |
| ARIA Pro SaaS (cloud hosting, premium voices, integrations) | $9/month |
| Enterprise API (meeting intelligence, sales coaching) | Custom pricing |
| Open-source (self-hosted, free forever) | $0 |

### Unit Economics

- **BOM cost**: ~$16 (wearable only)
- **Retail price**: $149 (kit with setup guide)
- **Gross margin**: ~89%
- **No recurring cloud costs** for self-hosted users (runs on your own Pi)

---

## Quick Start

### Prerequisites

- Raspberry Pi 5 (or any Linux machine)
- ESP32 DevKit + ST7789 display + LEDs
- AirPods or any Bluetooth headphones
- OpenAI API key

### Setup

```bash
# Clone the repo
git clone https://github.com/AlvaroBalbin/aria.git
cd aria

# Backend (on Pi 5)
cd backend
pip install -r requirements.txt
cp .env.example .env    # Add your API keys
python main.py          # Starts on http://0.0.0.0:8000

# ESP32: Flash firmware/aria_esp32/aria_esp32.ino via Arduino IDE
# Set WiFi credentials in the sketch to match your Pi's hotspot
```

### Environment Variables

```env
OPENAI_API_KEY=...          # Required - powers GPT-5.2, Whisper, Realtime
ELEVENLABS_API_KEY=...      # Optional - voice cloning TTS
ELEVENLABS_VOICE_ID=...     # Set after cloning your voice
BRAVE_API_KEY=...           # Optional - web search (DuckDuckGo fallback)
TWITTER_BEARER_TOKEN=...    # Optional - X/Twitter search
USER_NAME=...               # Your name for personalization
```

---

## File Structure

```
aria/
 backend/
   main.py              FastAPI server, 3 WebSocket endpoints, session management
   brain.py              GPT-5.2 agentic loop with 10 tools, 6-iteration depth
   tools.py              Tool implementations (web, social, calendar, memory)
   realtime.py           OpenAI Realtime API - bidirectional voice streaming
   memory.py             Automatic fact extraction from ambient audio
   transcriber.py        Whisper STT + hallucination filtering
   tts.py                3-tier TTS: ElevenLabs -> OpenAI -> espeak
   db.py                 SQLite schema (5 tables)
   config.py             Environment variable loading
   requirements.txt      Python dependencies

 firmware/aria_esp32/
   aria_esp32.ino        Main firmware: WiFi, WebSocket, button state machine
   display.h             ST7789 TFT driver with word-wrap text rendering
   leds.h                PWM LED animations (sine-wave breathing/pulsing)
   audio_stream.h        Audio streaming interface

 frontend/
   index.html            Dark-themed dashboard UI
   app.js                WebSocket client, waveform animation, Web Speech API

 BackPlate.ipt           3D model - back plate (Autodesk Inventor)
 MainBody.ipt            3D model - main enclosure body (Autodesk Inventor)
```

---

## Prize Track Justification

### Most Technically Impressive

Built a **complete distributed edge AI system in 24 hours** spanning 3 hardware layers, 3 WebSocket channels, 7 API integrations, a 10-tool agentic reasoning loop, real-time voice-to-voice streaming, automatic memory extraction, and graceful multi-level fallbacks. The system handles wearable disconnection, API failures, and network drops without losing conversation state.

### Best Use of AI

AI isn't a bolt-on feature - it's the entire product. **GPT-5.2** powers an agentic brain that chains up to 6 tool calls per query. **OpenAI Realtime API** enables sub-second voice-to-voice. **Whisper** transcribes ambient audio 24/7. **ElevenLabs** clones your actual voice. **GPT-5.2** automatically extracts memories from ambient conversation every 15 minutes. Five distinct AI systems working together as one seamless experience.

### Best Use of Embedded Systems

The ESP32 wearable runs a **real-time state machine** synced over WebSocket to the Pi 5. It drives a TFT display with word-wrapped text rendering, 4 PWM-animated RGB LEDs with sine-wave breathing patterns, and handles WiFi reconnection with queued state delivery. The Raspberry Pi 5 serves as an **edge AI server** running STT, LLM inference, TTS, and Bluetooth audio - no cloud compute required for the core pipeline.

### Most Commercially Viable

- **60+ waitlist signups** and **100+ B2B LinkedIn prospects** reached during the hackathon
- **$16 BOM, $149 retail = 89% gross margin**
- Direct competitors have raised **$435M combined** and failed to deliver what we built in 24 hours
- **Zero-config portability**: plug the Pi into any network anywhere and the whole system is live - no IT setup, no router config, no app install
- Clear B2B expansion: meeting intelligence, sales coaching, accessibility tools
- Open-source core drives adoption; SaaS tier ($9/mo) drives revenue
- Privacy-first positioning (all data on-device) is a genuine differentiator in a post-GDPR market

### Hackers' Choice

Picture this: you walk up to our table. You see a glowing box. Someone presses a button and asks "What have we been talking about for the last 10 minutes?" And ARIA answers - accurately - because it's been listening. Then it responds **in the speaker's own cloned voice**. That's the moment.

### Best Overall

ARIA combines a custom 3D-printed wearable, a distributed three-layer architecture, 7 API integrations, 10 agentic tools, real-time voice cloning, persistent memory, ambient intelligence, a live dashboard, and a validated commercial model with 60+ waitlist signups - all built from scratch in 24 hours by a small team. Plug it into any network and it just works. You can try it right now.

---

## Team

Built at **Bath Hack 2026** (March 29-30, 2026).

---

## License

MIT - Use it, fork it, build on it. The future of personal AI should be open.
