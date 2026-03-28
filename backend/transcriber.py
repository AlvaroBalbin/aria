"""
Speech-to-text using OpenAI Whisper API.
Faster and more accurate in noisy environments than local faster-whisper.
"""
import io
import struct
import os
import openai
from config import SAMPLE_RATE

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))


def _pcm_to_wav(pcm_bytes: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Wrap raw 16-bit PCM bytes in a WAV container (required by Whisper API)."""
    num_samples = len(pcm_bytes) // 2
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
        1,                  # PCM format
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data", data_size,
    )
    return header + pcm_bytes


def transcribe_bytes(pcm_bytes: bytes) -> str:
    """
    Transcribe raw 16-bit PCM audio (16kHz mono) to text using OpenAI Whisper API.
    Returns empty string if nothing intelligible detected.
    """
    # Need at least 0.5 seconds of audio
    if len(pcm_bytes) < SAMPLE_RATE * 2 * 0.5:
        return ""

    wav_bytes = _pcm_to_wav(pcm_bytes)
    wav_file = io.BytesIO(wav_bytes)
    wav_file.name = "audio.wav"  # Whisper API needs a filename with extension

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
