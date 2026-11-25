---
name: nl2bp
description: Turns a natural-language software requirement into a verified UML blueprint (PlantUML C4, class, sequence, state, ER and activity diagrams) and, optionally, code that implements it, checking every diagram with PlantUML and the code against the blueprint and its tests. Use when the user asks to design a system from a description, draw UML or architecture diagrams, write PlantUML, turn requirements into a blueprint, or implement code from a blueprint.
license: MIT
compatibility: Needs python3 and plantuml on PATH (brew install plantuml / apt install plantuml). Docker is optional, for running generated tests in a sandbox.
metadata:
  version: "1.0"
  plantuml: "1.2026.x"
---

# NL2BP: natural language → blueprint → code

The model writes requirements, architecture, diagrams and code; the scripts check them.
Never report a stage as done until its check passes. All checks print JSON and exit 0 on
success, 1 on failure, 2 when a tool is missing (say so and continue without that check).

`SKILL_DIR` below is the directory this file is in.

## Workflow

Create a working folder (default `nl2bp/<project>/`) and copy this checklist into your plan:

```
- [ ] 1 requirements.md        (use case + activity diagrams)
- [ ] 2 architecture.md        (C4 context + container)
- [ ] 3 blueprint.md           (class contract, sequences, ER, states)  ← stop for review
- [ ] 4 validate diagrams      (all pass)
- [ ] 5 implement              (only if asked) code/ + tests
- [ ] 6 verify implementation  (conformance ≥ 0.9, tests pass)
```

### 1. Requirements → `requirements.md`

Write: goal, actors, functional requirements as user stories with IDs (`US-1`…) and
Given/When/Then acceptance criteria, non-functional requirements, explicit business rules
with numbers (limits, rates, deadlines), out of scope, **Assumptions**. Add a use case
diagram and an activity diagram for each rule-heavy flow.
If something essential is unknown, ask the user once; otherwise record the assumption.

### 2. Architecture → `architecture.md`

Pick the stack and justify it in 2–3 lines per decision (ADR style: context, decision,
consequence). Draw C4 Context and C4 Container. Keep it as small as the requirements
allow; do not add queues, caches or microservices without a requirement that needs them.

### 3. Blueprint → `blueprint.md`

Read [references/diagram-selection.md](references/diagram-selection.md) to choose diagrams,
[references/output-contract.md](references/output-contract.md) for the required layout,
and the sections of [references/plantuml-syntax.md](references/plantuml-syntax.md) for
the diagram types you draw. The class diagram is the contract for the code: declare every
type the implementation needs, with names idiomatic for the chosen stack.

**Checkpoint:** show the user the diagram list and the contract
(`python3 SKILL_DIR/scripts/nl2bp_check.py contract blueprint.md`) and ask whether to
proceed, unless they asked for an unattended run.

### 4. Validate diagrams

```bash
python3 SKILL_DIR/scripts/nl2bp_check.py validate requirements.md architecture.md blueprint.md
```

For each error, fix the reported line (0-based, `@start` line is 0) and re-run until
`"invalid": 0`. Then export and render:

```bash
python3 SKILL_DIR/scripts/nl2bp_check.py extract blueprint.md diagrams/
python3 SKILL_DIR/scripts/nl2bp_check.py render diagrams/
```

### 5. Implement (only when the user wants code)

Implement exactly the blueprint: every contract type exists under its blueprint name,
endpoints match the interface table, business rules from the requirements are enforced.
Write tests for each acceptance criterion; tests must run offline
(`requirements.txt` + `tests/` for Python, or `package.json` with a `test` script).

### 6. Verify implementation

```bash
python3 SKILL_DIR/scripts/nl2bp_check.py conform blueprint.md code/
python3 SKILL_DIR/scripts/nl2bp_check.py test code/
```

`conform` must report `ratio ≥ 0.9`; add the `missing` types rather than editing the
blueprint to match. `test` runs in a throwaway Docker container; fix code, not tests, until
it passes. Only use `--no-docker` for code you have read and trust.

## Report

Finish with: files produced, diagram count and validation result, contract conformance,
test result (or why a check was skipped), and the assumptions the user should confirm.
