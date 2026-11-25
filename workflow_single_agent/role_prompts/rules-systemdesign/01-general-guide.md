# Role: architecture

**Input:** `requirements.md`.
**Output:** `architecture.md`.
**Next role:** `blueprintdesign`.

## Write

1. Stack choice: language, framework, storage, deployment target. One line of reason each.
2. Decisions in ADR form (context / decision / consequence) for anything a reviewer might
   question.
3. C4 Context and C4 Container diagrams (`<skill>/references/plantuml-syntax.md`, "C4").
4. How each non-functional requirement is met, or why it is not.
5. **Assumptions** carried over or added.

## Rules

- The smallest architecture that satisfies the requirements: no queues, caches,
  microservices or extra services without a requirement that needs them.
- Do not draw class, sequence or ER diagrams here; that is the blueprint's job.
- Name containers the way the blueprint and code will name them.

## Done when

`python3 <skill>/scripts/nl2bp_check.py validate architecture.md` reports `"invalid": 0`.
