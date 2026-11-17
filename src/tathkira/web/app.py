"""FastAPI application for the ticket review page."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Callable

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from tathkira.agent.draft import Ticket
from tathkira.agent.flag_gaps import Gap
from tathkira.agent.llm import call_gemini
from tathkira.pipeline import PipelineResult, run_pipeline
from tathkira.storage.db import DEFAULT_PATH, init_db, list_tickets, save_ticket

_STATIC_DIR = Path(__file__).parent / "static"
_INVALID_TICKET = "invalid ticket"
_LLM_UNAVAILABLE = "LLM unavailable, try again"


class DraftRequest(BaseModel):
    """Request body for the draft endpoint."""

    text: str


class TicketBody(BaseModel):
    """Ticket fields sent by the page."""

    title: str
    description: str
    acceptance_criteria: list[str]


class GapBody(BaseModel):
    """Gap fields sent by the page."""

    kind: str
    source_phrase: str
    requirement: str
    note: str


class SaveRequest(BaseModel):
    """Request body for saving an approved ticket."""

    original: str
    ticket: TicketBody
    gaps: list[GapBody]
    edited: bool


def get_llm() -> Callable[[str], str]:
    """Return the llm function used by the draft step."""
    return call_gemini


def get_db_path() -> str:
    """Return the SQLite database path."""
    return DEFAULT_PATH


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Create the tickets table when the app starts."""
    init_db(application.dependency_overrides.get(get_db_path, get_db_path)())
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_index() -> FileResponse:
    """Serve the review page."""
    return FileResponse(_STATIC_DIR / "index.html")


@app.post("/api/draft")
def create_draft(
    body: DraftRequest,
    llm: Callable[[str], str] = Depends(get_llm),
) -> dict:
    """Run the pipeline on a request and return the draft with its gaps."""
    try:
        result = run_pipeline(body.text, llm)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=_LLM_UNAVAILABLE) from exc
    return _draft_payload(result)


@app.post("/api/tickets", status_code=201)
def create_ticket(body: SaveRequest, db_path: str = Depends(get_db_path)) -> dict:
    """Save one approved ticket and return its id."""
    ticket = Ticket(
        title=body.ticket.title,
        description=body.ticket.description,
        acceptance_criteria=list(body.ticket.acceptance_criteria),
    )
    if not ticket.title.strip() or not ticket.description.strip():
        raise HTTPException(status_code=400, detail=_INVALID_TICKET)
    if not ticket.acceptance_criteria:
        raise HTTPException(status_code=400, detail=_INVALID_TICKET)

    gaps = [Gap(**gap.model_dump()) for gap in body.gaps]
    ticket_id = save_ticket(db_path, body.original, ticket, gaps, body.edited)
    return {"id": ticket_id}


@app.get("/api/tickets")
def read_tickets(db_path: str = Depends(get_db_path)) -> list[dict]:
    """Return all saved tickets, newest first."""
    return list_tickets(db_path)


def _draft_payload(result: PipelineResult) -> dict:
    """Turn a pipeline result into the JSON the page expects."""
    return {
        "original": result.original,
        "normalised": result.normalised,
        "ticket": {
            "title": result.ticket.title,
            "description": result.ticket.description,
            "acceptance_criteria": list(result.ticket.acceptance_criteria),
        },
        "gaps": [
            {
                "kind": gap.kind,
                "source_phrase": gap.source_phrase,
                "requirement": gap.requirement,
                "note": gap.note,
            }
            for gap in result.gaps
        ],
    }
