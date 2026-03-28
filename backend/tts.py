"""
Text-to-speech: ElevenLabs (voice clone) → espeak fallback.
Uses ElevenLabs SDK v1 API correctly for Raspberry Pi 5.
"""
import subprocess
import tempfile
import os
from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID


def speak(text: str) -> None:
    if not text.strip():
        return
    if ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID:
        _speak_elevenlabs(text)
    else:
        _speak_espeak(text)


def _speak_elevenlabs(text: str) -> None:
    try:
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

        # SDK v1: text_to_speech.convert returns a generator of bytes chunks
        audio_stream = client.text_to_speech.convert(
            text=text,
            voice_id=ELEVENLABS_VOICE_ID,
            model_id="eleven_turbo_v2_5",
            output_format="mp3_44100_128",
        )
        audio_bytes = b"".join(audio_stream)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_bytes)
            path = f.name

        # mpg123 is lightweight and available on Pi OS; ffplay works too
        played = False
        for player in [["mpg123", "-q", path], ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path]]:
            try:
                subprocess.run(player, check=True, timeout=30)
                played = True
                break
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue

        if not played:
            _speak_espeak(text)

        os.unlink(path)

    except Exception as e:
        print(f"ElevenLabs TTS failed: {e} — falling back to espeak")
        _speak_espeak(text)


def _speak_espeak(text: str) -> None:
    # Try multiple espeak locations (Windows installs vary)
    candidates = [
        ["espeak", "-s", "150", text],
        [r"C:\Program Files\eSpeak NG\espeak-ng.exe", "-s", "150", text],
        [r"C:\Program Files (x86)\eSpeak\command_line\espeak.exe", "-s", "150", text],
    ]
    for cmd in candidates:
        try:
            subprocess.run(cmd, timeout=15, check=True)
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    # Last resort: Windows built-in TTS via PowerShell
    try:
        ps = f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{text}")'
        subprocess.run(["powershell", "-Command", ps], timeout=15)
    except Exception as e:
        print(f"TTS completely failed: {e}")


def clone_voice(audio_path: str, name: str = "ARIA") -> str | None:
    """Record 60s of yourself talking, pass the file path here. Prints voice_id to add to .env."""
    if not ELEVENLABS_API_KEY:
        print("Set ELEVENLABS_API_KEY in .env first")
        return None
    try:
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        with open(audio_path, "rb") as f:
            voice = client.voices.add(name=name, files=[f])
        print(f"\nVoice cloned!")
        print(f"Add to .env:  ELEVENLABS_VOICE_ID={voice.voice_id}\n")
        return voice.voice_id
    except Exception as e:
        print(f"Voice cloning failed: {e}")
        return None
