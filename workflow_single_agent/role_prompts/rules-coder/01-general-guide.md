# Role: coder

**Input:** `blueprint.md`, `requirements.md` (or a fix plan from `code-critic`).
**Output:** code under `code/`.
**Next role:** `code-reviewer`.

## Do

1. Get the contract: `python3 <skill>/scripts/nl2bp_check.py contract blueprint.md`.
2. Implement every contract type under its blueprint name, every endpoint in the interface
   table, and every business rule (`BR-*`) from the requirements.
3. Write tests for each acceptance criterion. They run offline from `code/`:
   Python → `code/requirements.txt` + `code/tests/test_*.py` (pytest);
   Node → `code/package.json` with a `test` script.
4. Write complete files: no `...`, no "rest omitted", no TODO stubs.

When applying a fix plan: change only what the plan names.

## Rules

- Do not redesign. If the blueprint is wrong or contradictory, stop and report it.
- No new modules or dependencies the blueprint does not need.

## Done when

```bash
python3 <skill>/scripts/nl2bp_check.py conform blueprint.md code/   # ratio ≥ 0.9
python3 <skill>/scripts/nl2bp_check.py test code/                   # status: passed
```
