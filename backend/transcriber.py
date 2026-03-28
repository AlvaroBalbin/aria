import numpy as np
from faster_whisper import WhisperModel
from config import WHISPER_MODEL, SAMPLE_RATE

# Load model once at startup
print(f"Loading Whisper model: {WHISPER_MODEL}")
_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
print("Whisper ready.")


def transcribe_bytes(pcm_bytes: bytes) -> str:
    """
    Transcribe raw PCM audio bytes (16-bit, 16kHz, mono) to text.
    Returns empty string if nothing intelligible detected.
    """
    if len(pcm_bytes) < SAMPLE_RATE * 2 * 0.3:  # less than 0.3 seconds — skip
        return ""

    # Convert bytes → int16 → float32 in [-1.0, 1.0]
    audio_int16 = np.frombuffer(pcm_bytes, dtype=np.int16)
    audio_float32 = audio_int16.astype(np.float32) / 32768.0

    segments, info = _model.transcribe(
        audio_float32,
        language="en",
        beam_size=1,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 300},
    )

    texts = [seg.text.strip() for seg in segments if seg.text.strip()]
    return " ".join(texts)


def transcribe_file(path: str) -> str:
    """Transcribe from a wav/mp3 file path."""
    segments, _ = _model.transcribe(path, beam_size=1, vad_filter=True)
    return " ".join(seg.text.strip() for seg in segments)
