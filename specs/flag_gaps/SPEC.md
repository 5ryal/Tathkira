# SPEC: Flag gaps step (+ draft instruction update)

## Goal
Flag vague or ambiguous phrases in the request so the reviewer can see
what the LLM interpreted and what it could not interpret.

## Source files
- src/tathkira/agent/flag_gaps.py
- src/tathkira/agent/draft.py (instruction update only)
- tests/test_flag_gaps.py (new)
- tests/test_draft.py (update the prompt-text test only)

## Change to the draft step
Add these two sentences to the draft LLM instruction, before "Request:":
"If a detail is vague but its meaning can be reasonably inferred, include
your interpretation. If a detail is too vague to interpret, leave it out."
Nothing else in the draft step changes.

## Input / output contract
- flag_gaps(normalised: str, ticket: Ticket, llm: Callable[[str], str]) -> list[Gap]
- Gap is a dataclass:
  - kind: str ("assumed" or "unclear")
  - source_phrase: str (exact words from the request)
  - requirement: str (exact acceptance criterion it produced; "" if unclear)
  - note: str (short English explanation)

## LLM instruction (sent by flag_gaps)
"You are reviewing a developer ticket drafted from an informal Arabic
request. Find vague or ambiguous phrases in the request. For each one,
use kind "assumed" if the ticket includes a reasonable interpretation of
it, or "unclear" if it is too vague to interpret and the ticket leaves it
out. Return only JSON: {"gaps": [{"kind", "source_phrase" (exact words
copied from the request), "requirement" (the exact acceptance criterion
it produced, or "" if unclear), "note" (short English explanation)}]}.
Return at most 5 gaps, or an empty list if the request is clear.
Request: <normalised text>
Ticket: <ticket as JSON>"

## Validation (rules, not LLM)
Raise ValueError("invalid llm reply") if:
- The reply is not valid JSON, or "gaps" is missing or not a list
- There are more than 5 gaps
- Any field is missing, or kind / source_phrase / note is empty
- kind is not "assumed" or "unclear"
- source_phrase does not appear in the normalised request
- kind is "assumed" and requirement does not exactly match one of the
  ticket's acceptance criteria
- kind is "unclear" and requirement is not ""

## Acceptance criteria
- Given a fake llm returning one valid "assumed" gap → one Gap returned
- Given a fake llm returning one valid "unclear" gap → one Gap returned
- Given {"gaps": []} → empty list returned
- Failure path: "assumed" gap whose requirement is not in the ticket → ValueError
- Failure path: source_phrase not in the request → ValueError
- Boundary: 5 gaps accepted; 6 gaps → ValueError

## Constraints
- Tests use fake llm functions only; no network calls
- Expected test values written by hand

## Non-goals
- No saving, no UI, no pipeline wiring