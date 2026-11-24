"""Multi-agent agile workflow: natural language -> architecture -> UML blueprint -> code.

Stage graph (each stage runs once; frontend/backend and sprint planning run
concurrently):

    prepare
      └─ system_design
           └─ requirement_analysis
                ├─ sprint_planning ─────────────────────────────┐
                └─ blueprint_design (+ optional human review)    │
                     ├─ frontend_design ─┐                       │
                     └─ backend_design ──┴─ verify               │
                                              ├─ version_control │
                                              └─ agile_dashboard ◄┘
                                                   └─ feedback_planning
                                    version_control + feedback_planning
                                                   └─ system_design_summary ─ finish

Quality gates (real measurements, not agent claims):
- every stage's PlantUML blocks are syntax-checked; failures go back to the
  blueprint agent for repair (bounded rounds)
- the class diagrams' declared types become a checklist for the code stages,
  and `verify` measures how many reached the code (one fix round if short)
- `verify` runs backend tests in a Docker sandbox (one fix round on failure)
- the run directory is a git repo, committed after each stage; the version
  control agent reports on that real history, and the dashboard/feedback agents
  get the measured signals instead of inventing status
"""

from __future__ import annotations

import asyncio
import datetime as _dt
import json
from collections.abc import Callable
from typing import Any

from crewai.flow.flow import Flow, and_, listen, start
from pydantic import BaseModel, Field

from agileworkflow import contract, plantuml, quality
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
    diagram_checks: dict[str, dict[str, Any]] = Field(default_factory=dict)
    quality: dict[str, Any] = Field(default_factory=dict)
    commits: list[str] = Field(default_factory=list)


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
        self._git_lock = asyncio.Lock()
        self.workspace: Workspace | None = None

    # -- helpers ---------------------------------------------------------------

    @property
    def settings(self) -> Settings:
        return self._settings

    def _values(self) -> dict[str, Any]:
        s = self.state
        return {
            "project_name": s.project_name,
            "project_slug": slugify(s.project_name).lower(),
            "project_description": s.project_description,
            "sprint_duration": s.sprint_duration,
            "language": s.language,
            "review_feedback": s.review_feedback,
            "contract": contract.checklist([]),
            **s.outputs,
        }

    def _record(self, stage: str, result: StageResult, seconds: float) -> None:
        s = self.state
        s.timings[stage] = round(s.timings.get(stage, 0) + seconds, 1)
        if result.usage:
            prev = s.usage.get(stage)
            if prev:  # helper tasks can run several times; sum their token counts
                for key, value in result.usage.items():
                    if isinstance(value, (int, float)):
                        prev[key] = prev.get(key, 0) + value
            else:
                s.usage[stage] = dict(result.usage)

    async def _call(self, stage: str, extra: dict[str, Any] | None = None) -> str:
        values = {**self._values(), **(extra or {})}
        missing = stage_inputs(stage) - set(values) - {"blueprint_guide"}
        if missing:
            raise RuntimeError(f"stage {stage!r} started before its inputs: {sorted(missing)}")
        print(f"▶ {stage} …", flush=True)
        t0 = _dt.datetime.now()
        result: StageResult = await self._runner.run(stage, values)
        self._record(stage, result, (_dt.datetime.now() - t0).total_seconds())
        print(f"✔ {stage} ({self.state.timings[stage]}s)", flush=True)
        return result.text

    async def _commit(self, message: str, paths: list[str] | None = None) -> None:
        if not self.settings.git_history or not quality.git_available():
            return
        async with self._git_lock:
            sha = await asyncio.to_thread(quality.git_commit, self.workspace.root, message, paths)
        if sha:
            self.state.commits.append(f"{sha} {message}")

    async def _stage(self, stage: str) -> str:
        text = await self._call(stage)
        text = await self._check_and_repair(stage, text)
        self.state.outputs[stage] = text
        written = self.workspace.save_stage(stage, text)
        # Commit only this stage's files: concurrent stages must not swallow each other's.
        paths = [str(p.relative_to(self.workspace.root)) for p in written]
        code_dir = {"frontend_design": "frontend", "backend_design": "backend"}.get(stage)
        if code_dir and (self.workspace.root / code_dir).is_dir():
            paths.append(code_dir)
        kind = "feat" if code_dir else "docs"
        await self._commit(f"{kind}({stage}): {self.state.project_name}", paths)
        return text

    async def _check_and_repair(self, stage: str, text: str) -> str:
        diagrams = plantuml.extract(text, default_prefix=stage)
        if not diagrams:
            return text
        if not self.settings.check_diagrams or not quality.plantuml_available():
            self.state.diagram_checks[stage] = {
                "status": "skipped",
                "reason": "disabled"
                if not self.settings.check_diagrams
                else "plantuml not on PATH",
                "total": len(diagrams),
            }
            return text
        errors = await asyncio.to_thread(quality.check_diagrams, diagrams)
        record = {
            "status": "checked",
            "total": len(diagrams),
            "invalid_first": len(errors),
            "first_errors": [f"{e.name}: {e.message}" for e in errors],
            "repair_rounds": 0,
        }
        while errors and record["repair_rounds"] < self.settings.max_repair_rounds:
            record["repair_rounds"] += 1
            reply = await self._call(
                "diagram_repair",
                {"broken_diagrams": quality.describe_errors(diagrams, errors)},
            )
            text, _ = quality.replace_diagrams(text, plantuml.extract(reply))
            diagrams = plantuml.extract(text, default_prefix=stage)
            errors = await asyncio.to_thread(quality.check_diagrams, diagrams)
        record["invalid_final"] = len(errors)
        record["final_errors"] = [f"{e.name}: {e.message}" for e in errors]
        self.state.diagram_checks[stage] = record
        if record["invalid_first"]:
            print(
                f"  diagrams {stage}: {record['invalid_first']} invalid → "
                f"{record['invalid_final']} after {record['repair_rounds']} repair round(s)",
                flush=True,
            )
        return text

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
        self._settings = self._settings or Settings.from_env()
        settings = self._settings
        if s.language == DEFAULT_LANGUAGE and settings.language != DEFAULT_LANGUAGE:
            s.language = settings.language
        self.workspace = Workspace.create(settings.output_dir, s.project_name)
        self.workspace.write("requirements.md", s.project_description + "\n")
        s.run_dir = str(self.workspace.root)
        factory = self._runner_factory or (lambda ws: AgileCrew(settings, ws))
        self._runner = factory(self.workspace)
        print(f"\n=== NL2BP 多 Agent 工作流: {s.project_name} → {s.run_dir} ===\n")

    @listen(prepare)
    async def system_design(self):
        await self._commit("chore: requirements", ["requirements.md"])
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
        declared = contract.declared_types(plantuml.extract(text))
        self.state.quality["contract_types"] = declared
        self.state.outputs["contract"] = contract.checklist(declared)
        return text

    @listen(blueprint_design)
    async def frontend_design(self):
        return await self._stage("frontend_design")

    @listen(blueprint_design)
    async def backend_design(self):
        return await self._stage("backend_design")

    @listen(and_(frontend_design, backend_design))
    async def verify(self):
        root, q, settings = self.workspace.root, self.state.quality, self.settings
        declared = q.get("contract_types", [])

        def conformance():
            files = contract.code_files(root, ("frontend", "backend"))
            return contract.check_conformance(declared, files)

        conf = await asyncio.to_thread(conformance)
        q["conformance_first"] = conf.as_dict()
        if conf.missing and (conf.ratio or 0) < settings.conformance_threshold:
            await self._call(
                "conformance_fix", {"missing_types": "\n".join(f"- {n}" for n in conf.missing)}
            )
            await self._commit("fix: add blueprint types missing from the code")
            conf = await asyncio.to_thread(conformance)
        q["conformance"] = conf.as_dict()

        if settings.run_tests:
            tests = await asyncio.to_thread(quality.run_tests, root / "backend")
            q["tests_first"] = {k: v for k, v in tests.items() if k != "output"}
            if tests["status"] == "failed":
                await self._call(
                    "test_fix",
                    {"test_command": tests.get("command", ""), "test_output": tests["output"]},
                )
                await self._commit("fix: make backend tests pass")
                tests = await asyncio.to_thread(quality.run_tests, root / "backend")
            q["tests"] = tests
            if "output" in tests:
                self.workspace.write("verify/backend_tests.log", tests["output"])
        else:
            q["tests"] = {"status": "skipped", "reason": "disabled"}

        self.state.outputs["quality_signals"] = self._signals_text()
        self.state.outputs["git_log"] = await asyncio.to_thread(quality.git_log, root)
        self.workspace.write(
            "verify/quality.json",
            json.dumps(self._quality_summary(), ensure_ascii=False, indent=2),
        )
        await self._commit("chore: verification results")

    def _quality_summary(self) -> dict[str, Any]:
        q = self.state.quality
        checks = self.state.diagram_checks
        checked = [c for c in checks.values() if c.get("status") == "checked"]
        return {
            "diagrams": {
                "total": sum(c["total"] for c in checks.values()),
                "checked": sum(c["total"] for c in checked),
                "invalid_before_repair": sum(c["invalid_first"] for c in checked),
                "invalid_after_repair": sum(c["invalid_final"] for c in checked),
                "per_stage": checks,
            },
            "conformance_first": q.get("conformance_first"),
            "conformance": q.get("conformance"),
            "tests_first": q.get("tests_first"),
            "tests": {k: v for k, v in (q.get("tests") or {}).items() if k != "output"},
        }

    def _signals_text(self) -> str:
        summary = self._quality_summary()
        d, c, t = summary["diagrams"], summary["conformance"] or {}, summary["tests"] or {}
        lines = [
            f"- PlantUML 语法检查：共 {d['total']} 张图，检查 {d['checked']} 张，"
            f"修复前不合法 {d['invalid_before_repair']} 张，"
            f"修复后不合法 {d['invalid_after_repair']} 张",
            f"- 蓝图契约符合度：类图声明 {c.get('declared', 0)} 个类型，"
            f"代码中找到 {c.get('found', 0)} 个（{c.get('ratio')}），"
            f"缺失：{', '.join(c.get('missing', [])) or '无'}",
            f"- 后端测试（Docker 隔离运行）：{t.get('status', 'unknown')}"
            + (f"，原因：{t['reason']}" if t.get("reason") else "")
            + (f"，退出码 {t['exit_code']}" if "exit_code" in t else ""),
        ]
        tail = (self.state.quality.get("tests") or {}).get("output", "")
        if tail:
            lines.append("- 测试输出末尾：\n```\n" + tail[-1500:] + "\n```")
        return "\n".join(lines)

    @listen(verify)
    async def version_control(self):
        return await self._stage("version_control")

    @listen(and_(verify, sprint_planning))
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
        settings = self.settings
        usage_total: dict[str, int] = {}
        for stage_usage in s.usage.values():
            for key, value in stage_usage.items():
                if isinstance(value, int):
                    usage_total[key] = usage_total.get(key, 0) + value
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
                "token_usage_total": usage_total,
                "quality": self._quality_summary(),
                "commits": s.commits,
                "review_feedback": s.review_feedback if s.review_feedback != NO_FEEDBACK else None,
            }
        )
        print(f"\n=== 完成 / done: {s.run_dir} ===")
        return s.run_dir
