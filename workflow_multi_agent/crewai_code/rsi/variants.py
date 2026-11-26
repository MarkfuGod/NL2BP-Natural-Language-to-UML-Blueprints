"""Variants of the L0 workflow: snapshots of the editable surface, edits, materialisation."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

# Phase A surface (PROTOCOL.md). Paths relative to the repository root.
SURFACE = (
    "skills/nl2bp/references/diagram-selection.md",
    "skills/nl2bp/references/output-contract.md",
    "skills/nl2bp/references/plantuml-syntax.md",
    "workflow_multi_agent/crewai_code/agileworkflow/crews/agile_crew/config/tasks.yaml",
    "workflow_multi_agent/crewai_code/agileworkflow/crews/agile_crew/config/agents.yaml",
)
MAX_GROWTH = 1.25
MAX_EDITS = 3


class EditError(ValueError):
    pass


def snapshot(repo: Path) -> dict[str, str]:
    return {p: (repo / p).read_text(encoding="utf-8") for p in SURFACE}


def surface_size(files: dict[str, str]) -> int:
    return sum(len(v) for v in files.values())


def apply_edits(files: dict[str, str], edits: list[dict], baseline_size: int) -> dict[str, str]:
    """Return a new snapshot with search/replace edits applied, or raise EditError."""
    if not edits:
        raise EditError("no edits proposed")
    if len(edits) > MAX_EDITS:
        raise EditError(f"{len(edits)} edits > {MAX_EDITS}")
    out = dict(files)
    for e in edits:
        path, old, new = e.get("file"), e.get("old"), e.get("new")
        if path not in SURFACE:
            raise EditError(f"file outside the editable surface: {path}")
        if not isinstance(old, str) or not old or not isinstance(new, str):
            raise EditError("each edit needs non-empty 'old' and a string 'new'")
        count = out[path].count(old)
        if count != 1:
            raise EditError(f"'old' text found {count} times in {path} (must be exactly once)")
        out[path] = out[path].replace(old, new, 1)
    if surface_size(out) > baseline_size * MAX_GROWTH:
        raise EditError("surface would grow more than 25 % over baseline")
    if "tasks.yaml" in "".join(e["file"] for e in edits):
        import yaml

        for p in SURFACE:
            if p.endswith(".yaml"):
                try:
                    yaml.safe_load(out[p])
                except yaml.YAMLError as exc:
                    raise EditError(f"{p} is no longer valid YAML: {exc}") from exc
    return out


def materialise(repo: Path, base_commit: str, files: dict[str, str], dest: Path) -> Path:
    """A git worktree at base_commit with the variant's surface files written over it."""
    dest = dest.resolve()  # git runs in `repo`; a relative path would land somewhere else
    if dest.exists():
        subprocess.run(["git", "worktree", "remove", "--force", str(dest)], cwd=repo,
                       capture_output=True)  # fmt: skip
        shutil.rmtree(dest, ignore_errors=True)
    subprocess.run(["git", "worktree", "add", "-q", "--detach", str(dest), base_commit],
                   cwd=repo, check=True)  # fmt: skip
    for p, text in files.items():
        (dest / p).write_text(text, encoding="utf-8")
    return dest


def remove(repo: Path, dest: Path) -> None:
    subprocess.run(["git", "worktree", "remove", "--force", str(dest.resolve())], cwd=repo,
                   capture_output=True)  # fmt: skip


def parse_json(text: str) -> dict:
    """First JSON object in a model reply (tolerates ``` fences and prose around it)."""
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    raw = fenced.group(1) if fenced else text[text.find("{") : text.rfind("}") + 1]
    return json.loads(raw)
