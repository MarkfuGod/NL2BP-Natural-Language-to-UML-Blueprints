import pytest

from agileworkflow.main import build_parser, cli


def test_parser_subcommands():
    p = build_parser()
    a = p.parse_args(
        ["multi", "--name", "n", "--description", "d", "--sprint-days", "7", "--review"]
    )
    assert (a.name, a.description, a.sprint_days, a.review) == ("n", "d", 7, True)
    a = p.parse_args(["single", "--name", "n", "--description", "d", "--max-fix-rounds", "2"])
    assert a.max_fix_rounds == 2 and not a.no_tests
    a = p.parse_args(["multi", "--no-tests", "--no-diagram-check", "--no-git"])
    assert a.no_tests and a.no_diagram_check and a.no_git
    a = p.parse_args(["render", "out", "--format", "png"])
    assert a.format == "png" and a.server is None


def test_missing_model_is_a_clear_error(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MODEL", raising=False)
    with pytest.raises(SystemExit, match="No model configured"):
        cli(["multi", "--name", "n", "--description", "d"])


def test_render_without_plantuml_explains(monkeypatch, tmp_path):
    (tmp_path / "a.puml").write_text("@startuml\nA->B\n@enduml\n")
    monkeypatch.setattr("shutil.which", lambda _: None)
    with pytest.raises(SystemExit, match="plantuml"):
        cli(["render", str(tmp_path)])
