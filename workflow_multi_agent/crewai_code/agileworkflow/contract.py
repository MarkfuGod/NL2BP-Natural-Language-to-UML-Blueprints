"""Treat the blueprint as a contract: what the class diagrams declare, what the code has.

The class diagrams name the types the implementation must contain. We pull those
names out, hand them to the code stages as an explicit checklist, and afterwards
measure how many actually appear in the generated code.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from agileworkflow.plantuml import Diagram

_DECL = re.compile(
    r"^\s*(?:abstract\s+class|abstract|class|interface|enum|entity|record|struct)\s+"
    r"(?:\"[^\"]*\"\s+as\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)",
    re.MULTILINE,
)
_CODE_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".go",
    ".rb",
    ".php",
    ".cs",
    ".kt",
    ".html",
    ".vue",
    ".sql",
    ".rs",
    ".swift",
}
_SKIP_DIRS = {"node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".git"}


def declared_types(diagrams: list[Diagram]) -> list[str]:
    """Class/interface/enum names declared in @startuml class-style diagrams, in order."""
    seen: dict[str, None] = {}
    for d in diagrams:
        if d.kind != "uml":
            continue
        for m in _DECL.finditer(d.source):
            seen.setdefault(m.group("name"), None)
    return list(seen)


def name_variants(name: str) -> set[str]:
    words = re.findall(r"[A-Z]+(?=[A-Z][a-z]|\d|\b)|[A-Z]?[a-z]+|\d+", name) or [name]
    lower = [w.lower() for w in words]
    return {name.lower(), "_".join(lower), "-".join(lower), "".join(lower)}


def code_files(root: Path, subdirs: tuple[str, ...]) -> list[Path]:
    out = []
    for sub in subdirs:
        base = root / sub
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.suffix in _CODE_SUFFIXES and not _SKIP_DIRS & set(p.parts):
                out.append(p)
    return sorted(out)


@dataclass
class Conformance:
    declared: list[str]
    found: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    files_scanned: int = 0

    @property
    def ratio(self) -> float | None:
        return round(len(self.found) / len(self.declared), 3) if self.declared else None

    def as_dict(self) -> dict:
        return {
            "declared": len(self.declared),
            "found": len(self.found),
            "ratio": self.ratio,
            "missing": self.missing,
            "files_scanned": self.files_scanned,
        }


def check_conformance(declared: list[str], files: list[Path]) -> Conformance:
    haystack = "\n".join(f.read_text(encoding="utf-8", errors="replace") for f in files).lower()
    tokens = set(re.findall(r"[a-z0-9_\-]+", haystack))
    result = Conformance(declared=declared, files_scanned=len(files))
    for name in declared:
        hit = any(v in tokens for v in name_variants(name))
        (result.found if hit else result.missing).append(name)
    return result


def checklist(declared: list[str]) -> str:
    if not declared:
        return "（蓝图类图中没有声明类型）"
    return "\n".join(f"- {n}" for n in declared)
