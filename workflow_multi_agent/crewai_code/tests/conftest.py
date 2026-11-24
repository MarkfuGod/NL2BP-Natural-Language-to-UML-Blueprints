import os

import pytest

os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

from agileworkflow.settings import Settings  # noqa: E402


@pytest.fixture
def settings(tmp_path):
    return Settings(model="fake/model", output_dir=tmp_path / "out")
