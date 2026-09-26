"""
preflight.py — deterministic audit for the liang skill families.

Generic rules: _family-audit/criteria-common.md. Family data: every
liang-*-core/references/family/criteria.md (its `family:` block) and drift-ledger.md.
A check whose data key a family does not declare is skipped for that family.

Zero model involvement; zero writes outside the run output directory.
Python 3.11, stdlib + pyyaml only.
"""
from __future__ import annotations

import argparse
import datetime
import fnmatch
import re
import sys
from pathlib import Path

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


# Phrases a convention requires verbatim, ledger-ruled. Filled in main():
#   COMMON_PHRASES  — cross-family ledger `convention_lines`, applied to every file
#   FAMILY_PHRASES  — family block `convention_lines`, applied to that family's skills only
COMMON_PHRASES: list[str] = []
FAMILY_PHRASES: dict[str, list[str]] = {}
_break_seq = [0]


def _cut_phrases(body: str, phrases: list[str]) -> str:
    """Replace each phrase with a one-off token, so no shingle spans it and nothing else on its line is lost."""
    for phrase in phrases:
        while phrase in body:
            _break_seq[0] += 1
            body = body.replace(phrase, f" brk{_break_seq[0]}x ", 1)
    return body


def tokenize(text: str, phrases: list[str] | None = None) -> list[str]:
    """Lowercase words (strip punctuation). Skips frontmatter.

    Inline-code spans whose content looks like a file path or section
    citation are removed before tokenisation so that identical citations
    of the same canonical reference do not inflate the shingle count.
    """
    body, _ = strip_frontmatter(text)
    # Headings and convention phrases are structure the family mandates, not restated contracts.
    body = "\n".join(line for line in body.splitlines() if not line.lstrip().startswith("#"))
    body = _cut_phrases(body, COMMON_PHRASES + (phrases or []))
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

def load_suppressions(ledger_path: Path, cross_family: bool = False) -> tuple[list[dict], list[dict]]:
    """Return (suppressions, pair_suppressions) from drift-ledger."""
    text = read_text(ledger_path)
    # Extract fenced yaml block
    m = re.search(r"```yaml\n(.*?)```", text, re.DOTALL)
    if not m:
        return [], []
    parsed = yaml.safe_load(m.group(1))
    if not parsed:
        return [], []
    sups = parsed.get("suppressions") or []
    pair_sups = parsed.get("pair_suppressions") or []
    if cross_family:  # a family ledger declares its phrases in its family block, not here
        COMMON_PHRASES.extend(c["phrase"] for c in parsed.get("convention_lines") or [] if c.get("phrase"))
    return sups, pair_sups


def check_ledger_ids(ledgers: list[Path], root: Path, seq: list[int]) -> list[dict]:
    """C2: dv ids are unique across every ledger."""
    seen: dict[str, str] = {}
    out = []
    for ledger in ledgers:
        rel = fwd(ledger, root)
        for dv in re.findall(r"^\|\s*(dv\d{3})\s*\|", read_text(ledger), re.MULTILINE):
            if dv in seen:
                out.append(finding(seq, "C2", "mechanical", rel, "table",
                                   f"ledger id {dv} already used in {seen[dv]}"))
            seen[dv] = rel
    for ledger in ledgers:
        m = re.search(r"```yaml\n(.*?)```", read_text(ledger), re.DOTALL)
        for dv in sorted(set(re.findall(r"\bid:\s*(dv\d{3})", m.group(1) if m else ""))):
            if dv not in seen:
                out.append(finding(seq, "C2", "mechanical", fwd(ledger, root), "yaml block",
                                   f"suppression uses {dv}, which has no ruling row in any ledger table"))
    return out


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
            if FAMILY_DIR in p.relative_to(skill_dir).parts:
                continue
            files.append(p)
    return files


def collect_script_files(skill_dir: Path) -> list[Path]:
    """*.js / *.py inside a skill dir — C3 covers scripts too."""
    files: list[Path] = []
    for pattern in ("*.js", "*.py"):
        for p in sorted(skill_dir.rglob(pattern)):
            if "__pycache__" in p.parts:
                continue
            files.append(p)
    return files


# ---------------------------------------------------------------------------
# Family data
# ---------------------------------------------------------------------------

FAMILY_DIR = "family"


def load_families(root: Path) -> list[dict]:
    """Read the `family:` block from every liang-*-core/references/family/criteria.md."""
    families: list[dict] = []
    for crit in sorted(root.glob("liang-*-core/references/family/criteria.md")):
        m = re.search(r"```yaml\n(family:.*?)```", read_text(crit), re.DOTALL)
        if not m:
            continue
        block = (yaml.safe_load(m.group(1)) or {}).get("family") or {}
        if block.get("name") and block.get("members_glob"):
            block["_ledger"] = crit.parent / "drift-ledger.md"
            families.append(block)
    return families


def family_members(family: dict, skill_dirs: list[Path]) -> list[Path]:
    return [sd for sd in skill_dirs if fnmatch.fnmatch(sd.name, family["members_glob"])]


def h2_sections(text: str) -> dict[str, str]:
    """Map each H2 heading (as written) to the text under it."""
    sections: dict[str, str] = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.*)", line)
        if m:
            current = m.group(1).strip()
            sections[current] = ""
        elif current is not None:
            sections[current] += line + "\n"
    return sections


def finding(seq: list[int], criterion: str, klass: str, file: str, location: str,
            summary: str, excerpt: str = "", severity: str = "critical") -> dict:
    seq[0] += 1
    return {
        "id": f"f-{criterion.lower()}-{seq[0]:03d}",
        "criterion": criterion,
        "severity": severity,
        "class": klass,
        "file": file,
        "location": location,
        "summary": summary,
        "excerpt": excerpt,
        "proposed_fix": None,
    }


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
                        "summary": "line-number attribution; migrate to section-anchor form (<file> § <heading>)",
                        "excerpt": line.strip(),
                        "proposed_fix": None,
                    }
                )

    # Anchor heading-existence check
    # Pattern: <file> § <heading> or `<file>` § <heading>
    heading_ref_pat = re.compile(
        r"`?([a-z][a-z0-9/._-]+\.md)`?\s*§\s*((?:[^\n`()\[\],;.]|\.(?=\S))+?)(?=\s+per\s+\w+|\s*$|\s*[`(),;\]]|\.(?:\s|$))",
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
                heading = m.group(2).strip().rstrip(".,;:").lower()
                if not heading:
                    continue  # heading written in backticks — not machine-checkable
                # Resolve cited file
                candidate = root / cited_file_str
                if not candidate.exists():
                    candidate = skill_root / cited_file_str
                if not candidate.exists():
                    continue  # Already caught by citation-resolution
                actual_headings = headings_in_file(candidate)
                # a citation may name a heading by its leading words ("Model Routing Extensions"
                # for "Model Routing Extensions (optional)")
                # numbered sections are cited by number alone: "§7c", "§ 2a"
                if heading[0].isdigit():
                    token = re.escape(heading.split()[0])
                    if any(re.match(r"§?\s*" + token + r"(?![a-z0-9])", h) for h in actual_headings):
                        continue
                # Prose may follow the heading on the same line, so try every leading run of the
                # captured words: one word must equal a heading, two or more may prefix one.
                cited = heading.split()
                matched = any(
                    " ".join(cited[:k]) in actual_headings
                    or (k >= 2 and any(h.startswith(" ".join(cited[:k])) for h in actual_headings))
                    for k in range(len(cited), 0, -1)
                )
                if not matched:
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


def check_vendor_model(
    files: list[Path],
    root: Path,
    suppressions: list[dict],
    seq: list[int],
) -> tuple[list[dict], list[dict]]:
    findings: list[dict] = []
    suppressed: list[dict] = []
    vendor_pat = re.compile(
        r"\b(sonnet|opus|haiku|claude-(?:\d|opus|sonnet|haiku|fable|mythos|instant)[a-z0-9.\-]*|deepseek-[a-z0-9.\-]+|gpt-[a-z0-9.\-]+|gemini-[a-z0-9.\-]+)\b",
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
        rel = fwd(fpath, root)
        skill_dir_name = rel.split("/")[0]
        words = tokenize(text, FAMILY_PHRASES.get(skill_dir_name))
        sh = shingles(words)
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


def check_line_budget(
    files: list[Path], root: Path, seq: list[int], suppressions: list[dict] | None = None,
    suppressed: list[dict] | None = None,
) -> list[dict]:
    findings: list[dict] = []
    budgets = [s for s in (suppressions or []) if s.get("check") == "line-budget"]
    for fpath in files:
        if fpath.name != "SKILL.md":
            continue
        text = read_text(fpath)
        lines = text.splitlines()
        count = len(lines)
        rel = fwd(fpath, root)
        rule = max((s for s in budgets if fnmatch.fnmatch(rel, s.get("file_glob", ""))),
                   key=lambda s: s.get("max_lines", 0), default=None)
        if rule and 280 < count <= rule.get("max_lines", 0):
            if suppressed is not None:
                seq[0] += 1
                suppressed.append({"id": f"f-c4-{seq[0]:03d}", "ledger": rule.get("id", ""),
                                   "summary": f"line-budget suppressed: {rel} at {count} lines <= ruled max_lines={rule.get('max_lines')}"})
        elif count > 280:
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
            if FAMILY_DIR in md_file.relative_to(skill_dir).parts:
                continue
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
# Family checks (C3 scripts, C5a, C6, C7, C8, C9)
# ---------------------------------------------------------------------------

def check_script_models(
    script_files: list[Path], root: Path, suppressions: list[dict], seq: list[int]
) -> tuple[list[dict], list[dict]]:
    """C3: no vendor model name in .js/.py inside a skill dir."""
    findings: list[dict] = []
    suppressed: list[dict] = []
    vendor_pat = re.compile(
        r"""['"](sonnet|opus|haiku|claude-(?:\d|opus|sonnet|haiku|fable|mythos|instant)[a-z0-9.\-]*|deepseek-[a-z0-9.\-]+|gpt-[a-z0-9.\-]+|gemini-[a-z0-9.\-]+)['"]""",
        re.IGNORECASE,
    )
    for fpath in script_files:
        rel = fwd(fpath, root)
        for lineno, line in enumerate(read_text(fpath).splitlines(), 1):
            for m in vendor_pat.finditer(line):
                entry = finding(seq, "C3", "mechanical", rel, f"line {lineno}",
                                f"vendor model literal in script: {m.group(0)}", line.strip()[:200])
                flag, dv_id = is_suppressed("vendor-model-grep", rel, m.group(1), suppressions)
                if flag:
                    suppressed.append({"id": entry["id"], "ledger": dv_id})
                else:
                    findings.append(entry)
    return findings, suppressed


def check_registry(root: Path, family: dict, members: list[Path], seq: list[int]) -> list[dict]:
    """C7: every member is named in the registry file."""
    reg = family.get("registry_file")
    if not reg:
        return []
    table = ""
    for head, body in h2_sections(read_text(root / reg)).items():
        if head.lower().startswith("family skills"):
            table = body
    core = family.get("core", "")
    sub_pat = re.compile(re.escape(core) + r"/references/([a-z-]+)/")
    out = []
    for sd in members:
        row = next((ln for ln in table.splitlines() if f"**{sd.name}**" in ln), None)
        if row is None:
            out.append(finding(seq, "C7", "structural", reg, "## Family Skills",
                               f"family member not registered: {sd.name}"))
            continue
        if sd.name == core:
            continue
        sections = h2_sections(read_text(sd / "SKILL.md"))
        listed = ""
        for head, body in sections.items():
            if head.lower().startswith("reference files"):
                listed = body
        reads = set(sub_pat.findall(listed)) - {FAMILY_DIR}
        claimed = set(re.findall(r"`([a-z-]+)/`", row.split("|")[-2]))
        if reads != claimed:
            out.append(finding(seq, "C7", "mechanical", reg, "## Family Skills",
                               f"{sd.name}: registry says it reads {sorted(claimed)}, its Reference Files lists {sorted(reads)}"))
    return out


def check_project_keys(
    root: Path, family: dict, members: list[Path], seq: list[int]
) -> list[dict]:
    """C7: every models.<key> / claude_mode.<key> a member reads is documented in the contract."""
    contract = family.get("project_yaml_contract")
    if not contract:
        return []
    contract_path = root / contract
    contract_text = read_text(contract_path)
    words = set()
    for block in re.findall(r"```yaml\n(.*?)```", contract_text, re.DOTALL):
        try:
            models = (yaml.safe_load(block) or {}).get("models")
        except (yaml.YAMLError, AttributeError):
            continue
        if isinstance(models, dict):
            words.add("claude_mode")
            words.update(models)
            if isinstance(models.get("claude_mode"), dict):
                words.update(models["claude_mode"])
    key_pat = re.compile(r"\b(?:models|claude_mode)\.([a-z_]+)(\*?)")
    out = []
    seen: set[tuple[str, str]] = set()
    for sd in members:
        for fpath in collect_scan_files(sd):  # prose only: scripts read keys through code, not dotted paths
            if fpath == contract_path:
                continue
            rel = fwd(fpath, root)
            for lineno, line in enumerate(read_text(fpath).splitlines(), 1):
                for m in key_pat.finditer(line):
                    key, star = m.group(1), m.group(2)
                    is_prefix = bool(star) or key.endswith("_")
                    documented = (any(w.startswith(key) for w in words) if is_prefix
                                  else key in words)
                    if documented or (rel, key) in seen:
                        continue
                    seen.add((rel, key))
                    out.append(finding(seq, "C7", "structural", rel, f"line {lineno}",
                                       f"project.yaml key not documented in {contract}: {key}{star}",
                                       line.strip()[:200]))
    return out


def check_skeleton(root: Path, family: dict, members: list[Path], seq: list[int]) -> list[dict]:
    """C8: required H2 headings present (prefix match)."""
    skel = family.get("skeleton") or {}
    required = skel.get("required_h2") or []
    exempt = set(skel.get("exempt") or [])
    out = []
    for sd in members:
        if sd.name in exempt:
            continue
        skill_md = sd / "SKILL.md"
        heads = [h.lower() for h in h2_sections(read_text(skill_md))]
        for req in required:
            if not any(h.startswith(req.lower()) for h in heads):
                out.append(finding(seq, "C8", "structural", fwd(skill_md, root), "H2 sections",
                                   f"missing required section: ## {req}"))
    return out


def check_core_read_checklist(
    root: Path, family: dict, members: list[Path], seq: list[int]
) -> list[dict]:
    """C5(a): the checklist section lists every core file the SKILL.md cites, plus a fail-stop line."""
    cfg = family.get("core_read_checklist")
    core = family.get("core")
    if not cfg or not core:
        return []
    exempt = set((family.get("skeleton") or {}).get("exempt") or [])
    cite_pat = re.compile(re.escape(core) + r"/references/(?!" + FAMILY_DIR + r"/)[^\s`'\")]+\.md")
    out = []
    for sd in members:
        if sd.name in exempt:
            continue
        skill_md = sd / "SKILL.md"
        text = read_text(skill_md)
        cited = set(cite_pat.findall(text))
        if not cited:
            continue
        rel = fwd(skill_md, root)
        section = ""
        for head, body in h2_sections(text).items():
            if head.lower().startswith(cfg["section"].lower()):
                section = body
        for path in sorted(cited - set(cite_pat.findall(section))):
            out.append(finding(seq, "C5", "mechanical", rel, f"## {cfg['section']}",
                               f"core file cited in body but not listed in the checklist section: {path}"))
        if cfg.get("fail_stop_phrase", "").lower() not in section.lower():
            out.append(finding(seq, "C5", "mechanical", rel, f"## {cfg['section']}",
                               f"checklist section lacks the fail-stop line (\"{cfg['fail_stop_phrase']}\")"))
    return out


def check_topology(
    root: Path, family: dict, scan_files: list[Path], seq: list[int]
) -> list[dict]:
    """C9: a ladder statement outside the topology file is one line that cites it."""
    topo = family.get("topology_file")
    rungs = family.get("ladder_rungs") or []
    if not topo or len(rungs) < 2:
        return []
    arrow = r".*(?:→|->).*"
    ladder_pat = re.compile(arrow.join(re.escape(r) for r in rungs), re.IGNORECASE)
    topo_name = Path(topo).name
    out = []
    if not (root / topo).exists():
        out.append(finding(seq, "C9", "structural", topo, "file", "topology file missing"))
    for fpath in scan_files:
        rel = fwd(fpath, root)
        for lineno, line in enumerate(read_text(fpath).splitlines(), 1):
            if ladder_pat.search(line) and topo_name not in line:
                out.append(finding(seq, "C9", "mechanical", rel, f"line {lineno}",
                                   f"ladder restated without citing {topo_name}", line.strip()[:200]))
    return out


def check_decisions(root: Path, family: dict, seq: list[int]) -> list[dict]:
    """C6: the decision log exists and its ids are unique."""
    dec = family.get("decisions_file")
    if not dec:
        return []
    path = root / dec
    if not path.exists():
        return [finding(seq, "C6", "structural", dec, "file", "decision log missing")]
    ids = re.findall(r"^\|\s*([a-z]{2}\d{3})\s*\|", read_text(path), re.MULTILINE)
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    return [finding(seq, "C6", "mechanical", dec, "table", f"duplicate decision id: {i}") for i in dupes]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    script_path = Path(__file__).resolve()
    # Script is at <root>/_family-audit/preflight.py -> root = script_path.parent.parent
    default_root = script_path.parent.parent

    parser = argparse.ArgumentParser(description="preflight audit for liang skill families")
    parser.add_argument("--root", type=Path, default=default_root, help="liang-skills root")
    parser.add_argument(
        "--targets",
        default=None,
        help="comma-separated glob patterns for skill dirs (default: every family's members_glob)",
    )
    parser.add_argument("--out", type=Path, default=None, help="output directory")
    args = parser.parse_args()

    root: Path = args.root.resolve()
    if not root.is_dir():
        print(f"ERROR: root not found: {root}", file=sys.stderr)
        return 2

    common_ledger = script_path.parent / "drift-ledger.md"
    common_criteria = script_path.parent / "criteria-common.md"
    for p in (common_ledger, common_criteria):
        if not p.exists():
            print(f"ERROR: required file not found: {p}", file=sys.stderr)
            return 2

    families = load_families(root)
    if not families:
        print("ERROR: no liang-*-core/references/family/criteria.md with a family: block", file=sys.stderr)
        return 2

    for fam in families:
        for sd in collect_skill_dirs(root, [fam["members_glob"]]):
            FAMILY_PHRASES[sd.name] = list(fam.get("convention_lines") or [])

    suppressions: list[dict] = []
    pair_suppressions: list[dict] = []
    ledgers = [common_ledger] + [f["_ledger"] for f in families]
    for ledger in ledgers:
        if not ledger.exists():
            print(f"ERROR: required file not found: {ledger}", file=sys.stderr)
            return 2
        try:
            sups, pairs = load_suppressions(ledger, cross_family=(ledger == common_ledger))
        except Exception as exc:
            print(f"ERROR: failed to parse {ledger}: {exc}", file=sys.stderr)
            return 2
        suppressions.extend(sups)
        pair_suppressions.extend(pairs)

    # C3 alias home: the one file per family that may name Claude tier aliases. Built from the
    # family block, so no ledger entry can widen it.
    if any(s.get("check") == "vendor-model-grep" for s in suppressions):
        print("ERROR: vendor-model-grep suppressions are not allowed in a ledger; "
              "declare alias_home / alias_ledger_id in the family block", file=sys.stderr)
        return 2
    for fam in families:
        if fam.get("alias_home"):
            suppressions.append({"id": fam.get("alias_ledger_id", ""), "check": "vendor-model-grep",
                                 "file_glob": fam["alias_home"], "pattern": "haiku|sonnet|opus"})

    # Output directory
    if args.out is None:
        ts = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        out_dir = root / ".liang" / "goal" / "runs" / f"run-{ts}"
    else:
        out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Collect target skill dirs
    targets = args.targets or ",".join(f["members_glob"] for f in families)
    target_globs = [g.strip() for g in targets.split(",") if g.strip()]
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
    seq_fam = {c: [0] for c in ("C5", "C6", "C7", "C8", "C9")}

    # C2: citation resolution
    c2_cit = check_citation_resolution(all_scan_files_sorted, root, seq_c2)
    all_findings.extend(c2_cit)

    # C2: attribution anchors
    c2_attr = check_attribution_anchors(all_scan_files_sorted, root, seq_c2)
    all_findings.extend(c2_attr)

    # C2: ledger ids unique across ledgers
    c2_ids = check_ledger_ids(ledgers, root, seq_c2)
    all_findings.extend(c2_ids)

    # C3: vendor model grep
    c3_findings, c3_suppressed = check_vendor_model(
        all_scan_files_sorted, root, suppressions, seq_c3
    )
    all_findings.extend(c3_findings)
    all_suppressed.extend(c3_suppressed)

    # C3: scripts
    script_files = sorted((p for sd in skill_dirs for p in collect_script_files(sd)),
                          key=lambda p: fwd(p, root))
    c3_script, c3_script_sup = check_script_models(script_files, root, suppressions, seq_c3)
    all_findings.extend(c3_script)
    all_suppressed.extend(c3_script_sup)

    # Family checks
    fam_findings: list[dict] = []
    for family in families:
        members = family_members(family, skill_dirs)
        if not members:
            continue
        member_files = [p for p in all_scan_files_sorted
                        if any(p.is_relative_to(sd) for sd in members)]
        fam_findings += check_core_read_checklist(root, family, members, seq_fam["C5"])
        fam_findings += check_decisions(root, family, seq_fam["C6"])
        fam_findings += check_registry(root, family, members, seq_fam["C7"])
        fam_findings += check_project_keys(root, family, members, seq_fam["C7"])
        fam_findings += check_skeleton(root, family, members, seq_fam["C8"])
        fam_findings += check_topology(root, family, member_files, seq_fam["C9"])
    all_findings.extend(fam_findings)

    # C1: shingle duplication
    c1_findings, c1_suppressed = check_shingle_duplication(
        all_scan_files_sorted, root, seq_c1, pair_suppressions
    )
    all_findings.extend(c1_findings)
    all_suppressed.extend(c1_suppressed)

    # C4: line budget
    c4_budget = check_line_budget(all_scan_files_sorted, root, seq_c4, suppressions, all_suppressed)
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
    print(f"\npreflight.py - liang skill family audit")
    print(f"Families: {', '.join(f['name'] for f in families)}")
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
        ("C2  ledger-id-uniqueness", len(c2_ids),                "critical"),
        ("C3  vendor-model-grep",    len(c3_findings),           "critical"),
        ("C3  vendor-model-in-script", len(c3_script),           "critical"),
        ("C3  vendor-model-suppressed", len(c3_suppressed),      "(suppressed)"),
        ("C4  line-budget",          len(c4_budget),             "advisory"),
        ("C4  dead-files",           len(c4_dead),               "advisory/open-q"),
        ("C5  core-read-checklist",  by_criterion.get("C5", 0),  "critical"),
        ("C6  decision-log",         by_criterion.get("C6", 0),  "critical"),
        ("C7  registry + keys",      by_criterion.get("C7", 0),  "critical"),
        ("C8  section-skeleton",     by_criterion.get("C8", 0),  "critical"),
        ("C9  topology-citation",    by_criterion.get("C9", 0),  "critical"),
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
