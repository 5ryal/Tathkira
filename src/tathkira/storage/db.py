"""SQLite storage for approved tickets."""

import json
import sqlite3
from contextlib import closing
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from tathkira.agent.draft import Ticket
from tathkira.agent.flag_gaps import Gap

DEFAULT_PATH = "tathkira.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    original TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    acceptance_criteria TEXT NOT NULL,
    gaps TEXT NOT NULL,
    edited INTEGER NOT NULL
)
"""


def init_db(path: str = DEFAULT_PATH) -> None:
    """Create the tickets table if it does not exist yet."""
    with closing(_connect(path)) as conn, conn:
        conn.execute(_SCHEMA)


def save_ticket(path: str, original: str, ticket: Ticket, gaps: list[Gap], edited: bool) -> int:
    """Save one approved ticket and return its id."""
    init_db(path)
    with closing(_connect(path)) as conn, conn:
        cursor = conn.execute(
            "INSERT INTO tickets "
            "(created_at, original, title, description, acceptance_criteria, gaps, edited) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                _utc_now(),
                original,
                ticket.title,
                ticket.description,
                _dump(ticket.acceptance_criteria),
                _dump([asdict(gap) for gap in gaps]),
                int(edited),
            ),
        )
        return int(cursor.lastrowid or 0)


def list_tickets(path: str) -> list[dict]:
    """Return all saved tickets, newest first."""
    init_db(path)
    with closing(_connect(path)) as conn, conn:
        rows = conn.execute(
            "SELECT * FROM tickets ORDER BY created_at DESC, id DESC"
        ).fetchall()
    return [_row_to_ticket(row) for row in rows]


def _connect(path: str) -> sqlite3.Connection:
    """Open a connection that returns rows by column name."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _utc_now() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _dump(value: Any) -> str:
    """Serialise a value as JSON text with Arabic left unescaped."""
    return json.dumps(value, ensure_ascii=False)


def _row_to_ticket(row: sqlite3.Row) -> dict:
    """Turn a database row into a ticket dict with parsed JSON fields."""
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "original": row["original"],
        "title": row["title"],
        "description": row["description"],
        "acceptance_criteria": json.loads(row["acceptance_criteria"]),
        "gaps": json.loads(row["gaps"]),
        "edited": bool(row["edited"]),
    }
