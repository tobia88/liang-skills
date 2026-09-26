"""
liang-quest-planner — assemble_preview.py

Reusable harness: inlines base.css + a named skin with a fixture body
and writes a standalone preview HTML for screenshot validation.

Usage:
    python references/templates/assemble_preview.py <skin-name>
    e.g.:  python references/templates/assemble_preview.py nier-monochrome
           python references/templates/assemble_preview.py ff-gold

Output: references/templates/_preview-<skin-name>.html
"""
import pathlib, sys

TPL = pathlib.Path(__file__).parent

def assemble(skin_name: str) -> pathlib.Path:
    base   = (TPL / "base.css").read_text(encoding="utf-8")
    skin   = (TPL / f"skin-{skin_name}.css").read_text(encoding="utf-8")
    body   = (TPL / "_fixture-body.html").read_text(encoding="utf-8")
    html   = f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><style>{base}\n{skin}</style><div class=page>{body}</div>"
    out    = TPL / f"_preview-{skin_name}.html"
    out.write_text(html, encoding="utf-8")
    return out

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python assemble_preview.py <skin-name>", file=sys.stderr)
        print("  e.g. python assemble_preview.py nier-monochrome", file=sys.stderr)
        sys.exit(1)
    result = assemble(sys.argv[1])
    print(result)
