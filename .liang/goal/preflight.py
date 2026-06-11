"""
preflight.py — deterministic audit for liang-quest-* and liang-brainstorm-* skill families.
Zero model involvement; zero writes outside the run output directory.
Python 3.11, stdlib + pyyaml only.
"""
from __future__ import annotations

import argparse
import datetime
import fnmatch
import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fwd(p: Path, root: Path) -> str:
    """Return forward-slash path relative to root."""
    return p.relative_to(root).as_posix()


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def strip_frontmatter(text: str) -> tuple[str, int]:
    """Strip YAML frontmatter. Returns (body_text, offset_lines)."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            block = text[: end + 4]
            offset = block.count("\n") + 1
            return text[end + 4 :].lstrip("\n"), offset
    return text, 0


def headings_in_file(path: Path) -> set[str]:
    """Return set of heading texts (lowercase, stripped of # and whitespace)."""
    text = read_text(path)
    result = set()
    for line in text.splitlines():
        m = re.match(r"^#{1,6}\s+(.*)", line)
        if m:
            result.add(m.group(1).strip().lower())
    return result


_CITATION_TICK_RE = re.compile(
    r"`[^`\n]*(?:/|\xa7)[^`\n]*`"
)


def _strip_citation_ticks(text: str) -> str:
    """Remove inline backtick spans that look like file-path or section citations.

    A span is treated as a citation path when its content (on a single line)
    contains a forward-slash (directory separator) or § (section-anchor marker).
    Spans that only end with a file extension but contain no slash are kept —
    they are typically tool names, flag names, or field names, not citations.

    Kept spans: contract terms, flags, field names (e.g. `manifest.yaml`,
    `sweep.py`, `--dry-run`).
    Stripped spans: `liang-quest-core/references/foo.md § heading`, `.liang/project.yaml`.
    """
    return _CITATION_TICK_RE.sub("", text)


def tokenize(text: str) -> list[str]:
    """Lowercase words (strip punctuation). Skips frontmatter.

    Inline-code spans whose content looks like a file path or section
    citation are removed before tokenisation so that identical citations
    of the same canonical reference do not inflate the shingle count.
    """
    body, _ = strip_frontmatter(text)
    body = _strip_citation_ticks(body)
    return re.findall(r"[a-z0-9]+", body.lower())


def shingles(words: list[str], n: int = 8) -> set[tuple[str, ...]]:
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


def longest_run(shared: set[tuple[str, ...]], words_a: list[str]) -> str:
    """Return a sample of the longest shared run from words_a."""
    best: list[str] = []
    wa = list(words_a)
    for i in range(len(wa)):
        for length in range(len(best) + 1, len(wa) - i + 1):
            if tuple(wa[i : i + length]) in shared:
                best = wa[i : i + length]
            else:
                break
    return " ".join(best) if best else " ".join(next(iter(shared)))


# ---------------------------------------------------------------------------
# Load suppressions from drift-ledger
# ---------------------------------------------------------------------------

def load_suppressions(ledger_path: Path) -> tuple[list[dict], list[dict]]:
    """Return (suppressions, pair_suppressions) from drift-ledger."""
    text = read_text(ledger_path)
    # Extract fenced yaml block
    m = re.search(r"```yaml\n(.*?)```", text, re.DOTALL)
    if not m:
        return [], []
    parsed = yaml.safe_load(m.group(1))
    if not parsed:
        return [], []
    sups = parsed.get("suppressions", [])
    pair_sups = parsed.get("pair_suppressions", [])
    return sups, pair_sups


def is_suppressed(
    check: str,
    rel_path: str,
    matched_text: str,
    suppressions: list[dict],
) -> tuple[bool, str]:
    """Return (suppressed, dv_id)."""
    for sup in suppressions:
        if sup.get("check") != check:
            continue
        glob = sup.get("file_glob", "")
        pattern = sup.get("pattern", "")
        if fnmatch.fnmatch(rel_path, glob) and re.search(
            pattern, matched_text, re.IGNORECASE
        ):
            return True, sup.get("id", "")
    return False, ""


# ---------------------------------------------------------------------------
# Scan helpers
# ---------------------------------------------------------------------------

def collect_skill_dirs(root: Path, target_globs: list[str]) -> list[Path]:
    dirs = []
    for item in sorted(root.iterdir()):
        if not item.is_dir():
            continue
        for g in target_globs:
            if fnmatch.fnmatch(item.name, g):
                dirs.append(item)
                break
    return dirs


def collect_scan_files(skill_dir: Path) -> list[Path]:
    """SKILL.md + references/**/*.md"""
    files: list[Path] = []
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        files.append(skill_md)
    refs_dir = skill_dir / "references"
    if refs_dir.is_dir():
        for p in sorted(refs_dir.rglob("*.md")):
            files.append(p)
    return files


# ---------------------------------------------------------------------------
# Check implementations
# ---------------------------------------------------------------------------

def check_citation_resolution(
    files: list[Path], root: Path, seq: list[int]
) -> list[dict]:
    findings: list[dict] = []
    # Pattern 1: liang-<family>-<name>/references/<path>
    # Pattern 2: bare references/<path>  (relative to skill dir)
    # Pattern 3: backtick-wrapped paths containing /
    pat_full = re.compile(r"(?:liang-[a-z0-9-]+/references/[^\s`'\")]+\.md)")
    pat_bare = re.compile(r"(?<![`/])references/([^\s`'\")]+\.md)")
    pat_tick = re.compile(r"`([^`]*liang-[a-z0-9-]+/references/[^`]+\.md)`")

    for fpath in files:
        text = read_text(fpath)
        lines = text.splitlines()
        skill_dir = fpath.parent if fpath.name != "SKILL.md" else fpath.parent
        # For references/ files, the skill dir is two levels up from the file
        # (file is under skill_dir/references/...)
        # We need to find the skill root
        rel = fwd(fpath, root)
        parts = rel.split("/")
        skill_root = root / parts[0]

        seen: set[str] = set()

        def emit(ref_str: str, lineno: int, line_text: str):
            if ref_str in seen:
                return
            seen.add(ref_str)
            # Resolve path
            candidate = root / Path(ref_str)
            if candidate.exists():
                return
            # Try relative to skill dir
            candidate2 = skill_root / Path(ref_str)
            if candidate2.exists():
                return
            seq[0] += 1
            findings.append(
                {
                    "id": f"f-c2-{seq[0]:03d}",
                    "criterion": "C2",
                    "severity": "critical",
                    "class": "structural",
                    "file": fwd(fpath, root),
                    "location": f"line {lineno}",
                    "summary": f"unresolved citation: {ref_str}",
                    "excerpt": line_text.strip(),
                    "proposed_fix": None,
                }
            )

        for lineno, line in enumerate(lines, 1):
            for m in pat_full.finditer(line):
                emit(m.group(0), lineno, line)
            for m in pat_tick.finditer(line):
                emit(m.group(1), lineno, line)
            for m in pat_bare.finditer(line):
                ref = f"references/{m.group(1)}"
                # Resolve relative to skill dir
                candidate = skill_root / ref
                if candidate.exists():
                    continue
                if ref in seen:
                    continue
                seen.add(ref)
                seq[0] += 1
                findings.append(
                    {
                        "id": f"f-c2-{seq[0]:03d}",
                        "criterion": "C2",
                        "severity": "critical",
                        "class": "structural",
                        "file": fwd(fpath, root),
                        "location": f"line {lineno}",
                        "summary": f"unresolved citation: {ref} (relative to {parts[0]})",
                        "excerpt": line.strip(),
                        "proposed_fix": None,
                    }
                )
    return findings


def check_attribution_anchors(
    files: list[Path], root: Path, seq: list[int]
) -> list[dict]:
    findings: list[dict] = []
    # line-number attribution pattern
    line_num_pat = re.compile(r"lines?\s+\d+\s*[-–]\s*\d+", re.IGNORECASE)
    # anchor form: § <heading>
    anchor_pat = re.compile(r"§\s+([^`\n]+?)(?:\s+per\s+\w+|$|\n)")

    for fpath in files:
        text = read_text(fpath)
        lines = text.splitlines()
        for lineno, line in enumerate(lines, 1):
            if line_num_pat.search(line):
                seq[0] += 1
                findings.append(
                    {
                        "id": f"f-c2-{seq[0]:03d}",
                        "criterion": "C2",
                        "severity": "critical",
                        "class": "mechanical",
                        "file": fwd(fpath, root),
                        "location": f"line {lineno}",
                        "summary": "line-number attribution; migrate to section-anchor form (<file> § <heading> per dcNNN)",
                        "excerpt": line.strip(),
                        "proposed_fix": None,
                    }
                )

    # Anchor heading-existence check
    # Pattern: <file> § <heading> or `<file>` § <heading>
    heading_ref_pat = re.compile(
        r"`?([a-z][a-z0-9/._-]+\.md)`?\s*§\s*([^\n`()\[\]]+?)(?:\s+per\s+\w+|\s*$)",
        re.IGNORECASE,
    )
    for fpath in files:
        text = read_text(fpath)
        lines = text.splitlines()
        rel_parts = fwd(fpath, root).split("/")
        skill_root = root / rel_parts[0]

        for lineno, line in enumerate(lines, 1):
            for m in heading_ref_pat.finditer(line):
                cited_file_str = m.group(1)
                heading = m.group(2).strip().lower()
                # Resolve cited file
                candidate = root / cited_file_str
                if not candidate.exists():
                    candidate = skill_root / cited_file_str
                if not candidate.exists():
                    continue  # Already caught by citation-resolution
                actual_headings = headings_in_file(candidate)
                if heading not in actual_headings:
                    seq[0] += 1
                    findings.append(
                        {
                            "id": f"f-c2-{seq[0]:03d}",
                            "criterion": "C2",
                            "severity": "critical",
                            "class": "mechanical",
                            "file": fwd(fpath, root),
                            "location": f"line {lineno}",
                            "summary": f"anchor heading not found: '{heading}' in {cited_file_str}",
                            "excerpt": line.strip(),
                            "proposed_fix": None,
                        }
                    )
    return findings


def check_dc_uniqueness(files: list[Path], root: Path, seq: list[int]) -> list[dict]:
    findings: list[dict] = []
    dc_pat = re.compile(r"\b(d[cv]\d+)\b", re.IGNORECASE)
    dc_files: dict[str, list[str]] = {}

    for fpath in files:
        text = read_text(fpath)
        rel = fwd(fpath, root)
        for m in dc_pat.finditer(text):
            token = m.group(1).lower()
            dc_files.setdefault(token, [])
            if rel not in dc_files[token]:
                dc_files[token].append(rel)

    for token, file_list in sorted(dc_files.items()):
        if len(file_list) > 6:
            seq[0] += 1
            findings.append(
                {
                    "id": f"f-c2-{seq[0]:03d}",
                    "criterion": "C2",
                    "severity": "open-question",
                    "class": "judgment-needed",
                    "file": file_list[0],
                    "location": "family-wide",
                    "summary": f"{token} appears in {len(file_list)} files (>6); verify uniqueness",
                    "excerpt": "; ".join(file_list[:6]),
                    "proposed_fix": None,
                }
            )
    return findings


def check_vendor_model(
    files: list[Path],
    root: Path,
    suppressions: list[dict],
    seq: list[int],
) -> tuple[list[dict], list[dict]]:
    findings: list[dict] = []
    suppressed: list[dict] = []
    vendor_pat = re.compile(
        r"\b(sonnet|opus|haiku|claude-[a-z0-9.\-]+|deepseek-[a-z0-9.\-]+|gpt-[a-z0-9.\-]+|gemini-[a-z0-9.\-]+)\b",
        re.IGNORECASE,
    )
    for fpath in files:
        text = read_text(fpath)
        lines = text.splitlines()
        rel = fwd(fpath, root)
        for lineno, line in enumerate(lines, 1):
            for m in vendor_pat.finditer(line):
                matched = m.group(0)
                suppressed_flag, dv_id = is_suppressed(
                    "vendor-model-grep", rel, matched, suppressions
                )
                seq[0] += 1
                entry = {
                    "id": f"f-c3-{seq[0]:03d}",
                    "criterion": "C3",
                    "severity": "critical",
                    "class": "judgment-needed",
                    "file": rel,
                    "location": f"line {lineno}",
                    "summary": f"vendor model pin: '{matched}'",
                    "excerpt": line.strip(),
                    "proposed_fix": None,
                }
                if suppressed_flag:
                    suppressed.append({"id": entry["id"], "ledger": dv_id})
                else:
                    findings.append(entry)
    return findings, suppressed


def _match_pair_suppression(
    rel_a: str, rel_b: str, count: int, pair_suppressions: list[dict]
) -> tuple[bool, str, int]:
    """Check if (rel_a, rel_b) matches a pair_suppressions rule (order-insensitive).

    Returns (suppressed, dv_id, max_shingles).
    suppressed is True only when count <= max_shingles.
    If the pair matches but count exceeds max_shingles, returns (False, dv_id, max_shingles).
    If no rule matches, returns (False, "", 0).
    """
    pair = {rel_a, rel_b}
    for rule in pair_suppressions:
        if rule.get("check") != "shingle-duplication":
            continue
        rule_files = rule.get("files", [])
        if len(rule_files) != 2:
            continue
        if set(rule_files) == pair:
            dv_id = rule.get("id", "")
            max_sh = rule.get("max_shingles", 0)
            return (count <= max_sh), dv_id, max_sh
    return False, "", 0


def check_shingle_duplication(
    files: list[Path], root: Path, seq: list[int],
    pair_suppressions: list[dict] | None = None,
) -> tuple[list[dict], list[dict]]:
    findings: list[dict] = []
    suppressed: list[dict] = []
    if pair_suppressions is None:
        pair_suppressions = []

    # Build per-file shingle sets; skip files within same skill dir
    file_data: list[tuple[Path, str, list[str], set]] = []
    for fpath in files:
        text = read_text(fpath)
        words = tokenize(text)
        sh = shingles(words)
        rel = fwd(fpath, root)
        skill_dir_name = rel.split("/")[0]
        file_data.append((fpath, skill_dir_name, words, sh))

    n = len(file_data)
    for i in range(n):
        for j in range(i + 1, n):
            fa, skill_a, words_a, sh_a = file_data[i]
            fb, skill_b, words_b, sh_b = file_data[j]
            if skill_a == skill_b:
                continue
            shared = sh_a & sh_b
            if len(shared) >= 5:
                rel_a = fwd(fa, root)
                rel_b = fwd(fb, root)
                sup_flag, dv_id, max_sh = _match_pair_suppression(
                    rel_a, rel_b, len(shared), pair_suppressions
                )
                sample = longest_run(shared, words_a)
                seq[0] += 1
                entry = {
                    "id": f"f-c1-{seq[0]:03d}",
                    "criterion": "C1",
                    "severity": "critical",
                    "class": "judgment-needed",
                    "file": rel_a,
                    "location": f"vs {rel_b}",
                    "summary": f"shingle duplication: {len(shared)} shared 8-word shingles",
                    "excerpt": sample[:200],
                    "proposed_fix": None,
                }
                if sup_flag:
                    # Within budget: suppress with count in summary
                    suppressed.append({
                        "id": entry["id"],
                        "ledger": dv_id,
                        "summary": f"shingle-duplication suppressed ({len(shared)} shared shingles <= {dv_id} max_shingles={max_sh}): {rel_a} vs {rel_b}",
                    })
                elif dv_id:
                    # Pair matches but count exceeds max_shingles: keep as finding with annotation
                    entry["summary"] += f" — exceeds {dv_id} max_shingles={max_sh}"
                    findings.append(entry)
                else:
                    findings.append(entry)
    return findings, suppressed


def check_line_budget(files: list[Path], root: Path, seq: list[int]) -> list[dict]:
    findings: list[dict] = []
    for fpath in files:
        if fpath.name != "SKILL.md":
            continue
        text = read_text(fpath)
        lines = text.splitlines()
        count = len(lines)
        if count > 280:
            seq[0] += 1
            findings.append(
                {
                    "id": f"f-c4-{seq[0]:03d}",
                    "criterion": "C4",
                    "severity": "advisory",
                    "class": "structural",
                    "file": fwd(fpath, root),
                    "location": f"line count: {count}",
                    "summary": f"SKILL.md exceeds 280-line soft cap ({count} lines); consider extracting to references/",
                    "excerpt": f"{count} lines total",
                    "proposed_fix": None,
                }
            )
        # Check frontmatter description word count
        if text.startswith("---"):
            end = text.find("\n---", 3)
            if end != -1:
                fm_text = text[4:end]
                try:
                    fm = yaml.safe_load(fm_text)
                    if fm and isinstance(fm, dict):
                        desc = fm.get("description", "")
                        if desc:
                            word_count = len(desc.split())
                            if word_count > 120:
                                seq[0] += 1
                                findings.append(
                                    {
                                        "id": f"f-c4-{seq[0]:03d}",
                                        "criterion": "C4",
                                        "severity": "advisory",
                                        "class": "mechanical",
                                        "file": fwd(fpath, root),
                                        "location": "frontmatter description",
                                        "summary": f"frontmatter description exceeds 120 words ({word_count} words)",
                                        "excerpt": desc[:120] + "...",
                                        "proposed_fix": None,
                                    }
                                )
                except yaml.YAMLError:
                    pass
    return findings


def check_dead_files(
    skill_dirs: list[Path], all_scan_files: list[Path], root: Path, seq: list[int]
) -> list[dict]:
    findings: list[dict] = []
    # Build set of all basenames mentioned in .md files per skill dir
    skill_md_content: dict[str, str] = {}
    for skill_dir in skill_dirs:
        combined = ""
        for fp in all_scan_files:
            if fp.is_relative_to(skill_dir):
                combined += read_text(fp) + "\n"
        skill_md_content[skill_dir.name] = combined

    # Combined prose across ALL scanned skill dirs (for cross-skill orphan check)
    all_prose = "\n".join(skill_md_content.values())

    for skill_dir in skill_dirs:
        # Check for __pycache__ dirs
        for pycache in skill_dir.rglob("__pycache__"):
            if pycache.is_dir():
                seq[0] += 1
                findings.append(
                    {
                        "id": f"f-c4-{seq[0]:03d}",
                        "criterion": "C4",
                        "severity": "advisory",
                        "class": "mechanical",
                        "file": fwd(pycache, root),
                        "location": "directory",
                        "summary": "__pycache__ directory; safe to remove",
                        "excerpt": str(pycache),
                        "proposed_fix": None,
                    }
                )
        # Check for *.pyc files
        for pyc in skill_dir.rglob("*.pyc"):
            seq[0] += 1
            findings.append(
                {
                    "id": f"f-c4-{seq[0]:03d}",
                    "criterion": "C4",
                    "severity": "advisory",
                    "class": "mechanical",
                    "file": fwd(pyc, root),
                    "location": "file",
                    "summary": "compiled .pyc file; safe to remove",
                    "excerpt": str(pyc),
                    "proposed_fix": None,
                }
            )
        # Check for *.legacy files
        for legacy in skill_dir.rglob("*.legacy"):
            seq[0] += 1
            findings.append(
                {
                    "id": f"f-c4-{seq[0]:03d}",
                    "criterion": "C4",
                    "severity": "advisory",
                    "class": "mechanical",
                    "file": fwd(legacy, root),
                    "location": "file",
                    "summary": ".legacy file; verify it is superseded and remove",
                    "excerpt": str(legacy),
                    "proposed_fix": None,
                }
            )
        # Check for orphaned .md files in references/
        # Search by basename across ALL scanned .md files in ALL target skills
        # (cross-skill consumption is legitimate).
        refs_dir = skill_dir / "references"
        if not refs_dir.is_dir():
            continue
        for md_file in refs_dir.rglob("*.md"):
            basename = md_file.name
            if basename not in all_prose:
                seq[0] += 1
                findings.append(
                    {
                        "id": f"f-c4-{seq[0]:03d}",
                        "criterion": "C4",
                        "severity": "open-question",
                        "class": "mechanical",
                        "file": fwd(md_file, root),
                        "location": "file",
                        "summary": f"possibly orphaned: '{basename}' not mentioned by name in any scanned .md across all target skills",
                        "excerpt": str(md_file),
                        "proposed_fix": None,
                    }
                )
    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    script_path = Path(__file__).resolve()
    # Script is at <root>/.liang/goal/preflight.py -> root = script_path.parent.parent.parent
    default_root = script_path.parent.parent.parent

    parser = argparse.ArgumentParser(description="preflight audit for liang skill families")
    parser.add_argument("--root", type=Path, default=default_root, help="liang-skills root")
    parser.add_argument(
        "--targets",
        default="liang-quest-*,liang-brainstorm-*",
        help="comma-separated glob patterns for skill dirs",
    )
    parser.add_argument("--out", type=Path, default=None, help="output directory")
    args = parser.parse_args()

    root: Path = args.root.resolve()
    if not root.is_dir():
        print(f"ERROR: root not found: {root}", file=sys.stderr)
        return 2

    ledger_path = script_path.parent / "drift-ledger.md"
    criteria_path = script_path.parent / "criteria.md"
    for p in (ledger_path, criteria_path):
        if not p.exists():
            print(f"ERROR: required file not found: {p}", file=sys.stderr)
            return 2

    try:
        suppressions, pair_suppressions = load_suppressions(ledger_path)
    except Exception as exc:
        print(f"ERROR: failed to parse drift-ledger.md: {exc}", file=sys.stderr)
        return 2

    # Output directory
    if args.out is None:
        ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        out_dir = script_path.parent / "runs" / f"run-{ts}"
    else:
        out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Collect target skill dirs
    target_globs = [g.strip() for g in args.targets.split(",") if g.strip()]
    skill_dirs = collect_skill_dirs(root, target_globs)
    if not skill_dirs:
        print(f"ERROR: no skill dirs matched {target_globs} under {root}", file=sys.stderr)
        return 2

    # Collect all scan files
    all_scan_files: list[Path] = []
    for sd in skill_dirs:
        all_scan_files.extend(collect_scan_files(sd))

    all_findings: list[dict] = []
    all_suppressed: list[dict] = []

    # Stable ordering: sort by file then by check
    all_scan_files_sorted = sorted(all_scan_files, key=lambda p: fwd(p, root))

    # Run checks with per-criterion sequence counters
    seq_c1 = [0]
    seq_c2 = [0]
    seq_c3 = [0]
    seq_c4 = [0]

    # C2: citation resolution
    c2_cit = check_citation_resolution(all_scan_files_sorted, root, seq_c2)
    all_findings.extend(c2_cit)

    # C2: attribution anchors
    c2_attr = check_attribution_anchors(all_scan_files_sorted, root, seq_c2)
    all_findings.extend(c2_attr)

    # C2: dc uniqueness
    c2_dc = check_dc_uniqueness(all_scan_files_sorted, root, seq_c2)
    all_findings.extend(c2_dc)

    # C3: vendor model grep
    c3_findings, c3_suppressed = check_vendor_model(
        all_scan_files_sorted, root, suppressions, seq_c3
    )
    all_findings.extend(c3_findings)
    all_suppressed.extend(c3_suppressed)

    # C1: shingle duplication
    c1_findings, c1_suppressed = check_shingle_duplication(
        all_scan_files_sorted, root, seq_c1, pair_suppressions
    )
    all_findings.extend(c1_findings)
    all_suppressed.extend(c1_suppressed)

    # C4: line budget
    c4_budget = check_line_budget(all_scan_files_sorted, root, seq_c4)
    all_findings.extend(c4_budget)

    # C4: dead files
    c4_dead = check_dead_files(skill_dirs, all_scan_files_sorted, root, seq_c4)
    all_findings.extend(c4_dead)

    # Compute stats
    stats = {
        "files_scanned": len(all_scan_files),
        "critical": sum(1 for f in all_findings if f["severity"] == "critical"),
        "advisory": sum(1 for f in all_findings if f["severity"] == "advisory"),
        "open_question": sum(1 for f in all_findings if f["severity"] == "open-question"),
        "judgment_needed": sum(
            1 for f in all_findings if f.get("class") == "judgment-needed"
        ),
        "suppressed": len(all_suppressed),
    }

    output = {
        "findings": all_findings,
        "suppressed": all_suppressed,
        "stats": stats,
    }

    findings_path = out_dir / "findings.yaml"
    findings_path.write_text(
        yaml.dump(output, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )

    # Counts by criterion
    by_criterion: dict[str, int] = {}
    for f in all_findings:
        k = f["criterion"]
        by_criterion[k] = by_criterion.get(k, 0) + 1

    # Print summary table
    print(f"\npreflight.py — liang skill family audit")
    print(f"Root   : {root}")
    print(f"Skills : {', '.join(sd.name for sd in skill_dirs)}")
    print(f"Files  : {len(all_scan_files)} scanned")
    print(f"Run dir: {out_dir}")
    print()
    print(f"{'Check':<35} {'Count':>6}  {'Severity'}")
    print("-" * 60)
    rows = [
        ("C1  shingle-duplication",  by_criterion.get("C1", 0), "critical"),
        ("C1  shingle-dup-suppressed", len(c1_suppressed),       "(suppressed)"),
        ("C2  citation-resolution",  len(c2_cit),               "critical"),
        ("C2  attribution-anchors",  len(c2_attr),               "critical"),
        ("C2  dc-uniqueness",        len(c2_dc),                 "open-question"),
        ("C3  vendor-model-grep",    len(c3_findings),           "critical"),
        ("C3  vendor-model-suppressed", len(c3_suppressed),      "(suppressed)"),
        ("C4  line-budget",          len(c4_budget),             "advisory"),
        ("C4  dead-files",           len(c4_dead),               "advisory/open-q"),
    ]
    for name, count, sev in rows:
        print(f"  {name:<33} {count:>6}  {sev}")
    print("-" * 60)
    print(f"  {'TOTAL findings':<33} {len(all_findings):>6}")
    print(f"  {'critical':<33} {stats['critical']:>6}")
    print(f"  {'advisory':<33} {stats['advisory']:>6}")
    print(f"  {'open-question':<33} {stats['open_question']:>6}")
    print(f"  {'suppressed':<33} {stats['suppressed']:>6}")
    print()
    print(f"Findings written to: {findings_path}")

    return 1 if stats["critical"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
