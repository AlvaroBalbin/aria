"""
ARIA brain — OpenAI GPT-4o-mini with agentic tool use and personality.
"""
import json
import re
import datetime
import openai
from config import OPENAI_API_KEY, USER_NAME
from tools import OPENAI_TOOL_SCHEMAS, TOOL_MAP
from memory import build_memory_context
from db import get_conversation_history, save_conversation_turn

client = openai.OpenAI(api_key=OPENAI_API_KEY)

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


def build_system_prompt() -> str:
    memory_ctx = build_memory_context()
    now = datetime.datetime.now()
    time_str = now.strftime("%A, %B %d %Y at %H:%M")
    return SYSTEM_PROMPT_BASE.format(
        user_name=USER_NAME,
        memory_context=memory_ctx,
        current_time=time_str,
    )


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
    history = get_conversation_history(limit=24)
    messages = [{"role": "system", "content": build_system_prompt()}]
    for m in history[:-1]:
        messages.append({"role": m["role"], "content": m["text"]})
    messages.append({"role": "user", "content": user_text})

    # Agentic loop — max 6 rounds of tool use
    for _ in range(6):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=OPENAI_TOOL_SCHEMAS,
            tool_choice="auto",
            max_tokens=1024,
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
            print(f"[Result] {str(result)[:120]}".encode("ascii", "replace").decode())
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": str(result),
            })

    return {"response": "Sorry, I had trouble with that. Try again?", "mood": "neutral"}
