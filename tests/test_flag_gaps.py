"""Tests for the flag gaps step (specs/flag_gaps/SPEC.md)."""

from typing import Callable

import pytest

from tathkira.agent.draft import Ticket
from tathkira.agent.flag_gaps import Gap, flag_gaps

REQUEST = "ابي استرجع كلمة السر بسرعة"

TICKET = Ticket(
    title="Restore the expired password reset link",
    description="Users cannot reset their password. The link should stay valid longer.",
    acceptance_criteria=[
        "The reset link stays valid for 30 minutes.",
        "An expired link shows a clear error message.",
    ],
)

ASSUMED_REPLY = """{
  "gaps": [
    {
      "kind": "assumed",
      "source_phrase": "بسرعة",
      "requirement": "The reset link stays valid for 30 minutes.",
      "note": "Treated as a 30 minute link lifetime."
    }
  ]
}"""

UNCLEAR_REPLY = """{
  "gaps": [
    {
      "kind": "unclear",
      "source_phrase": "بسرعة",
      "requirement": "",
      "note": "No lifetime or deadline is given."
    }
  ]
}"""

EXPECTED_PROMPT = (
    "You are reviewing a developer ticket drafted from an informal Arabic "
    "request. Find vague or ambiguous phrases in the request. For each one, "
    'use kind "assumed" if the ticket includes a reasonable interpretation of '
    'it, or "unclear" if it is too vague to interpret and the ticket leaves it '
    'out. Return only JSON: {"gaps": [{"kind", "source_phrase" (exact words '
    'copied from the request), "requirement" (the exact acceptance criterion '
    'it produced, or "" if unclear), "note" (short English explanation)}]}. '
    "Return at most 5 gaps, or an empty list if the request is clear. "
    "Request: ابي استرجع كلمة السر بسرعة\n"
    'Ticket: {"title": "Restore the expired password reset link", '
    '"description": "Users cannot reset their password. The link should stay '
    'valid longer.", "acceptance_criteria": ["The reset link stays valid for '
    '30 minutes.", "An expired link shows a clear error message."]}'
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


def test_returns_assumed_gap() -> None:
    """A valid assumed gap is returned as a Gap."""
    gaps = flag_gaps(REQUEST, TICKET, _fake_llm(ASSUMED_REPLY))

    assert gaps == [
        Gap(
            kind="assumed",
            source_phrase="بسرعة",
            requirement="The reset link stays valid for 30 minutes.",
            note="Treated as a 30 minute link lifetime.",
        )
    ]


def test_returns_unclear_gap() -> None:
    """A valid unclear gap is returned with an empty requirement."""
    gaps = flag_gaps(REQUEST, TICKET, _fake_llm(UNCLEAR_REPLY))

    assert gaps == [
        Gap(
            kind="unclear",
            source_phrase="بسرعة",
            requirement="",
            note="No lifetime or deadline is given.",
        )
    ]


def test_empty_gaps_returns_empty_list() -> None:
    """An empty gaps list means the request is clear."""
    assert flag_gaps(REQUEST, TICKET, _fake_llm('{"gaps": []}')) == []


def test_sends_the_spec_instruction_with_request_and_ticket() -> None:
    """The llm receives the spec instruction, the request and the ticket JSON."""
    llm, prompts = _capturing_llm('{"gaps": []}')

    flag_gaps(REQUEST, TICKET, llm)

    assert prompts == [EXPECTED_PROMPT]


# --- Assumed / unclear requirement rules ---------------------------------


def test_assumed_requirement_not_in_ticket_raises() -> None:
    """An assumed gap must point at one of the ticket's criteria."""
    reply = """{
      "gaps": [
        {
          "kind": "assumed",
          "source_phrase": "بسرعة",
          "requirement": "The reset link stays valid for 10 minutes.",
          "note": "Guessed a shorter lifetime."
        }
      ]
    }"""
    with pytest.raises(ValueError) as excinfo:
        flag_gaps(REQUEST, TICKET, _fake_llm(reply))
    assert str(excinfo.value) == "invalid llm reply"


def test_unclear_with_requirement_raises() -> None:
    """An unclear gap must leave the requirement empty."""
    reply = """{
      "gaps": [
        {
          "kind": "unclear",
          "source_phrase": "بسرعة",
          "requirement": "The reset link stays valid for 30 minutes.",
          "note": "Should have been left empty."
        }
      ]
    }"""
    with pytest.raises(ValueError) as excinfo:
        flag_gaps(REQUEST, TICKET, _fake_llm(reply))
    assert str(excinfo.value) == "invalid llm reply"


# --- Source phrase rules -------------------------------------------------


def test_source_phrase_not_in_request_raises() -> None:
    """A phrase that is not in the request is rejected."""
    reply = """{
      "gaps": [
        {
          "kind": "unclear",
          "source_phrase": "بشكل جميل",
          "requirement": "",
          "note": "Phrase is not in the request."
        }
      ]
    }"""
    with pytest.raises(ValueError) as excinfo:
        flag_gaps(REQUEST, TICKET, _fake_llm(reply))
    assert str(excinfo.value) == "invalid llm reply"


def test_empty_source_phrase_raises() -> None:
    """An empty source phrase is rejected."""
    reply = """{
      "gaps": [
        {
          "kind": "unclear",
          "source_phrase": "",
          "requirement": "",
          "note": "Nothing to quote."
        }
      ]
    }"""
    with pytest.raises(ValueError) as excinfo:
        flag_gaps(REQUEST, TICKET, _fake_llm(reply))
    assert str(excinfo.value) == "invalid llm reply"


# --- Kind and field rules ------------------------------------------------


def test_unknown_kind_raises() -> None:
    """A kind other than assumed or unclear is rejected."""
    reply = """{
      "gaps": [
        {
          "kind": "guess",
          "source_phrase": "بسرعة",
          "requirement": "",
          "note": "Wrong kind."
        }
      ]
    }"""
    with pytest.raises(ValueError) as excinfo:
        flag_gaps(REQUEST, TICKET, _fake_llm(reply))
    assert str(excinfo.value) == "invalid llm reply"


def test_missing_field_raises() -> None:
    """A gap object without the note field is rejected."""
    reply = """{
      "gaps": [
        {
          "kind": "unclear",
          "source_phrase": "بسرعة",
          "requirement": ""
        }
      ]
    }"""
    with pytest.raises(ValueError) as excinfo:
        flag_gaps(REQUEST, TICKET, _fake_llm(reply))
    assert str(excinfo.value) == "invalid llm reply"


def test_empty_note_raises() -> None:
    """An empty note is rejected."""
    reply = """{
      "gaps": [
        {
          "kind": "unclear",
          "source_phrase": "بسرعة",
          "requirement": "",
          "note": ""
        }
      ]
    }"""
    with pytest.raises(ValueError) as excinfo:
        flag_gaps(REQUEST, TICKET, _fake_llm(reply))
    assert str(excinfo.value) == "invalid llm reply"


def test_gap_not_an_object_raises() -> None:
    """A gap that is not a JSON object is rejected."""
    reply = '{"gaps": ["بسرعة"]}'
    with pytest.raises(ValueError) as excinfo:
        flag_gaps(REQUEST, TICKET, _fake_llm(reply))
    assert str(excinfo.value) == "invalid llm reply"


# --- Invalid reply shapes ------------------------------------------------


def test_invalid_json_raises() -> None:
    """A reply that is not JSON is rejected."""
    with pytest.raises(ValueError) as excinfo:
        flag_gaps(REQUEST, TICKET, _fake_llm("not json"))
    assert str(excinfo.value) == "invalid llm reply"


def test_missing_gaps_key_raises() -> None:
    """A reply without the gaps key is rejected."""
    with pytest.raises(ValueError) as excinfo:
        flag_gaps(REQUEST, TICKET, _fake_llm('{"items": []}'))
    assert str(excinfo.value) == "invalid llm reply"


def test_gaps_not_a_list_raises() -> None:
    """A gaps value that is not a list is rejected."""
    with pytest.raises(ValueError) as excinfo:
        flag_gaps(REQUEST, TICKET, _fake_llm('{"gaps": {}}'))
    assert str(excinfo.value) == "invalid llm reply"


# --- Gap count boundaries -----------------------------------------------


def test_five_gaps_is_accepted() -> None:
    """Five gaps is the upper bound and is accepted."""
    reply = """{
      "gaps": [
        {"kind": "unclear", "source_phrase": "بسرعة", "requirement": "", "note": "One."},
        {"kind": "unclear", "source_phrase": "بسرعة", "requirement": "", "note": "Two."},
        {"kind": "unclear", "source_phrase": "بسرعة", "requirement": "", "note": "Three."},
        {"kind": "unclear", "source_phrase": "بسرعة", "requirement": "", "note": "Four."},
        {"kind": "unclear", "source_phrase": "بسرعة", "requirement": "", "note": "Five."}
      ]
    }"""
    gaps = flag_gaps(REQUEST, TICKET, _fake_llm(reply))

    assert [gap.note for gap in gaps] == ["One.", "Two.", "Three.", "Four.", "Five."]


def test_six_gaps_raises() -> None:
    """Six gaps is above the limit and is rejected."""
    reply = """{
      "gaps": [
        {"kind": "unclear", "source_phrase": "بسرعة", "requirement": "", "note": "One."},
        {"kind": "unclear", "source_phrase": "بسرعة", "requirement": "", "note": "Two."},
        {"kind": "unclear", "source_phrase": "بسرعة", "requirement": "", "note": "Three."},
        {"kind": "unclear", "source_phrase": "بسرعة", "requirement": "", "note": "Four."},
        {"kind": "unclear", "source_phrase": "بسرعة", "requirement": "", "note": "Five."},
        {"kind": "unclear", "source_phrase": "بسرعة", "requirement": "", "note": "Six."}
      ]
    }"""
    with pytest.raises(ValueError) as excinfo:
        flag_gaps(REQUEST, TICKET, _fake_llm(reply))
    assert str(excinfo.value) == "invalid llm reply"
