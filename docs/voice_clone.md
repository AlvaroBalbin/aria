# How to Clone Your Voice for ARIA

## Step 1 — Record your voice sample

You need 60 seconds of yourself speaking naturally. Quality matters more than length.

**On your phone:**
- iPhone: Voice Memos app → record → AirDrop to laptop
- Android: Voice Recorder app → record → transfer via cable/email

**What to say (read this aloud naturally):**
> "Hi, my name is Alvaro and I'm building ARIA at Bath Hackathon. ARIA is a wearable AI personal assistant that learns who you are and remembers your life. I wear it as a pendant around my neck. When I press the button, it listens to my question and responds through my AirPods in real time. The system uses OpenAI to transcribe my voice, GPT-4 to think and take actions, and ElevenLabs to speak back. It can search the web, remember facts about me, check what I've been talking about, and even look up what's trending on X. I've been building this for the last 24 hours and I genuinely think it's one of the most impressive projects at this hackathon. The pendant glows blue when idle, purple when it's listening, white when it's thinking, and green when it speaks."

That's about 90 seconds. Pick the best 60 seconds or just use it all.

**Save the file as:** `voice_sample.wav` or `voice_sample.mp3`

---

## Step 2 — Copy the file to the Raspberry Pi 5

**Via USB stick:**
```bash
cp voice_sample.wav /media/usb/voice_sample.wav
# then on Pi: cp /media/usb/voice_sample.wav ~/aria/voice_sample.wav
```

**Via SSH (if on same network):**
```bash
scp voice_sample.wav pi@10.42.0.1:~/aria/voice_sample.wav
```

**Via AirDrop to your laptop then scp — whatever is fastest.**

---

## Step 3 — Run the voice clone script

On the **Raspberry Pi 5**, in the `aria/backend` directory:

```bash
cd ~/aria/backend
source .venv/bin/activate
python3 -c "
from tts import clone_voice
clone_voice('../voice_sample.wav', name='Alvaro-ARIA')
"
```

It will print something like:
```
Voice cloned!
Add to .env:  ELEVENLABS_VOICE_ID=abc123xyz456...
```

---

## Step 4 — Add the voice ID to .env

Open `.env` on the Pi and fill in:
```
ELEVENLABS_VOICE_ID=abc123xyz456...
```

Then restart the backend:
```bash
python main.py
```

---

## Step 5 — Test it

In the dashboard chat box, type anything. ARIA should respond in your voice.

If it sounds wrong or robotic — record a longer sample (2 minutes) with more varied speech (questions, exclamations, normal sentences). ElevenLabs gets dramatically better with more variety.

---

## Troubleshooting

**"Voice cloning failed: 422"** — file format issue. Convert to wav:
```bash
ffmpeg -i voice_sample.mp3 -ar 44100 voice_sample.wav
```

**Audio plays but wrong voice** — check `ELEVENLABS_VOICE_ID` is set correctly in `.env` and backend was restarted.

**No audio at all** — check AirPods are connected: `pactl list sinks short` should show a bluez sink.
