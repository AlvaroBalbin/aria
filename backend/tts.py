"""
Text-to-speech: ElevenLabs (voice clone) with browser audio return.
"""
import io
import os
import re
import subprocess
import tempfile
from pathlib import Path
from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

# Runtime voice ID — can be updated without restart
_active_voice_id: str = ELEVENLABS_VOICE_ID


def get_active_voice_id() -> str:
    return _active_voice_id


TTS_CHAR_LIMIT = 200


def synthesize(text: str) -> bytes | None:
    """Generate TTS audio as MP3 bytes. Returns None if TTS unavailable."""
    if not text.strip():
        return None
    if not ELEVENLABS_API_KEY or not _active_voice_id:
        return None
    # Truncate to save credits — cut at last sentence boundary within limit
    if len(text) > TTS_CHAR_LIMIT:
        truncated = text[:TTS_CHAR_LIMIT]
        for sep in ['. ', '! ', '? ']:
            idx = truncated.rfind(sep)
            if idx > 0:
                truncated = truncated[:idx + 1]
                break
        text = truncated
    try:
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        audio_stream = client.text_to_speech.convert(
            text=text,
            voice_id=_active_voice_id,
            model_id="eleven_turbo_v2_5",
            output_format="mp3_44100_128",
        )
        return b"".join(audio_stream)
    except Exception as e:
        print(f"ElevenLabs synthesize failed: {e}")
        return None


def speak(text: str) -> None:
    """Synthesize and play audio locally (legacy, for pendant mode)."""
    if not text.strip():
        return
    audio = synthesize(text)
    if audio:
        _play_mp3_bytes(audio)
    else:
        _speak_piper(text)


def _play_mp3_bytes(audio: bytes) -> None:
    """Write MP3 bytes to temp file and play via available player."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio)
        path = f.name
    try:
        for player in [
            ["mpg123", "-q", path],
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
        ]:
            try:
                subprocess.run(player, check=True, timeout=30)
                return
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue
    finally:
        os.unlink(path)


def _speak_piper(text: str) -> None:
    model_path = Path(__file__).parent / "piper_models" / "en_US-lessac-medium.onnx"
    if not model_path.exists():
        _speak_espeak(text)
        return

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
        
    try:
        process = subprocess.Popen(
            ["piper", "--model", str(model_path), "--output_file", path],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        process.communicate(input=text.encode("utf-8"), timeout=15)
        
        # Play WAV
        for player in [
            ["aplay", path],
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
        ]:
            try:
                subprocess.run(player, check=True, timeout=30)
                return
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue
    except Exception as e:
        print(f"Piper TTS failed: {e}")
        _speak_espeak(text)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def _speak_espeak(text: str) -> None:
    try:
        subprocess.run(["espeak", "-s", "150", text], timeout=15)
    except Exception as e:
        print(f"espeak failed: {e}")


def clone_voice(audio_bytes: bytes, name: str = "ARIA", file_ext: str = ".webm") -> str | None:
    """Clone a voice from audio bytes. Returns voice_id or None."""
    global _active_voice_id
    if not ELEVENLABS_API_KEY:
        return None
    try:
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = f"voice_sample{file_ext}"
        voice = client.voices.add(name=name, files=[audio_file])
        new_id = voice.voice_id
        _active_voice_id = new_id
        _update_env_voice_id(new_id)
        print(f"Voice cloned! ID: {new_id}")
        return new_id
    except Exception as e:
        print(f"Voice cloning failed: {e}")
        return None


def _update_env_voice_id(voice_id: str) -> None:
    """Write voice_id to .env file for persistence across restarts."""
    env_path = Path(__file__).parent / ".env"
    try:
        if env_path.exists():
            content = env_path.read_text()
            if "ELEVENLABS_VOICE_ID=" in content:
                content = re.sub(r"ELEVENLABS_VOICE_ID=.*", f"ELEVENLABS_VOICE_ID={voice_id}", content)
            else:
                content += f"\nELEVENLABS_VOICE_ID={voice_id}\n"
            env_path.write_text(content)
    except Exception as e:
        print(f"Could not update .env: {e}")
