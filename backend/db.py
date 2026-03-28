"""
Supabase database layer — replaces SQLite.

Run this SQL in your Supabase SQL Editor before first use:

    CREATE TABLE transcripts (
      id bigserial primary key,
      ts float8 not null,
      speaker text not null default 'User',
      text text not null
    );

    CREATE TABLE memories (
      id bigserial primary key,
      ts float8 not null,
      key text not null,
      value text not null
    );

    CREATE TABLE conversations (
      id bigserial primary key,
      ts float8 not null,
      role text not null,
      text text not null
    );

    CREATE TABLE reminders (
      id bigserial primary key,
      ts float8 not null,
      text text not null,
      due float8
    );

    ALTER TABLE transcripts   DISABLE ROW LEVEL SECURITY;
    ALTER TABLE memories      DISABLE ROW LEVEL SECURITY;
    ALTER TABLE conversations DISABLE ROW LEVEL SECURITY;
    ALTER TABLE reminders     DISABLE ROW LEVEL SECURITY;
"""
import time
from config import SUPABASE_URL, SUPABASE_KEY

_client = None
_db_warned = False


def _get():
    global _client
    if _client is None:
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def _warn(fn: str, e: Exception):
    """Print a DB warning once per function to avoid log spam."""
    global _db_warned
    if not _db_warned:
        print(f"[DB] Supabase unavailable — {fn}: {e}")
        print("[DB] Create tables in Supabase SQL Editor (see db.py header). Running without persistence.")
        _db_warned = True


def init_db():
    """No-op: tables are managed via Supabase dashboard."""
    pass


def save_transcript(text: str, speaker: str = "User"):
    try:
        _get().table("transcripts").insert({"ts": time.time(), "speaker": speaker, "text": text}).execute()
    except Exception as e:
        _warn("save_transcript", e)


def save_memory(key: str, value: str):
    try:
        _get().table("memories").insert({"ts": time.time(), "key": key, "value": value}).execute()
    except Exception as e:
        _warn("save_memory", e)


def query_memories(query: str, limit: int = 20) -> list[dict]:
    try:
        q = query.replace("%", "").replace("_", "")
        result = (
            _get().table("memories")
            .select("key,value,ts")
            .or_(f"key.ilike.%{q}%,value.ilike.%{q}%")
            .order("ts", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data
    except Exception as e:
        _warn("query_memories", e)
        return []


def get_all_memories(limit: int = 20) -> list[dict]:
    try:
        result = (
            _get().table("memories")
            .select("key,value,ts")
            .order("ts", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data
    except Exception as e:
        _warn("get_all_memories", e)
        return []


def get_transcript(minutes: int = 30) -> list[dict]:
    try:
        since = time.time() - minutes * 60
        result = (
            _get().table("transcripts")
            .select("ts,speaker,text")
            .gt("ts", since)
            .order("ts")
            .execute()
        )
        return result.data
    except Exception as e:
        _warn("get_transcript", e)
        return []


def save_conversation_turn(role: str, text: str):
    try:
        _get().table("conversations").insert({"ts": time.time(), "role": role, "text": text}).execute()
    except Exception as e:
        _warn("save_conversation_turn", e)


def get_conversation_history(limit: int = 10) -> list[dict]:
    try:
        result = (
            _get().table("conversations")
            .select("role,text")
            .order("ts", desc=True)
            .limit(limit)
            .execute()
        )
        return list(reversed(result.data))
    except Exception as e:
        _warn("get_conversation_history", e)
        return []


def save_reminder(text: str, due: float | None = None):
    try:
        _get().table("reminders").insert({"ts": time.time(), "text": text, "due": due}).execute()
    except Exception as e:
        _warn("save_reminder", e)


def get_due_reminders() -> list[dict]:
    try:
        result = (
            _get().table("reminders")
            .select("id,text")
            .filter("due", "not.is", "null")
            .lte("due", time.time())
            .execute()
        )
        return result.data
    except Exception as e:
        _warn("get_due_reminders", e)
        return []


def delete_reminder(reminder_id: int):
    try:
        _get().table("reminders").delete().eq("id", reminder_id).execute()
    except Exception as e:
        _warn("delete_reminder", e)
