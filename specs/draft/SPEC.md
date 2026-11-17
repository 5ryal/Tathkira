# SPEC: Draft step

## Goal
Turn a normalised Arabic request into a structured developer ticket
written in formal, everyday developer English.

## Source files
- src/tathkira/agent/draft.py
- src/tathkira/agent/llm.py (new)
- tests/test_draft.py (new)
- requirements.txt (add google-genai)

## Input / output contract
- draft_ticket(normalised: str, llm: Callable[[str], str]) -> Ticket
- llm is any function that takes a prompt and returns the reply text
- Ticket is a dataclass:
  - title: str
  - description: str
  - acceptance_criteria: list[str]

## LLM instruction (sent by draft_ticket)
"You are a requirements analyst. Convert the following informal Arabic
request into a developer ticket in formal, everyday developer English.
Return only JSON with keys: title (one short line), description
(2-3 sentences), acceptance_criteria (2-5 testable statements).
Request: <normalised text>"

## Real LLM (llm.py)
- call_gemini(prompt: str) -> str
- Reads LLM_API_KEY and LLM_MODEL from .env
- Asks Gemini for a JSON response

## Error contract
- Reply is not valid JSON → ValueError("invalid llm reply")
- Missing key, empty string, or acceptance_criteria not 2-5 items
  → ValueError("invalid llm reply")

## Acceptance criteria
- Given a fake llm returning valid JSON
  When draft_ticket is called
  Then a Ticket with the same title, description and criteria is returned
- Failure path: Given a fake llm returning "not json"
  Then ValueError("invalid llm reply") is raised
- Boundary case: 5 criteria is accepted; 6 criteria raises ValueError

## Constraints
- Tests use only fake llm functions; no network calls in tests
- call_gemini is not unit tested; it is checked manually in the demo

## Non-goals
- No gap flagging (separate step), no saving, no UI

## Security
- API key only from .env, never in code, tests or logs