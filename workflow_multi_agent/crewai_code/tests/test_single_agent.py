import json

from agileworkflow.crews.agile_crew.agile_crew import StageResult
from agileworkflow.single_agent.roles import ROLES, find_role_prompts_dir, load_role_prompt
from agileworkflow.single_agent.runner import SingleAgentWorkflow, review_verdict


def test_every_role_has_a_prompt_folder():
    prompts = find_role_prompts_dir()
    for slug in ROLES:
        assert load_role_prompt(slug, prompts).strip(), slug
    assert "02-formatting" not in load_role_prompt("coder", prompts)
    assert "@startuml" in load_role_prompt("blueprintdesign", prompts)


def test_review_verdict_parsing():
    assert review_verdict("ok\nVERDICT: APPROVED") == "APPROVED"
    assert (
        review_verdict("VERDICT: approved\n...\nVERDICT: CHANGES_REQUESTED") == "CHANGES_REQUESTED"
    )
    assert review_verdict("no verdict") == "CHANGES_REQUESTED"


class ScriptedRoles:
    def __init__(self, verdicts, workspace=None, write_code=True):
        self.verdicts = list(verdicts)
        self.calls = []
        self.workspace = workspace
        self.write_code = write_code

    def run(self, task, description):
        self.calls.append((task.role, task.stage, description))
        text = f"# {task.stage}"
        if task.role == "blueprintdesign":
            text += "\n@startuml demo_class_x\nclass X\n@enduml\n"
        if task.role == "coder" and self.write_code:
            self.workspace.write("code/models.py", "class X:\n    pass\n")
        if task.role == "code-reviewer":
            text += f"\nVERDICT: {self.verdicts.pop(0)}"
        return StageResult(task.stage, text)


def _run(settings, verdicts, rounds=1, write_code=True):
    roles = ScriptedRoles(verdicts, write_code=write_code)

    def factory(ws, st):
        roles.workspace = ws
        return roles

    wf = SingleAgentWorkflow(
        project_name="demo",
        project_description="一个待办清单应用",
        settings=settings,
        max_fix_rounds=rounds,
        runner_factory=factory,
    )
    root = wf.run()
    return wf, roles, root


def test_linear_path_when_review_approves(settings):
    wf, roles, root = _run(settings, ["APPROVED"])
    assert [c[0] for c in roles.calls] == [
        "01-req-gen",
        "systemdesign",
        "blueprintdesign",
        "coder",
        "code-reviewer",
        "debugger-deployer",
    ]
    desc = roles.calls[2][2]
    assert "Blueprint Writer Role" in desc and "01_requirements" in desc
    assert (root / "diagrams" / "demo_class_x.puml").is_file()
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["final_review_verdict"] == "APPROVED" and manifest["fix_rounds"] == 0


def test_fix_loop_runs_critic_then_coder_then_review(settings):
    wf, roles, root = _run(settings, ["CHANGES_REQUESTED", "APPROVED"])
    assert [c[1] for c in roles.calls] == [
        "01_requirements",
        "02_system_design",
        "03_blueprint",
        "04_code",
        "05_review_0",
        "06_diagnosis_1",
        "04_code_fix_1",
        "05_review_1",
        "07_deploy",
    ]
    # second review sees the fix notes, not the original coder output
    assert "# 04_code_fix_1" in roles.calls[7][2]


def test_fix_loop_is_bounded(settings):
    wf, roles, root = _run(settings, ["CHANGES_REQUESTED", "CHANGES_REQUESTED"], rounds=1)
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["final_review_verdict"] == "CHANGES_REQUESTED"
    assert manifest["fix_rounds"] == 1
    assert roles.calls[-1][0] == "debugger-deployer"


def test_measured_failure_overrides_approved(settings):
    # coder writes nothing, so class X from the blueprint is missing: conformance 0 < 0.9
    wf, roles, root = _run(settings, ["APPROVED", "APPROVED"], rounds=1, write_code=False)
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["verdict_overridden_by"] == ["conformance 0.0 < 0.9"]
    assert manifest["final_review_verdict"] == "CHANGES_REQUESTED"
    assert manifest["quality"]["conformance"]["missing"] == ["X"]
    assert [c[1] for c in roles.calls].count("06_diagnosis_1") == 1
    assert "实测信号" in roles.calls[4][2]
