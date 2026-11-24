"""Quality gates: diagram repair, blueprint conformance, sandboxed tests."""

import json
import shutil

import pytest

from agileworkflow import contract, plantuml, quality
from agileworkflow.agile_flow import AgileWorkflowFlow
from tests.test_flow import StubRunner

BLUEPRINT = """# 蓝图

```plantuml
@startuml lib_class_core
class Book {
  +isbn: String
}
interface LoanService
enum LoanStatus
abstract class BaseEntity
class "借阅记录" as LendingRecord
@enduml
```

```plantuml
@startuml lib_seq_borrow
Student -> -> API
@enduml
```
"""


def test_declared_types_and_conformance(tmp_path):
    types = contract.declared_types(plantuml.extract(BLUEPRINT))
    assert types == ["Book", "LoanService", "LoanStatus", "BaseEntity", "LendingRecord"]
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "models.py").write_text(
        "class Book: ...\nclass LoanStatus: ...\nlending_record = Table('lending_record')\n"
    )
    (tmp_path / "backend" / "node_modules").mkdir()
    (tmp_path / "backend" / "node_modules" / "x.js").write_text("class LoanService {}")
    files = contract.code_files(tmp_path, ("frontend", "backend"))
    result = contract.check_conformance(types, files)
    assert result.found == ["Book", "LoanStatus", "LendingRecord"]
    assert result.missing == ["LoanService", "BaseEntity"]
    assert result.ratio == 0.6


def test_replace_diagrams_swaps_by_name():
    fixed = plantuml.extract("@startuml lib_seq_borrow\nStudent -> API\n@enduml\n")
    text, n = quality.replace_diagrams(BLUEPRINT, fixed)
    assert n == 1 and "Student -> API" in text and "-> ->" not in text
    assert "class Book" in text


@pytest.mark.skipif(not shutil.which("plantuml"), reason="plantuml not installed")
def test_real_plantuml_syntax_check():
    good, bad = plantuml.extract(BLUEPRINT)[0], plantuml.extract(BLUEPRINT)[1]
    assert quality.check_diagram(good.source) is None
    err = quality.check_diagram(bad.source)
    assert err is not None and err.line == 1


def test_git_commit_and_log(tmp_path):
    (tmp_path / "a.md").write_text("x")
    sha = quality.git_commit(tmp_path, "docs(a): first")
    assert sha and quality.git_commit(tmp_path, "nothing changed") is None
    assert "docs(a): first" in quality.git_log(tmp_path)


def test_detect_test_command(tmp_path):
    assert quality.detect_test_command(tmp_path) is None
    (tmp_path / "requirements.txt").write_text("fastapi\n")
    image, cmd = quality.detect_test_command(tmp_path)
    assert image.startswith("python") and "pytest" in cmd
    assert quality.run_tests(tmp_path / "missing")["status"] == "skipped"


def _flow_with_gates(settings, monkeypatch, *, test_results):
    """Flow whose external checks are simulated: first diagram check fails once."""
    settings.check_diagrams = True
    settings.run_tests = True
    calls = {"check": 0}

    def fake_check(diagrams):
        calls["check"] += 1
        return [
            quality.DiagramError(d.name, 1, "Syntax Error?")
            for d in diagrams
            if "-> ->" in d.source
        ]

    results = list(test_results)
    monkeypatch.setattr(quality, "plantuml_available", lambda: True)
    monkeypatch.setattr(quality, "check_diagrams", fake_check)
    monkeypatch.setattr(quality, "run_tests", lambda project: results.pop(0))

    runner = StubRunner()
    runner.replies = {
        "blueprint_design": BLUEPRINT,
        "diagram_repair": "```plantuml\n@startuml lib_seq_borrow\nStudent -> API\n@enduml\n```",
    }

    def write_code(ws):
        (ws.root / "backend").mkdir(parents=True, exist_ok=True)
        (ws.root / "backend" / "models.py").write_text("class Book: ...\n")
        return runner

    flow = AgileWorkflowFlow(settings=settings, runner_factory=write_code)
    flow.kickoff(
        inputs={"project_name": "lib", "project_description": "借书", "sprint_duration": "7"}
    )
    return flow, runner


def test_quality_gates_repair_and_fix(settings, monkeypatch):
    failed = {"status": "failed", "exit_code": 1, "command": "pytest", "output": "E assert 1 == 2"}
    passed = {"status": "passed", "exit_code": 0, "command": "pytest", "output": "1 passed"}
    flow, runner = _flow_with_gates(settings, monkeypatch, test_results=[failed, passed])

    assert runner.started.count("diagram_repair") == 1
    blueprint = (flow.workspace.root / "docs" / "blueprint_design.md").read_text()
    assert "-> ->" not in blueprint and "Student -> API" in blueprint
    assert (flow.workspace.root / "diagrams" / "lib_seq_borrow.puml").read_text().count("->") == 1

    # code stages got the contract checklist
    [backend_values] = runner.values["backend_design"]
    assert "- LoanService" in backend_values["contract"]

    # conformance 1/5 < 0.9 → one fix round; tests failed → one fix round
    assert runner.started.count("conformance_fix") == 1
    [fix_values] = runner.values["conformance_fix"]
    assert "- LoanService" in fix_values["missing_types"]
    assert runner.started.count("test_fix") == 1
    assert "assert 1 == 2" in runner.values["test_fix"][0]["test_output"]

    manifest = json.loads((flow.workspace.root / "manifest.json").read_text())
    q = manifest["quality"]
    assert q["diagrams"]["invalid_before_repair"] == 1
    assert q["diagrams"]["invalid_after_repair"] == 0
    assert q["tests_first"]["status"] == "failed" and q["tests"]["status"] == "passed"
    assert q["conformance"]["declared"] == 5
    [dash] = runner.values["agile_dashboard"]
    assert "后端测试（Docker 隔离运行）：passed" in dash["quality_signals"]


def test_no_fix_rounds_when_checks_pass(settings, monkeypatch):
    passed = {"status": "passed", "exit_code": 0, "command": "pytest", "output": "ok"}
    flow, runner = _flow_with_gates(settings, monkeypatch, test_results=[passed])
    assert "test_fix" not in runner.started
