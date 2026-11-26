"""RSI loop: anchor integrity, edit validation, and a full offline dry run."""

import hashlib
import json
import random
from pathlib import Path

import pytest

from rsi import fitness
from rsi.loop import Config, Loop
from rsi.variants import SURFACE, EditError, apply_edits, parse_json

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def test_anchor_files_are_unchanged():
    for line in (ROOT / "rsi" / "ANCHOR.sha256").read_text().splitlines():
        digest, path = line.split("  ", 1)
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path


def test_surface_is_disjoint_from_anchor_and_exists():
    anchored = {
        line.split("  ", 1)[1] for line in (ROOT / "rsi" / "ANCHOR.sha256").read_text().splitlines()
    }
    for p in SURFACE:
        assert (REPO / p).is_file(), p
        assert not any(p.endswith(a) for a in anchored), p


def test_split_and_hidden_checks_are_consistent():
    sp = fitness.split()
    assert len(sp["train"]) == 12 and len(sp["heldout"]) == 6
    assert not set(sp["train"]) & set(sp["heldout"])
    for name in sp["train"] + sp["heldout"]:
        h = json.loads((fitness.EVALS / "hidden" / f"{name}.json").read_text())
        assert h["concepts"] and h["rules"] and h["endpoints"] and h["states"], name
        assert (fitness.EVALS / "requirements" / f"{name}.md").is_file()


FILES = {p: f"content of {p}\nline two\n" for p in SURFACE}


def test_apply_edits_validates():
    size = sum(len(v) for v in FILES.values())
    good = apply_edits(FILES, [{"file": SURFACE[0], "old": "line two", "new": "line 2"}], size)
    assert good[SURFACE[0]].endswith("line 2\n") and FILES[SURFACE[0]].endswith("line two\n")
    bad = [
        [{"file": "rsi/fitness.py", "old": "x", "new": "y"}],  # outside surface
        [{"file": SURFACE[0], "old": "missing", "new": "y"}],  # not found
        [{"file": SURFACE[0], "old": "line two", "new": "x" * size}],  # growth cap
        [],
    ]
    for edits in bad:
        with pytest.raises(EditError):
            apply_edits(FILES, edits, size)


def test_parse_json_tolerates_fences():
    assert parse_json('ok\n```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json('prefix {"a": {"b": 2}} suffix') == {"a": {"b": 2}}


def _scores(names, value):
    return {n: {"score": value, "parts": {}, "feedback": [f"{n} feedback"]} for n in names}


def test_loop_dry_run_promotes_and_runs_meta(tmp_path):
    train = [f"t{i}" for i in range(12)]
    held = [f"h{i}" for i in range(6)]
    cfg = Config(train, held, sigma=0.01, generations=5, meta_every=4)
    calls = {"llm": 0}

    def llm(messages):
        calls["llm"] += 1
        if "strategy text" in messages[0]["content"]:  # meta prompt
            return json.dumps({"rationale": "r", "strategy": "Better strategy. " * 20})
        if calls["llm"] == 2:  # one proposal that cannot be applied
            return json.dumps(
                {"rationale": "bad", "edits": [{"file": "x", "old": "a", "new": "b"}]}
            )
        n = calls["llm"]
        return json.dumps(
            {
                "rationale": f"r{n}",
                "edits": [{"file": SURFACE[0], "old": "line two", "new": f"line two v{n}"}],
            }
        )

    def evaluate(files, names, out):
        improved = "v1" in files[SURFACE[0]]
        value = 0.9 if improved else 0.6
        return {"mean": value, "per_req": _scores(names, value)}

    loop = Loop(cfg, tmp_path, dict(FILES), _scores(train, 0.6), evaluate, llm, lambda: 0.0)
    loop.rng = random.Random(1)
    rep = loop.run()
    statuses = [e.status for e in loop.archive[1:]]
    assert any(s.startswith("rejected") for s in statuses)
    assert "candidate" in statuses
    assert rep["best_heldout"] == 0.9 and rep["heldout_gain"] == pytest.approx(0.3)
    assert len(loop.strategies) == 2  # meta step added a strategy version
    assert (tmp_path / "archive.json").is_file() and (tmp_path / "report.json").is_file()


def test_loop_stops_at_budget(tmp_path):
    train = [f"t{i}" for i in range(12)]
    cfg = Config(train, ["h"], sigma=0.01, generations=5, budget_usd=1.0)
    loop = Loop(
        cfg,
        tmp_path,
        dict(FILES),
        _scores(train, 0.5),
        lambda f, n, o: {"mean": 0.5, "per_req": _scores(n, 0.5)},
        lambda m: "{}",
        lambda: 2.0,
    )
    rep = loop.run()
    assert rep["generations"] == 0


def test_materialise_with_relative_path(tmp_path, monkeypatch):
    import subprocess

    from rsi.variants import materialise, remove

    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    (repo / "a.txt").write_text("base\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "b"],
                   cwd=repo, check=True)  # fmt: skip
    work = tmp_path / "elsewhere"
    work.mkdir()
    monkeypatch.chdir(work)  # cwd differs from repo, as in the real loop
    wt = materialise(repo, "HEAD", {"a.txt": "variant\n"}, Path("out/v1/worktree"))
    assert wt == (work / "out/v1/worktree").resolve()
    assert (wt / "a.txt").read_text() == "variant\n"
    assert (repo / "a.txt").read_text() == "base\n"
    remove(repo, wt)
    assert not wt.exists()


def test_harness_failure_is_not_counted_as_regression(tmp_path):
    train = [f"t{i}" for i in range(12)]
    cfg = Config(train, ["h"], sigma=0.01, generations=1)
    seen = []

    def evaluate(files, names, out):
        seen.append(out)
        return {
            "mean": 0.0,
            "per_req": {n: {"score": 0.0, "error": "no run directory"} for n in names},
        }

    reply = json.dumps(
        {"rationale": "r", "edits": [{"file": SURFACE[0], "old": "line two", "new": "x"}]}
    )
    loop = Loop(cfg, Path("relative/out"), dict(FILES), _scores(train, 0.6), evaluate,
                lambda m: reply, lambda: 0.0)  # fmt: skip
    loop.out = tmp_path  # keep test artefacts in tmp
    rep = loop.run()
    child = loop.archive[1]
    assert child.status.startswith("error") and child.delta is None
    assert rep["strategy_stats"][0]["n"] == 0
    assert Loop(cfg, Path("relative/out"), dict(FILES), _scores(train, 0.6), evaluate,
                lambda m: reply, lambda: 0.0).out.is_absolute()  # fmt: skip
