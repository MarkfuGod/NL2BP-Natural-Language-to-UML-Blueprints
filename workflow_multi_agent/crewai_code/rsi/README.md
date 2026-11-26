# RSI: recursive self-improvement of the NL2BP workflow

Three levels (details and pre-registered criteria: [PROTOCOL.md](PROTOCOL.md)):

- **L0** the workflow's instructions (`skills/nl2bp/references/`, `tasks.yaml`, `agents.yaml`)
- **L1** an optimizer that proposes edits to L0 from failure feedback (`propose.py`), whose
  strategy is rewritten every 4 generations by a meta-optimizer (`meta.py`)
- **Anchor** frozen and hashed (`ANCHOR.sha256`, checked by CI): `fitness.py`, the 18
  requirements, hidden checks and the train / held-out split in `../evals/rsi/`

```bash
# needs DEEPSEEK_API_KEY and plantuml on PATH
uv run python -m rsi.loop --noise rsi/results/noise-2026-11-26-raw.json \
  --base d44d8b1 --out output/rsi/<run> --generations 20 --budget 3.5
```

## Results so far (DeepSeek-V4.1-Flash)

| | |
|---|---|
| Baseline, 12 training requirements | 0.871 / 0.861 (two runs); σ per requirement 0.087 |
| Decision margins | minibatch 0.071, full train 0.050, held-out success 0.071 |
| Generation 1 | Δ +0.059 on a 6-requirement minibatch, all 6 up, **below the margin: not promoted** ([gen1-2026-11-26.json](results/gen1-2026-11-26.json), edited files in `results/gen1-surface/`) |
| Spend | probe 1.13 USD, generation 1 0.58 USD (plus 0.22 USD lost to a fixed path bug) |

With noise this large, a meaningful run needs about 40–60 generations (≈ 20–30 USD at these
prices); the meta level needs several proposals per strategy version to be judged.
