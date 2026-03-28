"""
Claude tool implementations.
Each function is called when Claude decides to use a tool.
"""
import datetime
import httpx
from db import save_memory, query_memories, get_transcript, save_reminder, get_all_memories
from config import BRAVE_API_KEY


def search_web(query: str) -> str:
    """Search the web. Uses Brave Search API if key available, else DuckDuckGo."""
    if BRAVE_API_KEY:
        return _brave_search(query)
    return _ddg_search(query)


def _brave_search(query: str) -> str:
    try:
        resp = httpx.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY},
            params={"q": query, "count": 5},
            timeout=10,
        )
        data = resp.json()
        results = data.get("web", {}).get("results", [])[:5]
        if not results:
            return "No results found."
        lines = []
        for r in results:
            lines.append(f"- {r.get('title', '')}: {r.get('description', '')}")
        return "\n".join(lines)
    except Exception as e:
        return f"Search failed: {e}"


def _ddg_search(query: str) -> str:
    """DuckDuckGo instant answer fallback (no API key needed)."""
    try:
        resp = httpx.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
            timeout=10,
            follow_redirects=True,
        )
        data = resp.json()
        abstract = data.get("AbstractText", "")
        answer = data.get("Answer", "")
        related = [r.get("Text", "") for r in data.get("RelatedTopics", [])[:3] if "Text" in r]
        parts = [p for p in [answer, abstract] + related if p]
        if parts:
            return "\n".join(parts[:3])
        return f"No quick answer found for '{query}'. Try a more specific query."
    except Exception as e:
        return f"Search failed: {e}"


def tool_save_memory(key: str, value: str) -> str:
    save_memory(key, value)
    return f"Remembered: {key} = {value}"


def tool_query_memories(query: str) -> str:
    memories = query_memories(query)
    if not memories:
        return "No relevant memories found."
    lines = [f"- {m['key']}: {m['value']}" for m in memories]
    return "\n".join(lines)


def tool_get_transcript(minutes: int = 30) -> str:
    rows = get_transcript(minutes)
    if not rows:
        return f"No transcript available from the last {minutes} minutes."
    lines = [f"[{datetime.datetime.fromtimestamp(r['ts']).strftime('%H:%M')}] {r['speaker']}: {r['text']}" for r in rows]
    return "\n".join(lines)


def tool_set_reminder(text: str, when_description: str = "") -> str:
    save_reminder(text)
    return f"Reminder set: '{text}'" + (f" ({when_description})" if when_description else "")


def tool_get_datetime() -> str:
    now = datetime.datetime.now()
    return now.strftime("It is %A, %B %d %Y at %H:%M.")


# Maps tool names to functions for brain.py dispatch
TOOL_MAP = {
    "search_web": lambda args: search_web(args["query"]),
    "save_memory": lambda args: tool_save_memory(args["key"], args["value"]),
    "query_memories": lambda args: tool_query_memories(args["query"]),
    "get_transcript": lambda args: tool_get_transcript(args.get("minutes", 30)),
    "set_reminder": lambda args: tool_set_reminder(args["text"], args.get("when_description", "")),
    "get_datetime": lambda args: tool_get_datetime(),
}

# Tool schemas for Claude
TOOL_SCHEMAS = [
    {
        "name": "search_web",
        "description": "Search the web for current information, news, facts, or any topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "save_memory",
        "description": "Permanently save an important fact or piece of information about the user or their life.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Short label for this memory, e.g. 'user_name', 'user_project'"},
                "value": {"type": "string", "description": "The value to remember"}
            },
            "required": ["key", "value"]
        }
    },
    {
        "name": "query_memories",
        "description": "Search your stored memories about the user to answer questions about them.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search for in memories"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_transcript",
        "description": "Get the recent ambient transcript of what has been said nearby.",
        "input_schema": {
            "type": "object",
            "properties": {
                "minutes": {"type": "integer", "description": "How many minutes back to retrieve (default 30)", "default": 30}
            },
            "required": []
        }
    },
    {
        "name": "set_reminder",
        "description": "Set a reminder or note something the user wants to remember to do later.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "What to remind the user about"},
                "when_description": {"type": "string", "description": "When (optional, e.g. 'after the hackathon')"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "get_datetime",
        "description": "Get the current date and time.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]
