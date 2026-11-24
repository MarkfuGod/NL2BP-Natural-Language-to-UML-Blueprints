"""The single-agent roles, backed by workflow_single_agent/role_prompts/rules-<slug>/."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Role:
    slug: str
    title: str
    tools: tuple[str, ...] = ()


ROLES: dict[str, Role] = {
    r.slug: r
    for r in (
        Role("01-req-gen", "需求分析师 / Requirements Analyst"),
        Role("systemdesign", "架构设计师 / System Architect"),
        Role("blueprintdesign", "蓝图设计师 / Blueprint Designer"),
        Role("coder", "编码工程师 / Coder", ("write_file", "read_file", "list_files")),
        Role("code-reviewer", "代码审查员 / Code Reviewer", ("read_file", "list_files")),
        Role("code-critic", "代码诊断师 / Code Critic", ("read_file", "list_files")),
        Role(
            "debugger-deployer",
            "部署调试员 / Debugger & Deployer",
            ("write_file", "read_file", "list_files"),
        ),
    )
}


def find_role_prompts_dir(start: Path | None = None) -> Path:
    """Locate role_prompts/: $NL2BP_ROLE_PROMPTS, else walk up to workflow_single_agent/."""
    env = os.environ.get("NL2BP_ROLE_PROMPTS")
    if env:
        path = Path(env).expanduser()
        if not path.is_dir():
            raise FileNotFoundError(f"NL2BP_ROLE_PROMPTS={env} is not a directory")
        return path
    here = (start or Path(__file__)).resolve()
    for parent in [here, *here.parents]:
        candidate = parent / "workflow_single_agent" / "role_prompts"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not find workflow_single_agent/role_prompts; run from the NL2BP repo "
        "or set NL2BP_ROLE_PROMPTS."
    )


def load_role_prompt(slug: str, prompts_dir: Path | None = None) -> str:
    folder = (prompts_dir or find_role_prompts_dir()) / f"rules-{slug}"
    files = sorted(folder.glob("*.md"))
    if not files:
        raise FileNotFoundError(f"no prompt files in {folder}")
    return "\n\n".join(f.read_text(encoding="utf-8").strip() for f in files)
