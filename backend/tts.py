"""
Text-to-speech module.
Priority: ElevenLabs (voice clone) → Piper (fast, offline)
"""
import subprocess
import tempfile
import os
from pathlib import Path
from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

# Piper model path — download at setup time
PIPER_MODEL = Path(__file__).parent / "piper_models" / "en_US-lessac-medium.onnx"


def speak(text: str) -> None:
    """Synthesise and play text. Blocks until playback done."""
    if not text.strip():
        return
    if ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID:
        _speak_elevenlabs(text)
    else:
        _speak_piper(text)


def _speak_elevenlabs(text: str) -> None:
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import play
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        audio = client.generate(
            text=text,
            voice=ELEVENLABS_VOICE_ID,
            model="eleven_turbo_v2",
        )
        play(audio)
    except Exception as e:
        print(f"ElevenLabs TTS failed ({e}), falling back to Piper")
        _speak_piper(text)


def _speak_piper(text: str) -> None:
    """Use Piper for fast offline TTS."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name

        if PIPER_MODEL.exists():
            subprocess.run(
                ["piper", "--model", str(PIPER_MODEL), "--output_file", wav_path],
                input=text.encode(),
                check=True,
                timeout=15,
            )
        else:
            # Fallback: espeak if piper not installed
            subprocess.run(
                ["espeak", "-w", wav_path, text],
                check=True, timeout=10,
            )

        # Play — aplay works on Pi 5 and routes through PulseAudio to AirPods
        subprocess.run(["aplay", wav_path], check=True, timeout=30)

    except FileNotFoundError:
        # Last resort: espeak direct
        subprocess.run(["espeak", text], timeout=10)
    except Exception as e:
        print(f"TTS error: {e}")
    finally:
        try:
            os.unlink(wav_path)
        except Exception:
            pass


def clone_voice(audio_path: str, name: str = "ARIA") -> str | None:
    """
    Upload audio file to ElevenLabs and return voice_id.
    Call once, then set ELEVENLABS_VOICE_ID in .env
    """
    if not ELEVENLABS_API_KEY:
        print("No ElevenLabs API key set")
        return None
    try:
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        with open(audio_path, "rb") as f:
            voice = client.voices.add(
                name=name,
                files=[f],
                description="ARIA voice clone",
            )
        print(f"Voice cloned! Voice ID: {voice.voice_id}")
        print(f"Add to .env: ELEVENLABS_VOICE_ID={voice.voice_id}")
        return voice.voice_id
    except Exception as e:
        print(f"Voice cloning failed: {e}")
        return None
