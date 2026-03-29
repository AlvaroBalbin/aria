"""
Claude/GPT tool implementations for ARIA.
"""
import datetime
import httpx
from db import (save_memory, query_memories, get_transcript, save_reminder, get_all_memories,
                save_calendar_event, list_calendar_events, delete_calendar_event)
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


# ── Calendar ─────────────────────────────────────────────────────────────────

def add_calendar_event_tool(args: dict) -> str:
    title = args["title"]
    start_str = args["start_time"]
    end_str = args.get("end_time")
    description = args.get("description", "")
    all_day = args.get("all_day", False)
    try:
        start_dt = datetime.datetime.fromisoformat(start_str)
        start_ts = start_dt.timestamp()
        end_ts = datetime.datetime.fromisoformat(end_str).timestamp() if end_str else None
    except ValueError as e:
        return f"Invalid date format: {e}. Use ISO 8601 (e.g., 2026-03-30T14:00:00)."
    event_id = save_calendar_event(title, start_ts, end_ts, description, all_day)
    nice_time = start_dt.strftime("%A %B %d at %H:%M")
    return f"Event '{title}' added for {nice_time} (ID: {event_id})."


def list_calendar_events_tool(args: dict) -> str:
    from_str = args.get("from_time")
    to_str = args.get("to_time")
    from_ts = datetime.datetime.fromisoformat(from_str).timestamp() if from_str else None
    to_ts = datetime.datetime.fromisoformat(to_str).timestamp() if to_str else None
    events = list_calendar_events(from_ts, to_ts)
    if not events:
        return "No upcoming events found."
    lines = []
    for e in events:
        dt = datetime.datetime.fromtimestamp(e["start_time"])
        time_str = dt.strftime("%a %b %d %H:%M")
        lines.append(f"- [{e['id']}] {time_str}: {e['title']}")
        if e.get("description"):
            lines.append(f"  {e['description']}")
    return "\n".join(lines)


def delete_calendar_event_tool(args: dict) -> str:
    event_id = args["event_id"]
    if delete_calendar_event(event_id):
        return f"Event {event_id} deleted."
    return f"Event {event_id} not found."


# ── Dispatch map ──────────────────────────────────────────────────────────────

TOOL_MAP = {
    "search_web":           search_web,
    "save_memory":          save_memory_tool,
    "query_memories":       query_memories_tool,
    "get_transcript":       get_transcript_tool,
    "set_reminder":         set_reminder_tool,
    "get_datetime":         get_datetime_tool,
    "search_x":             search_x,
    "add_calendar_event":   add_calendar_event_tool,
    "list_calendar_events": list_calendar_events_tool,
    "delete_calendar_event": delete_calendar_event_tool,
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

    _fn("add_calendar_event", "Add a calendar event for the user.",
        {
            "title":       {"type": "string", "description": "Event title"},
            "start_time":  {"type": "string", "description": "Start time in ISO 8601 (e.g., 2026-03-30T14:00:00)"},
            "end_time":    {"type": "string", "description": "End time in ISO 8601 (optional)"},
            "description": {"type": "string", "description": "Additional details (optional)"},
            "all_day":     {"type": "boolean", "description": "True if all-day event"},
        }, ["title", "start_time"]),

    _fn("list_calendar_events", "List upcoming calendar events for the user.",
        {
            "from_time": {"type": "string", "description": "Start of range in ISO 8601 (optional, defaults to now)"},
            "to_time":   {"type": "string", "description": "End of range in ISO 8601 (optional)"},
        }, []),

    _fn("delete_calendar_event", "Delete a calendar event by its ID.",
        {"event_id": {"type": "integer", "description": "The event ID to delete"}}, ["event_id"]),
]
