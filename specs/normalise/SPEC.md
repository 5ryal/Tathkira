# SPEC: Normalise step

## Goal
Clean an informal Arabic request into a consistent form before it is sent
to the LLM, while keeping the original text for the reviewer.

## Source files
- src/tathkira/agent/normalise.py
- tests/test_normalise.py

## Input / output contract
- Function: normalise_request(text: str) -> NormalisedRequest      [NEW]
- NormalisedRequest is a dataclass with two fields:                 [NEW]
  - original: str   (the input, unchanged)
  - normalised: str (the cleaned text)

## Normalisation rules (applied to the normalised field only)
1. Remove Arabic diacritics (tashkeel, U+064B–U+0652 and U+0670)
2. Remove tatweel (ـ, U+0640)
3. Replace أ إ آ with ا
4. Replace Arabic-Indic digits (٠–٩) with Western digits (0–9)
5. Collapse all runs of spaces, tabs and line breaks into a single space,
   and trim spaces from both ends
6. Leave English words, ة and ى unchanged

## Error contract
- Empty or whitespace-only input → raises ValueError("empty request")      [NEW]
- Input longer than 2000 characters → raises ValueError("request too long")
- Length is measured on the original input                                 [NEW]

## Acceptance criteria
- Given "  ابي  أسترجع كلمةُ السر بسرعة ١٠ ثواني  "
  When normalise_request is called
  Then normalised == "ابي استرجع كلمة السر بسرعة 10 ثواني"
  And original is unchanged

- Given "ابي صفحة login جديدة"
  When normalise_request is called
  Then normalised == "ابي صفحة login جديدة" (English kept)

- Failure path: Given "   "
  When normalise_request is called
  Then ValueError("empty request") is raised

- Boundary case: Given exactly 2000 characters
  Then it is accepted
  Given 2001 characters
  Then ValueError("request too long") is raised

## Constraints
- Pure Python standard library only; no LLM call, no new dependencies
- Deterministic: same input always gives the same output

## Non-goals
- No spelling correction, no translation, no changes to ة or ى
- No dialect conversion

## Security
- No logging of request text
- Tests use only synthetic messages

## Tests and oracle
- tests/test_normalise.py covers every rule, both errors and the boundary
- Expected outputs are written by hand in the tests (independent oracle),
  never computed by calling the function under test