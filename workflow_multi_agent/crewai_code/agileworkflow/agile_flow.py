"""Multi-agent agile workflow: natural language -> architecture -> UML blueprint -> code.

Stage graph (each stage runs exactly once, frontend/backend and sprint planning
run concurrently):

    prepare
      └─ system_design
           └─ requirement_analysis
                ├─ sprint_planning ───────────────────────────┐
                └─ blueprint_design (+ optional human review)  │
                     ├─ frontend_design ─┐                     │
                     └─ backend_design ──┤                     │
                                         ├─ version_control ───┼──┐
                                         └─ agile_dashboard ◄──┘  │
                                              └─ feedback_planning┤
                                                                  └─ system_design_summary
                                                                       └─ finish
"""

from __future__ import annotations

import datetime as _dt
from collections.abc import Callable
from typing import Any

from crewai.flow.flow import Flow, and_, listen, start
from pydantic import BaseModel, Field

from agileworkflow.crews.agile_crew.agile_crew import (
    AgileCrew,
    StageResult,
    StageRunner,
    stage_inputs,
)
from agileworkflow.settings import DEFAULT_LANGUAGE, Settings
from agileworkflow.workspace import Workspace, slugify

NO_FEEDBACK = "（无）"


class AgileWorkflowState(BaseModel):
    project_name: str = ""
    project_description: str = ""
    sprint_duration: str = "14"
    language: str = DEFAULT_LANGUAGE
    human_review: bool = False
    max_review_rounds: int = 3
    review_feedback: str = NO_FEEDBACK
    run_dir: str = ""
    outputs: dict[str, str] = Field(default_factory=dict)
    usage: dict[str, dict[str, Any]] = Field(default_factory=dict)
    timings: dict[str, float] = Field(default_factory=dict)


RunnerFactory = Callable[[Workspace], StageRunner]


class AgileWorkflowFlow(Flow[AgileWorkflowState]):
    """敏捷 LLM 多 Agent 开发工作流 / agile multi-agent workflow."""

    def __init__(
        self,
        settings: Settings | None = None,
        runner_factory: RunnerFactory | None = None,
        input_fn: Callable[[str], str] = input,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._settings = settings
        self._runner_factory = runner_factory
        self._input = input_fn
        self._runner: StageRunner | None = None
        self.workspace: Workspace | None = None

    # -- helpers ---------------------------------------------------------------

    def _values(self) -> dict[str, Any]:
        s = self.state
        return {
            "project_name": s.project_name,
            "project_slug": slugify(s.project_name).lower(),
            "project_description": s.project_description,
            "sprint_duration": s.sprint_duration,
            "language": s.language,
            "review_feedback": s.review_feedback,
            **s.outputs,
        }

    async def _stage(self, stage: str) -> str:
        values = self._values()
        missing = stage_inputs(stage) - set(values) - {"blueprint_guide"}
        if missing:
            raise RuntimeError(f"stage {stage!r} started before its inputs: {sorted(missing)}")
        print(f"▶ {stage} …", flush=True)
        t0 = _dt.datetime.now()
        result: StageResult = await self._runner.run(stage, values)
        self.state.timings[stage] = round((_dt.datetime.now() - t0).total_seconds(), 1)
        self.state.outputs[stage] = result.text
        if result.usage:
            self.state.usage[stage] = result.usage
        written = self.workspace.save_stage(stage, result.text)
        print(f"✔ {stage} ({self.state.timings[stage]}s, {len(written)} file(s))", flush=True)
        return result.text

    # -- stages ----------------------------------------------------------------

    @start()
    def prepare(self):
        s = self.state
        s.project_name = s.project_name.strip()
        s.project_description = s.project_description.strip()
        if not s.project_name or not s.project_description:
            raise ValueError("project_name and project_description are required")
        if not str(s.sprint_duration).isdigit() or not 1 <= int(s.sprint_duration) <= 60:
            raise ValueError("sprint_duration must be a whole number of days between 1 and 60")
        settings = self._settings or Settings.from_env()
        if s.language == DEFAULT_LANGUAGE and settings.language != DEFAULT_LANGUAGE:
            s.language = settings.language
        self.workspace = Workspace.create(settings.output_dir, s.project_name)
        s.run_dir = str(self.workspace.root)
        factory = self._runner_factory or (lambda ws: AgileCrew(settings, ws))
        self._runner = factory(self.workspace)
        print(f"\n=== NL2BP 多 Agent 工作流: {s.project_name} → {s.run_dir} ===\n")

    @listen(prepare)
    async def system_design(self):
        return await self._stage("system_design")

    @listen(system_design)
    async def requirement_analysis(self):
        return await self._stage("requirement_analysis")

    @listen(requirement_analysis)
    async def sprint_planning(self):
        self.state.outputs["sprint_plan"] = await self._stage("sprint_planning")

    @listen(requirement_analysis)
    async def blueprint_design(self):
        text = await self._stage("blueprint_design")
        rounds = 0
        while self.state.human_review and rounds < self.state.max_review_rounds:
            path = self.workspace.root / "docs" / "blueprint_design.md"
            feedback = self._input(
                f"\n[人类协作者] 请查看 {path}\n输入修改意见后回车重新生成，直接回车接受蓝图: "
            ).strip()
            if not feedback:
                break
            rounds += 1
            self.state.review_feedback = feedback
            self.workspace.write(f"docs/review_round_{rounds}.md", feedback)
            text = await self._stage("blueprint_design")
        return text

    @listen(blueprint_design)
    async def frontend_design(self):
        return await self._stage("frontend_design")

    @listen(blueprint_design)
    async def backend_design(self):
        return await self._stage("backend_design")

    @listen(and_(frontend_design, backend_design))
    async def version_control(self):
        return await self._stage("version_control")

    @listen(and_(frontend_design, backend_design, sprint_planning))
    async def agile_dashboard(self):
        return await self._stage("agile_dashboard")

    @listen(agile_dashboard)
    async def feedback_planning(self):
        return await self._stage("feedback_planning")

    @listen(and_(version_control, feedback_planning))
    async def system_design_summary(self):
        return await self._stage("system_design_summary")

    @listen(system_design_summary)
    def finish(self):
        s = self.state
        settings = self._settings
        self.workspace.write_manifest(
            {
                "workflow": "multi_agent",
                "run_id": self.workspace.run_id,
                "project_name": s.project_name,
                "project_description": s.project_description,
                "sprint_duration": s.sprint_duration,
                "language": s.language,
                "model": settings.model if settings else None,
                "stages": list(s.timings),
                "timings_s": s.timings,
                "token_usage": s.usage,
                "review_feedback": s.review_feedback if s.review_feedback != NO_FEEDBACK else None,
            }
        )
        print(f"\n=== 完成 / done: {s.run_dir} ===")
        return s.run_dir
