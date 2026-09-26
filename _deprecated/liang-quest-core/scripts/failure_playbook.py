#!/usr/bin/env python3
"""
failure_playbook.py - classify a failed build/test/child log against the
known-failure playbook (failure-playbook.yaml beside this file).

    python failure_playbook.py <log> [<log> ...]

Prints one JSON verdict for all logs combined:

    {"verdict": "false_failure" | "retry" | "blocker" | "hint" | "unknown" | "clean",
     "matches": [{"id", "class", "note", "line"}],
     "unexplained": [<error lines no ignore rule covers>]}

Verdict precedence: blocker > retry > false_failure > hint > unknown > clean.
false_failure means every error line is covered by an ignore rule.
Importable: classify_text(), classify_files(), infra_failure_types().
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

PLAYBOOK_PATH = Path(__file__).resolve().parent / "failure-playbook.yaml"
ERROR_LINE_RE = re.compile(
    r"\berror\b|\bfatal\b|Result: Failed|EXIT CODE: [1-9]|Result=\{(Fail|Error)",
    re.IGNORECASE,
)
ZERO_ERRORS_RE = re.compile(r"\b0 error", re.IGNORECASE)
WARNING_LINE_RE = re.compile(r"\bWarning:")
MAX_UNEXPLAINED = 10


def load_playbook(path: Path = PLAYBOOK_PATH) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def infra_failure_types(playbook: dict | None = None) -> set[str]:
    playbook = playbook or load_playbook()
    return set(playbook.get("infra_failure_types") or [])


def _compiled_rules(playbook: dict) -> list[dict]:
    return [
        {**rule, "regexes": [re.compile(p) for p in rule.get("patterns") or []]}
        for rule in playbook.get("rules") or []
    ]


def _is_error_line(line: str) -> bool:
    if WARNING_LINE_RE.search(line) or ZERO_ERRORS_RE.search(line):
        return False
    return bool(ERROR_LINE_RE.search(line))


def _match_lines(lines: list[str], rules: list[dict]) -> dict[str, list[str]]:
    """The first rule (in playbook order) that matches a line claims it."""
    hits: dict[str, list[str]] = {}
    for line in lines:
        rule = next((r for r in rules if any(rx.search(line) for rx in r["regexes"])), None)
        if rule:
            hits.setdefault(rule["id"], []).append(line)
    return hits


def _drop_unmet_requirements(hits: dict[str, list[str]], rules: list[dict]) -> dict[str, list[str]]:
    required = {rule["id"]: rule.get("requires") for rule in rules}
    return {rid: lines for rid, lines in hits.items() if not required.get(rid) or required[rid] in hits}


def _verdict(classes: set[str], has_errors: bool, unexplained: list[str]) -> str:
    if "blocker" in classes:
        return "blocker"
    if "retry" in classes:
        return "retry"
    if has_errors and not unexplained and "ignore" in classes:
        return "false_failure"
    if "hint" in classes:
        return "hint"
    return "unknown" if has_errors else "clean"


def classify_text(text: str, playbook: dict | None = None) -> dict:
    rules = _compiled_rules(playbook or load_playbook())
    by_id = {rule["id"]: rule for rule in rules}
    lines = text.splitlines()
    hits = _drop_unmet_requirements(_match_lines(lines, rules), rules)

    ignored_lines = {line for rid, matched in hits.items() if by_id[rid]["class"] == "ignore" for line in matched}
    error_lines = [line for line in lines if _is_error_line(line)]
    unexplained = [line.strip() for line in error_lines if line not in ignored_lines]

    matches = [
        {"id": rid, "class": by_id[rid]["class"], "note": (by_id[rid].get("note") or "").strip(), "line": matched[0].strip()}
        for rid, matched in hits.items()
    ]
    classes = {m["class"] for m in matches}
    return {
        "verdict": _verdict(classes, bool(error_lines), unexplained),
        "matches": matches,
        "unexplained": unexplained[:MAX_UNEXPLAINED],
    }


def classify_files(paths: list[Path], playbook: dict | None = None) -> dict:
    text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in paths if p.is_file())
    return classify_text(text, playbook)


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    print(json.dumps(classify_files([Path(a) for a in argv]), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
