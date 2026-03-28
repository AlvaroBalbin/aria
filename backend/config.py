import os
from dotenv import load_dotenv

load_dotenv()

# AI providers
OPENAI_API_KEY       = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY    = os.getenv("ANTHROPIC_API_KEY", "")  # unused but kept in case

# ElevenLabs
ELEVENLABS_API_KEY   = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_AGENT_ID  = os.getenv("ELEVENLABS_AGENT_ID", "")  # for conversational AI
ELEVENLABS_VOICE_ID  = os.getenv("ELEVENLABS_VOICE_ID", "")  # for TTS fallback

# Search
BRAVE_API_KEY        = os.getenv("BRAVE_API_KEY", "")

# Twitter / X  (only Bearer Token needed for reading tweets)
TWITTER_BEARER_TOKEN        = os.getenv("TWITTER_BEARER_TOKEN", "")

# ARIA identity
USER_NAME  = os.getenv("USER_NAME", "Alvaro")

# Server
HOST        = os.getenv("HOST", "0.0.0.0")
PORT        = int(os.getenv("PORT", "8000"))
DB_PATH     = os.getenv("DB_PATH", "aria.db")
SAMPLE_RATE = 16000

# Microphone device for arecord (Pi 5 → AirPods Bluetooth HFP, or "default")
# Find yours with: arecord -l
# For AirPods: typically "bluez_source.XX_XX_XX_XX_XX_XX.headset_head_unit"
# Set in .env as MIC_DEVICE=default or the full bluez device name
MIC_DEVICE     = os.getenv("MIC_DEVICE", "default")
MIC_DURATION   = int(os.getenv("MIC_DURATION", "8"))  # seconds to record per button press
