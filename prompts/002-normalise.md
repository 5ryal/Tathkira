Repository: 5ryal/Tathkira (branch: main)

Goal:
Implement the normalise step exactly as described in specs/normalise/SPEC.md.

Read first:
- RULES.md
- specs/normalise/SPEC.md

Files to change (only these):
- src/tathkira/agent/normalise.py
- tests/test_normalise.py (new)

Constraints:
- Follow the SPEC's input/output contract, rules and error messages exactly.
- Standard library only. No new dependencies.
- Expected test outputs must be written by hand, not computed by calling the function.
- Do not modify anything in prompts/ or specs/.

Acceptance:
- All acceptance criteria in the SPEC pass as tests.
- pytest passes with no failures.

Output:
List every changed file with one line on each.