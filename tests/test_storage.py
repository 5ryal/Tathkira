"""Tests for the SQLite storage step (specs/storage_pipeline/SPEC.md)."""

import sqlite3
from datetime import datetime, timedelta

import pytest

from tathkira.agent.draft import Ticket
from tathkira.agent.flag_gaps import Gap
from tathkira.storage.db import init_db, list_tickets, save_ticket

ORIGINAL = "  ابي  أسترجع كلمةُ السر بسرعة  "

TICKET = Ticket(
    title="Restore the expired password reset link",
    description="Users cannot reset their password. The link should stay valid longer.",
    acceptance_criteria=[
        "The reset link stays valid for 30 minutes.",
        "An expired link shows a clear error message.",
    ],
)

GAPS = [
    Gap(
        kind="assumed",
        source_phrase="بسرعة",
        requirement="The reset link stays valid for 30 minutes.",
        note="Treated as a 30 minute link lifetime.",
    )
]


def test_empty_database_returns_empty_list(tmp_path) -> None:
    """A freshly initialised database has no tickets."""
    path = str(tmp_path / "tickets.db")

    init_db(path)

    assert list_tickets(path) == []


def test_init_db_is_idempotent(tmp_path) -> None:
    """Calling init_db twice keeps the table and its rows."""
    path = str(tmp_path / "tickets.db")

    init_db(path)
    save_ticket(path, ORIGINAL, TICKET, GAPS, False)
    init_db(path)

    assert len(list_tickets(path)) == 1


def test_save_ticket_returns_increasing_ids(tmp_path) -> None:
    """Each saved ticket gets the next id."""
    path = str(tmp_path / "tickets.db")

    first = save_ticket(path, ORIGINAL, TICKET, GAPS, False)
    second = save_ticket(path, ORIGINAL, TICKET, GAPS, False)

    assert (first, second) == (1, 2)


def test_saved_ticket_round_trips(tmp_path) -> None:
    """Every stored field comes back with the same value."""
    path = str(tmp_path / "tickets.db")

    save_ticket(path, ORIGINAL, TICKET, GAPS, False)
    rows = list_tickets(path)

    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == 1
    assert row["original"] == "  ابي  أسترجع كلمةُ السر بسرعة  "
    assert row["title"] == "Restore the expired password reset link"
    assert row["description"] == (
        "Users cannot reset their password. The link should stay valid longer."
    )
    assert row["acceptance_criteria"] == [
        "The reset link stays valid for 30 minutes.",
        "An expired link shows a clear error message.",
    ]
    assert row["edited"] is False


def test_created_at_is_utc_iso(tmp_path) -> None:
    """created_at is an ISO 8601 string in UTC."""
    path = str(tmp_path / "tickets.db")

    save_ticket(path, ORIGINAL, TICKET, GAPS, False)
    created_at = list_tickets(path)[0]["created_at"]

    parsed = datetime.fromisoformat(created_at)
    assert parsed.utcoffset() == timedelta(0)


def test_gaps_round_trip_as_list_of_dicts(tmp_path) -> None:
    """Gaps come back as plain dicts with the same values."""
    path = str(tmp_path / "tickets.db")

    save_ticket(path, ORIGINAL, TICKET, GAPS, False)

    assert list_tickets(path)[0]["gaps"] == [
        {
            "kind": "assumed",
            "source_phrase": "بسرعة",
            "requirement": "The reset link stays valid for 30 minutes.",
            "note": "Treated as a 30 minute link lifetime.",
        }
    ]


def test_arabic_is_stored_unescaped(tmp_path) -> None:
    """Arabic text is written as UTF-8 JSON, not as \\u escapes."""
    path = str(tmp_path / "tickets.db")
    arabic_ticket = Ticket(
        title="استرجاع كلمة السر",
        description="يبقى الرابط صالحا 30 دقيقة.",
        acceptance_criteria=[
            "يبقى الرابط صالحا 30 دقيقة.",
            "تظهر رسالة خطأ واضحة.",
        ],
    )

    save_ticket(path, ORIGINAL, arabic_ticket, GAPS, False)

    with sqlite3.connect(path) as conn:
        criteria_text, gaps_text = conn.execute(
            "SELECT acceptance_criteria, gaps FROM tickets"
        ).fetchone()

    assert "\\u" not in criteria_text
    assert "يبقى الرابط صالحا 30 دقيقة." in criteria_text
    assert "\\u" not in gaps_text
    assert "بسرعة" in gaps_text


def test_edited_flag_true_is_returned(tmp_path) -> None:
    """A ticket saved as edited comes back with edited set to True."""
    path = str(tmp_path / "tickets.db")

    save_ticket(path, ORIGINAL, TICKET, GAPS, True)

    assert list_tickets(path)[0]["edited"] is True


def test_newest_ticket_comes_first(tmp_path) -> None:
    """Two saved tickets are listed newest first."""
    path = str(tmp_path / "tickets.db")
    older = Ticket(
        title="Older ticket",
        description="Saved first.",
        acceptance_criteria=["A.", "B."],
    )
    newer = Ticket(
        title="Newer ticket",
        description="Saved second.",
        acceptance_criteria=["C.", "D."],
    )

    save_ticket(path, "ابي تقرير", older, [], False)
    save_ticket(path, "ابي تقرير اسبوعي", newer, [], False)

    assert [row["title"] for row in list_tickets(path)] == ["Newer ticket", "Older ticket"]


def test_init_db_in_missing_folder_raises(tmp_path) -> None:
    """A path inside a folder that does not exist fails loudly."""
    path = str(tmp_path / "missing" / "tickets.db")

    with pytest.raises(sqlite3.OperationalError):
        init_db(path)
