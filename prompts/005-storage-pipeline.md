Repository: 5ryal/Tathkira (branch: main)

Goal:
Implement specs/storage_pipeline/SPEC.md.

Read first:
- RULES.md
- specs/storage_pipeline/SPEC.md

Files to change (only these):
- src/tathkira/storage/db.py
- src/tathkira/pipeline.py (new)
- tests/test_storage.py (new)
- tests/test_pipeline.py (new)
- .gitignore (add tathkira.db only)

Constraints:
- Follow the SPEC's contracts exactly.
- Reuse the existing Ticket, Gap and NormalisedRequest dataclasses.
- Tests use a temporary database and fake llm functions only.
- Expected test values must be written by hand.
- No new dependencies.
- Do not modify anything in prompts/ or specs/.

Acceptance:
- All acceptance criteria in the SPEC pass as tests.
- pytest passes with no failures, including existing tests.

Output:
List every changed file with one line on each. Flag any decision you made that is not in the SPEC.