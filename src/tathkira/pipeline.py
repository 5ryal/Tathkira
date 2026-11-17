"""Run the full ticket workflow on a request."""

from dataclasses import dataclass
from typing import Callable

from tathkira.agent.draft import Ticket, draft_ticket
from tathkira.agent.flag_gaps import Gap, flag_gaps
from tathkira.agent.normalise import normalise_request


@dataclass
class PipelineResult:
    """Everything the workflow produced for one request."""

    original: str
    normalised: str
    ticket: Ticket
    gaps: list[Gap]


def run_pipeline(text: str, llm: Callable[[str], str]) -> PipelineResult:
    """Run normalise, draft and flag gaps on a request without saving anything."""
    request = normalise_request(text)
    ticket = draft_ticket(request.normalised, llm)
    gaps = flag_gaps(request.normalised, ticket, llm)
    return PipelineResult(
        original=request.original,
        normalised=request.normalised,
        ticket=ticket,
        gaps=gaps,
    )
