"""
ARIA brain — OpenAI GPT-4o with agentic tool use.
"""
import json
import openai
from config import OPENAI_API_KEY, USER_NAME
from tools import OPENAI_TOOL_SCHEMAS, TOOL_MAP
from memory import build_memory_context
from db import get_conversation_history, save_conversation_turn

client = openai.OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT_BASE = """You are ARIA, a personal AI assistant worn as a pendant by {user_name}.
You are concise, warm, and genuinely helpful — like a brilliant friend, not a chatbot.
Keep responses short and conversational (1-3 sentences) unless detail is needed.
You have tools to search the web, remember things, check transcripts, set reminders, and post to X/Twitter.
Use tools proactively — don't ask permission.

{memory_context}"""


def build_system_prompt() -> str:
    memory_ctx = build_memory_context()
    return SYSTEM_PROMPT_BASE.format(user_name=USER_NAME, memory_context=memory_ctx)


def ask(user_text: str) -> str:
    """Send user text through GPT-4o with tools, return final response."""
    save_conversation_turn("user", user_text)

    # Build messages: system + history + current
    history = get_conversation_history(limit=8)
    messages = [{"role": "system", "content": build_system_prompt()}]
    for m in history[:-1]:  # history already has current turn from save above
        messages.append({"role": m["role"], "content": m["text"]})
    messages.append({"role": "user", "content": user_text})

    # Agentic loop — max 6 rounds of tool use
    for _ in range(6):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=OPENAI_TOOL_SCHEMAS,
            tool_choice="auto",
            max_tokens=512,
        )

        choice = response.choices[0]
        msg = choice.message

        # No tool calls → final answer
        if choice.finish_reason == "stop" or not msg.tool_calls:
            final_text = msg.content or ""
            save_conversation_turn("assistant", final_text)
            return final_text.strip()

        # Execute each tool call
        messages.append(msg)  # append assistant message with tool_calls
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
