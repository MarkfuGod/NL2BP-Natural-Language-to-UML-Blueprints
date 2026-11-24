# AgileWorkflow: the CrewAI implementation of NL2BP

[中文](README.md)

Turns a natural-language requirement into an architecture document, PlantUML UML blueprints and runnable frontend/backend code, through multi-agent collaboration or a single agent that switches roles. Built on **CrewAI 1.x** (tested on 1.15).

## Quick start

```bash
cd workflow_multi_agent/crewai_code
uv sync                       # Python 3.10–3.13; uv fetches a suitable Python
cp .env.example .env          # set MODEL and the matching provider key

# Multi-agent agile workflow
uv run nl2bp multi --name LibrarySystem \
  --description "Students search, borrow and return books; admins manage books and overdue fines." \
  --sprint-days 14 --language English

# Single agent, multiple roles (role prompts from workflow_single_agent/role_prompts)
uv run nl2bp single --name LibrarySystem --description-file requirements.md --language English

# Render generated .puml to SVG (needs local plantuml: brew install plantuml)
uv run nl2bp render output/<run>/diagrams
```

`uv run kickoff` or `crewai flow kickoff` without arguments prompts interactively.

### Models

`MODEL` is `<provider>/<model>`. CrewAI 1.x has native clients for openai, anthropic, gemini, deepseek, ollama, openrouter, azure and bedrock:

| MODEL example | Environment |
|---|---|
| `anthropic/claude-sonnet-5-5` | `ANTHROPIC_API_KEY` |
| `openai/gpt-5.1` | `OPENAI_API_KEY` |
| `deepseek/deepseek-chat` | `DEEPSEEK_API_KEY` |
| `ollama/qwen3:14b` | local Ollama, no key |

Other providers: `uv sync --extra litellm` and use a LiteLLM model string. CrewAI's anonymous telemetry and tracing are off by default (override with `CREWAI_DISABLE_TELEMETRY` etc.).

## Multi-agent workflow

```
prepare
  └─ system_design                       System Design Agent
       └─ requirement_analysis           Requirement Analysis Agent
            ├─ sprint_planning           Agile Dashboard Agent (concurrent)
            └─ blueprint_design          Blueprint Design Agent (--review: human collaborator, repeatable)
                 ├─ frontend_design      Frontend Agent ─┐ concurrent, writes code with write_file
                 └─ backend_design       Backend Agent  ─┤
                                                         ├─ version_control     Version Control Agent
                                                         └─ agile_dashboard     Agile Dashboard Agent
                                                              └─ feedback_planning  Feedback Planning Agent
                                                                   └─ system_design_summary  Blueprint Design Agent
```

- Each stage runs exactly once, as a one-agent, one-task crew, and receives only the upstream documents it needs.
- `--review` adds the human collaborator: the flow pauses after the blueprint; type feedback to regenerate, press Enter to accept (up to 3 rounds).
- Documents come back as each agent's final answer. The flow saves them and extracts every `@startuml … @enduml` (and `@startfiles`, …) block into a `.puml` file.

## Single-agent workflow

One agent switches roles; each role works only from the documents the previous role left:

```
01-req-gen → systemdesign → blueprintdesign → coder → code-reviewer
    ↺ changes requested: code-critic diagnoses → coder fixes → code-reviewer again (--max-fix-rounds, default 1)
→ debugger-deployer
```

Role rules are read from `workflow_single_agent/role_prompts/rules-<slug>/*.md` (point `NL2BP_ROLE_PROMPTS` elsewhere to override). The same prompts also work as Roo Code custom modes; see [workflow_single_agent](../../workflow_single_agent/).

## Output

Each run gets its own directory `output/<timestamp>_<project>/`:

```
docs/<stage>.md        one document per stage
diagrams/*.puml        PlantUML diagrams extracted from the documents
frontend/ backend/     multi-agent: code written through write_file
code/                  single-agent: code and deployment files
manifest.json          inputs, model, stage timings, token usage, review verdict
```

`write_file`, `read_file` and `list_files` can only touch the run directory; paths that escape it (`../`, symlinks) are refused.

## Development

```bash
uv sync --group dev
uv run pytest -q
uv run ruff check . && uv run ruff format --check .
uv run nl2bp plot             # flow graph as agile_workflow_flow.html
```

To add a stage, add entries to `agents.yaml` / `tasks.yaml`, then add an `@listen(...)` method in `agile_flow.py` that calls `self._stage("<stage>")`. `tests/test_core.py::test_config_is_consistent` checks the config references.

## Migrating from 0.1

- CrewAI `>=0.118,<1` → `>=1.15,<2`; Python up to 3.13; uv instead of pip.
- 0.1 ran the whole crew (all 10+ tasks) for every stage, 8 times over. Each stage now runs only its own task once, and frontend/backend run in parallel.
- Documents no longer depend on the agent remembering to call a file tool. The unused `developer_agent` / `testing_agent` and duplicated prompt files are gone.
- Output moved from `output/*.md` + `Project/` to one `output/<run>/` per run.
