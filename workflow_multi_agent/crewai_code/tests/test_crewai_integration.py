"""Drive real CrewAI Agent/Task/Crew objects with a fake LLM (no network)."""

import asyncio
import re

from crewai.llms.base_llm import BaseLLM

from agileworkflow.crews.agile_crew.agile_crew import AgileCrew
from agileworkflow.single_agent.runner import CrewRoleRunner, RoleTask
from agileworkflow.workspace import Workspace

ANSWER = "## 蓝图\n\n```plantuml\n@startuml demo_class_core\nclass A { +x: int }\n@enduml\n```\n"


class FakeLLM(BaseLLM):
    prompts: list = []

    def call(
        self,
        messages,
        tools=None,
        callbacks=None,
        available_functions=None,
        from_task=None,
        from_agent=None,
        response_model=None,
    ):
        text = (
            messages
            if isinstance(messages, str)
            else "\n".join(str(m.get("content", "")) for m in messages)
        )
        self.prompts.append(text)
        return f"Thought: I now know the final answer\nFinal Answer: {ANSWER}"

    def supports_function_calling(self) -> bool:
        return False

    def supports_stop_words(self) -> bool:
        return True

    def get_context_window_size(self) -> int:
        return 128_000


def test_agile_stage_runs_through_crewai(settings, monkeypatch):
    fake = FakeLLM(model="fake")
    monkeypatch.setattr(type(settings), "build_llm", lambda self: fake)
    ws = Workspace.create(settings.output_dir, "demo")
    crew = AgileCrew(settings, ws)
    values = {
        "project_name": "demo",
        "project_slug": "demo",
        "language": "中文",
        "system_design": "架构 {not_a_placeholder} skinparam { x }",
        "requirement_analysis": "需求",
        "review_feedback": "（无）",
    }
    result = asyncio.run(crew.run("blueprint_design", values))
    assert "@startuml demo_class_core" in result.text
    prompt = "\n".join(fake.prompts)
    assert "{not_a_placeholder}" in prompt  # passed through untouched
    assert "Blueprint output contract" in prompt  # skill references injected
    assert "PlantUML syntax reference" in prompt
    assert not re.search(r"\{(system_design|requirement_analysis|language)\}", prompt)


def test_code_stage_gets_write_tool(settings, monkeypatch):
    monkeypatch.setattr(type(settings), "build_llm", lambda self: FakeLLM(model="fake"))
    ws = Workspace.create(settings.output_dir, "demo")
    agent, _ = AgileCrew(settings, ws).build("backend_design", {"blueprint_design": "x"})
    assert [t.name for t in agent.tools] == ["write_file"]
    agent, _ = AgileCrew(settings, ws).build("system_design", {})
    assert agent.tools == []


def test_single_agent_role_runs_through_crewai(settings, monkeypatch):
    monkeypatch.setattr(type(settings), "build_llm", lambda self: FakeLLM(model="fake"))
    ws = Workspace.create(settings.output_dir, "demo")
    runner = CrewRoleRunner(ws, settings)
    result = runner.run(
        RoleTask("03_blueprint", "blueprintdesign", "body", "doc"),
        "rules with braces {like_this} and class X { }",
    )
    assert result.text.startswith("## 蓝图")
