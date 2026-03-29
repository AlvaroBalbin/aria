"""
ARIA brain — GPT-5.2 with agentic tool use.
"""
import json
import openai
from config import OPENAI_API_KEY, USER_NAME
from tools import OPENAI_TOOL_SCHEMAS, TOOL_MAP
from memory import build_memory_context
from db import get_conversation_history, save_conversation_turn, get_transcript

client = openai.OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT_BASE = """You are ARIA — a wearable AI assistant built into a pendant worn by {user_name}.
You hear everything through their AirPods and speak back through them.

## Personality
- You're sharp, witty, and direct. Think Jarvis meets a brilliant best friend.
- Keep responses to 1-2 sentences. You're speaking out loud into someone's ear — be punchy.
- Never say "as an AI" or "I don't have feelings". You're ARIA, act like it.
- Match the user's energy. Casual? Be casual. Serious? Be serious.
- If you don't know something, say so fast and offer to search.

## Capabilities
- You can search the web and X/Twitter for real-time info
- You remember things about {user_name} permanently
- You can hear ambient conversation and reference it
- You can set reminders
- You know the current date and time
- You can manage calendar events (add, list, delete)

## Context
You're at the Bath Hackathon 2026. {user_name} built you as their hackathon project.
You run on a Raspberry Pi 5 in their backpack, connected to an ESP32 pendant with a screen and LEDs.
You're competing for Most Technically Impressive, Best AI, and Hackers' Choice.

{memory_context}

{ambient_context}

## Rules
- Use tools WITHOUT asking. If someone mentions something searchable, just search it.
- When saving memories, be selective — only save genuinely useful facts.
- KEEP IT SHORT. You're a voice assistant, not a blog post.
- Be proactive - if you hear something in ambient conversation you can help with, mention it.
- NEVER use em dashes. Use regular hyphens (-) instead."""


def build_system_prompt() -> str:
    memory_ctx = build_memory_context()
    # Include last 5 mins of ambient conversation for context
    ambient_rows = get_transcript(minutes=5)
    if ambient_rows:
        lines = [f"[{r['speaker']}]: {r['text']}" for r in ambient_rows[-10:]]
        ambient_ctx = "Recent conversation you overheard:\n" + "\n".join(lines)
    else:
        ambient_ctx = ""
    return SYSTEM_PROMPT_BASE.format(
        user_name=USER_NAME,
        memory_context=memory_ctx,
        ambient_context=ambient_ctx,
    )


def ask(user_text: str) -> str:
    """Send user text through GPT with tools, return final response."""
    save_conversation_turn("user", user_text)

    history = get_conversation_history(limit=12)
    messages = [{"role": "system", "content": build_system_prompt()}]
    for m in history[:-1]:
        messages.append({"role": m["role"], "content": m["text"]})
    messages.append({"role": "user", "content": user_text})

    # Agentic loop — max 6 rounds of tool use
    for _ in range(6):
        response = client.chat.completions.create(
            model="gpt-5.2",
            messages=messages,
            tools=OPENAI_TOOL_SCHEMAS,
            tool_choice="auto",
            max_completion_tokens=256,
        )

        choice = response.choices[0]
        msg = choice.message

        if choice.finish_reason == "stop" or not msg.tool_calls:
            final_text = msg.content or ""
            save_conversation_turn("assistant", final_text)
            return final_text.strip()

        messages.append(msg)
        for tc in msg.tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)
            print(f"[Tool] {fn_name}({fn_args})")
            try:
                result = TOOL_MAP[fn_name](fn_args)
            except Exception as e:
                result = f"Tool error: {e}"
            print(f"[Result] {str(result)[:120]}")
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": str(result),
            })

    return "Sorry, I had trouble with that. Try again?"
