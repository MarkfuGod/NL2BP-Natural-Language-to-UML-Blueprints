"""L1 optimizer: rewrites the L0 optimizer's strategy from what its proposals achieved."""

from __future__ import annotations

MAX_STRATEGY_CHARS = 4000

INSTRUCTIONS = """You improve the strategy text that guides another model (the optimizer).
The optimizer reads failure feedback from a requirements→UML-blueprint system and proposes
small edits to that system's instructions. Below is its current strategy and every proposal
made so far with the measured result (minibatch Δ: change in score versus the parent on the
same requirements; positive is better; 'rejected' means the edit could not be applied).

Write a better strategy: keep what correlates with positive Δ, drop what produced rejected or
negative proposals, and add concrete guidance learned from the data (which kinds of edits,
which files, how large). The strategy must stay general: no training requirement names.
Reply with one JSON object: {"rationale": "...", "strategy": "<the full new strategy>"}.
The strategy must be under 4000 characters."""


def build_messages(strategy: str, history: list[dict], version_stats: dict) -> list[dict]:
    rows = [
        f"- gen {h['gen']} (strategy v{h['strategy']}): {h.get('rationale', '')[:300]} | "
        f"files: {', '.join(sorted({e['file'].split('/')[-1] for e in h.get('edits', [])}))} | "
        f"Δ {h.get('delta', 'n/a')} | {h.get('status', '')}"
        for h in history
    ]
    stats = "\n".join(
        f"- v{v}: {s['n']} proposals, mean Δ {s['mean']:+.4f}" for v, s in version_stats.items()
    )
    user = (
        f"## Current strategy\n\n{strategy}\n\n## Results by strategy version\n\n{stats}\n\n"
        f"## Proposals\n\n" + "\n".join(rows)
    )
    return [{"role": "system", "content": INSTRUCTIONS}, {"role": "user", "content": user}]
