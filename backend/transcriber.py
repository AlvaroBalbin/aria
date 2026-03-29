"""
Speech-to-text using OpenAI Whisper API.
Supports: button-press recording, ambient continuous recording.
"""
import io
import struct
import os
import subprocess
import tempfile
import openai
from config import SAMPLE_RATE, MIC_DEVICE, MIC_DURATION

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

AMBIENT_DURATION = 15  # seconds per ambient chunk


def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Wrap raw 16-bit PCM bytes in a WAV container."""
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = len(pcm_bytes)
    chunk_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", chunk_size, b"WAVE",
        b"fmt ", 16,
        1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample,
        b"data", data_size,
    )
    return header + pcm_bytes


def transcribe_bytes(pcm_bytes: bytes) -> str:
    """Transcribe raw 16-bit PCM audio (16kHz mono) via Whisper API."""
    if len(pcm_bytes) < SAMPLE_RATE * 2 * 0.5:
        return ""

    wav_bytes = _pcm_to_wav(pcm_bytes)
    wav_file = io.BytesIO(wav_bytes)
    wav_file.name = "audio.wav"

    try:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=wav_file,
            language="en",
        )
        return transcript.text.strip()
    except Exception as e:
        print(f"Whisper API error: {e}")
        return ""


def _record_wav(duration: int, device: str = MIC_DEVICE) -> str | None:
    """Record audio to a temp WAV file, return the path or None on failure."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name

    try:
        cmd = [
            "arecord", "-D", device,
            "-f", "S16_LE", "-r", str(SAMPLE_RATE), "-c", "1",
            "-d", str(duration),
            wav_path,
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=duration + 5)
        if result.returncode != 0:
            print(f"arecord failed: {result.stderr.decode()}")
            os.unlink(wav_path)
            return None
        return wav_path
    except Exception as e:
        print(f"Recording error: {e}")
        try:
            os.unlink(wav_path)
        except Exception:
            pass
        return None


def _transcribe_wav_file(wav_path: str) -> str:
    """Transcribe a WAV file via Whisper API."""
    try:
        with open(wav_path, "rb") as wf:
            wav_bytes = wf.read()

        if len(wav_bytes) < 1000:
            return ""

        wav_file = io.BytesIO(wav_bytes)
        wav_file.name = "audio.wav"
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=wav_file,
            language="en",
        )
        return transcript.text.strip()
    except Exception as e:
        print(f"Whisper API error: {e}")
        return ""


def record_and_transcribe(duration: int = MIC_DURATION, device: str = MIC_DEVICE) -> str:
    """Record from mic for button-press interaction, then transcribe."""
    print(f"Recording {duration}s from device '{device}'...")
    wav_path = _record_wav(duration, device)
    if not wav_path:
        return ""
    try:
        return _transcribe_wav_file(wav_path)
    finally:
        try:
            os.unlink(wav_path)
        except Exception:
            pass


def record_ambient_chunk(duration: int = AMBIENT_DURATION, device: str = MIC_DEVICE) -> str:
    """Record a short ambient chunk and transcribe. Used by 24/7 listening loop."""
    wav_path = _record_wav(duration, device)
    if not wav_path:
        return ""
    try:
        text = _transcribe_wav_file(wav_path)
        # Filter out Whisper hallucinations on silence
        noise_phrases = [
            "thank you", "thanks for watching", "subscribe",
            "you", "bye", "...", "the end",
        ]
        if text.lower().strip().rstrip('.') in noise_phrases:
            return ""
        return text
    finally:
        try:
            os.unlink(wav_path)
        except Exception:
            pass
