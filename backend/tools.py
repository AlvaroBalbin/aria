"""
Claude/GPT tool implementations for ARIA.
"""
import datetime
import httpx
from db import save_memory, query_memories, get_transcript, save_reminder, get_all_memories
from config import BRAVE_API_KEY, TWITTER_BEARER_TOKEN


# ── Web search ────────────────────────────────────────────────────────────────

def search_web(args: dict) -> str:
    query = args["query"]
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
        results = resp.json().get("web", {}).get("results", [])[:5]
        if not results:
            return "No results found."
        return "\n".join(f"- {r.get('title','')}: {r.get('description','')}" for r in results)
    except Exception as e:
        return f"Search failed: {e}"


def _ddg_search(query: str) -> str:
    try:
        resp = httpx.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": "1"},
            timeout=10, follow_redirects=True,
        )
        data = resp.json()
        parts = [p for p in [data.get("Answer",""), data.get("AbstractText","")] if p]
        parts += [r.get("Text","") for r in data.get("RelatedTopics",[])[:2] if "Text" in r]
        return "\n".join(parts[:3]) if parts else f"No quick answer for '{query}'."
    except Exception as e:
        return f"Search failed: {e}"


# ── Memory ────────────────────────────────────────────────────────────────────

def save_memory_tool(args: dict) -> str:
    save_memory(args["key"], args["value"])
    return f"Remembered: {args['key']} = {args['value']}"


def query_memories_tool(args: dict) -> str:
    memories = query_memories(args["query"])
    if not memories:
        return "No relevant memories found."
    return "\n".join(f"- {m['key']}: {m['value']}" for m in memories)


# ── Transcript ────────────────────────────────────────────────────────────────

def get_transcript_tool(args: dict) -> str:
    minutes = args.get("minutes", 30)
    rows = get_transcript(minutes)
    if not rows:
        return f"No transcript from the last {minutes} minutes."
    lines = [
        f"[{datetime.datetime.fromtimestamp(r['ts']).strftime('%H:%M')}] {r['speaker']}: {r['text']}"
        for r in rows
    ]
    return "\n".join(lines)


# ── Reminders ─────────────────────────────────────────────────────────────────

def set_reminder_tool(args: dict) -> str:
    save_reminder(args["text"], args.get("when_description", ""))
    return f"Reminder set: '{args['text']}'"


# ── Date/time ─────────────────────────────────────────────────────────────────

def get_datetime_tool(args: dict) -> str:
    return datetime.datetime.now().strftime("It is %A, %B %d %Y at %H:%M.")


# ── Twitter / X ───────────────────────────────────────────────────────────────

def search_x(args: dict) -> str:
    """Search X/Twitter for the latest tweets on a topic — real-time world news."""
    query = args["query"]
    if not TWITTER_BEARER_TOKEN:
        return "Twitter Bearer Token not configured."
    try:
        import tweepy
        client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)
        # Exclude retweets for cleaner results
        full_query = f"{query} -is:retweet lang:en"
        resp = client.search_recent_tweets(
            query=full_query,
            max_results=10,
            tweet_fields=["text", "created_at", "author_id"],
        )
        if not resp.data:
            return f"No recent tweets found about '{query}'."
        lines = [f"- {t.text[:180]}" for t in resp.data[:6]]
        return f"Latest on X about '{query}':\n" + "\n".join(lines)
    except Exception as e:
        return f"X search failed: {e}"


# ── Dispatch map ──────────────────────────────────────────────────────────────

TOOL_MAP = {
    "search_web":      search_web,
    "save_memory":     save_memory_tool,
    "query_memories":  query_memories_tool,
    "get_transcript":  get_transcript_tool,
    "set_reminder":    set_reminder_tool,
    "get_datetime":    get_datetime_tool,
    "search_x":        search_x,
}


# ── OpenAI tool schemas ───────────────────────────────────────────────────────

def _fn(name, description, properties, required=None):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required or [],
            },
        },
    }


OPENAI_TOOL_SCHEMAS = [
    _fn("search_web", "Search the web for current info, news, or facts.",
        {"query": {"type": "string", "description": "Search query"}}, ["query"]),

    _fn("save_memory", "Permanently save an important fact about the user.",
        {
            "key":   {"type": "string", "description": "Short label, e.g. 'user_name'"},
            "value": {"type": "string", "description": "The value to store"},
        }, ["key", "value"]),

    _fn("query_memories", "Search stored memories about the user.",
        {"query": {"type": "string", "description": "What to look for"}}, ["query"]),

    _fn("get_transcript", "Get recent ambient transcript of nearby conversation.",
        {"minutes": {"type": "integer", "description": "Minutes back to fetch (default 30)"}}, []),

    _fn("set_reminder", "Set a reminder for the user.",
        {
            "text":             {"type": "string", "description": "What to remind about"},
            "when_description": {"type": "string", "description": "When (optional)"},
        }, ["text"]),

    _fn("get_datetime", "Get the current date and time.", {}, []),

    _fn("search_x", "Search X/Twitter for the latest real-time tweets and news on any topic.",
        {"query": {"type": "string", "description": "Topic to search on X, e.g. 'AI news', 'Bath Hackathon'"}}, ["query"]),
]
