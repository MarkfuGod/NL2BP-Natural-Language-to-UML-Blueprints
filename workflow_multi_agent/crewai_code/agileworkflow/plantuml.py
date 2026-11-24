"""Find PlantUML diagrams in Markdown and optionally render them."""

from __future__ import annotations

import re
import shutil
import string
import subprocess
import urllib.request
import zlib
from dataclasses import dataclass
from pathlib import Path

# @startuml / @startfiles / @startmindmap ... matched with the same @endX.
_BLOCK = re.compile(
    r"^[ \t]*@start(?P<kind>[a-z]+)(?P<name>[^\n]*)\n(?P<body>.*?)^[ \t]*@end(?P=kind)\b[^\n]*",
    re.MULTILINE | re.DOTALL,
)


@dataclass(frozen=True)
class Diagram:
    kind: str
    name: str
    source: str

    @property
    def filename(self) -> str:
        return f"{self.name}.puml"


def _clean_name(raw: str) -> str:
    raw = raw.strip().strip('"').strip("'")
    raw = re.sub(r"[^\w\-]+", "_", raw, flags=re.UNICODE).strip("_")
    return raw[:80]


def extract(markdown: str, default_prefix: str = "diagram") -> list[Diagram]:
    """Every ``@startX … @endX`` block, with unique file-safe names."""
    diagrams: list[Diagram] = []
    seen: dict[str, int] = {}
    for i, m in enumerate(_BLOCK.finditer(markdown), start=1):
        kind = m.group("kind")
        name = _clean_name(m.group("name")) or f"{default_prefix}_{i:02d}"
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 1
        diagrams.append(Diagram(kind=kind, name=name, source=m.group(0).strip() + "\n"))
    return diagrams


# --- rendering -----------------------------------------------------------------

_PUML_ALPHABET = string.digits + string.ascii_uppercase + string.ascii_lowercase + "-_"


def server_encode(source: str) -> str:
    """PlantUML server text encoding: raw DEFLATE + PlantUML's base64 alphabet."""
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
    data = compressor.compress(source.encode("utf-8")) + compressor.flush()
    out = []
    for i in range(0, len(data), 3):
        chunk = data[i : i + 3] + b"\0" * (3 - len(data[i : i + 3]))
        n = int.from_bytes(chunk, "big")
        out.extend(_PUML_ALPHABET[(n >> s) & 0x3F] for s in (18, 12, 6, 0))
    return "".join(out)


def render_local(files: list[Path], fmt: str = "svg") -> list[Path]:
    exe = shutil.which("plantuml")
    if not exe:
        raise FileNotFoundError(
            "`plantuml` is not on PATH (macOS: brew install plantuml). "
            "Or pass --server <url> to render through a PlantUML server."
        )
    subprocess.run([exe, f"-t{fmt}", *map(str, files)], check=True)
    return [f.with_suffix(f".{fmt}") for f in files]


def render_server(files: list[Path], server: str, fmt: str = "svg") -> list[Path]:
    """Render via a PlantUML server you chose explicitly (diagram text is sent there)."""
    out = []
    for f in files:
        url = f"{server.rstrip('/')}/{fmt}/{server_encode(f.read_text(encoding='utf-8'))}"
        with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310 - user-chosen URL
            target = f.with_suffix(f".{fmt}")
            target.write_bytes(resp.read())
        out.append(target)
    return out
