"""Tests for the web page endpoints (specs/web/SPEC.md)."""

from contextlib import contextmanager
from typing import Callable, Iterator

from fastapi.testclient import TestClient

from tathkira.web.app import app, get_db_path, get_llm

REQUEST = "  ابي  أسترجع كلمة السر بسرعة ١٠ ثواني  "

DRAFT_REPLY = """{
  "title": "Restore the expired password reset link",
  "description": "Users cannot reset their password because the link expires too quickly. The link should stay valid longer.",
  "acceptance_criteria": [
    "The reset link stays valid for 30 minutes.",
    "An expired link shows a clear error message."
  ]
}"""

GAPS_REPLY = """{
  "gaps": [
    {
      "kind": "assumed",
      "source_phrase": "بسرعة",
      "requirement": "The reset link stays valid for 30 minutes.",
      "note": "Treated as a 30 minute link lifetime."
    }
  ]
}"""


def _scripted_llm(replies: list[str]) -> Callable[[str], str]:
    """Return a fake llm that replies in order."""
    prompts: list[str] = []

    def llm(prompt: str) -> str:
        prompts.append(prompt)
        return replies[len(prompts) - 1]

    return llm


def _failing_llm() -> Callable[[str], str]:
    """Return a fake llm that fails the way a network error would."""

    def llm(prompt: str) -> str:
        raise RuntimeError("network down")

    return llm


@contextmanager
def _client(tmp_path, llm: Callable[[str], str]) -> Iterator[TestClient]:
    """Yield a client wired to the fake llm and a temporary database."""
    app.dependency_overrides[get_db_path] = lambda: str(tmp_path / "tickets.db")
    app.dependency_overrides[get_llm] = lambda: llm
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db_path, None)
        app.dependency_overrides.pop(get_llm, None)


def test_index_returns_html(tmp_path) -> None:
    """GET / serves the review page."""
    with _client(tmp_path, _scripted_llm([])) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Generate ticket" in response.text


def test_draft_returns_ticket_and_gaps(tmp_path) -> None:
    """A valid request comes back as the draft and its gaps."""
    llm = _scripted_llm([DRAFT_REPLY, GAPS_REPLY])

    with _client(tmp_path, llm) as client:
        response = client.post("/api/draft", json={"text": REQUEST})

    assert response.status_code == 200
    assert response.json() == {
        "original": "  ابي  أسترجع كلمة السر بسرعة ١٠ ثواني  ",
        "normalised": "ابي استرجع كلمة السر بسرعة 10 ثواني",
        "ticket": {
            "title": "Restore the expired password reset link",
            "description": (
                "Users cannot reset their password because the link expires too "
                "quickly. The link should stay valid longer."
            ),
            "acceptance_criteria": [
                "The reset link stays valid for 30 minutes.",
                "An expired link shows a clear error message.",
            ],
        },
        "gaps": [
            {
                "kind": "assumed",
                "source_phrase": "بسرعة",
                "requirement": "The reset link stays valid for 30 minutes.",
                "note": "Treated as a 30 minute link lifetime.",
            }
        ],
    }


def test_draft_empty_request_returns_400(tmp_path) -> None:
    """A whitespace-only request is a 400 with the step's message."""
    with _client(tmp_path, _scripted_llm([])) as client:
        response = client.post("/api/draft", json={"text": "   "})

    assert response.status_code == 400
    assert response.json() == {"detail": "empty request"}


def test_draft_too_long_request_returns_400(tmp_path) -> None:
    """A request over the limit is a 400 with the step's message."""
    with _client(tmp_path, _scripted_llm([])) as client:
        response = client.post("/api/draft", json={"text": "ا" * 2001})

    assert response.status_code == 400
    assert response.json() == {"detail": "request too long"}


def test_draft_invalid_reply_returns_400(tmp_path) -> None:
    """A malformed llm reply is a 400, not a 503."""
    with _client(tmp_path, _scripted_llm(["not json"])) as client:
        response = client.post("/api/draft", json={"text": REQUEST})

    assert response.status_code == 400
    assert response.json() == {"detail": "invalid llm reply"}


def test_draft_llm_error_returns_503(tmp_path) -> None:
    """Any other llm failure is a 503 with a fixed message."""
    with _client(tmp_path, _failing_llm()) as client:
        response = client.post("/api/draft", json={"text": REQUEST})

    assert response.status_code == 503
    assert response.json() == {"detail": "LLM unavailable, try again"}


def test_save_then_list_returns_the_ticket(tmp_path) -> None:
    """An approved ticket is saved and then listed."""
    body = {
        "original": "ابي استرجع كلمة السر بسرعة",
        "ticket": {
            "title": "Restore the expired password reset link",
            "description": "The link should stay valid longer.",
            "acceptance_criteria": [
                "The reset link stays valid for 30 minutes.",
                "An expired link shows a clear error message.",
            ],
        },
        "gaps": [
            {
                "kind": "assumed",
                "source_phrase": "بسرعة",
                "requirement": "The reset link stays valid for 30 minutes.",
                "note": "Treated as a 30 minute link lifetime.",
            }
        ],
        "edited": True,
    }

    with _client(tmp_path, _scripted_llm([])) as client:
        saved = client.post("/api/tickets", json=body)
        listed = client.get("/api/tickets")

    assert saved.status_code == 201
    assert saved.json() == {"id": 1}
    assert listed.status_code == 200
    rows = listed.json()
    assert len(rows) == 1
    assert rows[0]["id"] == 1
    assert rows[0]["original"] == "ابي استرجع كلمة السر بسرعة"
    assert rows[0]["title"] == "Restore the expired password reset link"
    assert rows[0]["description"] == "The link should stay valid longer."
    assert rows[0]["acceptance_criteria"] == [
        "The reset link stays valid for 30 minutes.",
        "An expired link shows a clear error message.",
    ]
    assert rows[0]["gaps"] == [
        {
            "kind": "assumed",
            "source_phrase": "بسرعة",
            "requirement": "The reset link stays valid for 30 minutes.",
            "note": "Treated as a 30 minute link lifetime.",
        }
    ]
    assert rows[0]["edited"] is True


def test_save_with_empty_criteria_returns_400(tmp_path) -> None:
    """A ticket without acceptance criteria is rejected."""
    body = {
        "original": "ابي تقرير",
        "ticket": {
            "title": "Weekly report",
            "description": "Send a weekly report.",
            "acceptance_criteria": [],
        },
        "gaps": [],
        "edited": False,
    }

    with _client(tmp_path, _scripted_llm([])) as client:
        response = client.post("/api/tickets", json=body)

    assert response.status_code == 400
    assert response.json() == {"detail": "invalid ticket"}


def test_save_with_empty_title_returns_400(tmp_path) -> None:
    """A ticket with a blank title is rejected."""
    body = {
        "original": "ابي تقرير",
        "ticket": {
            "title": "   ",
            "description": "Send a weekly report.",
            "acceptance_criteria": ["The report arrives on Sunday."],
        },
        "gaps": [],
        "edited": False,
    }

    with _client(tmp_path, _scripted_llm([])) as client:
        response = client.post("/api/tickets", json=body)

    assert response.status_code == 400
    assert response.json() == {"detail": "invalid ticket"}
