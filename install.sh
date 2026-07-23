#!/usr/bin/env bash
# Symlinks every SKILL.md-bearing directory in this repo into ~/.claude/skills so
# Claude Code loads each skill natively.
# Re-runnable: links new skills, skips existing entries, prunes links that point
# into this repo but whose source skill no longer exists.
set -euo pipefail

repo="$(cd "$(dirname "$0")" && pwd)"
dest="$HOME/.claude/skills"
mkdir -p "$dest"

for link in "$dest"/*; do
  [ -L "$link" ] || continue
  target="$(readlink "$link")"
  case "$target" in
    "$repo"/*)
      if [ ! -f "$target/SKILL.md" ]; then
        echo "prune  $(basename "$link")  (dead link)"
        rm "$link"
      fi
      ;;
  esac
done

for dir in "$repo"/*/; do
  dir="${dir%/}"
  [ -f "$dir/SKILL.md" ] || continue
  name="$(basename "$dir")"
  if [ -e "$dest/$name" ]; then
    echo "skip   $name  (already present)"
  elif ln -s "$dir" "$dest/$name"; then
    echo "link   $name"
  else
    echo "FAIL   $name  (ln -s failed, continuing)" >&2
  fi
done
