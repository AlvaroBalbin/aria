"""
Speech-to-text using OpenAI Whisper API.
Faster and more accurate in noisy environments than local faster-whisper.
"""
import io
import struct
import os
import subprocess
import tempfile
import openai
from config import SAMPLE_RATE, MIC_DEVICE, MIC_DURATION

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


def record_and_transcribe(duration: int = MIC_DURATION, device: str = MIC_DEVICE) -> str:
    """
    Record `duration` seconds from the system mic (AirPods via Bluetooth on Pi 5),
    then transcribe with Whisper. Returns text or empty string.
    Set MIC_DEVICE in .env — find device name with: arecord -l
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = f.name

    try:
        cmd = [
            "arecord",
            "-D", device,
            "-f", "S16_LE",
            "-r", str(SAMPLE_RATE),
            "-c", "1",
            "-d", str(duration),
            wav_path,
        ]
        print(f"Recording {duration}s from device '{device}'…")
        result = subprocess.run(cmd, capture_output=True, timeout=duration + 5)
        if result.returncode != 0:
            print(f"arecord failed: {result.stderr.decode()}")
            return ""

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
        print(f"record_and_transcribe error: {e}")
        return ""
    finally:
        try:
            os.unlink(wav_path)
        except Exception:
            pass
