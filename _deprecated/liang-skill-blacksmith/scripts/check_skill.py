#!/usr/bin/env python3
"""Mechanical rubric checks for liang-skill-blacksmith.

Runs the deterministic subset of the rubric against one or more SKILL.md files
and prints a JSON array of finding records to stdout. The judgment checks
(L2-02 passive voice, L3-* cross-skill consistency) are NOT run here; the
inspecting agent performs those directly.

Checks implemented: L1-01, L1-02, L1-03, L1-04, L2-01, L2-03, L2-04.

Usage:
    python check_skill.py <skill.md> [<skill.md> ...]

Output: JSON array on stdout. Each finding:
    {check_id, layer, severity, fixable, file, line, section,
     description, evidence}

Exit codes: 0 = ran successfully (with or without findings), 2 = usage error.
"""

import json
import re
import sys

# Canonical H2 sections expected in workflow-style SKILL.md files.
# Value = accepted alias names (normalized form, substring-matched).
CANONICAL_SECTIONS = {
    "core contract": [],
    "activation": [],
    "startup flow": ["execution flow"],
    "boundaries": [],
    "failure modes": ["error handling"],
    "visual tone": [],
    "relationship to other skills": [],
    "reference files": ["reference index"],
}

# Known optional sections that do not count as orphans (L1-03).
OPTIONAL_SECTIONS = [
    "terminology",
    "design principle",
    "activation checklist",
    "non-goals",
    "what this skill provides",
    "what this skill does",
    "composition mechanism",
]

# Sections whose prose counts as directives for the L2 language checks.
DIRECTIVE_HEADINGS = [
    "boundaries", "core contract", "activation", "failure modes",
    "hard stops", "non-goals", "error handling",
]

VAGUE_PATTERNS = [
    r"\bvarious\b", r"\bsome\b", r"\betc\.?", r"\band so on\b", r"\bthings\b",
    r"\bstuff\b", r"\bmany\b", r"\bseveral\b", r"\ba number of\b", r"\ba lot of\b",
]

STOPWORDS = set(
    """the a an and or but if then else when at by for with about against
    between into through during before after above below to from up down in
    out on off over under again further is are was were be been being do does
    did doing have has had having it its this that these those of as not no
    never all any""".split()
)

CHECK_META = {
    "L1-01": (1, "critical", True,  "Valid YAML frontmatter"),
    "L1-02": (1, "advisory", False, "Required sections present"),
    "L1-03": (1, "advisory", True,  "No orphan sections"),
    "L1-04": (1, "advisory", True,  "Consistent heading hierarchy"),
    "L2-01": (2, "advisory", True,  "Long sentences"),
    "L2-03": (2, "advisory", True,  "Vague quantifiers"),
    "L2-04": (2, "advisory", True,  "Duplicate phrasing"),
}


def normalize(text):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def make_finding(check_id, path, line, section, description, evidence):
    layer, severity, fixable, _name = CHECK_META[check_id]
    return {
        "check_id": check_id,
        "layer": layer,
        "severity": severity,
        "fixable": fixable,
        "file": path,
        "line": line,
        "section": section,
        "description": description,
        "evidence": evidence.strip()[:300],
    }


def parse_document(lines):
    """Classify each line: frontmatter, fence, table, heading, prose."""
    n = len(lines)
    fm_start = fm_end = None
    if lines and lines[0].strip() == "---":
        for i in range(1, n):
            if lines[i].strip() == "---":
                fm_start, fm_end = 0, i
                break
    in_fence = False
    kinds = []
    headings = []  # (level, text, line_number 1-based)
    for i, raw in enumerate(lines):
        if fm_start is not None and fm_start <= i <= fm_end:
            kinds.append("frontmatter")
            continue
        stripped = raw.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            kinds.append("fence")
            continue
        if in_fence:
            kinds.append("fence")
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            kinds.append("heading")
            headings.append((len(m.group(1)), m.group(2).strip(), i + 1))
            continue
        if stripped.startswith("|"):
            kinds.append("table")
            continue
        kinds.append("prose")
    return kinds, headings, (fm_start, fm_end)


def section_of(headings, line_no):
    """Nearest H2 at or above line_no."""
    current = "(preamble)"
    for level, text, hline in headings:
        if hline > line_no:
            break
        if level == 2:
            current = text
    return current


def extract_sentences(lines, kinds, headings):
    """Yield (sentence, line_number, h2_section). Bullets are standalone units;
    consecutive plain prose lines join into paragraphs."""
    units = []  # (text, start_line)
    buf, buf_line = [], None
    for i, raw in enumerate(lines):
        if kinds[i] != "prose" or not raw.strip():
            if buf:
                units.append((" ".join(buf), buf_line))
                buf, buf_line = [], None
            continue
        stripped = raw.strip()
        if re.match(r"^([-*+]|\d+\.)\s", stripped):
            if buf:
                units.append((" ".join(buf), buf_line))
                buf, buf_line = [], None
            units.append((re.sub(r"^([-*+]|\d+\.)\s+", "", stripped), i + 1))
        else:
            if not buf:
                buf_line = i + 1
            buf.append(stripped)
    if buf:
        units.append((" ".join(buf), buf_line))
    for text, line_no in units:
        for sent in re.split(r"(?<=[.!?])\s+", text):
            sent = sent.strip()
            if sent:
                yield sent, line_no, section_of(headings, line_no)


def strip_inline_code(text):
    return re.sub(r"`[^`]*`", "", text)


def word_count(text):
    return len(re.findall(r"\b[\w'-]+\b", text))


def is_directive_section(section):
    norm = normalize(section)
    return any(d in norm for d in DIRECTIVE_HEADINGS)


def check_file(path):
    findings = []
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
    except OSError as exc:
        return [make_finding("L1-01", path, 1, "(file)",
                             f"Cannot read file: {exc}", "")]

    kinds, headings, (fm_start, fm_end) = parse_document(lines)
    h2_headings = [(t, ln) for lvl, t, ln in headings if lvl == 2]

    # L1-01: frontmatter
    if fm_start is None:
        findings.append(make_finding(
            "L1-01", path, 1, "(frontmatter)",
            "No YAML frontmatter block found.", lines[0] if lines else ""))
    else:
        fm_text = "\n".join(lines[fm_start + 1:fm_end])
        parsed = None
        try:
            import yaml  # optional; minimal field checks run regardless
            parsed = yaml.safe_load(fm_text)
            if not isinstance(parsed, dict):
                findings.append(make_finding(
                    "L1-01", path, 1, "(frontmatter)",
                    "Frontmatter does not parse to a YAML mapping.", fm_text))
                parsed = {}
        except ImportError:
            pass
        except Exception as exc:
            findings.append(make_finding(
                "L1-01", path, 1, "(frontmatter)",
                f"Frontmatter is not valid YAML: {exc}", fm_text))
            parsed = {}
        for field in ("name", "description"):
            if parsed is not None:
                ok = bool(str(parsed.get(field) or "").strip())
            else:
                ok = bool(re.search(
                    rf"^{field}\s*:\s*\S", fm_text, re.MULTILINE))
            if not ok:
                findings.append(make_finding(
                    "L1-01", path, 1, "(frontmatter)",
                    f"Frontmatter field `{field}` is missing or empty.",
                    fm_text))

    # L1-02: required sections (advisory, report-only)
    norm_h2 = [(normalize(t), t, ln) for t, ln in h2_headings]
    for canonical, aliases in CANONICAL_SECTIONS.items():
        accepted = [canonical] + aliases
        if not any(any(a in nh for a in accepted) for nh, _t, _ln in norm_h2):
            findings.append(make_finding(
                "L1-02", path, 1, "(document)",
                f"Canonical section `{canonical}` not found "
                f"(accepted aliases: {', '.join(accepted)}).",
                "; ".join(t for t, _ln in h2_headings) or "(no H2 headings)"))

    # L1-03: orphan sections
    recognized = (
        [a for c, al in CANONICAL_SECTIONS.items() for a in [c] + al]
        + OPTIONAL_SECTIONS
    )
    for nh, text, ln in norm_h2:
        if not any(r in nh for r in recognized):
            findings.append(make_finding(
                "L1-03", path, ln, text,
                f"H2 heading `{text}` is not a recognized canonical or "
                "optional section. Mark it skill-specific via "
                "rubric-override.md or map it to a standard section.", text))

    # L1-04: heading hierarchy
    prev_level = None
    for level, text, ln in headings:
        if prev_level is not None and level > prev_level + 1:
            findings.append(make_finding(
                "L1-04", path, ln, section_of(headings, ln),
                f"Heading level jumps from H{prev_level} to H{level} "
                f"at `{text}`.", text))
        prev_level = level

    # Sentences for L2 checks
    sentences = list(extract_sentences(lines, kinds, headings))

    # L2-01 + L2-03: directive sections only
    for sent, ln, section in sentences:
        if not is_directive_section(section):
            continue
        plain = strip_inline_code(sent)
        wc = word_count(plain)
        if wc > 40:
            findings.append(make_finding(
                "L2-01", path, ln, section,
                f"Sentence has {wc} words (limit 40) in a directive section.",
                sent))
        for pattern in VAGUE_PATTERNS:
            m = re.search(pattern, plain, re.IGNORECASE)
            if m:
                findings.append(make_finding(
                    "L2-03", path, ln, section,
                    f"Vague quantifier `{m.group(0)}` in a directive section.",
                    sent))

    # L2-04: duplicate phrasing, whole file, sentences > 10 words
    candidates = []
    for sent, ln, section in sentences:
        plain = strip_inline_code(sent)
        if word_count(plain) > 10:
            tokens = frozenset(
                w for w in re.findall(r"\b[\w'-]+\b", plain.lower())
                if w not in STOPWORDS)
            if tokens:
                candidates.append((sent, ln, tokens))
    reported = set()
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            a, b = candidates[i], candidates[j]
            inter = len(a[2] & b[2])
            union = len(a[2] | b[2])
            if union and inter / union >= 0.8 and (a[1], b[1]) not in reported:
                reported.add((a[1], b[1]))
                findings.append(make_finding(
                    "L2-04", path, a[1], section_of(headings, a[1]),
                    f"Sentences at lines {a[1]} and {b[1]} share >=80% of "
                    "their significant words.",
                    f"[{a[1]}] {a[0]}\n[{b[1]}] {b[0]}"))
    return findings


def main(argv):
    if len(argv) < 2:
        print("usage: check_skill.py <skill.md> [<skill.md> ...]",
              file=sys.stderr)
        return 2
    all_findings = []
    for path in argv[1:]:
        all_findings.extend(check_file(path))
    json.dump(all_findings, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
