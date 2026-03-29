"""
Speech-to-text via OpenAI Whisper API.
"""
import io
import os
import struct
from config import SAMPLE_RATE

_api_client = None


def _get_api_client():
    global _api_client
    if _api_client is None:
        import openai
        _api_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
    return _api_client


def _transcribe_api(file_bytes: bytes, filename: str) -> str:
    try:
        audio_file = io.BytesIO(file_bytes)
        audio_file.name = filename
        transcript = _get_api_client().audio.transcriptions.create(
            model="whisper-1", file=audio_file, language="en")
        return transcript.text.strip()
    except Exception as e:
        print(f"[Whisper] API error: {e}")
        return ""


def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = len(pcm_bytes)
    chunk_size = 36 + data_size
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", chunk_size, b"WAVE",
        b"fmt ", 16, 1, num_channels, sample_rate,
        byte_rate, block_align, bits_per_sample,
        b"data", data_size,
    )
    return header + pcm_bytes


def transcribe_webm(webm_bytes: bytes) -> str:
    """Transcribe webm/opus audio from browser MediaRecorder."""
    if len(webm_bytes) < 1000:
        return ""
    return _transcribe_api(webm_bytes, "audio.webm")


def transcribe_bytes(pcm_bytes: bytes) -> str:
    """Transcribe raw 16-bit PCM audio (16kHz mono) from ESP32 pendant."""
    if len(pcm_bytes) < SAMPLE_RATE * 2 * 0.5:
        return ""
    wav_bytes = _pcm_to_wav(pcm_bytes)
    return _transcribe_api(wav_bytes, "audio.wav")
