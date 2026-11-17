# RULES.md — Tathkira

## Project
Tathkira turns informal Arabic requests into structured developer tickets.
No ticket is saved until a human reviewer approves it.

## Stack
- Python 3.12, FastAPI, SQLite, pytest
- Code lives in src/tathkira/, tests in tests/
- Do not add dependencies without them being listed in the prompt

## Code rules
- Small functions with type hints and a one-line docstring
- Agent steps stay separate: normalise.py, draft.py, flag_gaps.py
- Every function that is added must have at least one test, including a failure case
- Arabic text must be handled as UTF-8 everywhere

## Security
- Never write real API keys, tokens or personal data in any file
- Secrets come only from .env, which is never committed
- Use only fake or synthetic data in tests and examples

## Workflow
- Never modify or delete anything in prompts/ or specs/
- Only change files that the prompt names
- Every change must keep pytest passing
- End every reply with a list of changed files and one line on each