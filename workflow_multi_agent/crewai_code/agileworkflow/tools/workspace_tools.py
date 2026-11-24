"""Read-only tools confined to one run's workspace directory."""

from __future__ import annotations

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from agileworkflow.workspace import UnsafePathError, Workspace

MAX_READ_CHARS = 60_000


class ReadFileInput(BaseModel):
    path: str = Field(
        ..., description="相对于本次运行目录的文件路径 / path relative to the run directory"
    )


class ReadFileTool(BaseTool):
    name: str = "read_file"
    description: str = "读取本次运行目录中的一个文件 / read one file from this run's directory."
    args_schema: type[BaseModel] = ReadFileInput
    _workspace: Workspace = PrivateAttr()

    def __init__(self, workspace: Workspace, **kwargs):
        super().__init__(**kwargs)
        self._workspace = workspace

    def _run(self, path: str) -> str:
        try:
            target = self._workspace.resolve(path)
        except UnsafePathError as exc:
            return f"拒绝 / refused: {exc}"
        if not target.is_file():
            return f"不存在 / not found: {path}"
        text = target.read_text(encoding="utf-8", errors="replace")
        if len(text) > MAX_READ_CHARS:
            text = text[:MAX_READ_CHARS] + f"\n… [truncated at {MAX_READ_CHARS} chars]"
        return text


class ListFilesInput(BaseModel):
    directory: str = Field(
        ".", description="相对目录，默认根目录 / relative directory, default root"
    )


class ListFilesTool(BaseTool):
    name: str = "list_files"
    description: str = "列出本次运行目录中的文件 / list files in this run's directory."
    args_schema: type[BaseModel] = ListFilesInput
    _workspace: Workspace = PrivateAttr()

    def __init__(self, workspace: Workspace, **kwargs):
        super().__init__(**kwargs)
        self._workspace = workspace

    def _run(self, directory: str = ".") -> str:
        root = self._workspace.root
        try:
            base = (
                root if directory.strip() in ("", ".", "/") else self._workspace.resolve(directory)
            )
        except UnsafePathError as exc:
            return f"拒绝 / refused: {exc}"
        if not base.is_dir():
            return f"不存在 / not found: {directory}"
        files = sorted(str(p.relative_to(root)) for p in base.rglob("*") if p.is_file())
        return "\n".join(files[:500]) or "(空 / empty)"
