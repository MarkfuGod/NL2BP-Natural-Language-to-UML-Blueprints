# Live results, 2026-11-25

Model `deepseek/deepseek-flash` (DeepSeek-V4.1-Flash) through CrewAI 1.15.45.
Requirement: [requirements/library.md](requirements/library.md) (campus library: search,
borrow/return, 5-book limit, 30-day loans, 0.5 CNY/day fines, admin management).
Each arm ran from a frozen commit in its own git worktree; scores were re-measured
from the files on disk by [score.py](score.py), not taken from the run's own claims.

**Criteria fixed before the runs:** M1 = 100% of `.puml` pass `plantuml -syntax`;
M2 ≥ 0.9 of class-diagram types present in the code; M3 = generated backend tests pass
in Docker.

## Multi-agent: before vs after the quality gates

| | baseline `f9dfdb3` | quality gates `046a6db` |
|---|---|---|
| M1 diagrams valid | 22/22 | 30/30 (repair loop never needed) |
| M2 conformance (name appears in code) | 0.656 (42/64) | **1.0** (71/71) |
| stricter: declared types actually *defined* as types | 0.609 (39/64) | **1.0** (71/71), 0 empty stubs |
| M3 backend tests in Docker | **failed** | **passed** (failed first, one `test_fix` round) |
| requests / tokens | 31 / ~2.37M | 52 / ~3.80M (+60%, mostly the fix round) |
| wall time (sum of stage times) | ~21 min | ~28 min |

Verdict against the criteria: M1 met in both arms (no difference). M2 and M3 missed by
the baseline, met with the gates.

What the gate caught: the baseline blueprint names Java/Spring types (`*ServiceImpl`,
`*Controller`, `SecurityConfig`) while the backend was written in Python, so a third of
the blueprint never reached the code. With the checklist in the prompt, every type was
implemented on the first pass. The `test_fix` round changed only `tests/test_admin.py`
(+20/−5, no test functions or asserts removed); 57 test functions remain.

## Single-agent with the quality gates

Commit with the request timeout (the first attempt hung 33 min on one stalled request,
which is what added the 300 s timeout; its partial data agreed with the rerun below).

| | single-agent, gates |
|---|---|
| M1 diagrams valid | 22/22 |
| M2 conformance | 1.0 (43/43) |
| M3 tests in Docker | failed first → **passed** (86 tests) after critic → coder fix round |
| reviewer's final verdict | CHANGES_REQUESTED (its own judgment; 1 fix round by default) |
| requests / tokens (true per-stage sums) | 148 / 12.8M (~0.46 USD) |

Where the tokens go: `04_code` 4.2M / 32 requests, `07_deploy` 3.3M / 32, `04_code_fix_1`
2.4M / 33. Every `write_file` call re-sends the conversation. Review and diagnosis hit the
iteration cap (16 requests), reading files one by one. Next cost lever: let code roles
return a multi-file bundle in one answer, and give the reviewer the code inline.

No pre-improvement single-agent arm was run (it had no gates to compare; budget kept for
the multi-agent comparison).

## Caveats

- One requirement, one run per arm: this shows the mechanism works on a real model, not
  an effect size. A multi-requirement comparison needs more runs (≈2–3 CNY per
  multi-agent run at the prices on this date).
- Token numbers for these two runs are the true totals (largest per-stage value).
  Their manifests recorded running totals because one LLM object was shared across
  stages; fixed afterwards (fresh LLM per stage, `usage_is_per_stage: true`).
- M2 matches names, so it can be gamed by empty classes; the stricter "defined as a
  type, not an empty stub" check is reported alongside it.
