"""Per-run output directory with path confinement."""

from __future__ import annotations

import datetime as _dt
import json
import re
from dataclasses import dataclass
from pathlib import Path

from agileworkflow import plantuml


def slugify(text: str, fallback: str = "project") -> str:
    """Filesystem-safe name that keeps CJK characters."""
    slug = re.sub(r"[^\w\-]+", "_", text.strip(), flags=re.UNICODE).strip("_")
    return slug[:60] or fallback


class UnsafePathError(ValueError):
    pass


@dataclass
class Workspace:
    root: Path

    @classmethod
    def create(cls, base: Path, project_name: str, now: _dt.datetime | None = None) -> Workspace:
        now = now or _dt.datetime.now()
        root = Path(base) / f"{now:%Y%m%d-%H%M%S}_{slugify(project_name)}"
        root.mkdir(parents=True, exist_ok=False)
        return cls(root.resolve())

    @property
    def run_id(self) -> str:
        return self.root.name

    def resolve(self, relative: str) -> Path:
        """Resolve a model-supplied relative path, refusing anything outside root."""
        rel = Path(relative.strip().lstrip("/\\"))
        if not rel.parts or rel.is_absolute():
            raise UnsafePathError(f"invalid path: {relative!r}")
        target = (self.root / rel).resolve()
        if target != self.root and self.root not in target.parents:
            raise UnsafePathError(f"path escapes the run directory: {relative!r}")
        return target

    def write(self, relative: str, content: str) -> Path:
        target = self.resolve(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def save_stage(self, stage: str, content: str) -> list[Path]:
        """Write ``docs/<stage>.md`` and every PlantUML block in it to ``diagrams/``."""
        written = [self.write(f"docs/{stage}.md", content)]
        for diagram in plantuml.extract(content, default_prefix=stage):
            written.append(self.write(f"diagrams/{diagram.filename}", diagram.source))
        return written

    def write_manifest(self, data: dict) -> Path:
        return self.write("manifest.json", json.dumps(data, ensure_ascii=False, indent=2))
