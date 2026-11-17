Repository: 5ryal/Tathkira (branch: main)

Goal:
Implement the draft step exactly as described in specs/draft/SPEC.md.

Read first:
- RULES.md
- specs/draft/SPEC.md

Files to change (only these):
- src/tathkira/agent/draft.py
- src/tathkira/agent/llm.py (new)
- tests/test_draft.py (new)
- requirements.txt (add google-genai only)

Constraints:
- Follow the SPEC's contract, LLM instruction, validation rules and error message exactly.
- Tests must use fake llm functions only. No network calls in tests.
- call_gemini reads LLM_API_KEY and LLM_MODEL from .env using python-dotenv. Never hardcode a key.
- Expected test values must be written by hand.
- Do not modify anything in prompts/ or specs/.

Acceptance:
- All acceptance criteria in the SPEC pass as tests.
- pytest passes with no failures, including the existing normalise tests.

Output:
List every changed file with one line on each.