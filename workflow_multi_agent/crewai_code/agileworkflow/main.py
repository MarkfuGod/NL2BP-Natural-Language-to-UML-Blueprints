#!/usr/bin/env python
"""Command line entry points.

    nl2bp multi  --name 图书馆 --description "..."   # multi-agent CrewAI flow
    nl2bp single --name 图书馆 --description "..."   # single agent, role switching
    nl2bp render output/<run>/diagrams               # .puml -> .svg
    nl2bp plot                                       # flow graph as HTML

`crewai flow kickoff` / `uv run kickoff` still start the multi-agent flow
(interactive prompts when no arguments are given).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agileworkflow.settings import ConfigError, Settings, load_dotenv, quiet_crewai


def _ask(prompt: str) -> str:
    if not sys.stdin.isatty():
        raise SystemExit(f"missing argument ({prompt.strip(': ')}); pass it on the command line")
    return input(prompt)


def _project_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--name", help="项目名称 / project name")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--description", help="自然语言需求 / requirements in natural language")
    g.add_argument(
        "--description-file", type=Path, help="从文件读取需求 / read requirements from file"
    )
    p.add_argument("--model", help="覆盖 MODEL，例如 anthropic/claude-sonnet-5-5")
    p.add_argument("--language", help="文档输出语言，默认 中文 / output language")
    p.add_argument("--output-dir", type=Path, help="输出根目录，默认 output/")
    p.add_argument("--temperature", type=float)
    p.add_argument("-v", "--verbose", action="store_true", help="显示 CrewAI 详细日志")
    p.add_argument("--no-diagram-check", action="store_true", help="跳过 PlantUML 语法检查与修复")
    p.add_argument("--no-tests", action="store_true", help="不在 Docker 中运行生成代码的测试")
    p.add_argument("--no-git", action="store_true", help="不为运行目录建立 git 历史")


def _project_inputs(args) -> tuple[str, str]:
    name = args.name or _ask("项目名称 / project name: ")
    if args.description_file:
        desc = args.description_file.read_text(encoding="utf-8")
    else:
        desc = args.description or _ask("项目需求 / requirements: ")
    return name.strip(), desc.strip()


def _settings(args) -> Settings:
    try:
        return Settings.from_env(
            model=args.model,
            language=args.language,
            output_dir=args.output_dir,
            temperature=args.temperature,
            verbose=args.verbose or None,
            check_diagrams=False if args.no_diagram_check else None,
            run_tests=False if args.no_tests else None,
            git_history=False if args.no_git else None,
        )
    except ConfigError as exc:
        raise SystemExit(f"error: {exc}") from None


def _cmd_multi(args) -> None:
    from agileworkflow.agile_flow import AgileWorkflowFlow

    settings = _settings(args)
    name, desc = _project_inputs(args)
    sprint = args.sprint_days
    if sprint is None:
        sprint = (
            int(_ask("Sprint 周期（天，1-60）/ sprint days: ") or 14) if sys.stdin.isatty() else 14
        )
    flow = AgileWorkflowFlow(settings=settings)
    flow.kickoff(
        inputs={
            "project_name": name,
            "project_description": desc,
            "sprint_duration": str(sprint),
            "language": settings.language,
            "human_review": args.review,
        }
    )


def _cmd_single(args) -> None:
    from agileworkflow.single_agent import SingleAgentWorkflow

    settings = _settings(args)
    name, desc = _project_inputs(args)
    SingleAgentWorkflow(
        project_name=name,
        project_description=desc,
        settings=settings,
        language=settings.language,
        max_fix_rounds=args.max_fix_rounds,
    ).run()


def _cmd_render(args) -> None:
    from agileworkflow import plantuml

    files: list[Path] = []
    for target in args.paths:
        files.extend(sorted(target.rglob("*.puml")) if target.is_dir() else [target])
    if not files:
        raise SystemExit("no .puml files found")
    try:
        if args.server:
            out = plantuml.render_server(files, args.server, args.format)
        else:
            out = plantuml.render_local(files, args.format)
    except FileNotFoundError as exc:
        raise SystemExit(f"error: {exc}") from None
    for path in out:
        print(path)


def _cmd_plot(args) -> None:
    from agileworkflow.agile_flow import AgileWorkflowFlow

    AgileWorkflowFlow().plot(args.filename)
    print(f"已保存 / saved {args.filename}.html")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nl2bp", description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    multi = sub.add_parser("multi", help="多 Agent 敏捷工作流 / multi-agent flow")
    _project_args(multi)
    multi.add_argument("--sprint-days", type=int, help="Sprint 周期（天）, default 14")
    multi.add_argument(
        "--review", action="store_true", help="蓝图生成后暂停，由你评审（人类协作者）"
    )
    multi.set_defaults(func=_cmd_multi)

    single = sub.add_parser("single", help="单 Agent 多角色工作流 / single-agent workflow")
    _project_args(single)
    single.add_argument(
        "--max-fix-rounds", type=int, default=1, help="审查不通过时的修复轮数, default 1"
    )
    single.set_defaults(func=_cmd_single)

    render = sub.add_parser("render", help="把 .puml 渲染成 svg/png")
    render.add_argument("paths", nargs="+", type=Path, help=".puml 文件或目录")
    render.add_argument("--format", choices=["svg", "png"], default="svg")
    render.add_argument(
        "--server",
        help="PlantUML 服务器 URL（图源会发送到该服务器），例如 https://www.plantuml.com/plantuml",
    )
    render.set_defaults(func=_cmd_render)

    plot = sub.add_parser("plot", help="导出工作流结构图 HTML")
    plot.add_argument("--filename", default="agile_workflow_flow")
    plot.set_defaults(func=_cmd_plot)
    return parser


def cli(argv: list[str] | None = None) -> None:
    quiet_crewai()
    load_dotenv()
    args = build_parser().parse_args(argv)
    args.func(args)


def kickoff() -> None:
    """`crewai flow kickoff` / `uv run kickoff`: multi-agent flow."""
    cli(["multi", *sys.argv[1:]])


def single_agent() -> None:
    cli(["single", *sys.argv[1:]])


def render() -> None:
    cli(["render", *sys.argv[1:]])


def plot() -> None:
    cli(["plot", *sys.argv[1:]])


if __name__ == "__main__":
    cli()
