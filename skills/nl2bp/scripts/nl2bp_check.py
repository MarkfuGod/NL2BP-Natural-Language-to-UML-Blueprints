#!/usr/bin/env python3
"""Deterministic checks for the nl2bp skill. Standard library only.

    nl2bp_check.py validate  <file.md|file.puml|dir> ...   PlantUML syntax check, every diagram
    nl2bp_check.py extract   <blueprint.md> <out_dir>      write each diagram to <name>.puml
    nl2bp_check.py contract  <blueprint.md>                types declared in the class diagrams
    nl2bp_check.py conform   <blueprint.md> <code_dir>...  share of declared types defined in code
    nl2bp_check.py render    <file.puml|dir> ... [--format svg|png]
    nl2bp_check.py test      <project_dir> [--no-docker]   run the project's tests (Docker sandbox)

Exit code 0 means the check passed, 1 means it failed, 2 means a tool is missing.
Output is JSON on stdout so an agent can read it back.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# --- diagrams --------------------------------------------------------------------

BLOCK = re.compile(
    r"^[ \t]*@start(?P<kind>[a-z]+)(?P<name>[^\n]*)\n(?P<body>.*?)^[ \t]*@end(?P=kind)\b[^\n]*",
    re.MULTILINE | re.DOTALL,
)


def clean_name(raw: str) -> str:
    raw = raw.strip().strip('"').strip("'")
    return re.sub(r"[^\w\-]+", "_", raw, flags=re.UNICODE).strip("_")[:80]


def extract(text: str, prefix: str = "diagram") -> list[dict]:
    """Every @startX … @endX block with a unique, file-safe name."""
    out, seen = [], {}
    for i, m in enumerate(BLOCK.finditer(text), start=1):
        name = clean_name(m.group("name")) or f"{prefix}_{i:02d}"
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 1
        out.append({"kind": m.group("kind"), "name": name, "source": m.group(0).strip() + "\n"})
    return out


def diagrams_from(paths: list[Path]) -> list[dict]:
    found = []
    for p in paths:
        files = sorted(p.rglob("*")) if p.is_dir() else [p]
        for f in files:
            if f.suffix in {".md", ".puml", ".plantuml", ".txt"} and f.is_file():
                for d in extract(f.read_text(encoding="utf-8"), prefix=f.stem):
                    d["file"] = str(f)
                    found.append(d)
    return found


def plantuml_exe() -> str | None:
    return shutil.which("plantuml")


def check_syntax(source: str) -> dict | None:
    """None if PlantUML parses it, else {"line": n, "message": ...} (line is 0-based)."""
    proc = subprocess.run(
        [plantuml_exe(), "-syntax"], input=source, capture_output=True, text=True, timeout=60
    )
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    if lines and lines[0] == "ERROR":
        line = int(lines[1]) if len(lines) > 1 and lines[1].isdigit() else None
        return {"line": line, "message": " ".join(lines[2:]) or "syntax error"}
    return None


# --- blueprint contract ------------------------------------------------------------

DECL = re.compile(
    r"^\s*(?:abstract\s+class|abstract|class|interface|enum|entity|record|struct)\s+"
    r"(?:\"[^\"]*\"\s+as\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)",
    re.MULTILINE,
)
CODE_SUFFIXES = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rb", ".php", ".cs", ".kt",
    ".html", ".vue", ".sql", ".rs", ".swift",
}  # fmt: skip
SKIP_DIRS = {"node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".git"}


def declared_types(text: str) -> list[str]:
    """Type names declared in @startuml diagrams (class/interface/enum/…), in order.

    Entities inside ER diagrams count too; C4/Chen blocks use other keywords and are skipped.
    """
    seen: dict[str, None] = {}
    for d in extract(text):
        if d["kind"] != "uml":
            continue
        for m in DECL.finditer(d["source"]):
            seen.setdefault(m.group("name"), None)
    return list(seen)


def name_variants(name: str) -> set[str]:
    words = re.findall(r"[A-Z]+(?=[A-Z][a-z]|\d|\b)|[A-Z]?[a-z]+|\d+", name) or [name]
    lower = [w.lower() for w in words]
    return {name.lower(), "_".join(lower), "-".join(lower), "".join(lower)}


def code_files(dirs: list[Path]) -> list[Path]:
    out = []
    for base in dirs:
        if base.is_dir():
            out += [
                p
                for p in base.rglob("*")
                if p.is_file() and p.suffix in CODE_SUFFIXES and not SKIP_DIRS & set(p.parts)
            ]
    return sorted(out)


def conformance(declared: list[str], files: list[Path]) -> dict:
    code = "\n".join(f.read_text(encoding="utf-8", errors="replace") for f in files)
    tokens = set(re.findall(r"[a-z0-9_\-]+", code.lower()))
    found = [n for n in declared if name_variants(n) & tokens]
    missing = [n for n in declared if n not in found]
    defined = [
        n
        for n in declared
        if re.search(
            rf"^\s*(?:export\s+)?(?:abstract\s+)?(?:class|interface|enum|type|struct|record)\s+{n}\b",
            code,
            re.MULTILINE,
        )
    ]
    return {
        "declared": len(declared),
        "found": len(found),
        "ratio": round(len(found) / len(declared), 3) if declared else None,
        "defined_as_type": len(defined),
        "missing": missing,
        "files_scanned": len(files),
    }


# --- tests ---------------------------------------------------------------------

PY_IMAGE, NODE_IMAGE = "python:3.12-slim", "node:22-slim"


def test_command(project: Path) -> tuple[str, str] | None:
    if (project / "requirements.txt").is_file() or (project / "pyproject.toml").is_file():
        install = (
            "pip install -q -r requirements.txt"
            if (project / "requirements.txt").is_file()
            else "pip install -q ."
        )
        quiet = "export PIP_ROOT_USER_ACTION=ignore PIP_DISABLE_PIP_VERSION_CHECK=1;"
        # no -q: a project's own `addopts = -q` would make it -qq and drop the summary line
        return PY_IMAGE, (
            f"{quiet} {install} && pip install -q pytest httpx"
            " && python -m pytest -p no:cacheprovider"
        )
    if (project / "package.json").is_file():
        return NODE_IMAGE, "npm install --silent --no-audit --no-fund && npm test"
    return None


def docker_ok() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        return subprocess.run(["docker", "info"], capture_output=True, timeout=20).returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def run_tests(project: Path, use_docker: bool = True, timeout: int = 600) -> dict:
    detected = test_command(project)
    if not detected:
        reason = "no requirements.txt / pyproject.toml / package.json"
        return {"status": "skipped", "reason": reason}
    image, command = detected
    if use_docker and not docker_ok():
        return {"status": "skipped", "reason": "docker daemon not available (use --no-docker)"}
    with tempfile.TemporaryDirectory(prefix="nl2bp-test-") as tmp:
        work = Path(tmp) / "app"
        shutil.copytree(project, work, ignore=shutil.ignore_patterns("node_modules", ".venv"))
        if use_docker:
            cmd = [
                "docker", "run", "--rm", "--memory=1g", "--cpus=2", "--pids-limit=256",
                "--security-opt=no-new-privileges", "-v", f"{work}:/app", "-w", "/app",
                image, "sh", "-c", command,
            ]  # fmt: skip
        else:
            cmd = ["sh", "-c", command.replace("pip install", "python -m pip install")]
        try:
            proc = subprocess.run(
                cmd,
                cwd=work,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return {"status": "failed", "reason": f"timed out after {timeout}s"}
    return {
        "status": "passed" if proc.returncode == 0 else "failed",
        "exit_code": proc.returncode,
        "sandbox": "docker" if use_docker else "none",
        "command": command,
        "output_tail": (proc.stdout or "")[-4000:],
    }


# --- CLI ---------------------------------------------------------------------------


def emit(data: dict, ok: bool | None) -> int:
    """Print JSON; exit 0 = passed, 1 = failed, 2 = check could not run (ok is None)."""
    print(json.dumps(data, ensure_ascii=False, indent=2))
    if ok is None:
        return 2
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("paths", nargs="+", type=Path)
    e = sub.add_parser("extract")
    e.add_argument("blueprint", type=Path)
    e.add_argument("out_dir", type=Path)
    c = sub.add_parser("contract")
    c.add_argument("blueprint", type=Path)
    f = sub.add_parser("conform")
    f.add_argument("blueprint", type=Path)
    f.add_argument("code_dirs", nargs="+", type=Path)
    f.add_argument("--threshold", type=float, default=0.9)
    r = sub.add_parser("render")
    r.add_argument("paths", nargs="+", type=Path)
    r.add_argument("--format", choices=["svg", "png"], default="svg")
    t = sub.add_parser("test")
    t.add_argument("project", type=Path)
    t.add_argument("--no-docker", action="store_true", help="run on the host (trusted code only)")
    a = ap.parse_args(argv)

    if a.cmd in ("validate", "render") and not plantuml_exe():
        return emit({"error": "plantuml not on PATH (macOS: brew install plantuml)"}, None)

    if a.cmd == "validate":
        diagrams = diagrams_from(a.paths)
        errors = []
        for d in diagrams:
            err = check_syntax(d["source"])
            if err:
                numbered = "\n".join(
                    f"{i:3d}| {ln}" for i, ln in enumerate(d["source"].splitlines())
                )
                errors.append({"file": d["file"], "name": d["name"], **err, "source": numbered})
        return emit(
            {"diagrams": len(diagrams), "invalid": len(errors), "errors": errors},
            bool(diagrams) and not errors,
        )
    if a.cmd == "extract":
        a.out_dir.mkdir(parents=True, exist_ok=True)
        written = []
        for d in extract(a.blueprint.read_text(encoding="utf-8"), prefix=a.blueprint.stem):
            path = a.out_dir / f"{d['name']}.puml"
            path.write_text(d["source"], encoding="utf-8")
            written.append(str(path))
        return emit({"written": written}, bool(written))
    if a.cmd == "contract":
        types = declared_types(a.blueprint.read_text(encoding="utf-8"))
        return emit({"declared": types}, bool(types))
    if a.cmd == "conform":
        types = declared_types(a.blueprint.read_text(encoding="utf-8"))
        result = conformance(types, code_files(a.code_dirs))
        result["threshold"] = a.threshold
        return emit(result, result["ratio"] is not None and result["ratio"] >= a.threshold)
    if a.cmd == "render":
        files = []
        for p in a.paths:
            files += sorted(p.rglob("*.puml")) if p.is_dir() else [p]
        proc = subprocess.run([plantuml_exe(), f"-t{a.format}", *map(str, files)])
        outputs = [str(f.with_suffix(f".{a.format}")) for f in files]
        return emit({"rendered": outputs}, proc.returncode == 0)
    if a.cmd == "test":
        result = run_tests(a.project, use_docker=not a.no_docker)
        if result["status"] == "skipped":
            return emit(result, None)
        return emit(result, result["status"] == "passed")
    return 2


if __name__ == "__main__":
    sys.exit(main())
