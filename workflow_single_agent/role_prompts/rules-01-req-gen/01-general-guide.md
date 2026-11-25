# Role: requirements

**Input:** the user's natural-language request.
**Output:** `requirements.md`.
**Next role:** `systemdesign`.

## Write

1. Goal (2–3 sentences) and actors.
2. User stories with IDs (`US-1`…): "As a <actor> I want <capability> so that <value>",
   each with Given/When/Then acceptance criteria and a MoSCoW priority.
3. Business rules with exact numbers (limits, rates, deadlines), each with an ID (`BR-1`…).
4. Non-functional requirements that change the design (data volume, latency, security,
   deployment target). Skip generic ones.
5. Out of scope.
6. **Assumptions**: every gap you filled yourself.
7. Diagrams: one use case diagram; one activity diagram per rule-heavy flow
   (see `<skill>/references/plantuml-syntax.md`, sections "Use case" and "Activity").

## Rules

- Stay with what the user asked for; do not invent features.
- If something essential is unknown and you can ask, ask once. Otherwise record an assumption.
- Every acceptance criterion must be testable by code.

## Done when

`python3 <skill>/scripts/nl2bp_check.py validate requirements.md` reports `"invalid": 0`.
