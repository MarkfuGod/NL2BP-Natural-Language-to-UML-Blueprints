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

from agileworkflow.crews.agile_crew.agile_crew import StageResult
from agileworkflow.settings import DEFAULT_LANGUAGE, Settings
from agileworkflow.single_agent.roles import ROLES, find_role_prompts_dir, load_role_prompt
from agileworkflow.workspace import Workspace

PREAMBLE = """你是“单代理多角色”开发工作流中的同一个 AI 代理，现在切换到角色：{title}。

下面是该角色的规则。它们原本写给 Roo Code 的自定义模式：角色切换由工作流替你完成，
忽略规则中提到的 switch_mode、ask_followup_question、attempt_completion、execute_command、
apply_diff、browser_action 等工具。本环境可用的工具只有：{tools}。
信息不足时不要提问，在文档中写出“假设”一节说明你的假设后继续。

===== 角色规则开始 =====
{prompt}
===== 角色规则结束 =====
"""

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

    def _describe(self, task: RoleTask) -> str:
        role = ROLES[task.role]
        head = PREAMBLE.format(
            title=role.title,
            tools=", ".join(role.tools) or "无 / none",
            prompt=load_role_prompt(role.slug, self.prompts_dir),
        )
        return (
            f"{head}\n项目名称：{self.project_name}\n\n{task.body}\n\n输出语言：{self.language}。"
        )

    def _do(self, task: RoleTask) -> str:
        print(f"▶ [{task.role}] {task.stage} …", flush=True)
        result = self.runner.run(task, self._describe(task))
        self.outputs[task.stage] = result.text
        if result.usage:
            self.usage[task.stage] = result.usage
        self.workspace.save_stage(task.stage, result.text)
        self.log.append(f"{task.role}:{task.stage}")
        print(f"✔ [{task.role}] {task.stage}", flush=True)
        return result.text

    def run(self) -> Path:
        if not self.project_name.strip() or not self.project_description.strip():
            raise ValueError("project_name and project_description are required")
        self.prompts_dir = self.prompts_dir or find_role_prompts_dir()
        self.workspace = Workspace.create(self.settings.output_dir, self.project_name)
        factory = self.runner_factory or (lambda ws, st: CrewRoleRunner(ws, st))
        self.runner = factory(self.workspace, self.settings)
        print(f"\n=== NL2BP 单 Agent 工作流: {self.project_name} → {self.workspace.root} ===\n")

        o = self.outputs
        self._do(
            RoleTask(
                "01_requirements",
                "01-req-gen",
                f"用户的自然语言需求：\n{self.project_description}\n\n输出结构化的需求文档（Markdown）作为最终答案。",
                "Markdown 需求文档",
            )
        )
        self._do(
            RoleTask(
                "02_system_design",
                "systemdesign",
                f"需求文档：\n{o['01_requirements']}\n\n输出架构设计文档（Markdown）作为最终答案，本角色不画图。",
                "Markdown 架构设计文档",
            )
        )
        self._do(
            RoleTask(
                "03_blueprint",
                "blueprintdesign",
                f"需求文档：\n{o['01_requirements']}\n\n架构设计文档：\n{o['02_system_design']}\n\n"
                "按项目阶段生成 PlantUML 图。每张图放在 ```plantuml 代码块中，首行写 "
                "@startuml <project>_<diagram_type>_<module>，并在图后写简短说明。"
                "以包含全部图的 Markdown 文档作为最终答案。",
                "含 PlantUML 代码块的 Markdown 蓝图文档",
            )
        )
        self._do(
            RoleTask(
                "04_code",
                "coder",
                f"PlantUML 蓝图：\n{o['03_blueprint']}\n\n需求文档：\n{o['01_requirements']}\n\n"
                "严格按蓝图实现可运行代码：用 write_file 逐个写入完整文件，路径以 code/ 开头。"
                "最终答案是实现说明：已写入的文件列表、运行方式。",
                "code/ 下的完整代码文件与实现说明",
            )
        )

        verdict, round_no = "CHANGES_REQUESTED", 0
        while True:
            review_stage = f"05_review_{round_no}"
            review = self._do(
                RoleTask(
                    review_stage,
                    "code-reviewer",
                    f"PlantUML 蓝图：\n{o['03_blueprint']}\n\n"
                    f"需求文档：\n{o['01_requirements']}\n\n"
                    f"编码说明：\n{o[self._last('04_code')]}\n\n"
                    "用 list_files / read_file 检查 code/ 下的代码，对照蓝图审查。"
                    "最终答案是审查报告，最后一行必须是 "
                    "`VERDICT: APPROVED` 或 `VERDICT: CHANGES_REQUESTED`。",
                    "审查报告，以 VERDICT 行结尾",
                )
            )
            verdict = review_verdict(review)
            if verdict == "APPROVED" or round_no >= self.max_fix_rounds:
                break
            round_no += 1
            self._do(
                RoleTask(
                    f"06_diagnosis_{round_no}",
                    "code-critic",
                    f"审查报告：\n{review}\n\nPlantUML 蓝图：\n{o['03_blueprint']}\n\n"
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

        self._do(
            RoleTask(
                "07_deploy",
                "debugger-deployer",
                f"架构设计文档：\n{o['02_system_design']}\n\n最终审查结论：{verdict}\n\n"
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
                "fix_rounds": round_no,
                "token_usage": self.usage,
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
        self.llm = settings.build_llm()

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
            llm=self.llm,
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
