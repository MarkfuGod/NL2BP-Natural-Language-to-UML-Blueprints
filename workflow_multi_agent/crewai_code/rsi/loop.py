"""The RSI loop (PROTOCOL.md): propose → evaluate → archive → promote, with a meta step.

    uv run python -m rsi.loop --noise <noise.json> --base <commit> --out output/rsi/<run>

Evaluation, model calls and balance checks are injected, so the loop runs offline in tests.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

from rsi import meta, propose
from rsi.variants import (
    EditError,
    apply_edits,
    materialise,
    parse_json,
    remove,
    surface_size,
)

HERE = Path(__file__).resolve().parent
REJECT_DELTA = -0.02  # how a proposal that cannot be applied counts in strategy statistics


@dataclass
class Entry:
    id: str
    parent: str | None
    gen: int
    strategy: int
    rationale: str = ""
    edits: list = field(default_factory=list)
    status: str = ""
    delta: float | None = None
    train: dict = field(default_factory=dict)  # req -> score dict (all evaluated reqs)
    train_mean: float | None = None  # only when all training reqs are evaluated
    heldout_mean: float | None = None
    heldout: dict = field(default_factory=dict)


@dataclass
class Config:
    train: list[str]
    heldout: list[str]
    sigma: float
    minibatch: int = 6
    meta_every: int = 4
    generations: int = 20
    budget_usd: float = 3.5
    seed: int = 7

    @property
    def delta_mini(self) -> float:
        return max(0.02, 2 * self.sigma / math.sqrt(self.minibatch))

    @property
    def delta_train(self) -> float:
        return max(0.02, 2 * self.sigma / math.sqrt(len(self.train)))


def mean_score(per_req: dict, names: list[str]) -> float:
    return statistics.fmean(per_req[n]["score"] for n in names)


class Loop:
    def __init__(
        self,
        cfg: Config,
        out: Path,
        base_files: dict[str, str],
        base_train: dict,
        evaluate: Callable[[dict[str, str], list[str], Path], dict],
        llm: Callable[[list[dict]], str],
        spent: Callable[[], float],
    ):
        self.cfg, self.out = cfg, out
        self.evaluate, self.llm, self.spent = evaluate, llm, spent
        self.rng = random.Random(cfg.seed)
        self.baseline_size = surface_size(base_files)
        self.files: dict[str, dict[str, str]] = {"v0": base_files}
        self.strategies = [(HERE / "strategy_v0.md").read_text(encoding="utf-8")]
        self.archive: list[Entry] = [
            Entry(
                "v0",
                None,
                0,
                0,
                status="baseline",
                train=base_train,
                train_mean=mean_score(base_train, cfg.train),
            )  # fmt: skip
        ]
        self.baseline_heldout: float | None = None
        out.mkdir(parents=True, exist_ok=True)

    # -- selection -------------------------------------------------------------

    def pick_parent(self) -> Entry:
        full = [e for e in self.archive if e.train_mean is not None]
        weights = [math.exp(e.train_mean / 0.05) for e in full]
        return self.rng.choices(full, weights=weights, k=1)[0]

    def strategy_stats(self) -> dict[int, dict]:
        stats = {}
        for v in range(len(self.strategies)):
            ds = [
                e.delta
                for e in self.archive
                if e.strategy == v and e.parent and e.delta is not None
            ]
            stats[v] = {"n": len(ds), "mean": statistics.fmean(ds) if ds else 0.0}
        return stats

    def pick_strategy(self) -> int:
        stats = self.strategy_stats()
        for v in sorted(stats, reverse=True):  # try every version (newest first) once
            if stats[v]["n"] == 0:
                return v
        total = sum(s["n"] for s in stats.values())
        return max(
            stats,
            key=lambda v: stats[v]["mean"] + 0.02 * math.sqrt(math.log(total) / stats[v]["n"]),
        )

    # -- one generation --------------------------------------------------------

    def generation(self, gen: int) -> Entry:
        parent = self.pick_parent()
        sv = self.pick_strategy()
        history = [asdict(e) | {"strategy": e.strategy} for e in self.archive if e.parent]
        messages = propose.build_messages(
            self.strategies[sv], self.files[parent.id], parent.train, history
        )
        child = Entry(f"v{len(self.archive)}", parent.id, gen, sv)
        try:
            reply = parse_json(self.llm(messages))
            child.rationale = str(reply.get("rationale", ""))[:1000]
            child.edits = list(reply.get("edits", []))
            files = apply_edits(self.files[parent.id], child.edits, self.baseline_size)
        except (EditError, ValueError, KeyError, TypeError) as exc:
            child.status, child.delta = f"rejected: {exc}"[:300], REJECT_DELTA
            return child
        self.files[child.id] = files
        mini = self.rng.sample(self.cfg.train, self.cfg.minibatch)
        res = self.evaluate(files, mini, self.out / child.id / "mini")
        child.train.update(res["per_req"])
        child.delta = round(mean_score(child.train, mini) - mean_score(parent.train, mini), 4)
        if child.delta <= self.cfg.delta_mini:
            child.status = "minibatch: not better"
            return child
        rest = [n for n in self.cfg.train if n not in mini]
        child.train.update(self.evaluate(files, rest, self.out / child.id / "rest")["per_req"])
        child.train_mean = round(mean_score(child.train, self.cfg.train), 4)
        best = max(e.train_mean for e in self.archive if e.train_mean is not None)
        if child.train_mean <= best + self.cfg.delta_train:
            child.status = "full train: not above best"
            return child
        if self.baseline_heldout is None:
            base = self.evaluate(self.files["v0"], self.cfg.heldout, self.out / "v0" / "heldout")
            self.archive[0].heldout = base["per_req"]
            self.baseline_heldout = self.archive[0].heldout_mean = base["mean"]
        held = self.evaluate(files, self.cfg.heldout, self.out / child.id / "heldout")
        child.heldout, child.heldout_mean = held["per_req"], held["mean"]
        child.status = "candidate"
        return child

    def meta_step(self, gen: int) -> None:
        history = [asdict(e) for e in self.archive if e.parent]
        best_v = max(self.strategy_stats().items(), key=lambda kv: kv[1]["mean"])[0]
        msgs = meta.build_messages(self.strategies[best_v], history, self.strategy_stats())
        try:
            reply = parse_json(self.llm(msgs))
            text = str(reply["strategy"]).strip()
        except (ValueError, KeyError, TypeError):
            return
        if 200 <= len(text) <= meta.MAX_STRATEGY_CHARS:
            self.strategies.append(text)
            (self.out / f"strategy_v{len(self.strategies) - 1}.md").write_text(
                text, encoding="utf-8"
            )

    # -- run -------------------------------------------------------------------

    def save(self) -> None:
        (self.out / "archive.json").write_text(
            json.dumps([asdict(e) for e in self.archive], ensure_ascii=False, indent=2)
        )
        for e in self.archive:
            if e.id in self.files and e.parent:
                d = self.out / e.id / "surface"
                for p, text in self.files[e.id].items():
                    (d / p).parent.mkdir(parents=True, exist_ok=True)
                    (d / p).write_text(text, encoding="utf-8")

    def run(self) -> dict:
        for gen in range(1, self.cfg.generations + 1):
            if self.spent() >= self.cfg.budget_usd:
                print(f"budget reached before gen {gen}", flush=True)
                break
            child = self.generation(gen)
            self.archive.append(child)
            print(f"gen {gen}: {child.id} from {child.parent} (strategy v{child.strategy}) "
                  f"Δ={child.delta} {child.status}", flush=True)  # fmt: skip
            if gen % self.cfg.meta_every == 0:
                self.meta_step(gen)
                print(f"meta: {len(self.strategies)} strategy versions", flush=True)
            self.save()
        return self.report()

    def report(self) -> dict:
        cands = [e for e in self.archive if e.status == "candidate"]
        best = max(cands, key=lambda e: e.heldout_mean or 0, default=None)
        stats = self.strategy_stats()
        rep = {
            "generations": len([e for e in self.archive if e.parent]),
            "spent_usd": round(self.spent(), 4),
            "baseline_train": self.archive[0].train_mean,
            "baseline_heldout": self.baseline_heldout,
            "best_candidate": best.id if best else None,
            "best_heldout": best.heldout_mean if best else None,
            "heldout_gain": round(best.heldout_mean - self.baseline_heldout, 4) if best else None,
            "primary_threshold": round(
                max(0.03, 2 * self.cfg.sigma / math.sqrt(len(self.cfg.heldout))), 4
            ),
            "strategy_stats": stats,
            "statuses": [f"{e.id}: {e.status} Δ={e.delta}" for e in self.archive if e.parent],
        }
        (self.out / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
        return rep


# -- real wiring -----------------------------------------------------------------


def main() -> int:  # pragma: no cover - needs network and a model key
    import os
    import urllib.request

    from crewai import LLM

    from rsi.fitness import evaluate as fit_eval
    from rsi.fitness import split

    ap = argparse.ArgumentParser()
    ap.add_argument("--noise", type=Path, required=True)
    ap.add_argument("--base", required=True, help="commit whose surface is the baseline")
    ap.add_argument("--repo", type=Path, default=HERE.parents[2])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--generations", type=int, default=20)
    ap.add_argument("--budget", type=float, default=3.5)
    a = ap.parse_args()

    noise = json.loads(a.noise.read_text())
    A, B = noise["A"]["per_req"], noise["B"]["per_req"]
    sp = split()
    diffs = [A[n]["score"] - B[n]["score"] for n in sp["train"]]
    sigma = statistics.stdev(diffs)
    base_train = {n: {**A[n], "score": (A[n]["score"] + B[n]["score"]) / 2} for n in sp["train"]}
    cfg = Config(sp["train"], sp["heldout"], sigma, generations=a.generations, budget_usd=a.budget)

    key = os.environ["DEEPSEEK_API_KEY"]

    def usd() -> float:
        req = urllib.request.Request("https://api.deepseek.com/user/balance",
                                     headers={"Authorization": f"Bearer {key}"})  # fmt: skip
        data = json.load(urllib.request.urlopen(req, timeout=30))
        return {b["currency"]: float(b["total_balance"]) for b in data["balance_infos"]}["USD"]

    start = usd()
    llm = LLM(
        model=os.environ.get("MODEL", "deepseek/deepseek-flash"), temperature=0.7, timeout=300
    )

    def evaluate(files: dict[str, str], names: list[str], out: Path) -> dict:
        wt = materialise(a.repo, a.base, files, out / "worktree")
        try:
            return fit_eval(wt, names, out / "runs", parallel=12)
        finally:
            remove(a.repo, wt)

    import subprocess

    from rsi.variants import SURFACE

    base_files = {
        p: subprocess.run(
            ["git", "show", f"{a.base}:{p}"], cwd=a.repo, check=True, capture_output=True, text=True
        ).stdout  # fmt: skip
        for p in SURFACE
    }
    loop = Loop(cfg, a.out, base_files, base_train, evaluate,
                lambda m: llm.call(m), lambda: start - usd())  # fmt: skip
    print(f"σ={sigma:.4f} δ_mini={cfg.delta_mini:.4f} δ_train={cfg.delta_train:.4f}", flush=True)
    print(json.dumps(loop.run(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
