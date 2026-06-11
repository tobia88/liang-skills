"""
liang-quest-planner — assemble_plan.py

Assembles a self-contained plan.html from:
  - a body fragment (content of <div class="page">)
  - base.css (structure layer)
  - skin-<name>.css (palette + motif layer)
  - mockup.css (conditional: only when body uses ui-mock-section)

Usage:
    python assemble_plan.py <body-html-path> <skin-name> <output-html-path> [--title "Campaign Title"]

Example:
    python assemble_plan.py body.html ff-gold plan.html --title "My Campaign"
"""

from __future__ import annotations

import argparse
import html
import pathlib
import re
import sys

TPL = pathlib.Path(__file__).parent

# ---------------------------------------------------------------------------
# Helpers — class token matching
# ---------------------------------------------------------------------------

def _has_class(tag_attrs: str, *class_tokens: str) -> bool:
    """Return True if the tag attribute string contains ALL the given class tokens."""
    m = re.search(r'class\s*=\s*"([^"]*)"', tag_attrs)
    if not m:
        m = re.search(r"class\s*=\s*'([^']*)'", tag_attrs)
    if not m:
        return False
    classes = set(m.group(1).split())
    return all(tok in classes for tok in class_tokens)


def _find_tags(html: str, tag: str) -> list[str]:
    """Return list of opening-tag attribute strings for the given tag name."""
    return re.findall(rf'<{tag}(\s[^>]*)?>',  html, re.IGNORECASE)


def _find_tags_with_class(html: str, tag: str, *class_tokens: str) -> list[str]:
    """Return opening-tag attribute strings for <tag> where all class_tokens are present."""
    return [a for a in _find_tags(html, tag) if _has_class(a, *class_tokens)]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate(body: str) -> list[str]:
    """
    Run all validation rules against the body HTML fragment.
    Returns a list of violation messages (empty = pass).
    """
    violations: list[str] = []

    # ------------------------------------------------------------------
    # Rule 4: No document shell in body
    # ------------------------------------------------------------------
    # Match the tag name as a whole word: <html, <head, <body followed by
    # whitespace, >, or end-of-string — so <header does NOT trigger <head.
    for tag in ("html", "head", "body"):
        if re.search(rf'<{tag}(?:\s|>|/)', body, re.IGNORECASE):
            violations.append(
                f"Rule 4: document-shell tag '<{tag}' found in body fragment"
            )

    # ------------------------------------------------------------------
    # Rule 5: No <style>, <script>, <link> tags, no @import
    # ------------------------------------------------------------------
    for tag in ("style", "script", "link"):
        if re.search(rf'<{tag}[\s>]', body, re.IGNORECASE):
            violations.append(
                f"Rule 5: forbidden <{tag}> tag found in body fragment"
            )
    if re.search(r'@import', body, re.IGNORECASE):
        violations.append("Rule 5: @import found in body fragment")

    # ------------------------------------------------------------------
    # Rule 6: Inline style exception — only --mock-cols custom property allowed
    # ------------------------------------------------------------------
    # Find all style="..." attributes
    for m in re.finditer(r'\bstyle\s*=\s*"([^"]*)"', body, re.IGNORECASE):
        value = m.group(1).strip()
        # Allow only a single --mock-cols declaration (with optional trailing semicolon/whitespace)
        # e.g. "--mock-cols: 2fr 1fr 1fr;" or "--mock-cols:2fr 1fr 1fr"
        if not re.fullmatch(r'\s*--mock-cols\s*:\s*[^;]+;?\s*', value):
            violations.append(
                f"Rule 6: forbidden inline style attribute: style=\"{value}\""
            )
    # Also check single-quoted style attributes
    for m in re.finditer(r"\bstyle\s*=\s*'([^']*)'", body, re.IGNORECASE):
        value = m.group(1).strip()
        if not re.fullmatch(r'\s*--mock-cols\s*:\s*[^;]+;?\s*', value):
            violations.append(
                f"Rule 6: forbidden inline style attribute: style='{value}'"
            )

    # ------------------------------------------------------------------
    # Rule 7: No external assets
    # ------------------------------------------------------------------
    # src= starting with http:// or https://
    for m in re.finditer(r'\bsrc\s*=\s*["\']?(https?://)', body, re.IGNORECASE):
        violations.append(
            f"Rule 7: external src= URL found: {m.group(0)[:80]}"
        )
    # No <img> or <iframe> at all
    for tag in ("img", "iframe"):
        if re.search(rf'<{tag}[\s>]', body, re.IGNORECASE):
            violations.append(
                f"Rule 7: forbidden <{tag}> element found in body fragment"
            )

    # ------------------------------------------------------------------
    # Rule 2: Required structure
    # ------------------------------------------------------------------
    # header.masthead
    if not _find_tags_with_class(body, "header", "masthead"):
        violations.append("Rule 2: missing <header class=\"masthead\">")
    else:
        # h1.campaign-title inside masthead region
        # Extract masthead block (rough heuristic: from opening <header class="masthead"> to </header>)
        masthead_m = re.search(
            r'<header\s[^>]*class\s*=\s*"[^"]*masthead[^"]*"[^>]*>(.*?)</header>',
            body, re.IGNORECASE | re.DOTALL
        )
        if masthead_m:
            masthead_content = masthead_m.group(1)
            if not _find_tags_with_class(masthead_content, "h1", "campaign-title"):
                violations.append(
                    "Rule 2: <header class=\"masthead\"> exists but contains no <h1 class=\"campaign-title\">"
                )
        else:
            violations.append(
                "Rule 2: <header class=\"masthead\"> could not be parsed for inner h1"
            )

    # nav.toc with at least one toc-item
    if not _find_tags_with_class(body, "nav", "toc"):
        violations.append("Rule 2: missing <nav class=\"toc\">")
    else:
        toc_items = _find_tags_with_class(body, "li", "toc-item")
        if not toc_items:
            violations.append("Rule 2: <nav class=\"toc\"> has no element with class toc-item")

    # main.quests with at least one section.quest
    if not _find_tags_with_class(body, "main", "quests"):
        violations.append("Rule 2: missing <main class=\"quests\">")
    else:
        quest_sections = _find_tags_with_class(body, "section", "quest")
        if not quest_sections:
            violations.append("Rule 2: <main class=\"quests\"> has no <section class=\"quest\">")

    # section.notes
    if not _find_tags_with_class(body, "section", "notes"):
        violations.append("Rule 2: missing <section class=\"notes\">")

    # footer.page-footer
    if not _find_tags_with_class(body, "footer", "page-footer"):
        violations.append("Rule 2: missing <footer class=\"page-footer\">")

    # ------------------------------------------------------------------
    # Rule 1: Anchor integrity, bidirectional
    # ------------------------------------------------------------------
    # Collect TOC hrefs (only anchors inside nav.toc)
    toc_m = re.search(
        r'<nav\s[^>]*class\s*=\s*"[^"]*\btoc\b[^"]*"[^>]*>(.*?)</nav>',
        body, re.IGNORECASE | re.DOTALL
    )
    toc_hrefs: set[str] = set()
    if toc_m:
        toc_block = toc_m.group(1)
        for href_m in re.finditer(r'href\s*=\s*"#([^"]+)"', toc_block, re.IGNORECASE):
            toc_hrefs.add(href_m.group(1))

    # Collect quest ids
    quest_ids: set[str] = set()
    for attr_str in _find_tags_with_class(body, "section", "quest"):
        id_m = re.search(r'\bid\s*=\s*"([^"]+)"', attr_str)
        if id_m:
            quest_ids.add(id_m.group(1))

    # Forward: every TOC href must resolve to a quest id
    for href_id in toc_hrefs:
        # Check against ANY id in the body (not just quest ids), per contract
        if not re.search(rf'\bid\s*=\s*"{re.escape(href_id)}"', body, re.IGNORECASE):
            violations.append(
                f"Rule 1: TOC href=\"#{href_id}\" has no matching id in the body"
            )

    # Reverse: every section.quest id must be referenced by a TOC href
    for quest_id in quest_ids:
        if quest_id not in toc_hrefs:
            violations.append(
                f"Rule 1: <section class=\"quest\" id=\"{quest_id}\"> is not referenced by any TOC href"
            )

    # ------------------------------------------------------------------
    # Rule 3: Difficulty badges
    # ------------------------------------------------------------------
    DIFF_CLASSES = {"diff-easy", "diff-medium", "diff-hard"}

    def _item_has_diff_badge(item_html: str) -> bool:
        """
        Given the HTML of a toc-item or quest-header (extracted by enclosing element),
        check whether there is at least one element carrying both diff-badge AND one of
        the diff-* level classes.
        """
        for attr_str in re.findall(r'<\w+(\s[^>]*)?>', item_html, re.IGNORECASE):
            if attr_str and _has_class(attr_str, "diff-badge"):
                m = re.search(r'class\s*=\s*"([^"]*)"', attr_str)
                if not m:
                    m = re.search(r"class\s*=\s*'([^']*)'", attr_str)
                if m:
                    classes = set(m.group(1).split())
                    if classes & DIFF_CLASSES:
                        return True
        return False

    # toc-items — use regex to extract each li.toc-item block
    for toc_item_m in re.finditer(
        r'<li(\s[^>]*)?>.*?</li>',
        body, re.IGNORECASE | re.DOTALL
    ):
        attr_str = toc_item_m.group(1) or ""
        if not _has_class(attr_str, "toc-item"):
            continue
        if not _item_has_diff_badge(toc_item_m.group(0)):
            violations.append(
                "Rule 3: a toc-item element has no diff-badge with a diff-easy/medium/hard class"
            )

    # quest-headers
    for qh_m in re.finditer(
        r'<header(\s[^>]*)?>.*?</header>',
        body, re.IGNORECASE | re.DOTALL
    ):
        attr_str = qh_m.group(1) or ""
        if not _has_class(attr_str, "quest-header"):
            continue
        if not _item_has_diff_badge(qh_m.group(0)):
            violations.append(
                "Rule 3: a quest-header element has no diff-badge with a diff-easy/medium/hard class"
            )

    return violations


# ---------------------------------------------------------------------------
# Title extraction
# ---------------------------------------------------------------------------

def _extract_title(body: str, fallback: str) -> str:
    """Extract text content of <h1 class="campaign-title">; fall back to fallback."""
    m = re.search(
        r'<h1\s[^>]*class\s*=\s*"[^"]*campaign-title[^"]*"[^>]*>(.*?)</h1>',
        body, re.IGNORECASE | re.DOTALL
    )
    if m:
        # Strip inner tags
        text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        if text:
            return text
    return fallback


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def assemble(
    body_path: pathlib.Path,
    skin_name: str,
    output_path: pathlib.Path,
    title: str | None = None,
) -> int:
    """
    Assemble the plan.html.
    Returns 0 on success, 1 on validation failure.
    """
    # --- Read inputs -------------------------------------------------------
    try:
        body = body_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"ERROR: body file not found: {body_path}", file=sys.stderr)
        return 1

    skin_path = TPL / f"skin-{skin_name}.css"
    try:
        skin_css = skin_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"ERROR: skin file not found: {skin_path}", file=sys.stderr)
        return 1

    base_css = (TPL / "base.css").read_text(encoding="utf-8")

    include_mockup = bool(re.search(r'class\s*=\s*"[^"]*\bui-mock-section\b', body))
    mockup_css = ""
    if include_mockup:
        mockup_css = (TPL / "mockup.css").read_text(encoding="utf-8")

    # --- Validate ----------------------------------------------------------
    violations = validate(body)
    if violations:
        for v in violations:
            print(f"VALIDATION: {v}", file=sys.stderr)
        return 1

    # --- Resolve title -----------------------------------------------------
    if title is None:
        # Extracted from the body, so already entity-encoded — do not re-escape.
        title = _extract_title(body, output_path.stem)
    else:
        title = html.escape(title)

    # --- Write output ------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)

    combined_css = base_css + "\n" + skin_css
    if mockup_css:
        combined_css += "\n" + mockup_css

    doc = (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f"<title>{title}</title>\n"
        "<style>\n"
        f"{combined_css}"
        "\n</style>\n"
        "</head>\n"
        "<body>\n"
        '<div class="page">\n'
        f"{body}\n"
        "</div>\n"
        "</body>\n"
        "</html>\n"
    )
    output_path.write_text(doc, encoding="utf-8")
    print(output_path.resolve())
    return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assemble a self-contained plan.html from body + CSS layers."
    )
    parser.add_argument("body_html_path", type=pathlib.Path, help="Body fragment HTML file")
    parser.add_argument("skin_name", help="Skin name, e.g. ff-gold")
    parser.add_argument("output_html_path", type=pathlib.Path, help="Output plan.html path")
    parser.add_argument("--title", default=None, help="Optional <title> text")

    args = parser.parse_args()
    sys.exit(assemble(args.body_html_path, args.skin_name, args.output_html_path, args.title))


if __name__ == "__main__":
    main()
