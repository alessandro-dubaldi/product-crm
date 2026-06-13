"""
SQLite store for interviews and weekly digests.
DB file: data/productcrm.db (gitignored).
"""
import os
import sqlite3
from datetime import datetime

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "productcrm.db")


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                company     TEXT NOT NULL,
                contact     TEXT NOT NULL,
                date        TEXT NOT NULL,
                transcript  TEXT NOT NULL,
                exec_summary TEXT NOT NULL,
                created_at  TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS digests (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                content    TEXT NOT NULL,
                date_range TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


# ── Interviews ─────────────────────────────────────────────────────────────────

def save_interview(
    company: str,
    contact: str,
    date: str,
    transcript: str,
    exec_summary: str,
) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO interviews (company, contact, date, transcript, exec_summary, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (company, contact, date, transcript, exec_summary, datetime.utcnow().isoformat()),
        )
        return cur.lastrowid


def list_interviews() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, company, contact, date, exec_summary, created_at "
            "FROM interviews ORDER BY date DESC, created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_interview(interview_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM interviews WHERE id = ?", (interview_id,)
        ).fetchone()
    return dict(row) if row else None


# ── Digests ────────────────────────────────────────────────────────────────────

def save_digest(content: str, date_range: str) -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO digests (content, date_range, created_at) VALUES (?, ?, ?)",
            (content, date_range, datetime.utcnow().isoformat()),
        )
        return cur.lastrowid


def list_digests() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, date_range, created_at FROM digests ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_digest(digest_id: int) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM digests WHERE id = ?", (digest_id,)
        ).fetchone()
    return dict(row) if row else None
