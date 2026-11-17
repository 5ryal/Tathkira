# SPEC: Storage + pipeline

## Goal
Run the full workflow on a request, and save tickets only after a human approves them.

## Source files
- src/tathkira/storage/db.py
- src/tathkira/pipeline.py (new)
- tests/test_storage.py (new)
- tests/test_pipeline.py (new)
- .gitignore (add tathkira.db)

## Pipeline contract
- run_pipeline(text: str, llm: Callable[[str], str]) -> PipelineResult
- Runs normalise_request → draft_ticket → flag_gaps, in that order
- PipelineResult is a dataclass:
  - original: str
  - normalised: str
  - ticket: Ticket
  - gaps: list[Gap]
- Saves nothing
- Any error from a step is raised unchanged

## Storage contract (SQLite, standard library sqlite3)
- init_db(path: str = "tathkira.db") -> None
  Creates the tickets table if it does not exist
- save_ticket(path: str, original: str, ticket: Ticket, gaps: list[Gap], edited: bool) -> int
  Saves one approved ticket and returns its id
- list_tickets(path: str) -> list[dict]
  Returns all saved tickets, newest first
- Each saved ticket stores: id, created_at (UTC, ISO format), original,
  title, description, acceptance_criteria, gaps, edited
- acceptance_criteria and gaps are stored as JSON text with Arabic unescaped
- list_tickets returns acceptance_criteria as a list and gaps as a list of dicts

## Acceptance criteria
- Given a fake llm returning a valid draft reply then a valid gaps reply
  When run_pipeline is called
  Then a PipelineResult with the expected ticket and gaps is returned
- Failure path: Given a fake llm returning "not json" for the draft
  Then ValueError("invalid llm reply") is raised
- Boundary: Given an empty request
  Then ValueError("empty request") is raised and the llm is never called
- Given a saved ticket with Arabic text
  When list_tickets is called
  Then the same values come back, Arabic unchanged
- Given an empty database, list_tickets returns []
- Given two saved tickets, list_tickets returns the newer one first
- The edited flag is stored and returned correctly

## Constraints
- Tests use a temporary database (pytest tmp_path), never tathkira.db
- Tests use fake llm functions only; no network calls
- Expected test values written by hand
- No new dependencies

## Non-goals
- No web page, no deleting or updating tickets, rejected tickets are not saved