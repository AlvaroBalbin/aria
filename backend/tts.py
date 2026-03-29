"""
Text-to-speech: ElevenLabs → OpenAI TTS → espeak fallback.
"""
import subprocess
import tempfile
import os
import openai
from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

oai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


def speak(text: str) -> None:
    if not text.strip():
        return
    if ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID:
        _speak_elevenlabs(text)
    elif os.getenv("OPENAI_API_KEY"):
        _speak_openai(text)
    else:
        _speak_espeak(text)


def _speak_openai(text: str) -> None:
    """OpenAI TTS — high quality, low latency."""
    try:
        response = oai_client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text,
            response_format="mp3",
            speed=1.05,
        )
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            response.stream_to_file(f.name)
            path = f.name

        _play_audio(path)
        os.unlink(path)
    except Exception as e:
        print(f"OpenAI TTS failed: {e} — falling back to espeak")
        _speak_espeak(text)


def _speak_elevenlabs(text: str) -> None:
    try:
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

        audio_stream = client.text_to_speech.convert(
            text=text,
            voice_id=ELEVENLABS_VOICE_ID,
            model_id="eleven_flash_v2_5",
            output_format="mp3_44100_128",
        )
        audio_bytes = b"".join(audio_stream)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_bytes)
            path = f.name

        _play_audio(path)
        os.unlink(path)

    except Exception as e:
        print(f"ElevenLabs TTS failed: {e} — trying OpenAI TTS")
        _speak_openai(text)


def _play_audio(path: str) -> None:
    """Play an audio file through the default output (AirPods)."""
    for player in [
        ["mpg123", "-q", path],
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
    ]:
        try:
            subprocess.run(player, check=True, timeout=30)
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    _speak_espeak("audio playback failed")


def _speak_espeak(text: str) -> None:
    try:
        subprocess.run(["espeak", "-s", "150", text], timeout=15, check=True)
    except Exception as e:
        print(f"TTS completely failed: {e}")


def clone_voice(audio_path: str, name: str = "ARIA") -> str | None:
    """Record 60s of yourself talking, pass the file path here."""
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
