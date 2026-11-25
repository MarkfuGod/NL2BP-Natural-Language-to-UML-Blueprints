"""The nl2bp skill: SKILL.md metadata, script CLI, parity with the package, references."""

import importlib.util
import json
import re
import shutil
from pathlib import Path

import pytest

from agileworkflow import contract, plantuml
from agileworkflow.single_agent.roles import find_skill_dir

SKILL = find_skill_dir()
spec = importlib.util.spec_from_file_location("nl2bp_check", SKILL / "scripts" / "nl2bp_check.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)

BLUEPRINT = (Path(__file__).parent / "test_quality.py").read_text()  # contains BLUEPRINT text


def test_skill_frontmatter_follows_spec():
    text = (SKILL / "SKILL.md").read_text()
    fm = text.split("---")[1]
    name = re.search(r"^name: (.*)$", fm, re.M).group(1)
    desc = re.search(r"^description: (.*)$", fm, re.M).group(1)
    assert name == SKILL.name == "nl2bp"
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) and len(name) <= 64
    assert 0 < len(desc) <= 1024
    assert len(text.splitlines()) < 500
    for link in re.findall(r"\]\((references/[^)]+)\)", text):
        assert (SKILL / link).is_file(), link


def test_script_matches_package_on_extraction_and_contract(tmp_path):
    ours = [(d.kind, d.name) for d in plantuml.extract(BLUEPRINT)]
    theirs = [(d["kind"], d["name"]) for d in check.extract(BLUEPRINT)]
    assert ours == theirs
    assert contract.declared_types(plantuml.extract(BLUEPRINT)) == check.declared_types(BLUEPRINT)
    (tmp_path / "code").mkdir()
    (tmp_path / "code" / "m.py").write_text("class Book:\n    pass\nlending_record = 1\n")
    types = check.declared_types(BLUEPRINT)
    a = contract.check_conformance(types, contract.code_files(tmp_path, ("code",)))
    b = check.conformance(types, check.code_files([tmp_path / "code"]))
    assert (a.found, a.missing, a.ratio) == (
        types[:0] + [t for t in types if t not in b["missing"]],
        b["missing"],
        b["ratio"],
    )
    assert b["defined_as_type"] == 1  # Book is a class; lending_record is only a name


def test_cli_contract_and_conform_exit_codes(tmp_path, capsys):
    bp = tmp_path / "blueprint.md"
    bp.write_text("@startuml x_class\nclass Book\ninterface LoanService\n@enduml\n")
    assert check.main(["contract", str(bp)]) == 0
    assert json.loads(capsys.readouterr().out)["declared"] == ["Book", "LoanService"]
    (tmp_path / "code").mkdir()
    (tmp_path / "code" / "a.py").write_text("class Book: ...\n")
    assert check.main(["conform", str(bp), str(tmp_path / "code")]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["ratio"] == 0.5 and out["missing"] == ["LoanService"]
    assert check.main(["test", str(tmp_path / "code")]) == 2  # no manifest → skipped


@pytest.mark.skipif(not shutil.which("plantuml"), reason="plantuml not installed")
def test_every_reference_example_is_valid_plantuml(capsys):
    code = check.main(["validate", str(SKILL / "references")])
    out = json.loads(capsys.readouterr().out)
    assert code == 0, out["errors"]
    assert out["diagrams"] >= 20


@pytest.mark.skipif(not shutil.which("plantuml"), reason="plantuml not installed")
def test_validate_reports_line_of_error(tmp_path, capsys):
    bad = tmp_path / "bad.md"
    bad.write_text("```plantuml\n@startuml bad_seq\nA -> -> B\n@enduml\n```\n")
    assert check.main(["validate", str(bad)]) == 1
    err = json.loads(capsys.readouterr().out)["errors"][0]
    assert err["name"] == "bad_seq" and err["line"] == 1
