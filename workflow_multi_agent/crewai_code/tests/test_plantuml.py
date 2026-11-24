from agileworkflow import plantuml

DOC = """# Blueprint

### Class diagram: borrowing

```plantuml
@startuml library_class_borrowing
class Book {
  +isbn: String
}
@enduml
```

Text between.

```plantuml
@startfiles layout
/src/app.py
@endfiles
```

```plantuml
@startuml
A -> B
@enduml
```

```plantuml
@startuml library_class_borrowing
class Dup
@enduml
```
"""


def test_extracts_all_kinds_with_unique_names():
    diagrams = plantuml.extract(DOC, default_prefix="blueprint")
    assert [d.kind for d in diagrams] == ["uml", "files", "uml", "uml"]
    assert [d.name for d in diagrams] == [
        "library_class_borrowing",
        "layout",
        "blueprint_03",
        "library_class_borrowing_2",
    ]
    first = diagrams[0].source
    assert first.startswith("@startuml library_class_borrowing")
    assert first.rstrip().endswith("@enduml")
    assert "```" not in first


def test_unterminated_block_is_ignored():
    assert plantuml.extract("@startuml x\nA -> B\n") == []


def test_names_are_filesystem_safe():
    [d] = plantuml.extract('@startuml "../../etc/passwd me"\nA->B\n@enduml\n')
    assert "/" not in d.filename and ".." not in d.filename


def _decode(encoded: str) -> str:
    import zlib

    n_bits = [plantuml._PUML_ALPHABET.index(c) for c in encoded]
    raw = bytearray()
    for i in range(0, len(n_bits), 4):
        n = 0
        for v in n_bits[i : i + 4]:
            n = (n << 6) | v
        raw += n.to_bytes(3, "big")
    return zlib.decompressobj(-15).decompress(bytes(raw)).decode("utf-8")


def test_server_encoding_round_trips():
    for src in ["Bob -> Alice : hello", "@startuml\n用户 -> 系统 : 借书\n@enduml\n" * 20]:
        assert _decode(plantuml.server_encode(src)) == src


def test_server_encoding_matches_published_example():
    # Example from https://plantuml.com/text-encoding
    assert plantuml.server_encode("Bob -> Alice : hello") == "SyfFKj2rKt3CoKnELR1Io4ZDoSa70000"
