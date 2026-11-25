"""Single-agent, multi-role workflow.

One agent persona switches through the roles in order, each role seeing only the
documents the previous roles left behind (the "memory reset" rule in the prompts):

    01-req-gen → systemdesign → blueprintdesign → coder → code-reviewer
        ↺ (CHANGES_REQUESTED) code-critic → coder → code-reviewer   (≤ max_fix_rounds)
    → debugger-deployer
"""

from __future__ import annotations

import datetime as _dt
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from agileworkflow import contract, plantuml, quality
from agileworkflow.crews.agile_crew.agile_crew import StageResult
from agileworkflow.settings import DEFAULT_LANGUAGE, Settings
from agileworkflow.single_agent.roles import (
    ROLES,
    find_role_prompts_dir,
    load_reference,
    load_role_prompt,
)
from agileworkflow.workspace import Workspace

PREAMBLE = """Current role: {title}.

How this run works: the workflow switches roles for you and runs every check command
(`nl2bp_check.py validate / contract / conform / test`) itself; you cannot run commands,
and measured results are given to you where a role needs them. Tools available to you:
{tools}. `<skill>` files the rules mention are included below when this role needs them.
You cannot ask the user questions: record assumptions in an "Assumptions" section.
Return the document itself as your final answer (the workflow saves it).

===== ROLE RULES =====
{prompt}
===== END ROLE RULES ====={references}
"""

# Skill references each diagram-producing role gets inline.
ROLE_REFERENCES = {
    "01-req-gen": ("diagram-selection.md", "plantuml-syntax.md"),
    "systemdesign": ("diagram-selection.md", "plantuml-syntax.md"),
    "blueprintdesign": ("diagram-selection.md", "output-contract.md", "plantuml-syntax.md"),
}

VERDICT_RE = re.compile(r"VERDICT:\s*(APPROVED|CHANGES_REQUESTED)", re.IGNORECASE)


@dataclass
class RoleTask:
    stage: str
    role: str
    body: str
    expected_output: str


class RoleRunner(Protocol):
    def run(self, task: RoleTask, description: str) -> StageResult: ...


def review_verdict(text: str) -> str:
    """Last VERDICT line wins; missing verdict counts as CHANGES_REQUESTED."""
    found = VERDICT_RE.findall(text)
    return found[-1].upper() if found else "CHANGES_REQUESTED"


@dataclass
class SingleAgentWorkflow:
    project_name: str
    project_description: str
    settings: Settings
    language: str = DEFAULT_LANGUAGE
    max_fix_rounds: int = 1
    runner_factory: Callable[[Workspace, Settings], RoleRunner] | None = None
    prompts_dir: Path | None = None
    outputs: dict[str, str] = field(default_factory=dict)
    usage: dict[str, dict[str, Any]] = field(default_factory=dict)
    log: list[str] = field(default_factory=list)
    quality: dict[str, Any] = field(default_factory=dict)
    contract_types: list[str] = field(default_factory=list)

    def _describe(self, task: RoleTask) -> str:
        role = ROLES[task.role]
        refs = "".join(
            f"\n\n===== <skill>/references/{name} =====\n{load_reference(name)}"
            for name in ROLE_REFERENCES.get(role.slug, ())
        )
        head = PREAMBLE.format(
            title=role.title,
            tools=", ".join(role.tools) or "none",
            prompt=load_role_prompt(role.slug, self.prompts_dir),
            references=refs,
        )
        return (
            f"{head}\n项目名称：{self.project_name}\n\n{task.body}\n\n输出语言：{self.language}。"
        )

    stage_roles = {
        "01_requirements": "01-req-gen",
        "02_system_design": "systemdesign",
        "03_blueprint": "blueprintdesign",
    }

    def _do(self, task: RoleTask, save: bool = True) -> str:
        print(f"▶ [{task.role}] {task.stage} …", flush=True)
        result = self.runner.run(task, self._describe(task))
        self.outputs[task.stage] = result.text
        if result.usage:
            self.usage[task.stage] = result.usage
        if save:
            self.workspace.save_stage(task.stage, result.text)
        self.log.append(f"{task.role}:{task.stage}")
        print(f"✔ [{task.role}] {task.stage}", flush=True)
        return result.text

    # -- quality gates (shared with the multi-agent flow) -------------------------

    def _repair_diagrams(self, stage: str) -> None:
        text = self.outputs[stage]
        diagrams = plantuml.extract(text, default_prefix=stage)
        if not diagrams:
            return
        if not self.settings.check_diagrams or not quality.plantuml_available():
            self.quality.setdefault("diagrams", {})[stage] = {
                "status": "skipped",
                "reason": "disabled"
                if not self.settings.check_diagrams
                else "plantuml not on PATH",
                "total": len(diagrams),
            }
            return
        errors = quality.check_diagrams(diagrams)
        record = {
            "status": "checked",
            "total": len(diagrams),
            "invalid_first": len(errors),
            "repair_rounds": 0,
        }
        while errors and record["repair_rounds"] < self.settings.max_repair_rounds:
            record["repair_rounds"] += 1
            reply = self._do(
                RoleTask(
                    f"{stage}_repair_{record['repair_rounds']}",
                    self.stage_roles.get(stage, "blueprintdesign"),
                    "下面的 PlantUML 图无法通过语法检查（行号从 0 开始）：\n\n"
                    f"{quality.describe_errors(diagrams, errors)}\n\n"
                    "只修语法错误，保持图名与命名不变。最终答案只包含修复后的图，"
                    "每张一个 ```plantuml 代码块，首行保留原来的 @startXXX <图名>。",
                    "修复后的 PlantUML 代码块",
                ),
                save=False,
            )
            text, _ = quality.replace_diagrams(text, plantuml.extract(reply))
            diagrams = plantuml.extract(text, default_prefix=stage)
            errors = quality.check_diagrams(diagrams)
        record["invalid_final"] = len(errors)
        record["final_errors"] = [f"{e.name}: {e.message}" for e in errors]
        self.quality.setdefault("diagrams", {})[stage] = record
        self.outputs[stage] = text
        self.workspace.save_stage(stage, text)

    def _measure_code(self) -> str:
        """Conformance + sandboxed tests for code/; returns the signal text for the reviewer."""
        files = contract.code_files(self.workspace.root, ("code",))
        conf = contract.check_conformance(self.contract_types, files)
        self.quality.setdefault("conformance_first", conf.as_dict())
        self.quality["conformance"] = conf.as_dict()
        if self.settings.run_tests:
            tests = quality.run_tests(self.workspace.root / "code")
        else:
            tests = {"status": "skipped", "reason": "disabled"}
        self.quality.setdefault("tests_first", {k: v for k, v in tests.items() if k != "output"})
        self.quality["tests"] = {k: v for k, v in tests.items() if k != "output"}
        if tests.get("output"):
            self.workspace.write("verify/code_tests.log", tests["output"])
        lines = [
            f"- 蓝图契约符合度：声明 {len(conf.declared)} 个类型，代码中找到 {len(conf.found)} 个"
            f"（{conf.ratio}），缺失：{', '.join(conf.missing) or '无'}",
            f"- 测试（Docker 隔离运行）：{tests['status']}"
            + (f"，原因：{tests['reason']}" if tests.get("reason") else ""),
        ]
        if tests.get("output"):
            lines.append("- 测试输出末尾：\n```\n" + tests["output"][-1500:] + "\n```")
        return "\n".join(lines)

    def _gate_failed(self) -> list[str]:
        """Measured problems that override an APPROVED verdict."""
        reasons = []
        ratio = self.quality.get("conformance", {}).get("ratio")
        if ratio is not None and ratio < self.settings.conformance_threshold:
            reasons.append(f"conformance {ratio} < {self.settings.conformance_threshold}")
        if self.quality.get("tests", {}).get("status") == "failed":
            reasons.append("tests failed")
        return reasons

    # -- workflow --------------------------------------------------------------

    def run(self) -> Path:
        if not self.project_name.strip() or not self.project_description.strip():
            raise ValueError("project_name and project_description are required")
        self.prompts_dir = self.prompts_dir or find_role_prompts_dir()
        self.workspace = Workspace.create(self.settings.output_dir, self.project_name)
        self.workspace.write("input.md", self.project_description + "\n")
        factory = self.runner_factory or (lambda ws, st: CrewRoleRunner(ws, st))
        self.runner = factory(self.workspace, self.settings)
        print(f"\n=== NL2BP 单 Agent 工作流: {self.project_name} → {self.workspace.root} ===\n")

        o = self.outputs
        self._do(
            RoleTask(
                "01_requirements",
                "01-req-gen",
                f"User request:\n{self.project_description}\n\n"
                "Write requirements.md as the role rules describe.",
                "requirements.md: user stories, business rules, use case and activity diagrams",
            )
        )
        self._do(
            RoleTask(
                "02_system_design",
                "systemdesign",
                f"requirements.md:\n{o['01_requirements']}\n\n"
                "Write architecture.md as the role rules describe.",
                "architecture.md: stack, ADRs, C4 context and container diagrams",
            )
        )
        self._do(
            RoleTask(
                "03_blueprint",
                "blueprintdesign",
                f"requirements.md:\n{o['01_requirements']}\n\n"
                f"architecture.md:\n{o['02_system_design']}\n\n"
                "Write blueprint.md following references/output-contract.md exactly.",
                "blueprint.md: class contract, sequence, ER and state diagrams, interfaces",
            )
        )
        for stage in ("01_requirements", "02_system_design", "03_blueprint"):
            self._repair_diagrams(stage)
        self.contract_types = contract.declared_types(plantuml.extract(o["03_blueprint"]))
        self._do(
            RoleTask(
                "04_code",
                "coder",
                f"PlantUML 蓝图：\n{o['03_blueprint']}\n\n需求文档：\n{o['01_requirements']}\n\n"
                f"蓝图类图声明的类型（契约清单，必须用同名类型实现）：\n"
                f"{contract.checklist(self.contract_types)}\n\n"
                "严格按蓝图实现可运行代码：用 write_file 逐个写入完整文件，路径以 code/ 开头。"
                "优先 Python（FastAPI + SQLite）或 Node.js；依赖清单放在 code/requirements.txt 或 "
                "code/package.json；测试放在 code/tests/（在 code/ 目录下用 `python -m pytest` 或 "
                "`npm test` 可直接运行），覆盖核心业务规则，不依赖外部服务。"
                "最终答案是实现说明：已写入的文件列表、运行方式。",
                "code/ 下的完整代码文件与实现说明",
            )
        )

        verdict, round_no, overridden = "CHANGES_REQUESTED", 0, []
        while True:
            signals = self._measure_code()
            review = self._do(
                RoleTask(
                    f"05_review_{round_no}",
                    "code-reviewer",
                    f"PlantUML 蓝图：\n{o['03_blueprint']}\n\n"
                    f"需求文档：\n{o['01_requirements']}\n\n"
                    f"编码说明：\n{o[self._last('04_code')]}\n\n"
                    f"工作流实测信号（真实测量，结论不得与之矛盾）：\n{signals}\n\n"
                    "用 list_files / read_file 检查 code/ 下的代码，对照蓝图审查。"
                    "最终答案是审查报告，最后一行必须是 "
                    "`VERDICT: APPROVED` 或 `VERDICT: CHANGES_REQUESTED`。",
                    "审查报告，以 VERDICT 行结尾",
                )
            )
            verdict = review_verdict(review)
            overridden = self._gate_failed() if verdict == "APPROVED" else []
            if overridden:
                verdict = "CHANGES_REQUESTED"
                review += "\n\n[工作流] 实测未通过，审查结论改为 CHANGES_REQUESTED：" + "; ".join(
                    overridden
                )
            if verdict == "APPROVED" or round_no >= self.max_fix_rounds:
                break
            round_no += 1
            self._do(
                RoleTask(
                    f"06_diagnosis_{round_no}",
                    "code-critic",
                    f"审查报告：\n{review}\n\n实测信号：\n{signals}\n\n"
                    f"PlantUML 蓝图：\n{o['03_blueprint']}\n\n"
                    "用 read_file 定位问题，输出诊断表与给编码工程师的最小修复计划作为最终答案。",
                    "诊断与修复计划",
                )
            )
            self._do(
                RoleTask(
                    f"04_code_fix_{round_no}",
                    "coder",
                    f"修复计划：\n{o[f'06_diagnosis_{round_no}']}\n\n"
                    f"PlantUML 蓝图：\n{o['03_blueprint']}\n\n"
                    "只按修复计划修改 code/ 下的文件"
                    "（用 read_file 读取，用 write_file 写回完整文件）。"
                    "最终答案是修改说明。",
                    "修改后的代码文件与修改说明",
                )
            )
        final_signals = signals if round_no == 0 or verdict == "APPROVED" else self._measure_code()

        self._do(
            RoleTask(
                "07_deploy",
                "debugger-deployer",
                f"架构设计文档：\n{o['02_system_design']}\n\n最终审查结论：{verdict}\n\n"
                f"实测信号：\n{final_signals}\n\n"
                "本环境不能执行命令：用 read_file 做静态检查（依赖、入口、配置、导入路径），"
                "用 write_file 写入部署文件（如 code/Dockerfile、code/DEPLOY.md）。"
                "最终答案是部署与调试报告：检查结果、发现的问题、用户本地验证的命令。",
                "部署与调试报告",
            )
        )

        self.workspace.write_manifest(
            {
                "workflow": "single_agent",
                "run_id": self.workspace.run_id,
                "project_name": self.project_name,
                "project_description": self.project_description,
                "language": self.language,
                "model": self.settings.model,
                "role_sequence": self.log,
                "final_review_verdict": verdict,
                "verdict_overridden_by": overridden,
                "fix_rounds": round_no,
                "quality": self.quality,
                "token_usage": self.usage,
                "usage_is_per_stage": True,
                "finished_at": _dt.datetime.now().isoformat(timespec="seconds"),
            }
        )
        print(f"\n=== 完成 / done: {self.workspace.root} (review: {verdict}) ===")
        return self.workspace.root

    def _last(self, prefix: str) -> str:
        """Most recent coder output (initial code or latest fix)."""
        fixes = sorted(k for k in self.outputs if k.startswith("04_code_fix_"))
        return fixes[-1] if fixes else prefix


class CrewRoleRunner:
    """One persistent persona; each role runs as its own one-task crew."""

    def __init__(self, workspace: Workspace, settings: Settings):
        self.workspace = workspace
        self.settings = settings

    def _tools(self, names: tuple[str, ...]):
        from agileworkflow.tools import FileWriterTool, ListFilesTool, ReadFileTool

        table = {
            "write_file": FileWriterTool,
            "read_file": ReadFileTool,
            "list_files": ListFilesTool,
        }
        return [table[n](self.workspace) for n in names]

    def run(self, task: RoleTask, description: str) -> StageResult:
        from crewai import Agent, Crew, Process, Task

        role = ROLES[task.role]
        agent = Agent(
            role="单代理多角色软件工程师 / single agent, multiple roles",
            goal="按当前角色的规则，把自然语言需求一步步变成 UML 蓝图和可运行代码",
            backstory="你依次扮演需求分析、架构、蓝图、编码、审查、诊断、部署等角色；"
            "每次切换角色后只依据上一个角色留下的文档工作。",
            llm=self.settings.build_llm(),  # fresh per role: usage is accumulated per LLM object
            tools=self._tools(role.tools),
            allow_delegation=False,
            verbose=self.settings.verbose,
            max_iter=40 if "write_file" in role.tools else 15,
        )
        crew_task = Task(
            name=task.stage,
            description=description,
            expected_output=task.expected_output,
            agent=agent,
        )
        crew = Crew(
            agents=[agent],
            tasks=[crew_task],
            process=Process.sequential,
            verbose=self.settings.verbose,
        )
        output = crew.kickoff()
        usage = getattr(output, "token_usage", None)
        return StageResult(
            task.stage, output.raw or "", usage.model_dump() if hasattr(usage, "model_dump") else {}
        )
