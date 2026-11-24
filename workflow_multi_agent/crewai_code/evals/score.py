"""Score a finished run directory with the pre-registered metrics.

    uv run python evals/score.py output/<run> [...]

M1  share of .puml files that pass `plantuml -syntax`
M2  share of types declared in the blueprint's class diagrams that appear in the code
M3  the generated backend's tests pass in a Docker sandbox
Applied identically to baseline (pre-improvement) and improved runs; it re-measures
everything from the files on disk and ignores what the run itself claims.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from agileworkflow import contract, plantuml, quality

BLUEPRINT_DOCS = ("docs/blueprint_design.md", "docs/03_blueprint.md")
CODE_DIRS = ("frontend", "backend", "code")


def score(run: Path, run_tests: bool = True) -> dict:
    pumls = sorted((run / "diagrams").glob("*.puml"))
    invalid = []
    for f in pumls:
        err = quality.check_diagram(f.read_text(encoding="utf-8"))
        if err:
            invalid.append(f"{f.name}: line {err.line}: {err.message}")
    blueprint = next((run / d for d in BLUEPRINT_DOCS if (run / d).is_file()), None)
    declared = (
        contract.declared_types(plantuml.extract(blueprint.read_text(encoding="utf-8")))
        if blueprint
        else []
    )
    conf = contract.check_conformance(declared, contract.code_files(run, CODE_DIRS))
    project = run / "backend" if (run / "backend").is_dir() else run / "code"
    tests = quality.run_tests(project) if run_tests else {"status": "skipped"}
    manifest = (
        json.loads((run / "manifest.json").read_text()) if (run / "manifest.json").is_file() else {}
    )
    tokens = manifest.get("token_usage_total") or {}
    if not tokens:
        for u in (manifest.get("token_usage") or {}).values():
            for k, v in u.items():
                if isinstance(v, int):
                    tokens[k] = tokens.get(k, 0) + v
    return {
        "run": run.name,
        "M1_diagrams_valid": f"{len(pumls) - len(invalid)}/{len(pumls)}",
        "M1_ratio": round((len(pumls) - len(invalid)) / len(pumls), 3) if pumls else None,
        "M1_invalid": invalid,
        "M2_conformance": conf.ratio,
        "M2_declared": len(declared),
        "M2_missing": conf.missing,
        "M3_tests": tests.get("status"),
        "M3_reason": tests.get("reason"),
        "M3_tail": (tests.get("output") or "")[-800:],
        "code_files": conf.files_scanned,
        "wall_s": round(sum((manifest.get("timings_s") or {}).values()), 1),
        "tokens": tokens,
    }


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(json.dumps(score(Path(arg)), ensure_ascii=False, indent=2))
