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
PROMPTS_DIR = HERE / "prompts"

# Stages that write code files through the write_file tool.
CODE_STAGES = frozenset({"frontend_design", "backend_design"})


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


def stage_names() -> list[str]:
    return [key.removesuffix("_task") for key in load_config()[1]]


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
    def llm(self):
        return self.settings.build_llm()

    @cached_property
    def blueprint_guide(self) -> str:
        return (PROMPTS_DIR / "blueprint_guide.md").read_text(encoding="utf-8")

    def build(self, stage: str, values: Mapping[str, Any]):
        from crewai import Agent, Task

        from agileworkflow.tools import FileWriterTool

        task_spec = self.tasks_config[f"{stage}_task"]
        agent_key = task_spec["agent"]
        agent_spec = self.agents_config[agent_key]
        values = {"blueprint_guide": self.blueprint_guide, **values}

        agent = Agent(
            role=agent_spec["role"].strip(),
            goal=agent_spec["goal"].strip(),
            backstory=agent_spec["backstory"].strip(),
            llm=self.llm,
            tools=[FileWriterTool(self.workspace)] if stage in CODE_STAGES else [],
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
