"""Flag vague or ambiguous phrases in a request against a drafted ticket."""

import json
from dataclasses import asdict, dataclass
from typing import Any, Callable

from tathkira.agent.draft import Ticket

MAX_GAPS = 5
KIND_ASSUMED = "assumed"
KIND_UNCLEAR = "unclear"

_INVALID_REPLY = "invalid llm reply"

_INSTRUCTION = (
    "You are reviewing a developer ticket drafted from an informal Arabic "
    "request. Find vague or ambiguous phrases in the request. For each one, "
    'use kind "assumed" if the ticket includes a reasonable interpretation of '
    'it, or "unclear" if it is too vague to interpret and the ticket leaves it '
    'out. Return only JSON: {"gaps": [{"kind", "source_phrase" (exact words '
    'copied from the request), "requirement" (the exact acceptance criterion '
    'it produced, or "" if unclear), "note" (short English explanation)}]}. '
    "Return at most 5 gaps, or an empty list if the request is clear. "
    "Request: "
)


@dataclass
class Gap:
    """A vague phrase the ticket either interpreted or left out."""

    kind: str
    source_phrase: str
    requirement: str
    note: str


def flag_gaps(normalised: str, ticket: Ticket, llm: Callable[[str], str]) -> list[Gap]:
    """Flag vague phrases in a request using the given llm function."""
    return _parse_gaps(llm(_build_prompt(normalised, ticket)), normalised, ticket)


def _build_prompt(normalised: str, ticket: Ticket) -> str:
    """Build the review instruction with the request and the ticket as JSON."""
    ticket_json = json.dumps(asdict(ticket), ensure_ascii=False)
    return f"{_INSTRUCTION}{normalised}\nTicket: {ticket_json}"


def _parse_gaps(reply: str, normalised: str, ticket: Ticket) -> list[Gap]:
    """Parse and validate an llm reply into a list of gaps."""
    try:
        data: Any = json.loads(reply)
    except (json.JSONDecodeError, TypeError):
        raise ValueError(_INVALID_REPLY) from None
    if not isinstance(data, dict):
        raise ValueError(_INVALID_REPLY)

    raw_gaps = data.get("gaps")
    if not isinstance(raw_gaps, list) or len(raw_gaps) > MAX_GAPS:
        raise ValueError(_INVALID_REPLY)

    return [_build_gap(item, normalised, ticket) for item in raw_gaps]


def _build_gap(item: Any, normalised: str, ticket: Ticket) -> Gap:
    """Validate one raw gap object and turn it into a Gap."""
    if not isinstance(item, dict):
        raise ValueError(_INVALID_REPLY)

    kind = item.get("kind")
    source_phrase = item.get("source_phrase")
    requirement = item.get("requirement")
    note = item.get("note")

    if not _is_filled_text(kind) or not _is_filled_text(source_phrase):
        raise ValueError(_INVALID_REPLY)
    if not _is_filled_text(note) or not isinstance(requirement, str):
        raise ValueError(_INVALID_REPLY)
    if kind not in (KIND_ASSUMED, KIND_UNCLEAR):
        raise ValueError(_INVALID_REPLY)
    if source_phrase not in normalised:
        raise ValueError(_INVALID_REPLY)
    if kind == KIND_ASSUMED and requirement not in ticket.acceptance_criteria:
        raise ValueError(_INVALID_REPLY)
    if kind == KIND_UNCLEAR and requirement != "":
        raise ValueError(_INVALID_REPLY)

    return Gap(kind=kind, source_phrase=source_phrase, requirement=requirement, note=note)


def _is_filled_text(value: Any) -> bool:
    """Return True when the value is a non-blank string."""
    return isinstance(value, str) and bool(value.strip())
