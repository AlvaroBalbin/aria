"""
Dual-mode database: SQLite (local-first) with optional Supabase cloud sync.

SQLite is always the primary store — data never leaves the device.
Supabase mirrors writes in the background for cloud backup/access.
If Supabase is unavailable, everything still works locally.
"""
import sqlite3
import time
import threading
from config import SUPABASE_URL, SUPABASE_KEY

# ── SQLite (primary) ────────────────────────────────────────────────────────

DB_PATH = "aria.db"
_local = threading.local()


def _get_conn():
    if not hasattr(_local, "conn") or _local.conn is None:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _local.conn = conn
    return _local.conn


def init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS transcripts (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            ts       REAL    NOT NULL,
            speaker  TEXT    NOT NULL DEFAULT 'User',
            text     TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS memories (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            ts    REAL    NOT NULL,
            key   TEXT    NOT NULL,
            value TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS conversations (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            ts   REAL    NOT NULL,
            role TEXT    NOT NULL,
            text TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reminders (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            ts   REAL    NOT NULL,
            text TEXT    NOT NULL,
            due  REAL
        );
        CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key);
        CREATE INDEX IF NOT EXISTS idx_transcripts_ts ON transcripts(ts);
        CREATE INDEX IF NOT EXISTS idx_conversations_ts ON conversations(ts);
    """)
    # Deduplicate existing memories: keep newest per key
    dupes = conn.execute("""
        DELETE FROM memories WHERE id NOT IN (
            SELECT MAX(id) FROM memories GROUP BY key
        )
    """)
    if dupes.rowcount > 0:
        print(f"[DB] Cleaned up {dupes.rowcount} duplicate memories")
    conn.commit()
    _init_supabase()


# ── Supabase (optional cloud sync) ──────────────────────────────────────────

_supa = None
_supa_ok = False
_supa_error = ""


def _init_supabase():
    global _supa, _supa_ok, _supa_error
    if not SUPABASE_URL or not SUPABASE_KEY:
        _supa_error = "Supabase credentials not configured"
        print(f"[DB] {_supa_error} — running local-only")
        return
    try:
        from supabase import create_client
        _supa = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Test connectivity
        _supa.table("transcripts").select("id").limit(1).execute()
        _supa_ok = True
        print("[DB] Supabase connected — cloud sync active")
    except Exception as e:
        _supa_error = str(e)
        _supa_ok = False
        print(f"[DB] Supabase unavailable: {e} — running local-only")


def get_supabase_status() -> dict:
    return {"connected": _supa_ok, "error": _supa_error if not _supa_ok else ""}


def _sync(table: str, data: dict):
    """Fire-and-forget write to Supabase in a background thread. Never blocks."""
    if not _supa_ok or not _supa:
        return
    def _do():
        try:
            _supa.table(table).insert(data).execute()
        except Exception:
            pass
    threading.Thread(target=_do, daemon=True).start()


# ── Public API ──────────────────────────────────────────────────────────────

def save_transcript(text: str, speaker: str = "User"):
    ts = time.time()
    conn = _get_conn()
    conn.execute("INSERT INTO transcripts (ts, speaker, text) VALUES (?, ?, ?)", (ts, speaker, text))
    conn.commit()
    _sync("transcripts", {"ts": ts, "speaker": speaker, "text": text})


def save_memory(key: str, value: str):
    ts = time.time()
    conn = _get_conn()
    # Dedup: if an identical key already exists, update the value instead of inserting
    existing = conn.execute(
        "SELECT id FROM memories WHERE key = ?", (key,)
    ).fetchone()
    if existing:
        conn.execute("UPDATE memories SET value = ?, ts = ? WHERE id = ?", (value, ts, existing["id"]))
    else:
        conn.execute("INSERT INTO memories (ts, key, value) VALUES (?, ?, ?)", (ts, key, value))
    conn.commit()
    _sync("memories", {"ts": ts, "key": key, "value": value})


def query_memories(query: str, limit: int = 20) -> list[dict]:
    conn = _get_conn()
    # Split query into individual words and match ANY word in key or value
    # This handles "dog name" matching a memory about "Rex" keyed as "pet_dog_name"
    words = [w.strip() for w in query.split() if len(w.strip()) >= 2]
    if not words:
        words = [query]
    conditions = []
    params = []
    for word in words[:5]:  # cap at 5 terms to avoid huge queries
        conditions.append("(key LIKE ? COLLATE NOCASE OR value LIKE ? COLLATE NOCASE)")
        params.extend([f"%{word}%", f"%{word}%"])
    where = " OR ".join(conditions)
    params.append(limit)
    rows = conn.execute(
        f"SELECT key, value, ts FROM memories WHERE {where} ORDER BY ts DESC LIMIT ?",
        params
    ).fetchall()
    return [dict(r) for r in rows]


def get_all_memories(limit: int = 20) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT key, value, ts FROM memories ORDER BY ts DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_transcript(minutes: int = 30) -> list[dict]:
    since = time.time() - minutes * 60
    conn = _get_conn()
    rows = conn.execute(
        "SELECT ts, speaker, text FROM transcripts WHERE ts > ? ORDER BY ts ASC", (since,)
    ).fetchall()
    return [dict(r) for r in rows]


def save_conversation_turn(role: str, text: str):
    ts = time.time()
    conn = _get_conn()
    conn.execute("INSERT INTO conversations (ts, role, text) VALUES (?, ?, ?)", (ts, role, text))
    conn.commit()
    _sync("conversations", {"ts": ts, "role": role, "text": text})


def get_conversation_history(limit: int = 10) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT role, text FROM conversations ORDER BY ts DESC LIMIT ?", (limit,)
    ).fetchall()
    return list(reversed([dict(r) for r in rows]))


def save_reminder(text: str, due: float | None = None):
    ts = time.time()
    conn = _get_conn()
    conn.execute("INSERT INTO reminders (ts, text, due) VALUES (?, ?, ?)", (ts, text, due))
    conn.commit()
    _sync("reminders", {"ts": ts, "text": text, "due": due})


def get_due_reminders() -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, text FROM reminders WHERE due IS NOT NULL AND due <= ?", (time.time(),)
    ).fetchall()
    return [dict(r) for r in rows]


def delete_reminder(reminder_id: int):
    conn = _get_conn()
    conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    conn.commit()
