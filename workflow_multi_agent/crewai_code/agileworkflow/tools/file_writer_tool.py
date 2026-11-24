"""File writer confined to one run's workspace directory."""

from __future__ import annotations

from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

from agileworkflow.workspace import UnsafePathError, Workspace

MAX_BYTES = 512 * 1024


class FileWriterToolInput(BaseModel):
    path: str = Field(
        ...,
        description="相对于本次运行目录的文件路径 / path relative to the run directory, "
        "例如 e.g. frontend/index.html, backend/src/app.py",
    )
    content: str = Field(..., description="完整文件内容 / full file content")


class FileWriterTool(BaseTool):
    name: str = "write_file"
    description: str = (
        "把一个完整文件写入本次运行目录（只能写相对路径，不能写到目录之外）。"
        "Write one complete file inside this run's directory; relative paths only."
    )
    args_schema: type[BaseModel] = FileWriterToolInput
    _workspace: Workspace = PrivateAttr()

    def __init__(self, workspace: Workspace, **kwargs):
        super().__init__(**kwargs)
        self._workspace = workspace

    def _run(self, path: str, content: str) -> str:
        if len(content.encode("utf-8")) > MAX_BYTES:
            return f"拒绝 / refused: {path} 超过 exceeds {MAX_BYTES} bytes"
        try:
            target = self._workspace.write(path, content)
        except UnsafePathError as exc:
            return f"拒绝 / refused: {exc}"
        return f"已写入 / wrote {target.relative_to(self._workspace.root)}"
