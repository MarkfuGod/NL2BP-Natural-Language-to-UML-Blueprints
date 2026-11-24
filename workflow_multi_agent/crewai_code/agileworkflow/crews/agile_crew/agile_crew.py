"""Builds and runs one workflow stage as a one-agent, one-task crew."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any, Protocol

import yaml

from agileworkflow.settings import Settings
from agileworkflow.templating import placeholders, render
from agileworkflow.workspace import Workspace

HERE = Path(__file__).parent
CONFIG_DIR = HERE / "config"

# Tools per stage; stages not listed get none.
STAGE_TOOLS: dict[str, tuple[str, ...]] = {
    "frontend_design": ("write_file",),
    "backend_design": ("write_file",),
    "conformance_fix": ("write_file", "read_file", "list_files"),
    "test_fix": ("write_file", "read_file", "list_files"),
}
CODE_STAGES = frozenset(STAGE_TOOLS)


@dataclass
class StageResult:
    stage: str
    text: str
    usage: dict[str, Any] = field(default_factory=dict)


class StageRunner(Protocol):
    async def run(self, stage: str, values: Mapping[str, Any]) -> StageResult: ...


def load_config() -> tuple[dict, dict]:
    agents = yaml.safe_load((CONFIG_DIR / "agents.yaml").read_text(encoding="utf-8"))
    tasks = yaml.safe_load((CONFIG_DIR / "tasks.yaml").read_text(encoding="utf-8"))
    return agents, tasks


def stage_names(include_helpers: bool = False) -> list[str]:
    return [
        key.removesuffix("_task")
        for key, spec in load_config()[1].items()
        if include_helpers or not spec.get("helper")
    ]


def stage_inputs(stage: str) -> set[str]:
    """Placeholders a stage's task text needs."""
    _, tasks = load_config()
    spec = tasks[f"{stage}_task"]
    return placeholders(spec["description"]) | placeholders(spec["expected_output"])


class AgileCrew:
    """Real runner: calls the configured LLM through CrewAI."""

    def __init__(self, settings: Settings, workspace: Workspace):
        self.settings = settings
        self.workspace = workspace
        self.agents_config, self.tasks_config = load_config()

    @cached_property
    def blueprint_guide(self) -> str:
        # Single source shared with the single-agent workflow and the Roo Code mode.
        from agileworkflow.single_agent.roles import find_role_prompts_dir

        path = find_role_prompts_dir() / "rules-blueprintdesign" / "03-output-contract.md"
        return path.read_text(encoding="utf-8")

    def build(self, stage: str, values: Mapping[str, Any]):
        from crewai import Agent, Task

        from agileworkflow.tools import FileWriterTool, ListFilesTool, ReadFileTool

        table = {
            "write_file": FileWriterTool,
            "read_file": ReadFileTool,
            "list_files": ListFilesTool,
        }

        task_spec = self.tasks_config[f"{stage}_task"]
        agent_key = task_spec["agent"]
        agent_spec = self.agents_config[agent_key]
        values = {"blueprint_guide": self.blueprint_guide, **values}

        agent = Agent(
            role=agent_spec["role"].strip(),
            goal=agent_spec["goal"].strip(),
            backstory=agent_spec["backstory"].strip(),
            # A fresh LLM per stage: CrewAI accumulates token usage on the LLM object,
            # so a shared one would report running totals (and mix concurrent stages).
            llm=self.settings.build_llm(),
            tools=[table[name](self.workspace) for name in STAGE_TOOLS.get(stage, ())],
            allow_delegation=False,
            verbose=self.settings.verbose,
            max_iter=40 if stage in CODE_STAGES else 15,
        )
        task = Task(
            name=stage,
            description=render(task_spec["description"], values),
            expected_output=render(task_spec["expected_output"], values),
            agent=agent,
        )
        return agent, task

    async def run(self, stage: str, values: Mapping[str, Any]) -> StageResult:
        from crewai import Crew, Process

        agent, task = self.build(stage, values)
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=self.settings.verbose,
        )
        # No inputs: text is already rendered, so CrewAI does no interpolation.
        output = await crew.kickoff_async()
        usage = getattr(output, "token_usage", None)
        usage = usage.model_dump() if hasattr(usage, "model_dump") else {}
        return StageResult(stage=stage, text=output.raw or "", usage=usage)
