"""Real signals the agents could not produce by themselves.

- PlantUML syntax check (``plantuml -syntax``) for every extracted diagram
- generated backend tests, executed inside a throwaway Docker container
- a real git history of the run directory

Every check degrades to ``{"status": "skipped", "reason": ...}`` when its tool
is missing, and the reason is recorded instead of being guessed.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from agileworkflow import plantuml

# --- PlantUML -------------------------------------------------------------------


@dataclass(frozen=True)
class DiagramError:
    name: str
    line: int | None
    message: str


def plantuml_available() -> bool:
    return shutil.which("plantuml") is not None


def check_diagram(source: str, timeout: int = 60) -> DiagramError | None:
    """None if PlantUML parses the source, else the first error it reports."""
    proc = subprocess.run(
        ["plantuml", "-syntax"],
        input=source,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    if lines and lines[0] == "ERROR":
        line = int(lines[1]) if len(lines) > 1 and lines[1].isdigit() else None
        message = " ".join(lines[2:]) or "syntax error"
        return DiagramError("", line, message)
    return None


def check_diagrams(diagrams: list[plantuml.Diagram]) -> list[DiagramError]:
    errors = []
    for d in diagrams:
        err = check_diagram(d.source)
        if err:
            errors.append(DiagramError(d.name, err.line, err.message))
    return errors


def describe_errors(diagrams: list[plantuml.Diagram], errors: list[DiagramError]) -> str:
    by_name = {d.name: d for d in diagrams}
    parts = []
    for e in errors:
        src = by_name[e.name].source
        numbered = "\n".join(f"{i:3d}| {ln}" for i, ln in enumerate(src.splitlines()))
        where = f"第 {e.line} 行" if e.line is not None else "位置未知"
        parts.append(f"### {e.name}\nPlantUML 报错（{where}）：{e.message}\n\n```\n{numbered}\n```")
    return "\n\n".join(parts)


def replace_diagrams(text: str, fixed: list[plantuml.Diagram]) -> tuple[str, int]:
    """Swap each block in ``text`` whose name matches a fixed diagram. Returns (text, count)."""
    by_name = {d.name: d.source.strip() for d in fixed}
    count = 0
    out = text
    for original in plantuml.extract(text):
        if original.name in by_name:
            out = out.replace(original.source.strip(), by_name[original.name], 1)
            count += 1
    return out, count


# --- Docker test run ----------------------------------------------------------------

PY_IMAGE = "python:3.12-slim"
NODE_IMAGE = "node:22-slim"


def docker_available() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=20).returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def detect_test_command(project: Path) -> tuple[str, str] | None:
    """(image, shell command) for a generated project, or None if it has no tests."""
    if (project / "requirements.txt").is_file() or (project / "pyproject.toml").is_file():
        install = (
            "pip install -q -r requirements.txt"
            if (project / "requirements.txt").is_file()
            else "pip install -q ."
        )
        quiet = "PIP_ROOT_USER_ACTION=ignore PIP_DISABLE_PIP_VERSION_CHECK=1"
        return (
            PY_IMAGE,
            # no -q: a project's own `addopts = -q` would make it -qq and drop the summary line
            f"export {quiet}; {install} && pip install -q pytest httpx"
            " && python -m pytest -p no:cacheprovider",
        )
    if (project / "package.json").is_file():
        return NODE_IMAGE, "npm install --silent --no-audit --no-fund && npm test"
    return None


def run_tests(project: Path, timeout: int = 600) -> dict:
    """Run the project's tests in a container on a copy of the code.

    The container sees only a temporary copy (nothing on the host is writable),
    has memory/CPU/process limits, and is removed afterwards. It has network
    access so it can install the project's dependencies.
    """
    if not project.is_dir():
        return {"status": "skipped", "reason": f"{project.name}/ was not generated"}
    detected = detect_test_command(project)
    if not detected:
        return {
            "status": "skipped",
            "reason": "no requirements.txt / pyproject.toml / package.json",
        }
    if not docker_available():
        return {"status": "skipped", "reason": "docker daemon not available"}
    image, command = detected
    with tempfile.TemporaryDirectory(prefix="nl2bp-test-") as tmp:
        work = Path(tmp) / "app"
        shutil.copytree(project, work, ignore=shutil.ignore_patterns("node_modules", ".venv"))
        cmd = [
            "docker", "run", "--rm", "--memory=1g", "--cpus=2", "--pids-limit=256",
            "--security-opt=no-new-privileges", "-v", f"{work}:/app", "-w", "/app",
            image, "sh", "-c", command,
        ]  # fmt: skip
        try:
            # stderr merged into stdout so the tail we keep is the test runner's verdict
            proc = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            return {"status": "failed", "reason": f"timed out after {timeout}s", "output": ""}
    output = (proc.stdout or "")[-6000:]
    return {
        "status": "passed" if proc.returncode == 0 else "failed",
        "exit_code": proc.returncode,
        "image": image,
        "command": command,
        "output": output,
    }


# --- git --------------------------------------------------------------------------

_GIT_ID = [
    "-c",
    "user.name=nl2bp",
    "-c",
    "user.email=nl2bp@localhost",
    "-c",
    "commit.gpgsign=false",
]


def git_available() -> bool:
    return shutil.which("git") is not None


def git_commit(root: Path, message: str, paths: list[str] | None = None) -> str | None:
    """Commit (part of) the run directory; returns the short hash or None if nothing changed."""
    if not git_available():
        return None
    if not (root / ".git").exists():
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
    subprocess.run(["git", "add", "--", *(paths or ["."])], cwd=root, check=True)
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=root)
    if staged.returncode == 0:
        return None
    subprocess.run(["git", *_GIT_ID, "commit", "-q", "-m", message], cwd=root, check=True)
    out = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True
    )
    return out.stdout.strip()


def git_log(root: Path) -> str:
    if not (root / ".git").exists():
        return "（没有 git 历史）"
    out = subprocess.run(
        ["git", "log", "--stat", "--format=%h %s", "--no-color"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    return out.stdout.strip()[-8000:] or "（没有提交）"
