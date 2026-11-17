# SPEC: Web page

## Goal
One page where a requester submits an Arabic request, a reviewer edits and
approves or rejects the drafted ticket, and approved tickets are listed.

## Source files
- src/tathkira/web/app.py
- src/tathkira/web/static/index.html (new)
- tests/test_web.py (new)
- requirements.txt (add httpx only)

## Endpoints
- GET /  → serves index.html
- POST /api/draft  body {"text": str}
  → 200 {"original", "normalised", "ticket": {title, description,
    acceptance_criteria}, "gaps": [{kind, source_phrase, requirement, note}]}
  → 400 {"detail": <ValueError message>} for empty, too long or invalid llm reply
  → 503 {"detail": "LLM unavailable, try again"} for any other llm error
- POST /api/tickets  body {"original", "ticket", "gaps", "edited": bool}
  → 201 {"id": int}
  → 400 if title or description is empty, or acceptance_criteria is empty
- GET /api/tickets  → 200 list of saved tickets, newest first

## Wiring
- The llm and the database path are FastAPI dependencies:
  get_llm() returns call_gemini; get_db_path() returns "tathkira.db"
- Tests replace both with app.dependency_overrides
- init_db runs when the app starts

## Page (index.html, plain HTML + JavaScript, no frameworks)
- Request section: textarea (dir="rtl") + "Generate ticket" button
- Review section: editable title, description, and criteria (one per line);
  gaps listed below:
  - assumed: "<source_phrase> → <requirement>" + note
  - unclear: source_phrase highlighted + note
  - "Approve" and "Reject" buttons
- edited = true if any field changed before Approve
- Reject clears the review section and saves nothing
- Approved tickets section: list from GET /api/tickets, refreshed after Approve
- Errors shown as a red message
- UI text in English

## Acceptance criteria
- Given a fake llm, POST /api/draft with a valid request → 200 with ticket and gaps
- Failure path: POST /api/draft with "   " → 400 {"detail": "empty request"}
- Failure path: llm raises a non-ValueError exception → 503
- POST /api/tickets then GET /api/tickets → the saved ticket is returned
- Boundary: POST /api/tickets with empty acceptance_criteria → 400
- GET / → 200 HTML

## Constraints
- Tests use fake llm and a temporary database only; no network calls
- Only new dependency: httpx
- Run with: uvicorn tathkira.web.app:app --app-dir src

## Non-goals
- No login, no styling framework, no editing saved tickets