"""
Claude agentic brain with tool use.
Handles the full conversation loop: system prompt → tool calls → final response.
"""
import anthropic
from config import ANTHROPIC_API_KEY, USER_NAME
from tools import TOOL_SCHEMAS, TOOL_MAP
from memory import build_memory_context
from db import get_conversation_history, save_conversation_turn

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT_BASE = """You are ARIA, a personal AI assistant worn as a pendant by {user_name}.
You are concise, warm, and genuinely helpful. You speak naturally — like a brilliant friend, not a chatbot.
Keep responses short and conversational (1-3 sentences) unless detail is needed.
You have tools to search the web, remember things, check transcripts of nearby conversations, and set reminders.
Use tools proactively when relevant — don't ask permission to search or save a memory.

{memory_context}"""


def build_system_prompt() -> str:
    memory_ctx = build_memory_context()
    return SYSTEM_PROMPT_BASE.format(
        user_name=USER_NAME,
        memory_context=memory_ctx,
    )


def ask(user_text: str) -> str:
    """
    Send user text to Claude with tools, handle the full agentic loop,
    return the final text response.
    """
    # Save user turn
    save_conversation_turn("user", user_text)

    # Build messages: history + current
    history = get_conversation_history(limit=8)
    messages = [{"role": m["role"], "content": m["text"]} for m in history]
    # Ensure last message is the current user turn
    if not messages or messages[-1]["content"] != user_text:
        messages.append({"role": "user", "content": user_text})

    system = build_system_prompt()

    # Agentic loop
    for _ in range(6):  # max 6 tool-use rounds
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=system,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        # Collect text + tool use blocks
        text_parts = []
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(block)

        # If no tool calls, we have the final answer
        if not tool_calls:
            final_text = " ".join(text_parts).strip()
            save_conversation_turn("assistant", final_text)
            return final_text

        # Execute tools and feed results back
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for tc in tool_calls:
            print(f"[Tool] {tc.name}({tc.input})")
            try:
                result = TOOL_MAP[tc.name](tc.input)
            except Exception as e:
                result = f"Tool error: {e}"
            print(f"[Tool result] {result[:120]}")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": str(result),
            })
        messages.append({"role": "user", "content": tool_results})

    # Fallback if loop exhausted
    return "Sorry, I had trouble answering that. Try again?"
