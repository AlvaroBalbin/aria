import sqlite3
import time
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
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
    """)
    conn.commit()
    conn.close()


def save_transcript(text: str, speaker: str = "User"):
    conn = get_conn()
    conn.execute("INSERT INTO transcripts (ts, speaker, text) VALUES (?, ?, ?)",
                 (time.time(), speaker, text))
    conn.commit()
    conn.close()


def save_memory(key: str, value: str):
    conn = get_conn()
    conn.execute("INSERT INTO memories (ts, key, value) VALUES (?, ?, ?)",
                 (time.time(), key, value))
    conn.commit()
    conn.close()


def query_memories(query: str, limit: int = 20) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT key, value, ts FROM memories WHERE key LIKE ? OR value LIKE ? ORDER BY ts DESC LIMIT ?",
        (f"%{query}%", f"%{query}%", limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_memories(limit: int = 20) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT key, value, ts FROM memories ORDER BY ts DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_transcript(minutes: int = 30) -> list[dict]:
    since = time.time() - minutes * 60
    conn = get_conn()
    rows = conn.execute(
        "SELECT ts, speaker, text FROM transcripts WHERE ts > ? ORDER BY ts ASC",
        (since,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_conversation_turn(role: str, text: str):
    conn = get_conn()
    conn.execute("INSERT INTO conversations (ts, role, text) VALUES (?, ?, ?)",
                 (time.time(), role, text))
    conn.commit()
    conn.close()


def get_conversation_history(limit: int = 10) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT role, text FROM conversations ORDER BY ts DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return list(reversed([dict(r) for r in rows]))


def save_reminder(text: str, due: float | None = None):
    conn = get_conn()
    conn.execute("INSERT INTO reminders (ts, text, due) VALUES (?, ?, ?)",
                 (time.time(), text, due))
    conn.commit()
    conn.close()
