#!/usr/bin/env sh
# Re-extract, validate and render every example's diagrams from its Markdown sources.
#   sh examples/regenerate.sh            (needs python3 and plantuml on PATH)
set -eu
here=$(cd "$(dirname "$0")" && pwd)
check="$here/../skills/nl2bp/scripts/nl2bp_check.py"
for dir in "$here"/*/; do
  [ -f "$dir/blueprint.md" ] || continue
  rm -f "$dir"/diagrams/*.puml "$dir"/diagrams/*.svg
  for doc in "$dir"/*.md; do
    case "$(basename "$doc")" in README.md) continue ;; esac
    python3 -I "$check" extract "$doc" "$dir/diagrams" > /dev/null || true
  done
  python3 -I "$check" validate "$dir/diagrams" > /dev/null
  python3 -I "$check" render "$dir/diagrams" > /dev/null
  echo "ok: $(basename "$dir") ($(ls "$dir"/diagrams/*.puml | wc -l | tr -d ' ') diagrams)"
done
