"""L0 optimizer: reads failure feedback and proposes a small edit to the workflow surface."""

from __future__ import annotations

from collections import Counter

from rsi.variants import MAX_EDITS, SURFACE

OUTPUT_FORMAT = f"""
Reply with one JSON object and nothing else:
{{"rationale": "<which failure pattern, why this edit fixes it>",
  "edits": [{{"file": "<one of the editable paths>", "old": "<exact text copied from that file,
  unique in it>", "new": "<replacement text>"}}]}}
At most {MAX_EDITS} edits. `old` must be copied exactly and occur exactly once in the file.
Editable paths: {", ".join(SURFACE)}.
"""


def feedback_digest(per_req: dict[str, dict]) -> str:
    counts: Counter[str] = Counter()
    lines = []
    for name, r in sorted(per_req.items()):
        lines.append(f"- {name}: score {r['score']:.3f} {r.get('parts', {})}")
        for f in r.get("feedback", []):
            lines.append(f"    · {f}")
            counts[f.split(":")[0]] += 1
    top = "\n".join(f"- {n}× {k}" for k, n in counts.most_common())
    return f"Failure patterns (count of requirements):\n{top}\n\nPer requirement:\n" + "\n".join(
        lines
    )


def history_digest(history: list[dict], limit: int = 8) -> str:
    if not history:
        return "(no earlier proposals)"
    rows = []
    for h in history[-limit:]:
        rows.append(
            f"- gen {h['gen']}: {h.get('rationale', '')[:220]} | files: "
            f"{', '.join(sorted({e['file'].split('/')[-1] for e in h.get('edits', [])}))} | "
            f"minibatch Δ {h.get('delta', 'n/a')} | {h.get('status', '')}"
        )
    return "\n".join(rows)


def build_messages(strategy: str, files: dict[str, str], per_req: dict, history: list[dict]):
    body = "\n\n".join(f"===== {p} =====\n{t}" for p, t in files.items())
    user = (
        f"## Editable files\n\n{body}\n\n## Feedback from the current version on training "
        f"requirements\n\n{feedback_digest(per_req)}\n\n## Earlier proposals\n\n"
        f"{history_digest(history)}"
    )
    return [
        {"role": "system", "content": strategy.strip() + "\n" + OUTPUT_FORMAT},
        {"role": "user", "content": user},
    ]
