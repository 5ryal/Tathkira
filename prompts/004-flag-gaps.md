Repository: 5ryal/Tathkira (branch: main)

Goal:
Implement specs/flag_gaps/SPEC.md: the flag gaps step and the small draft instruction update.

Read first:
- RULES.md
- specs/flag_gaps/SPEC.md
- specs/draft/SPEC.md

Files to change (only these):
- src/tathkira/agent/flag_gaps.py
- src/tathkira/agent/draft.py (instruction update only)
- tests/test_flag_gaps.py (new)
- tests/test_draft.py (update the prompt-text test only)

Constraints:
- Follow the SPEC's contract, LLM instruction, validation rules and error message exactly.
- Reuse the existing Ticket dataclass from draft.py.
- Tests must use fake llm functions only. No network calls.
- Expected test values must be written by hand.
- No new dependencies.
- Do not modify anything in prompts/ or specs/.

Acceptance:
- All acceptance criteria in the SPEC pass as tests.
- pytest passes with no failures, including existing tests.

Output:
List every changed file with one line on each. Flag any decision you made that is not in the SPEC.