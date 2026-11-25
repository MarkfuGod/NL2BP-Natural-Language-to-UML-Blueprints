import pytest

from agileworkflow.crews.agile_crew.agile_crew import load_config, stage_inputs, stage_names
from agileworkflow.settings import ConfigError, Settings
from agileworkflow.templating import render
from agileworkflow.tools import FileWriterTool, ListFilesTool, ReadFileTool
from agileworkflow.workspace import UnsafePathError, Workspace


def test_render_single_pass_and_leaves_unknown_braces():
    out = render("a {x} b {unknown} c { not a var } {{y}}", {"x": "{y}", "y": "Y"})
    assert out == "a {y} b {unknown} c { not a var } {Y}"


def test_workspace_confines_paths(tmp_path):
    ws = Workspace.create(tmp_path, "图书 管理/系统")
    assert "/" not in ws.run_id.split("_", 1)[1]
    assert ws.write("frontend/index.html", "<h1/>").read_text() == "<h1/>"
    assert ws.resolve("/abs/ok.txt") == ws.root / "abs" / "ok.txt"  # leading slash stripped
    for bad in ["../x", "a/../../x", "", "."]:
        with pytest.raises(UnsafePathError):
            ws.resolve(bad)


def test_workspace_rejects_symlink_escape(tmp_path):
    ws = Workspace.create(tmp_path / "runs", "p")
    (ws.root / "link").symlink_to(tmp_path)
    with pytest.raises(UnsafePathError):
        ws.resolve("link/evil.txt")


def test_save_stage_writes_doc_and_diagrams(tmp_path):
    ws = Workspace.create(tmp_path, "p")
    written = ws.save_stage("blueprint_design", "x\n@startuml a_b\nA->B\n@enduml\n")
    assert sorted(p.relative_to(ws.root).as_posix() for p in written) == [
        "diagrams/a_b.puml",
        "docs/blueprint_design.md",
    ]


def test_tools_stay_inside_workspace(tmp_path):
    ws = Workspace.create(tmp_path, "p")
    writer, reader, lister = FileWriterTool(ws), ReadFileTool(ws), ListFilesTool(ws)
    assert "wrote" in writer._run("backend/app.py", "print(1)")
    assert "refused" in writer._run("../../escape.py", "x")
    assert not (tmp_path / "escape.py").exists()
    assert reader._run("backend/app.py") == "print(1)"
    assert "refused" in reader._run("../secret")
    assert "backend/app.py" in lister._run(".")


def test_config_is_consistent():
    agents, tasks = load_config()
    for key, spec in tasks.items():
        assert key.endswith("_task")
        assert spec["agent"] in agents, f"{key} uses unknown agent {spec['agent']}"
        assert spec["description"].strip() and spec["expected_output"].strip()
    used = {spec["agent"] for spec in tasks.values()}
    assert used == set(agents), f"agents never used: {set(agents) - used}"
    assert len(stage_names()) == 10
    assert len(stage_names(include_helpers=True)) == 13
    assert "blueprint_guide" in stage_inputs("blueprint_design")


def test_settings_require_model(monkeypatch):
    monkeypatch.delenv("MODEL", raising=False)
    with pytest.raises(ConfigError):
        Settings.from_env()
    monkeypatch.setenv("MODEL", "deepseek/deepseek-chat")
    monkeypatch.setenv("NL2BP_LANGUAGE", "English")
    s = Settings.from_env(temperature=0.5)
    assert (s.model, s.language, s.temperature) == ("deepseek/deepseek-chat", "English", 0.5)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test")
    llm = s.build_llm()
    assert llm.timeout == 300.0 and llm.max_retries == 2
