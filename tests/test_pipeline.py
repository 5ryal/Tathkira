"""Tests for the pipeline (specs/storage_pipeline/SPEC.md)."""

from typing import Callable

import pytest

from tathkira.agent.draft import Ticket
from tathkira.agent.flag_gaps import Gap
from tathkira.pipeline import PipelineResult, run_pipeline

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


def _scripted_llm(replies: list[str]) -> tuple[Callable[[str], str], list[str]]:
    """Return a fake llm that replies in order, plus the prompts it saw."""
    prompts: list[str] = []

    def llm(prompt: str) -> str:
        prompts.append(prompt)
        return replies[len(prompts) - 1]

    return llm, prompts


def _counting_llm() -> tuple[Callable[[str], str], list[str]]:
    """Return a fake llm that records calls and never returns a usable reply."""
    return _scripted_llm(["not json", "not json", "not json"])


def test_returns_pipeline_result() -> None:
    """The pipeline returns the normalised request, the ticket and the gaps."""
    llm, _ = _scripted_llm([DRAFT_REPLY, GAPS_REPLY])

    result = run_pipeline(REQUEST, llm)

    assert result == PipelineResult(
        original="  ابي  أسترجع كلمة السر بسرعة ١٠ ثواني  ",
        normalised="ابي استرجع كلمة السر بسرعة 10 ثواني",
        ticket=Ticket(
            title="Restore the expired password reset link",
            description=(
                "Users cannot reset their password because the link expires too "
                "quickly. The link should stay valid longer."
            ),
            acceptance_criteria=[
                "The reset link stays valid for 30 minutes.",
                "An expired link shows a clear error message.",
            ],
        ),
        gaps=[
            Gap(
                kind="assumed",
                source_phrase="بسرعة",
                requirement="The reset link stays valid for 30 minutes.",
                note="Treated as a 30 minute link lifetime.",
            )
        ],
    )


def test_calls_the_llm_twice_draft_first() -> None:
    """The draft prompt is sent before the gap review prompt."""
    llm, prompts = _scripted_llm([DRAFT_REPLY, GAPS_REPLY])

    run_pipeline(REQUEST, llm)

    assert len(prompts) == 2
    assert prompts[0].startswith("You are a requirements analyst.")
    assert prompts[1].startswith("You are reviewing a developer ticket")


def test_draft_error_is_raised_unchanged() -> None:
    """An invalid draft reply surfaces as the draft step's error."""
    llm, _ = _scripted_llm(["not json"])

    with pytest.raises(ValueError) as excinfo:
        run_pipeline(REQUEST, llm)

    assert str(excinfo.value) == "invalid llm reply"


def test_gap_error_is_raised_unchanged() -> None:
    """An invalid gap reply surfaces as the gap step's error."""
    llm, _ = _scripted_llm([DRAFT_REPLY, "not json"])

    with pytest.raises(ValueError) as excinfo:
        run_pipeline(REQUEST, llm)

    assert str(excinfo.value) == "invalid llm reply"


def test_empty_request_raises_before_the_llm() -> None:
    """An empty request fails in normalise and the llm is never called."""
    llm, prompts = _counting_llm()

    with pytest.raises(ValueError) as excinfo:
        run_pipeline("", llm)

    assert str(excinfo.value) == "empty request"
    assert prompts == []


def test_whitespace_request_raises_before_the_llm() -> None:
    """A whitespace-only request never reaches the llm."""
    llm, prompts = _counting_llm()

    with pytest.raises(ValueError) as excinfo:
        run_pipeline("   \n  ", llm)

    assert str(excinfo.value) == "empty request"
    assert prompts == []


def test_pipeline_saves_nothing(tmp_path, monkeypatch) -> None:
    """Running the pipeline does not create a database file."""
    monkeypatch.chdir(tmp_path)
    llm, _ = _scripted_llm([DRAFT_REPLY, GAPS_REPLY])

    run_pipeline(REQUEST, llm)

    assert not (tmp_path / "tathkira.db").exists()
