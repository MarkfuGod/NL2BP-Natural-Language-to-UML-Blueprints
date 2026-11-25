# Role: blueprint

**Input:** `requirements.md`, `architecture.md`.
**Output:** `blueprint.md` and `diagrams/*.puml`.
**Next role:** `coder`.

## Read first

- `<skill>/references/diagram-selection.md`: which diagrams to draw.
- `<skill>/references/output-contract.md`: the exact document layout (tooling parses it).
- `<skill>/references/plantuml-syntax.md`: only the sections for the diagrams you draw.

## Write

1. A class diagram per module that declares **every** type the code must contain. This is
   the implementation contract; names fit the chosen stack.
2. A sequence diagram per core user story.
3. An IE entity-relationship diagram if there is a database; a state diagram for each
   entity with a lifecycle.
4. The interface table (endpoint/method, request, response, errors) and the data flow.
5. 2–3 sentences of explanation after each diagram.

## Rules

- Use only what the requirements and architecture contain; record gaps as assumptions.
- Same names for the same thing in every diagram.

## Done when

```bash
python3 <skill>/scripts/nl2bp_check.py validate blueprint.md     # "invalid": 0
python3 <skill>/scripts/nl2bp_check.py extract blueprint.md diagrams/
python3 <skill>/scripts/nl2bp_check.py contract blueprint.md     # non-empty list
```
