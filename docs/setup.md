# ARIA Setup Guide

## Raspberry Pi 5 — First-time setup

### 1. OS + system deps
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git espeak ffmpeg
```

### 2. Piper TTS (fast offline voice)
```bash
pip install piper-tts
mkdir -p backend/piper_models && cd backend/piper_models
# Download the model (en_US-lessac-medium is good quality + speed)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
cd ../..
```

### 3. Python environment
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
> Whisper `tiny.en` model downloads automatically on first run (~75MB).

### 4. Environment config
```bash
cp .env.example .env
nano .env   # fill in ANTHROPIC_API_KEY and USER_NAME at minimum
```

### 5. WiFi hotspot (so ESP32 connects directly to Pi — no hackathon WiFi needed)
```bash
# NetworkManager method (default on Pi OS Bookworm)
sudo nmcli device wifi hotspot ssid ARIA-BASE password aria1234 ifname wlan0
# Pi IP on hotspot: 10.42.0.1
# This survives reboots if you add --save
```

### 6. Bluetooth AirPods pairing
```bash
sudo bluetoothctl
  power on
  agent on
  scan on
  # Wait to see your AirPods appear (e.g. "AA:BB:CC:DD:EE:FF AirPods Pro")
  pair AA:BB:CC:DD:EE:FF
  connect AA:BB:CC:DD:EE:FF
  trust AA:BB:CC:DD:EE:FF
  exit

# Set as default audio output (replace MAC with yours)
pactl set-default-sink bluez_sink.AA_BB_CC_DD_EE_FF.a2dp_sink
# Test it works:
espeak "ARIA is ready"
```

### 7. Run the backend
```bash
cd backend
source .venv/bin/activate
python main.py
# Server starts on http://10.42.0.1:8000
# Dashboard: open Chromium on Pi → http://localhost:8000 (fullscreen F11)
```

---

## Voice Cloning with ElevenLabs

1. Record 60 seconds of yourself speaking naturally (any topic, vary sentences)
2. Save as `voice_sample.wav` or `.mp3`
3. Run:
```python
# In the backend directory with venv activated:
python3 -c "
from tts import clone_voice
clone_voice('voice_sample.wav', name='ARIA')
"
```
4. Copy the printed `voice_id` into `.env` as `ELEVENLABS_VOICE_ID=...`
5. Restart the backend

---

## ESP32 Arduino Setup

### Libraries to install (Arduino Library Manager):
- `WebSockets` by Markus Sattler
- `FastLED`
- `Adafruit GFX Library`
- `Adafruit SSD1306`
- `ArduinoJson`

### Board: ESP32 Dev Module (or ESP32-S3)
- Board manager URL: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`

### Wiring
See `docs/hardware.md` for full wiring diagram.

### Flash
1. Open `firmware/aria_esp32/aria_esp32.ino` in Arduino IDE
2. Edit the WiFi IP at top if needed (default `10.42.0.1` works with Pi hotspot)
3. Select board: `ESP32 Dev Module`
4. Upload at 921600 baud

---

## Quick test (no pendant)

If you haven't wired the ESP32 yet, you can test the full AI pipeline via the dashboard:
1. Start backend: `python main.py`
2. Open `http://localhost:8000` in browser
3. Type in the chat box — ARIA responds with voice through speakers/AirPods
