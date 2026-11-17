Repository: 5ryal/Tathkira (branch: main)

Goal:
Set up the initial project skeleton for Tathkira, a Python project. Do not implement any features yet.

Context:
Tathkira is an agentic workflow that turns informal Arabic requests into structured developer tickets. A human reviewer approves, edits or rejects each ticket before it is saved. Stack: Python 3.11+, FastAPI for a thin web page, SQLite for ticket storage, pytest for tests. The LLM provider will be configured later through environment variables.

Create:
1. Folder structure:
   - src/tathkira/ (package with __init__.py)
   - src/tathkira/agent/ (empty modules: normalise.py, draft.py, flag_gaps.py)
   - src/tathkira/web/ (empty app.py)
   - src/tathkira/storage/ (empty db.py)
   - tests/ (one placeholder test that passes)
   - specs/ (empty, for SPEC.md files)
2. requirements.txt with only: fastapi, uvicorn, pytest, python-dotenv
3. .env.example with fake placeholder values only: LLM_API_KEY=your-key-here, LLM_MODEL=your-model-here
4. Make sure .gitignore includes .env

Constraints:
- No real API keys or secrets anywhere.
- No feature logic, only empty modules with a one-line docstring each.
- Do not add any dependencies beyond the four listed.
- Do not modify or delete anything in the prompts/ folder.

Non-goals:
- No agent logic, no UI, no database schema yet.

Acceptance criteria:
- Given a fresh clone, when I run "pip install -r