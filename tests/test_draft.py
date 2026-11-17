"""Tests for the draft step (specs/draft/SPEC.md)."""

from typing import Callable

import pytest

from tathkira.agent.draft import Ticket, draft_ticket

VALID_REPLY = """{
  "title": "Restore the expired password reset link",
  "description": "Users cannot reset their password because the emailed link expires too quickly. The link should stay valid long enough to be used.",
  "acceptance_criteria": [
    "The reset link stays valid for 30 minutes.",
    "An expired link shows a clear error message.",
    "A new link can be requested from the reset page."
  ]
}"""

EXPECTED_PROMPT = (
    "You are a requirements analyst. Convert the following informal Arabic "
    "request into a developer ticket in formal, everyday developer English. "
    "Return only JSON with keys: title (one short line), description "
    "(2-3 sentences), acceptance_criteria (2-5 testable statements). "
    "If a detail is vague but its meaning can be reasonably inferred, include "
    "your interpretation. If a detail is too vague to interpret, leave it out. "
    "Request: ابي صفحة login جديدة"
)


def _fake_llm(reply: str) -> Callable[[str], str]:
    """Return a fake llm that always replies with the given text."""

    def llm(prompt: str) -> str:
        return reply

    return llm


def _capturing_llm(reply: str) -> tuple[Callable[[str], str], list[str]]:
    """Return a fake llm plus the list of prompts it was given."""
    prompts: list[str] = []

    def llm(prompt: str) -> str:
        prompts.append(prompt)
        return reply

    return llm, prompts


# --- Acceptance criteria ---------------------------------------------------


def test_returns_ticket_from_valid_reply() -> None:
    """A valid JSON reply becomes a Ticket with the same values."""
    ticket = draft_ticket("ابي صفحة login جديدة", _fake_llm(VALID_REPLY))

    assert ticket == Ticket(
        title="Restore the expired password reset link",
        description=(
            "Users cannot reset their password because the emailed link expires "
            "too quickly. The link should stay valid long enough to be used."
        ),
        acceptance_criteria=[
            "The reset link stays valid for 30 minutes.",
            "An expired link shows a clear error message.",
            "A new link can be requested from the reset page.",
        ],
    )


def test_sends_the_spec_instruction_with_the_request() -> None:
    """The llm receives the spec's instruction followed by the request text."""
    llm, prompts = _capturing_llm(VALID_REPLY)

    draft_ticket("ابي صفحة login جديدة", llm)

    assert prompts == [EXPECTED_PROMPT]


def test_prompt_keeps_the_arabic_request_verbatim() -> None:
    """The normalised request is appended unchanged, including English words."""
    llm, prompts = _capturing_llm(VALID_REPLY)

    draft_ticket("ابي تقرير اسبوعي", llm)

    assert prompts[0].endswith("Request: ابي تقرير اسبوعي")


# --- Invalid replies ------------------------------------------------------


def test_invalid_json_raises() -> None:
    """A reply that is not JSON is rejected with the spec's message."""
    with pytest.raises(ValueError) as excinfo:
        draft_ticket("ابي صفحة login جديدة", _fake_llm("not json"))
    assert str(excinfo.value) == "invalid llm reply"


def test_json_array_reply_raises() -> None:
    """A JSON value that is not an object is rejected."""
    with pytest.raises(ValueError) as excinfo:
        draft_ticket("ابي تقرير", _fake_llm('["title", "description"]'))
    assert str(excinfo.value) == "invalid llm reply"


def test_missing_title_raises() -> None:
    """A reply without the title key is rejected."""
    reply = """{
      "description": "Users cannot reset their password.",
      "acceptance_criteria": ["Link works.", "Expired link errors."]
    }"""
    with pytest.raises(ValueError) as excinfo:
        draft_ticket("ابي تقرير", _fake_llm(reply))
    assert str(excinfo.value) == "invalid llm reply"


def test_missing_description_raises() -> None:
    """A reply without the description key is rejected."""
    reply = """{
      "title": "Restore the reset link",
      "acceptance_criteria": ["Link works.", "Expired link errors."]
    }"""
    with pytest.raises(ValueError) as excinfo:
        draft_ticket("ابي تقرير", _fake_llm(reply))
    assert str(excinfo.value) == "invalid llm reply"


def test_missing_acceptance_criteria_raises() -> None:
    """A reply without the acceptance_criteria key is rejected."""
    reply = """{
      "title": "Restore the reset link",
      "description": "Users cannot reset their password."
    }"""
    with pytest.raises(ValueError) as excinfo:
        draft_ticket("ابي تقرير", _fake_llm(reply))
    assert str(excinfo.value) == "invalid llm reply"


def test_empty_title_raises() -> None:
    """An empty title string is rejected."""
    reply = """{
      "title": "",
      "description": "Users cannot reset their password.",
      "acceptance_criteria": ["Link works.", "Expired link errors."]
    }"""
    with pytest.raises(ValueError) as excinfo:
        draft_ticket("ابي تقرير", _fake_llm(reply))
    assert str(excinfo.value) == "invalid llm reply"


def test_blank_description_raises() -> None:
    """A whitespace-only description is rejected."""
    reply = """{
      "title": "Restore the reset link",
      "description": "   ",
      "acceptance_criteria": ["Link works.", "Expired link errors."]
    }"""
    with pytest.raises(ValueError) as excinfo:
        draft_ticket("ابي تقرير", _fake_llm(reply))
    assert str(excinfo.value) == "invalid llm reply"


def test_criteria_not_a_list_raises() -> None:
    """A string instead of a list of criteria is rejected."""
    reply = """{
      "title": "Restore the reset link",
      "description": "Users cannot reset their password.",
      "acceptance_criteria": "Link works."
    }"""
    with pytest.raises(ValueError) as excinfo:
        draft_ticket("ابي تقرير", _fake_llm(reply))
    assert str(excinfo.value) == "invalid llm reply"


def test_blank_criterion_raises() -> None:
    """An empty statement inside the criteria list is rejected."""
    reply = """{
      "title": "Restore the reset link",
      "description": "Users cannot reset their password.",
      "acceptance_criteria": ["Link works.", ""]
    }"""
    with pytest.raises(ValueError) as excinfo:
        draft_ticket("ابي تقرير", _fake_llm(reply))
    assert str(excinfo.value) == "invalid llm reply"


# --- Criteria boundaries -------------------------------------------------


def test_single_criterion_raises() -> None:
    """One criterion is below the 2-5 range and is rejected."""
    reply = """{
      "title": "Restore the reset link",
      "description": "Users cannot reset their password.",
      "acceptance_criteria": ["Link works."]
    }"""
    with pytest.raises(ValueError) as excinfo:
        draft_ticket("ابي تقرير", _fake_llm(reply))
    assert str(excinfo.value) == "invalid llm reply"


def test_six_criteria_raises() -> None:
    """Six criteria is above the 2-5 range and is rejected."""
    reply = """{
      "title": "Restore the reset link",
      "description": "Users cannot reset their password.",
      "acceptance_criteria": ["A.", "B.", "C.", "D.", "E.", "F."]
    }"""
    with pytest.raises(ValueError) as excinfo:
        draft_ticket("ابي تقرير", _fake_llm(reply))
    assert str(excinfo.value) == "invalid llm reply"


def test_two_criteria_is_accepted() -> None:
    """Two criteria is the lower bound and is accepted."""
    reply = """{
      "title": "Restore the reset link",
      "description": "Users cannot reset their password.",
      "acceptance_criteria": ["Link works.", "Expired link errors."]
    }"""
    ticket = draft_ticket("ابي تقرير", _fake_llm(reply))

    assert ticket.acceptance_criteria == ["Link works.", "Expired link errors."]


def test_five_criteria_is_accepted() -> None:
    """Five criteria is the upper bound and is accepted."""
    reply = """{
      "title": "Restore the reset link",
      "description": "Users cannot reset their password.",
      "acceptance_criteria": ["A.", "B.", "C.", "D.", "E."]
    }"""
    ticket = draft_ticket("ابي تقرير", _fake_llm(reply))

    assert ticket.acceptance_criteria == ["A.", "B.", "C.", "D.", "E."]


# --- Tolerated replies ---------------------------------------------------


def test_extra_keys_are_ignored() -> None:
    """Unknown keys in the reply do not change the ticket."""
    reply = """{
      "title": "Restore the reset link",
      "description": "Users cannot reset their password.",
      "acceptance_criteria": ["Link works.", "Expired link errors."],
      "priority": "high",
      "notes": "ignored"
    }"""
    ticket = draft_ticket("ابي تقرير", _fake_llm(reply))

    assert ticket == Ticket(
        title="Restore the reset link",
        description="Users cannot reset their password.",
        acceptance_criteria=["Link works.", "Expired link errors."],
    )
