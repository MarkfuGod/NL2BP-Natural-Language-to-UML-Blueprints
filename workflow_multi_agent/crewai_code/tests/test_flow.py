import asyncio
import json

from agileworkflow.agile_flow import AgileWorkflowFlow
from agileworkflow.crews.agile_crew.agile_crew import StageResult, stage_names

EXPECTED_ORDER_CONSTRAINTS = [
    ("requirement_analysis", "system_design"),
    ("requirement_analysis", "sprint_planning"),
    ("system_design", "blueprint_design"),
    ("blueprint_design", "frontend_design"),
    ("blueprint_design", "backend_design"),
    ("frontend_design", "verify"),
    ("backend_design", "verify"),
    ("sprint_planning", "system_design_summary"),
    ("frontend_design", "system_design_summary"),
    ("backend_design", "system_design_summary"),
]


class StubRunner:
    replies: dict = {}

    def __init__(self):
        self.started, self.finished, self.values = [], [], {}
        self.active, self.max_active = 0, 0

    async def run(self, stage, values):
        self.started.append(stage)
        self.values.setdefault(stage, []).append(dict(values))
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        await asyncio.sleep(0.05)
        self.active -= 1
        self.finished.append(stage)
        text = (
            self.replies.get(stage) or f"# {stage}\n\n@startuml {stage}_diagram\nA -> B\n@enduml\n"
        )
        return StageResult(stage, text, {"total_tokens": 10})


def _kickoff(settings, runner, review=False, answers=()):
    answers = list(answers)
    flow = AgileWorkflowFlow(
        settings=settings,
        runner_factory=lambda ws: runner,
        input_fn=lambda _prompt: answers.pop(0) if answers else "",
    )
    result = flow.kickoff(
        inputs={
            "project_name": "图书馆系统",
            "project_description": "学生可以借书还书，管理员管理图书。",
            "sprint_duration": "7",
            "human_review": review,
        }
    )
    return flow, result


def test_every_stage_runs_once_in_dependency_order(settings):
    runner = StubRunner()
    flow, run_dir = _kickoff(settings, runner)

    assert sorted(runner.started) == sorted(stage_names())
    assert len(runner.started) == len(set(runner.started)) == 7
    for before, after in EXPECTED_ORDER_CONSTRAINTS:
        if "verify" in (before, after):  # verify is flow code, not an LLM stage
            continue
        assert runner.finished.index(before) < runner.started.index(after), (before, after)
    assert runner.finished.index("backend_design") < runner.started.index("system_design_summary")
    assert runner.max_active >= 2, "frontend/backend should overlap"

    root = flow.workspace.root
    assert str(root) == run_dir
    for stage in stage_names():
        assert (root / "docs" / f"{stage}.md").is_file()
        assert (root / "diagrams" / f"{stage}_diagram.puml").is_file()
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["workflow"] == "multi_agent"
    assert set(manifest["stages"]) == set(stage_names())
    assert manifest["token_usage"]["system_design"] == {"total_tokens": 10}
    assert manifest["token_usage_total"]["total_tokens"] == 70
    assert manifest["quality"]["tests"]["status"] == "skipped"
    # real git history of the run directory, one commit per stage plus bookkeeping
    # input + 7 stages + verification + project status
    assert len(manifest["commits"]) == 10
    [summary] = runner.values["system_design_summary"]
    status = summary["project_status"]
    assert "PlantUML" in status and "docs(system_design)" in status
    assert (root / "docs" / "project_status.md").is_file()


def test_stages_receive_previous_outputs(settings):
    runner = StubRunner()
    _kickoff(settings, runner)
    [summary_values] = runner.values["system_design_summary"]
    for stage in ["system_design", "blueprint_design", "backend_design"]:
        assert summary_values[stage].startswith(f"# {stage}")
    assert summary_values["project_status"].startswith("# Project status")


def test_human_review_reruns_blueprint_with_feedback(settings):
    runner = StubRunner()
    flow, _ = _kickoff(settings, runner, review=True, answers=["加上部署图", ""])
    assert runner.started.count("blueprint_design") == 2
    assert runner.values["blueprint_design"][1]["review_feedback"] == "加上部署图"
    assert (flow.workspace.root / "docs" / "review_round_1.md").read_text() == "加上部署图"


def test_rejects_bad_inputs(settings):
    import pytest

    flow = AgileWorkflowFlow(settings=settings, runner_factory=lambda ws: StubRunner())
    with pytest.raises(ValueError):
        flow.kickoff(
            inputs={"project_name": "x", "project_description": "y", "sprint_duration": "0"}
        )


def test_until_blueprint_runs_only_design_stages(settings):
    settings.stop_after = "blueprint"
    runner = StubRunner()
    flow, _ = _kickoff(settings, runner)
    assert runner.started == ["requirement_analysis", "system_design", "blueprint_design"]
    manifest = json.loads((flow.workspace.root / "manifest.json").read_text())
    assert manifest["stop_after"] == "blueprint"
    assert (flow.workspace.root / "docs" / "blueprint_design.md").is_file()
