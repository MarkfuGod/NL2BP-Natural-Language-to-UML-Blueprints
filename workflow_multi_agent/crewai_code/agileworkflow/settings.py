"""Runtime settings: which model to call and where outputs go."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_LANGUAGE = "中文"

# CrewAI sends anonymous telemetry and run traces by default; each call adds
# seconds of latency and leaves the machine. Off unless the user opts back in.
_QUIET_ENV = {
    "CREWAI_DISABLE_TELEMETRY": "true",
    "CREWAI_TRACING_ENABLED": "false",
    "OTEL_SDK_DISABLED": "true",
}


def quiet_crewai() -> None:
    for key, value in _QUIET_ENV.items():
        os.environ.setdefault(key, value)


def load_dotenv(path: Path | None = None) -> None:
    """Minimal .env loader: KEY=VALUE lines, existing env wins."""
    path = path or Path.cwd() / ".env"
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and value:
            os.environ.setdefault(key, value)


class ConfigError(RuntimeError):
    pass


@dataclass
class Settings:
    model: str
    temperature: float = 0.2
    output_dir: Path = field(default_factory=lambda: Path("output"))
    language: str = DEFAULT_LANGUAGE
    verbose: bool = False
    # Quality gates (each one is skipped, with the reason recorded, if its tool is missing)
    check_diagrams: bool = True
    max_repair_rounds: int = 2
    run_tests: bool = True
    git_history: bool = True
    conformance_threshold: float = 0.9
    # Per-request timeout and retries: without one, a stalled connection hangs the run forever.
    llm_timeout: float = 300.0
    llm_max_retries: int = 2
    # "blueprint": stop after requirements → architecture → blueprint (used by the RSI loop)
    stop_after: str | None = None

    @classmethod
    def from_env(cls, **overrides) -> Settings:
        overrides = {k: v for k, v in overrides.items() if v is not None}
        model = overrides.pop("model", None) or os.environ.get("MODEL", "").strip()
        if not model:
            raise ConfigError(
                "No model configured. Set MODEL (e.g. MODEL=anthropic/claude-sonnet-5-5, "
                "openai/gpt-5.1, deepseek/deepseek-chat, ollama/qwen3:14b) in the "
                "environment or .env, or pass --model."
            )
        return cls(
            model=model,
            temperature=float(
                overrides.pop("temperature", None) or os.environ.get("NL2BP_TEMPERATURE", 0.2)
            ),
            output_dir=Path(
                overrides.pop("output_dir", None) or os.environ.get("NL2BP_OUTPUT_DIR", "output")
            ),
            language=overrides.pop("language", None)
            or os.environ.get("NL2BP_LANGUAGE", DEFAULT_LANGUAGE),
            llm_timeout=float(
                overrides.pop("llm_timeout", None) or os.environ.get("NL2BP_LLM_TIMEOUT", 300)
            ),
            **overrides,
        )

    def build_llm(self):
        from crewai import LLM

        return LLM(
            model=self.model,
            temperature=self.temperature,
            timeout=self.llm_timeout,
            max_retries=self.llm_max_retries,
        )
