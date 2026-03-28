import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")  # Set after cloning voice
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")              # Optional: for web search
USER_NAME = os.getenv("USER_NAME", "User")
DB_PATH = os.getenv("DB_PATH", "aria.db")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny.en")       # tiny.en is fastest on Pi 5
SAMPLE_RATE = 16000
CHUNK_SAMPLES = 512
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
