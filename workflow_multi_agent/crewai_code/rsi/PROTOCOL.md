# RSI protocol (pre-registered 2026-11-26, before any baseline measurement)

## Levels

- **L0 workflow** (what gets improved), Phase A surface, the only files the optimizer may edit:
  `skills/nl2bp/references/*.md`,
  `workflow_multi_agent/crewai_code/agileworkflow/crews/agile_crew/config/tasks.yaml`,
  `workflow_multi_agent/crewai_code/agileworkflow/crews/agile_crew/config/agents.yaml`.
- **L1 optimizer**: `rsi/propose.py` driven by a versioned strategy prompt; `rsi/meta.py`
  rewrites that strategy every 4 generations from archive statistics (the recursive level).
- **Anchor** (frozen, hashed in `rsi/ANCHOR.sha256`, edited only by the human):
  `rsi/fitness.py`, `evals/rsi/hidden/*.json`, `evals/rsi/requirements/*.md`,
  `evals/rsi/split.json`, this file.

## Fitness

`rsi/fitness.py`: design stages only (`nl2bp multi --until blueprint`), model
`deepseek/deepseek-flash`, score per requirement
`validity × (0.30 concepts + 0.30 rules + 0.15 endpoints + 0.10 states + 0.15 diagram kinds)`.
12 training requirements, 6 held out. The optimizer sees feedback text for training
requirements only; held-out results are never shown to L0 or L1.

## Noise

Before the loop: evaluate the baseline (current main) twice on all 12 training requirements.
σ = sd of per-requirement score differences; the noise of a mean over n requirements is
σ/√n. Decision margins: δ_train = max(0.02, 2σ/√12), δ_mini = max(0.02, 2σ/√6).

## Loop

1. Parent: sample from the archive, weight ∝ exp(train_mean / 0.05).
2. Optimizer version: UCB1 over versions by mean minibatch improvement.
3. Propose ≤ 3 search/replace edits to surface files; reject if a file is outside the surface,
   an edit's `old` text is not found exactly once, or total surface size grows > 25 % over
   baseline.
4. Evaluate on a random minibatch of 6 training requirements; compare with the parent's
   scores on the same requirements. If the child is better by more than δ_mini, evaluate the
   other 6 training requirements too.
5. Everything goes into the archive (diff, parent, optimizer version, scores, cost).
6. Promotion candidate: full-train mean > best full-train mean + δ_train. Candidates are run on
   the held-out set (the baseline's held-out score is measured once).
7. Every 4 generations: meta step.
8. Stop at 20 generations or when spend reaches 3.50 USD (read from the provider's balance
   API), whichever comes first.

## Success criteria (fixed now)

- **Primary:** best candidate's held-out mean − baseline held-out mean ≥ max(0.03, 2σ/√6).
- **No regression:** on held-out, no score component (validity, concepts, rules, endpoints,
  states, diagrams) drops by more than 0.05 versus baseline.
- **Recursion check:** mean minibatch improvement of proposals made with meta-generated
  strategies vs. the initial strategy, reported with all values. No claim that the meta level
  helps unless it is higher in both halves of the run.
- Ties, losses and a failed primary criterion are reported as such. A winning variant becomes a
  PR for the human to review; nothing is merged automatically.
