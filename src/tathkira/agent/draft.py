"""Draft a structured developer ticket from a normalised request."""

import json
from dataclasses import dataclass
from typing import Any, Callable

MIN_CRITERIA = 2
MAX_CRITERIA = 5

_INVALID_REPLY = "invalid llm reply"

_INSTRUCTION = (
    "You are a requirements analyst. Convert the following informal Arabic "
    "request into a developer ticket in formal, everyday developer English. "
    "Return only JSON with keys: title (one short line), description "
    "(2-3 sentences), acceptance_criteria (2-5 testable statements). "
    "If a detail is vague but its meaning can be reasonably inferred, include "
    "your interpretation. If a detail is too vague to interpret, leave it out. "
    "Request: "
)


@dataclass
class Ticket:
    """A developer ticket drafted from a normalised request."""

    title: str
    description: str
    acceptance_criteria: list[str]


def draft_ticket(normalised: str, llm: Callable[[str], str]) -> Ticket:
    """Draft a ticket from a normalised request using the given llm function."""
    return _parse_ticket(llm(_INSTRUCTION + normalised))


def _parse_ticket(reply: str) -> Ticket:
    """Parse and validate an llm reply into a Ticket."""
    try:
        data: Any = json.loads(reply)
    except (json.JSONDecodeError, TypeError):
        raise ValueError(_INVALID_REPLY) from None
    if not isinstance(data, dict):
        raise ValueError(_INVALID_REPLY)

    title = data.get("title")
    description = data.get("description")
    criteria = data.get("acceptance_criteria")

    if not _is_filled_text(title) or not _is_filled_text(description):
        raise ValueError(_INVALID_REPLY)
    if not isinstance(criteria, list):
        raise ValueError(_INVALID_REPLY)
    if not MIN_CRITERIA <= len(criteria) <= MAX_CRITERIA:
        raise ValueError(_INVALID_REPLY)
    if not all(_is_filled_text(item) for item in criteria):
        raise ValueError(_INVALID_REPLY)

    return Ticket(title=title, description=description, acceptance_criteria=list(criteria))


def _is_filled_text(value: Any) -> bool:
    """Return True when the value is a non-blank string."""
    return isinstance(value, str) and bool(value.strip())
