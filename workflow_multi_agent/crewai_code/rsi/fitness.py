"""FROZEN fitness function. The optimizer never edits this file, evals/rsi/hidden/ or split.json.

Runs a variant's design stages (requirements → architecture → blueprint) on requirements,
re-checks every diagram with PlantUML itself (never trusting the variant's own report),
and scores against hidden checks:

    score = validity × (0.30 · concepts + 0.30 · rules + 0.15 · endpoints + 0.10 · states
                        + 0.15 · diagram_kinds)

- concepts: share of hidden concept groups with a synonym declared as a type/entity name
- rules: per business rule, 1 if one of its patterns appears in the blueprint, 0.5 if only in
  the requirements document, else 0
- endpoints: share of key API operations (regexes) named in the blueprint
- states: share of lifecycle state groups with a name appearing inside a state diagram
- diagram_kinds: share of required kinds (class, sequence, er, state, c4) present
- validity: share of extracted diagrams that pass `plantuml -syntax` (after the run's repairs)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

from agileworkflow import contract, plantuml, quality

EVALS = Path(__file__).resolve().parent.parent / "evals" / "rsi"
WEIGHTS = {"concepts": 0.30, "rules": 0.30, "endpoints": 0.15, "states": 0.10, "diagrams": 0.15}


def split() -> dict[str, list[str]]:
    return json.loads((EVALS / "split.json").read_text())


def norm(name: str) -> str:
    return re.sub(r"[_\-\s]", "", name).lower()


def diagram_kinds(diagrams: list[plantuml.Diagram]) -> set[str]:
    kinds = set()
    for d in diagrams:
        s = d.source
        if d.kind != "uml":
            continue
        if "!include <C4" in s:
            kinds.add("c4")
        if re.search(r"^\s*(class|interface|enum|abstract\s+class)\b", s, re.M):
            kinds.add("class")
        if re.search(r"^\s*entity\b", s, re.M):
            kinds.add("er")
        if "[*]" in s:
            kinds.add("state")
        if re.search(r"^\s*(participant|autonumber)\b", s, re.M) or (
            re.search(r"^\s*actor\b", s, re.M) and re.search(r"^\s*\w+\s*-+>+\s*\w+\s*:", s, re.M)
        ):
            kinds.add("sequence")
    return kinds


@dataclass
class ReqScore:
    name: str
    score: float = 0.0
    parts: dict = field(default_factory=dict)
    feedback: list[str] = field(default_factory=list)
    tokens: int = 0
    seconds: float = 0.0
    error: str | None = None

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def score_run(name: str, run_dir: Path) -> ReqScore:
    hidden = json.loads((EVALS / "hidden" / f"{name}.json").read_text(encoding="utf-8"))
    rs = ReqScore(name)
    docs = run_dir / "docs"
    bp_path, req_path = docs / "blueprint_design.md", docs / "requirement_analysis.md"
    if not bp_path.is_file():
        rs.error = "no blueprint produced"
        rs.feedback.append("The run produced no blueprint.")
        return rs
    blueprint = bp_path.read_text(encoding="utf-8")
    requirements = req_path.read_text(encoding="utf-8") if req_path.is_file() else ""
    arch = (
        (docs / "system_design.md").read_text(encoding="utf-8")
        if (docs / "system_design.md").is_file()
        else ""
    )

    diagrams = plantuml.extract(requirements + "\n" + arch + "\n" + blueprint)
    invalid = quality.check_diagrams(diagrams) if diagrams else []
    validity = (len(diagrams) - len(invalid)) / len(diagrams) if diagrams else 0.0

    names = {norm(n) for n in contract.declared_types(plantuml.extract(blueprint))}
    missing_concepts = [g for g in hidden["concepts"] if not any(norm(s) in names for s in g)]
    concepts = 1 - len(missing_concepts) / len(hidden["concepts"])

    rule_hits, weak, missing_rules = 0.0, [], []
    for rule in hidden["rules"]:
        if any(re.search(p, blueprint) for p in rule["any"]):
            rule_hits += 1
        elif any(re.search(p, requirements) for p in rule["any"]):
            rule_hits += 0.5
            weak.append(rule["id"])
        else:
            missing_rules.append(rule["id"])
    rules = rule_hits / len(hidden["rules"])

    missing_endpoints = [p for p in hidden["endpoints"] if not re.search(p, blueprint, re.I)]
    endpoints = 1 - len(missing_endpoints) / len(hidden["endpoints"])

    state_text = "\n".join(d.source for d in plantuml.extract(blueprint) if "[*]" in d.source)
    state_tokens = {norm(t) for t in re.findall(r"[A-Za-z_]+", state_text)}
    missing_states = [g for g in hidden["states"] if not any(norm(s) in state_tokens for s in g)]
    states = 1 - len(missing_states) / len(hidden["states"])

    present = diagram_kinds(plantuml.extract(blueprint) + plantuml.extract(arch))
    missing_kinds = [k for k in hidden["diagrams"] if k not in present]
    kinds = 1 - len(missing_kinds) / len(hidden["diagrams"])

    rs.parts = {
        "validity": round(validity, 3),
        "concepts": round(concepts, 3),
        "rules": round(rules, 3),
        "endpoints": round(endpoints, 3),
        "states": round(states, 3),
        "diagrams": round(kinds, 3),
        "n_diagrams": len(diagrams),
    }
    rs.score = round(
        validity
        * (
            WEIGHTS["concepts"] * concepts
            + WEIGHTS["rules"] * rules
            + WEIGHTS["endpoints"] * endpoints
            + WEIGHTS["states"] * states
            + WEIGHTS["diagrams"] * kinds
        ),
        4,
    )
    if missing_concepts:
        rs.feedback.append(
            "Domain concepts the blueprint's class/ER diagrams never declare as a type: "
            + "; ".join("/".join(g[:3]) for g in missing_concepts)
        )
    if weak:
        rs.feedback.append(
            "Business rules stated in requirements but absent from the blueprint: "
            + ", ".join(weak)
        )
    if missing_rules:
        rs.feedback.append(
            "Business rules missing from both documents: " + ", ".join(missing_rules)
        )
    if missing_endpoints:
        rs.feedback.append(
            f"{len(missing_endpoints)} key API operations are not named in the blueprint's "
            "interface (endpoint table / sequence messages)."
        )
    if missing_states:
        rs.feedback.append(
            "Lifecycle states missing from the state diagrams: "
            + "; ".join("/".join(g[:2]) for g in missing_states)
        )
    if missing_kinds:
        rs.feedback.append("Required diagram kinds missing: " + ", ".join(missing_kinds))
    if invalid:
        rs.feedback.append(
            f"{len(invalid)} diagrams still fail PlantUML: "
            + "; ".join(f"{e.name}: {e.message}" for e in invalid[:5])
        )
    manifest = run_dir / "manifest.json"
    if manifest.is_file():
        m = json.loads(manifest.read_text())
        rs.tokens = int((m.get("token_usage_total") or {}).get("total_tokens", 0))
        rs.seconds = round(sum((m.get("timings_s") or {}).values()), 1)
        repairs = sum(
            c.get("repair_rounds", 0)
            for c in (m.get("quality", {}).get("diagrams", {}).get("per_stage", {}) or {}).values()
        )
        if repairs:
            rs.feedback.append(
                f"Needed {repairs} PlantUML repair round(s) before diagrams were valid."
            )
    return rs


def run_one(variant: Path, name: str, out: Path, env: dict, timeout: int) -> ReqScore:
    req = EVALS / "requirements" / f"{name}.md"
    base = out / name
    base.mkdir(parents=True, exist_ok=True)
    cmd = [
        "uv", "run", "--quiet", "--project", str(variant / "workflow_multi_agent" / "crewai_code"),
        "nl2bp", "multi", "--until", "blueprint", "--no-git", "--no-tests",
        "--name", name, "--description-file", str(req), "--output-dir", str(base),
    ]  # fmt: skip
    log = base / "run.log"
    try:
        with open(log, "w") as fh:
            subprocess.run(cmd, cwd=variant, env=env, stdout=fh, stderr=subprocess.STDOUT,
                           timeout=timeout, check=False)  # fmt: skip
    except subprocess.TimeoutExpired:
        return ReqScore(name, error=f"timed out after {timeout}s", feedback=["The run timed out."])
    runs = sorted(p for p in base.iterdir() if p.is_dir())
    if not runs:
        return ReqScore(name, error="no run directory", feedback=["The run crashed; see run.log."])
    return score_run(name, runs[-1])


def evaluate(variant: Path, names: list[str], out: Path, parallel: int = 6,
             timeout: int = 1500) -> dict:  # fmt: skip
    env = dict(os.environ)
    env.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
    env.setdefault("CREWAI_TRACING_ENABLED", "false")
    env.setdefault("OTEL_SDK_DISABLED", "true")
    with ThreadPoolExecutor(max_workers=parallel) as pool:
        results = list(pool.map(lambda n: run_one(variant, n, out, env, timeout), names))
    scores = {r.name: r.as_dict() for r in results}
    mean = sum(r.score for r in results) / len(results) if results else 0.0
    return {"mean": round(mean, 4), "per_req": scores,
            "tokens": sum(r.tokens for r in results)}  # fmt: skip
