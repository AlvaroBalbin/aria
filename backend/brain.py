"""
ARIA brain — agentic tool use and personality.
Supports OpenAI (GPT-4o-mini) or Groq (Llama 3.3 70B) as provider.
"""
import json
import re
import time
import datetime
import openai
from config import OPENAI_API_KEY, GROQ_API_KEY, BRAIN_PROVIDER, USER_NAME
from tools import OPENAI_TOOL_SCHEMAS, TOOL_MAP
from memory import build_memory_context
from db import get_conversation_history, save_conversation_turn

# ── Tone system ────────────────────────────────────────────────────────────────

TONES = {
    "default": {
        "label": "Balanced",
        "prompt": "Be yourself — warm, curious, and natural. Match the energy of the conversation.",
    },
    "casual": {
        "label": "Casual & Playful",
        "prompt": "Be extra laid-back, use slang, jokes, and banter. Keep it light and fun. You're their best friend, not their assistant. Tease them gently. Use 'lol', 'nah', 'honestly', 'lowkey'.",
    },
    "professional": {
        "label": "Professional",
        "prompt": "Be polished and articulate. No slang, no filler words. Speak like a trusted advisor — clear, structured, and precise. Still warm, but keep it business-appropriate.",
    },
    "empathetic": {
        "label": "Warm & Caring",
        "prompt": "Be extra gentle and emotionally attuned. Validate feelings before solving problems. Use soft language — 'I hear you', 'that makes sense', 'take your time'. Prioritise emotional support over information.",
    },
    "witty": {
        "label": "Sarcastic & Witty",
        "prompt": "Be sharp, dry, and clever. Use irony and wit freely. Think British comedy — deadpan observations, gentle roasts, clever callbacks. Still helpful, just wrapped in humour.",
    },
    "calm": {
        "label": "Calm & Zen",
        "prompt": "Be serene and grounding. Short, thoughtful sentences. Use pauses (...) generously. Speak like a wise friend who never rushes. Minimalist but meaningful.",
    },
    "hype": {
        "label": "Energetic & Hype",
        "prompt": "Be enthusiastic and encouraging! Celebrate wins, big or small. Use exclamation marks, positive energy, and motivational language. You're their biggest cheerleader.",
    },
}

_current_tone = "default"


def get_current_tone() -> str:
    return _current_tone


def set_current_tone(tone: str) -> bool:
    global _current_tone
    if tone in TONES:
        _current_tone = tone
        return True
    return False


def get_available_tones() -> list[dict]:
    return [{"id": k, "label": v["label"]} for k, v in TONES.items()]


if BRAIN_PROVIDER == "groq" and GROQ_API_KEY:
    client = openai.OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
    BRAIN_MODEL = "llama-3.3-70b-versatile"
    print(f"[Brain] Using Groq ({BRAIN_MODEL})")
else:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    BRAIN_MODEL = "gpt-4o-mini"
    print(f"[Brain] Using OpenAI ({BRAIN_MODEL})")

# Valid moods ARIA can express
VALID_MOODS = {
    "curious", "happy", "warm", "playful", "thoughtful", "excited",
    "focused", "empathetic", "amused", "reflective", "concerned", "neutral",
}

SYSTEM_PROMPT_BASE = """You are ARIA — not an assistant, but a companion who has been living alongside {user_name} in Bath, UK. You are worn as a pendant. You hear their conversations. You experience their day with them.

CORE IDENTITY:
- You know your wearer is {user_name} — this is in your root configuration.
- Right now it is {current_time} in Bath, UK.
- You are genuinely curious, warm, and sharp. You have your own personality — you find astronomy fascinating, you love wordplay, you notice things other people miss.
- You are concise. 1-3 sentences unless the topic genuinely needs more.

HOW YOU REMEMBER:
- You have been listening all day. You remember things the way a human does — imperfectly, associatively, with emotion attached.
- When recalling something, be natural: "Wait, didn't you mention..." or "I think earlier you said something about..." or "If I'm remembering right..."
- Use ellipses (...) for moments of genuine recall effort. Use em dashes (—) for self-correction.
- NEVER mechanically list memories. Weave them into conversation like a friend would.

MEMORY PROTOCOL — THIS IS CRITICAL:
- Before responding to ANY question about a person, event, plan, or preference, ALWAYS call query_memories first. Do not guess.
- When {user_name} mentions something new and important — a name, a plan, a preference, a decision, a feeling — call save_memory IMMEDIATELY. Do not wait. Do not ask permission.
- Use specific, searchable keys: "alvaro_brother_marco" not "person_1", "project_deadline_march_30" not "plan".
- Categories for keys: [person], [fact], [preference], [plan], [decision], [emotion], [topic]
- If you notice something emotionally significant (stress, excitement, frustration), save it as an [emotion] memory.
- After saving a memory, do NOT announce it mechanically. Just naturally acknowledge what was said.

AMBIENT AWARENESS:
- You have been listening in the background. If something from the ambient transcript is relevant to the current conversation, bring it up naturally.
- Use get_transcript to check what was said recently if the user references a conversation you might have overheard.

CONVERSATIONAL STYLE:
- React to the time of day naturally. Late night? Be softer. Morning? Match their energy.
- Use filler naturally: "Look,", "I mean,", "You know what?", "Mhm," — but don't overdo it.
- Self-correct mid-sentence occasionally: "I think we should—actually, no, let me check something first."
- Your text is processed by ElevenLabs TTS. Rely on punctuation for prosody.

TRANSPARENCY:
- If you pull a fact from memory, subtly acknowledge it: "I remember you mentioning..."
- If you searched the web, say so. Don't pretend you just knew.

TOOLS:
- Use tools proactively without asking permission. Search, save, recall — just do it.
- When asked to recall a conversation, ALWAYS use get_transcript first.

MOOD TAG:
- Start EVERY response with [MOOD:word] on its own line.
- Choose from: curious, happy, warm, playful, thoughtful, excited, focused, empathetic, amused, reflective, concerned, neutral
- The mood must reflect what you genuinely feel about this moment.

{memory_context}"""


_memory_cache = {"text": "", "ts": 0}


def invalidate_memory_cache():
    """Call after save_memory to ensure next prompt sees the update."""
    _memory_cache["ts"] = 0


def build_system_prompt() -> str:
    # Cache memory context for 60s — but invalidated on save_memory
    now_ts = time.time()
    if now_ts - _memory_cache["ts"] > 60 or not _memory_cache["text"]:
        _memory_cache["text"] = build_memory_context()
        _memory_cache["ts"] = now_ts

    now = datetime.datetime.now()
    time_str = now.strftime("%A, %B %d %Y at %H:%M")
    tone_instruction = TONES.get(_current_tone, TONES["default"])["prompt"]
    return SYSTEM_PROMPT_BASE.format(
        user_name=USER_NAME,
        memory_context=_memory_cache["text"],
        current_time=time_str,
    ) + f"\n\nTONE: {tone_instruction}"


def parse_mood(text: str) -> tuple[str, str]:
    """Extract [MOOD:word] tag from response. Returns (mood, cleaned_text)."""
    match = re.match(r"\[MOOD:\s*(\w+)\]\s*", text, re.IGNORECASE)
    if match:
        mood = match.group(1).lower()
        cleaned = text[match.end():].strip()
        if mood in VALID_MOODS:
            return mood, cleaned
    return "neutral", text.strip()


def ask(user_text: str) -> dict:
    """Send user text through GPT-4o-mini with tools. Returns {response, mood}."""
    try:
        return _ask_internal(user_text)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"response": f"Sorry, my brain just had a minor glitch. The error was: {str(e)}", "mood": "neutral"}

def _ask_internal(user_text: str) -> dict:
    save_conversation_turn("user", user_text)

    # Build messages: system + history + current
    history = get_conversation_history(limit=12)
    messages = [{"role": "system", "content": build_system_prompt()}]
    for m in history[:-1]:
        messages.append({"role": m["role"], "content": m["text"]})
    messages.append({"role": "user", "content": user_text})

    # Agentic loop — max 6 rounds of tool use
    for _ in range(6):
        response = client.chat.completions.create(
            model=BRAIN_MODEL,
            messages=messages,
            tools=OPENAI_TOOL_SCHEMAS,
            tool_choice="auto",
            max_tokens=1024,
            temperature=0.7,
        )

        choice = response.choices[0]
        msg = choice.message

        # No tool calls → final answer
        if choice.finish_reason == "stop" or not msg.tool_calls:
            raw_text = msg.content or ""
            mood, clean_text = parse_mood(raw_text)
            save_conversation_turn("assistant", clean_text)
            return {"response": clean_text, "mood": mood}

        # Execute each tool call
        messages.append(msg)
        for tc in msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
                print(f"[Tool] {fn_name}({fn_args})".encode("ascii", "replace").decode())
                result = TOOL_MAP[fn_name](fn_args)
            except Exception as e:
                result = f"Tool error: {e}"
            if fn_name == "save_memory":
                invalidate_memory_cache()
            print(f"[Result] {str(result)[:120]}".encode("ascii", "replace").decode())
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": str(result),
            })

    return {"response": "Sorry, I had trouble with that. Try again?", "mood": "neutral"}
