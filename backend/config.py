import os
from dotenv import load_dotenv

load_dotenv()

# AI providers
OPENAI_API_KEY       = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY         = os.getenv("GROQ_API_KEY", "")
BRAIN_PROVIDER       = os.getenv("BRAIN_PROVIDER", "openai")  # "openai" or "groq"

# ElevenLabs
ELEVENLABS_API_KEY   = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_AGENT_ID  = os.getenv("ELEVENLABS_AGENT_ID", "")  # for conversational AI
ELEVENLABS_VOICE_ID  = os.getenv("ELEVENLABS_VOICE_ID", "")  # for TTS fallback

# Search
BRAVE_API_KEY        = os.getenv("BRAVE_API_KEY", "")

# Twitter / X
TWITTER_BEARER_TOKEN   = os.getenv("TWITTER_BEARER_TOKEN", "")
TWITTER_CLIENT_ID      = os.getenv("TWITTER_CLIENT_ID", "")
TWITTER_CLIENT_SECRET  = os.getenv("TWITTER_CLIENT_SECRET", "")

# ARIA identity
USER_NAME  = os.getenv("USER_NAME", "Alvaro")

# Supabase
SUPABASE_URL  = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY  = os.getenv("SUPABASE_KEY", "")  # service role key (bypasses RLS)

# Server
HOST        = os.getenv("HOST", "0.0.0.0")
PORT        = int(os.getenv("PORT", "8000"))
SAMPLE_RATE = 16000
