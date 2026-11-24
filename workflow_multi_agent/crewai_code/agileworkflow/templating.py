"""Single-pass placeholder rendering.

CrewAI's own interpolation raises on any ``{word}`` it cannot fill, which breaks
on PlantUML/JSON in prompts and on earlier stage outputs fed into later tasks.
We render task text ourselves and hand CrewAI finished strings.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

_PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def placeholders(template: str) -> set[str]:
    return set(_PLACEHOLDER.findall(template))


def render(template: str, values: Mapping[str, object]) -> str:
    """Replace ``{name}`` for names present in ``values``; leave others alone.

    One regex pass, so a value that itself contains ``{name}`` is not expanded
    again.
    """

    def sub(match: re.Match[str]) -> str:
        key = match.group(1)
        return str(values[key]) if key in values else match.group(0)

    return _PLACEHOLDER.sub(sub, template)
