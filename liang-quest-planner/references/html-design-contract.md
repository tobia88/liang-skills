# HTML Design Contract

This document governs the `plan.html` generation phase of `liang-quest-planner`. It defines the **quality floor every output must clear**, the **aesthetic catalog** the planner picks from, the **selection heuristics** for matching direction to campaign, the **delegation protocol** for the body-drafting subagent, the **CSS pitfall guardrails** to avoid common AI-generated layout bugs, and the **anti-patterns** that mark generic AI-slop output.

Read this document **before every HTML generation**, whether delegating or generating inline.

---

## 1. Quality Contract (Non-Negotiable)

Every generated `plan.html` must satisfy all nine clauses below. These are the gates the HTML must pass regardless of aesthetic direction.

```yaml
toc_anchors:        work; every <a href="#id"> targets an existing element id
code_blocks:        monospace; sufficient contrast; horizontal-scroll for long lines;
                    file path label visible above each block;
                    CSS-only syntax highlighting per §9 (token classes wrap comments,
                    keywords, types, macros, strings, numbers — no JS libraries)
html_escape:        all content derived from Decision Summary or conversation is
                    HTML-escaped — never inject user content as raw HTML
no_javascript:      CSS-only motion is permitted; <script> is forbidden
no_external_deps:   no CDN, no Google Fonts, no remote images, no @import of external CSS;
                    fonts use the system stack only
responsive:         usable down to 360px viewport width without horizontal scroll on the
                    outer page (code blocks may scroll internally)
accessible:         text contrast >= 4.5:1 against background; all decorative elements
                    have aria-hidden="true" or empty alt; semantic HTML structure;
                    syntax highlighting tokens also clear the 4.5:1 bar against the
                    code-block background
print_safe:         print stylesheet strips chrome; no clipped content when printed;
                    syntax-highlight tokens collapse to greyscale on print
self_contained:     single HTML file; no companion CSS/JS/image assets
```

If the generator (whether delegated or inline) cannot satisfy a clause, it must adapt the design rather than skip the clause.

---

## 2. Aesthetic Direction Catalog

Eight named directions. Each defines mood keywords, palette anchors (3–4 hex codes — guides, not prescriptions), typography pairing (system stack only), decorative motif, and layout direction. The planner picks one direction per campaign based on selection heuristics (section 3).

Each direction is a **starting point**, not a template. The model is encouraged to flavor decorative elements, hero treatments, and section transitions within the direction's spirit.

---

### 2.1 — Persona-blue

- **Mood keywords**: narrative, dialogue, character work, branching story, social systems, voice acting, cutscene authoring
- **Palette**: `#102447` (deep cobalt), `#f0c64a` (chrome yellow), `#d94545` (signal red), `#efe9d9` (paper cream)
- **Typography**: display sans with strong condensed weights (`"Bebas Neue"` *avoid — not system*; instead `"Franklin Gothic Medium", "Trebuchet MS", "Helvetica Neue Condensed", "Impact"`); body in modern serif (`"Charter", "Sitka Text", "Constantia", Georgia`); mono `"JetBrains Mono", "Cascadia Mono", Consolas`
- **Decorative motif**: slanted text overlays, geometric speech-bubble framing, oversized arrow markers, asymmetric high-contrast text blocks
- **Layout direction**: asymmetric grids, diagonal flow, slanted dividers, off-center heroes

### 2.2 — FF-gold

- **Mood keywords**: infrastructure, cloud, systems, foundational, classic, careful, deliberate, polished
- **Palette**: `#2a1f0e` (deep umber), `#c49a3c` (antique gold), `#f7eccf` (parchment), `#4a3818` (warm dark)
- **Typography**: display serif with classical weight (`"Trajan Pro", "Cinzel"` *not system — use* `"Goudy Old Style", "Hoefler Text", "Big Caslon", "Palatino Linotype"`); body refined serif (`"Iowan Old Style", "Charter", "Sitka Text", Georgia`); mono `"IBM Plex Mono", "Consolas"`
- **Decorative motif**: ornamental flourishes, gilt-style frames, scroll-edge dividers, illuminated initial capitals
- **Layout direction**: classical vertical scroll, centered hero, generous margins, single-column tutorial flow

### 2.3 — Octopath-watercolor

- **Mood keywords**: creative tooling, content authoring, narrative design, painterly, hand-crafted, atelier
- **Palette**: `#f1e7d2` (warm linen), `#b8d2c4` (sage wash), `#d99a6c` (terra), `#6c8a8f` (slate teal)
- **Typography**: display serif with calligraphic quality (`"Sitka Heading", "Cambria", "Iowan Old Style", "Hoefler Text", "Baskerville"`); body humanist serif (`"Charter", "Constantia", Georgia`); mono `"IBM Plex Mono", "Cascadia Code"`
- **Decorative motif**: watercolor wash backgrounds (radial-gradient noise textures), painterly borders, story-book column rules, hand-lettered-feeling section marks
- **Layout direction**: column-based storybook reading, full-bleed wash backgrounds, generous line-height, illustrated-feeling section transitions

### 2.4 — Chrono-pixel

- **Mood keywords**: retro CLI, scripts, time-shifted, vintage tooling, hacker aesthetic
- **Palette**: `#1e1f3d` (twilight), `#5fc6c2` (terminal cyan), `#f0a1d4` (sunset rose), `#f4e6a3` (cathode amber)
- **Typography**: display monospace with retro feel (`"Cascadia Code", "JetBrains Mono", "IBM Plex Mono", "Consolas"`); body monospace (same stack); decorative serif sparingly (`"Hoefler Text", Georgia`)
- **Decorative motif**: CRT scanlines (CSS repeating-linear-gradient), pixel-art accents (square-cornered borders), step-shaped headings, glitched text overlays
- **Layout direction**: terminal-style stacked blocks, ASCII-art-inspired dividers, fixed-width feel even in proportional sections

### 2.5 — Xenoblade-cosmic

- **Mood keywords**: systems, cosmic, large-scale, planetary, orbital, abstract architecture
- **Palette**: `#0a0b1f` (deep space), `#2a3d8f` (nebula blue), `#8c5fd9` (cosmic violet), `#b8d4ff` (stellar white)
- **Typography**: display sans with futurist quality (`"Avenir Next Heavy", "Avenir Heavy", "Optima", "Gill Sans Bold"`); body sans (`"Avenir Next", "Avenir", "Optima", "Gill Sans"`); mono `"JetBrains Mono", "IBM Plex Mono"`
- **Decorative motif**: radial-gradient nebula backgrounds, orbital ring overlays, holographic accent strokes, parallax-feeling depth via layered transparencies
- **Layout direction**: cosmic-grid (irregular sized blocks), full-bleed hero with deep gradient, floating section cards

### 2.6 — Dragon-Quest-classic

- **Mood keywords**: DSL, grammar, foundations, language work, primitives, iconic, message-box clarity
- **Palette**: `#1a3a8a` (heritage blue), `#f5d442` (slime gold), `#ffffff` (clean white), `#c44545` (signal red)
- **Typography**: display sans-serif with chunky weight (`"Franklin Gothic Bold", "Verdana Bold", "Trebuchet MS"`); body sans (`"Verdana", "Trebuchet MS", "Lucida Sans"`); mono `"Consolas", "Cascadia Mono"`
- **Decorative motif**: rounded-rect message-box framing, iconic enemy-sprite-style accents (geometric clip-paths), drop-shadow heavy borders
- **Layout direction**: rectangular card stack, message-box per quest, high-contrast block layout

### 2.7 — NieR-monochrome

- **Mood keywords**: data, analytics, observability, brutalist, technical, instrumentation, telemetry
- **Palette**: `#f6f3eb` (bone), `#1a1a1a` (ink), `#b8442f` (rust accent), `#4a4a4a` (slate)
- **Typography**: display sans uppercase (`"Avenir Next Heavy", "Franklin Gothic Heavy", "Gill Sans Bold"`); body sans (`"Helvetica Neue", "Avenir Next", "Optima"`); mono `"JetBrains Mono", "IBM Plex Mono", "Consolas"` (used heavily)
- **Decorative motif**: technical readout framing, instrument-panel labels, oversized identifier glyphs, single-stroke rules, terminal-style data callouts
- **Layout direction**: hard left-aligned grid, dense data tables, oversized monospace identifiers, technical-document feel

### 2.8 — Tactics-Ogre-tactical

- **Mood keywords**: planning, strategy, tactics, dossier, brief, command, deliberation
- **Palette**: `#2a2e3d` (deep ink — alt `#14110d`), `#d97757` (tactical orange — alt `#c8341c` vermilion), `#f0e8d4` (cream paper), `#7a8a9a` (slate)
- **Typography**: display serif with editorial weight (`"Big Caslon", "Bodoni 72", "Didot", "Hoefler Text", "Baskerville"`); body characterful serif (`"Charter", "Sitka Text", "Constantia", Georgia`); meta sans sparingly (`"Avenir Next", "Gill Sans"`); mono `"Iosevka", "JetBrains Mono"`
- **Decorative motif**: hex-frame motifs, faction-color coding, tactical-map sigils, editorial dossier folio bars, vermilion editorial-red accent, hand-set drop caps, oversized roman-numeral section marks
- **Layout direction**: editorial 2-column with margin gutter for folio numerals, dossier-style filed-bar metadata strip, hanging numbered lists, paint-chip catalog grids

---

## 3. Selection Heuristics

The planner picks one direction per campaign automatically. Match in this order:

1. **Match Planning Lens keywords first**:
   - Skill creation, pipeline architecture, framework, scaffolding → FF-gold or Xenoblade-cosmic
   - Narrative, dialogue, character, story → Persona-blue or Octopath-watercolor
   - Tooling, content authoring, creative workflow → Octopath-watercolor
   - CLI, scripts, retro, command-line → Chrono-pixel
   - Cosmic, systems-level, large-scale architecture → Xenoblade-cosmic
   - DSL, grammar, primitives, foundations → Dragon-Quest-classic
   - Data, analytics, profiling, observability, telemetry → NieR-monochrome
   - Planning, strategy, brief, dossier, command → Tactics-Ogre-tactical

2. **Fall back to Main Quest content keywords** when the lens is too abstract to match.

3. **When ambiguity remains, default to FF-gold** (most legible classic).

4. **Avoid back-to-back repeats** if the user has run multiple campaigns recently. Best-effort only — the planner is stateless, so this is heuristic at best.

5. **Announce the choice in one sentence** before generating. The user can override during open discussion (Phase 3).

---

## 4. Assembly Protocol

The planner assembles `plan.html` from three fixed layers rather than regenerating CSS every run. Body drafting is delegated to the body-drafter subagent (model resolved per SKILL.md Phase 2c: `project.yaml` `models.body_drafter` → `execution_by_difficulty.medium` → harness default); CSS inlining and structural validation are owned by a deterministic script — no model re-types CSS in any standard path.

1. **The body-drafter subagent generates ONLY the fixed-body HTML** per `references/templates/class-contract.md` — the variable per-campaign content (masthead, TOC, quest sections, notes, footer), briefed with the Decision Summary, the Phase 2a quest decomposition, the wireframe recipe (UI-bearing campaigns only), and the class contract itself. The HTML structure and class names are identical regardless of which aesthetic direction is chosen. No theme needs bespoke markup.
2. **`references/templates/assemble_plan.py` validates and assembles** — it structurally validates the body (bidirectional TOC-anchor ↔ section-id integrity, required skeleton classes, difficulty badges, no `<style>`/`<script>`/`<link>`/document-shell tags, no inline styles beyond the `--mock-cols` exception, no external assets), then inlines `base.css`, the chosen `skin-<name>.css`, and `mockup.css` (auto-included only when the body contains a `ui-mock-section`, §10) into a single `<style>` block, in that order. The CSS cascade is deliberate: skins override nothing structural, only variables and optional motif rules; `mockup.css` consumes the same skin variables and adds only wireframe classes.
3. **On validation failure** the script exits non-zero with `VALIDATION:` lines on stderr and writes nothing; the planner sends the violations back to the subagent and re-runs (max 2 retries, then the planner drafts the body itself).
4. **Output remains a single self-contained file** — the contract's `self_contained` and `no_external_deps` clauses (§1) are satisfied by the script's inlining. The `.css` files live in the skill's `references/templates/` directory; they never ship beside `plan.html`.

### 4.1 Body-Only Generation Contract

The body generator — the body-drafter subagent, or the planner in fallback — emits **only the fixed semantic body** — no inline CSS, no `<style>` block, no palette selection in the body markup. The body skeleton is defined in `references/templates/class-contract.md` and is identical across all aesthetic directions.

### 4.2 Delegation Scope

Body drafting goes to a general-purpose subagent on the resolved body-drafter model (configurable via `project.yaml` — see §4 intro). The delegation is transcription, never decision-making: quest decomposition, difficulty, wireframe recipe, and aesthetic direction are all decided by the planner before the subagent is briefed. CSS is never delegated to any model — `assemble_plan.py` owns it. If subagent spawning is unavailable, or the subagent fails validation twice, the planner drafts the body inline and still assembles via the script. Manual CSS inlining is a last resort reserved for environments without Python.

### 4.3 Verification

Regardless of path, after assembly:

- `assemble_plan.py` exited 0 — it enforces TOC-anchor integrity, required structure, and the no-`<script>`/no-`<style>` rules; do not re-derive those checks by hand except in the manual fallback
- Confirm the file exists at the expected path
- Confirm the output is a single self-contained file
- Run the Visual Spot-Check (§4.4) before auto-opening in the browser

### 4.4 Visual Spot-Check

Take Playwright screenshots at **375px viewport width only**, sampling the two content extremes plus the decisions table:

1. **Longest-content quest** — the quest with the most steps + longest code block.
2. **Shortest-content quest** — the quest with the fewest steps + shortest code block.
3. **Decisions table section** — the `notes-wide` block containing the Locked Decisions table (a known §5.5 / §5.11 risk at narrow widths).

`base.css` + every skin have been pre-audited at 1440 / 720 / 375 (§5 pitfall fixes, §9 syntax-token contrast, responsive collapse). Only **content-driven layout breaks** remain — overflow in unusually long inline `<code>` that wasn't in the fixture, edge cases in per-campaign objective lists, very long file-path labels in code blocks. Sampling the extremes catches both sides of the failure spectrum.

**Python invocation** (assumes `playwright` is installed):

```python
from playwright.sync_api import sync_playwright
URL = "file:///<absolute-path-to-plan.html>"
OUT = "<absolute-path-to-screenshot-dir>"
with sync_playwright() as p:
    b = p.chromium.launch()
    c = b.new_context(viewport={"width": 375, "height": 800})
    pg = c.new_page()
    pg.goto(URL)
    pg.locator("#qNNN").screenshot(path=f"{OUT}/longest-375.png")     # longest quest ID
    pg.locator("#qMMM").screenshot(path=f"{OUT}/shortest-375.png")    # shortest quest ID
    pg.locator(".notes-wide").screenshot(path=f"{OUT}/notes-table-375.png")
    b.close()
```

**If Playwright is unavailable**, skip the screenshot loop silently and proceed to auto-open — the user becomes the visual audit.

---

## 4a. Templates Reference

The three-layer generation model is backed by authoring sources in `references/templates/`. The planner reads these at generation time; they never ship beside `plan.html`.

| File | Role | Notes |
|------|------|-------|
| `references/templates/class-contract.md` | Fixed body structure + CSS variable interface | The single source of truth for class names, HTML skeleton, and the skin variable contract. Read by the planner's body generator. |
| `references/templates/base.css` | Shared structure + all 14 pitfall fixes (§5.1–5.14) and syntax-token rules | Written and visually audited **once**. Contains zero hardcoded colors — every visual value is a `var(--x)` resolved by the skin. **§5.1–§5.14 are baked into this file — the planner must not re-derive them per campaign.** |
| `references/templates/skin-<name>.css` | Per-direction palette + motif | Naming convention: `skin-` + lowercase-hyphenated direction slug (e.g., `skin-nier-monochrome.css`, `skin-ff-gold.css`). Each skin defines the full `:root` variable block plus optional motif rules. |
| `references/templates/mockup.css` | Generic UI-wireframe kit (Layer 4, conditional) | Zero hardcoded colors — consumes the skin's variable interface. Auto-included by `assemble_plan.py` **only** when the body contains a `ui-mock-section` (§10). Provides reusable primitives (frame, tabs, toolbar, fields, grouped lists, data grid, split panes, status bar, empty state, inline annotation badges). |
| `references/templates/assemble_plan.py` | Deterministic assembler + structural validator | Run by the planner after body drafting: validates the body against the class contract, inlines base + skin (+ mockup when wireframed) into one `<style>` block, writes the self-contained `plan.html`. Exits non-zero with `VALIDATION:` lines on contract violations. |

When the planner picks an aesthetic direction, it resolves the skin filename as `skin-<lowercase-hyphenated-direction>.css` and reads it from `references/templates/`.

---

## 5. CSS Pitfall Guardrails

These are common AI-generated CSS bugs now **baked into `base.css` — the planner does not re-derive these rules per campaign.** They are preserved here as documentation of what `base.css` solves.

### 5.1 — Do not use `display: grid` or `display: flex` on `<li>`, `<p>`, or `<a>` elements that contain mixed inline content

**Bug**: Each text node and inline element (`<code>`, `<em>`, `<strong>`, `<a>`) becomes a separate grid/flex item. Content breaks into one-cell-per-word.

**Symptom**: every word of a sentence appears on its own line, with code blocks taking full row width between text fragments.

**Fix**: Use `position: relative` on the parent and `position: absolute` on `::before` for hanging markers (em-dashes, numerals, bullets). The parent stays as normal block flow; the marker hangs in the padding.

```css
/* WRONG */
ul.scope-list li {
  display: grid;
  grid-template-columns: 28px 1fr;
}

/* RIGHT */
ul.scope-list li {
  position: relative;
  padding-left: 32px;
}
ul.scope-list li::before {
  content: "—";
  position: absolute;
  left: 0;
  top: 0;
}
```

**When grid is safe on lists**: only when every child of `<li>` is an explicit element (no bare text nodes) and the number of children matches the column count. Mixing pseudo-elements with bare text is the bug.

### 5.2 — Grid children with long strings need `min-width: 0`

**Bug**: Grid items default to `min-width: auto`, which respects content's intrinsic width. Long URLs, code identifiers, or unbreakable strings can blow out the column.

**Fix**: Apply `min-width: 0` to grid items that contain code or long strings. For text wrapping, also add `overflow-wrap: anywhere` or `word-break: break-word`.

### 5.3 — Anchor targets must exist

**Bug**: TOC links to `#section-id` where the section's actual `id=""` was forgotten or misspelled.

**Fix**: Self-check after generation — every `href="#..."` in TOC must have a matching `id="..."` in the document.

### 5.4 — Responsive collapse at 360px

**Bug**: Multi-column grid templates don't collapse on narrow viewports; content overflows or compresses unreadably.

**Fix**: Test the rendered output at 360px viewport. Multi-column grids must have a `@media (max-width: 720px)` (or similar) breakpoint that collapses to single column.

### 5.5 — `<code>` inside table cells

**Bug**: Long code identifiers inside `<td>` expand the cell, breaking table layout.

**Fix**: Apply `word-break: break-word` or `overflow-wrap: anywhere` on `<td>`, and use a fixed-or-fluid table layout (`table-layout: fixed` with column widths, or careful min-width on cells).

### 5.6 — Sticky positioning with overflow ancestors

**Bug**: `position: sticky` doesn't work if any ancestor has `overflow: hidden` or `overflow: auto`.

**Fix**: Audit ancestor overflow when sticky elements fail to stick. Typically, the body and main wrapper should leave overflow alone.

### 5.7 — Print stylesheet

**Bug**: Default web layout prints with sidebars, navigation, sticky elements, and dark backgrounds bleeding ink.

**Fix**: Provide a `@media print` block that strips chrome (TOC, marginalia, sticky elements), removes background colors, sets text to black, and uses `page-break-inside: avoid` on cards.

### 5.8 — Reading margins and desktop content width

**Bug**: Defaulting to a narrow content container (e.g., `max-width: 720px` or `880px`) with small side padding feels claustrophobic on desktop — the page reads like a mobile-first literary layout shoehorned onto a 1920px monitor, with tables and code blocks bumping the column edges and 60–70% of the viewport wasted on outer whitespace.

**Fix**: Default `plan.html` to tech-dossier widths — `max-width: 1280–1400px` on the main container, with `48–64px` of side padding on desktop. Layer responsive breakpoints below it so the layout breathes everywhere.

```css
/* RIGHT — tech-dossier defaults */
.page {
  max-width: 1360px;
  margin: 0 auto;
  padding: 56px 64px 72px;
}
@media (max-width: 1000px) {
  .page { padding: 48px 40px 64px; }
}
@media (max-width: 720px) {
  .page { padding: 28px 20px 48px; }
}
```

The 720–880px range is for prose-only literary layouts. The 1080–1200px range works for single-column tech blogs but felt cramped in practice when the body uses a 2:1 grid (main + aside) on 1920px+ monitors — the aside collapsed to ~320px and the table/code area lost too much breathing room. `plan.html` is a dossier with tables, code blocks, per-quest 2-column bodies, and grid sections — pick the upper end of the range unless you have specific reason not to. Aesthetic direction does not change this rule: FF-gold's "generous margins" means generous *side* margins around a wide column, not a narrow column on a wide page.

### 5.9 — Don't uppercase titles that carry technical identifiers

**Bug**: Applying `text-transform: uppercase` to quest titles, TOC entries, or any heading that includes class names, function names, or other CamelCase identifiers destroys the case structure that carries the word boundaries. `USoEDialogueFlowComponent` becomes `USOEDIALOGUEFLOWCOMPONENT` — a wall of letters that reads as one undifferentiated blob.

**Symptom**: technical identifiers in titles look like noise; readers have to mentally parse word boundaries from context; class-name-heavy quest titles are markedly harder to scan than purely-prose titles in the same document.

**Fix**: Use the display font + heavy weight + tight letter-spacing to carry the title's visual hierarchy, not uppercase. Hero/masthead titles that are pure prose (no identifiers) can still use uppercase if the aesthetic direction calls for it; titles that mix prose and identifiers should not.

```css
/* WRONG — class names lose word boundaries */
.quest-title {
  font-family: var(--font-display);
  font-weight: 700;
  text-transform: uppercase;
}

/* RIGHT — CamelCase identifiers stay readable */
.quest-title {
  font-family: var(--font-display);
  font-weight: 700;
  letter-spacing: -0.005em;
}
```

Apply to: quest section titles, TOC entry titles, any heading where one or more identifiers (`U*`, `A*`, `F*`, `T*`, `E*`, `BP_*`, function names) appear in the text content.

Eyebrow labels, section dividers ("Steps", "Victory", "Difficulty"), and pill text remain uppercase — those are short prose labels with no identifiers, and the uppercase carries the editorial rhythm.

### 5.10 — Status pills and short uppercase labels need `white-space: nowrap`

**Bug**: A short uppercase pill like "RECOMMENDED" or "MEDIUM" placed in a narrow table cell or constrained container wraps letter-by-letter when the cell shrinks — each letter ends up on its own line ("R / E / C / O / M / M / E / N / D / E / D"). The text technically fits but reads as garbage.

**Symptom**: pill labels in decision tables, status badges, or difficulty chips render as vertical strips of single letters when the surrounding container is narrow.

**Fix**: Every short-label pill / badge / chip CSS class must include `white-space: nowrap`. The pill should either fit on one line or push the cell wider — never wrap mid-word.

```css
.pill, .badge, .chip {
  display: inline-block;
  white-space: nowrap;
}
```

Pair this with `word-break: break-word` / `overflow-wrap: anywhere` on the surrounding `<td>` so the *table cell text* can wrap, but the pill itself stays atomic.

### 5.11 — Multi-column tables don't fit inside auto-fit grid cards

**Bug**: Placing a decision table (3+ columns, including a status pill column) inside a `repeat(auto-fit, minmax(320px, 1fr))` grid card forces the table to fit into a ~320px column on wide displays. The status column collapses, the reason column wraps unreadably, and pills wrap letter-by-letter (see Pitfall 5.10).

**Symptom**: campaign-notes "Locked Decisions" table renders tiny and unreadable next to a risks card and an open-questions card; the table needs the full container width to be usable.

**Fix**: Put narrative-card content (risks, open questions, short bulleted notes) in the multi-column auto-fit grid. Pull tables out into their own full-width row below. Two-column layout (notes-grid + notes-wide table) reads cleanly on desktop and collapses correctly on mobile.

```css
.notes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
}
.notes-wide {
  margin-top: 24px;
}
@media (max-width: 720px) {
  .notes-grid { grid-template-columns: 1fr; }
}
```

```html
<div class="notes-grid">
  <div class="note-card risk">...</div>
  <div class="note-card question">...</div>
</div>
<div class="notes-wide">
  <div class="note-card">
    <table class="decisions">...</table>
  </div>
</div>
```

Same rule applies to any block whose intrinsic minimum width exceeds ~320px — wide code listings, screenshot grids, side-by-side comparison tables. If it doesn't fit in the auto-fit cell, give it its own row.

### 5.12 — Inline-`code` base styling leaks into `<pre><code>`

**Bug**: A bare `code { color: var(--ink); background: ...; border: ...; padding: ... }` rule meant for inline code in prose also matches `<code>` nested inside `<pre>`. The dark code block now has near-black text everywhere *except* on tokens explicitly wrapped in a `.kw` / `.ty` / `.cm` / `.mc` / `.st` / `.nm` span. Wrapped tokens keep their syntax color; unwrapped glue — `::`, parens, braces, semicolons, plain function and variable identifiers — vanishes into the dark background.

**Symptom**: code blocks look "half-painted" — keywords and types appear, but the connective tissue between them is invisible; viewers see disconnected color fragments with empty space between, not a code listing.

**Fix**: Explicitly reset every property on `pre code` so the bare `code` rule does not bleed in. Pair the reset with the syntax-token rules in §9.3.

```css
/* WRONG — pre code inherits color: var(--ink) from the bare code rule */
code {
  color: var(--ink);
  background: rgba(26, 26, 26, 0.06);
  border: 1px solid rgba(26, 26, 26, 0.1);
  padding: 1px 6px;
  font-size: 0.92em;
}
pre code .kw { color: var(--syn-kw); font-weight: 600; }
/* ...other token rules — but the unwrapped text is still dark ink */

/* RIGHT — pre code resets every inherited property before tokens layer on */
pre code {
  color: var(--code-fg);   /* the default "identifier" color for unwrapped text */
  background: transparent;
  border: none;
  padding: 0;
  font-size: inherit;
}
pre code .kw { color: var(--syn-kw); font-weight: 600; }
```

Equivalent alternative: scope the inline-code rule with `:not(pre) > code` so it never matches `pre code` in the first place. Either approach works; the explicit reset is louder and easier to audit.

### 5.13 — Asymmetric content in 2-column grids leaves empty space

**Bug**: A `grid-template-columns: 2fr 1fr` quest body (or any 2-column grid where one column carries the bulk of the content) stretches both grid cells to the row's intrinsic height. When the heavy column (steps + code blocks + rationale) is much taller than the light column (Dependencies + Victory Conditions), the light column finishes early and the rest of its cell renders as a visible paper-colored void — often 60-70% of the quest card height when step counts diverge across quests.

**Symptom**: The sidebar finishes ~30% down the quest card; the remaining vertical space is empty cream/paper with no content. The bug is invisible on quests with short step lists and dramatic on quests with long step lists, so it grows asymmetrically as content varies across the campaign.

**Fix**, in order of preference for dossier/brief aesthetics:

1. **Restructure to footer (preferred)** — main content fills full width, sidebar content moves to a 2-column footer strip below with a horizontal rule above. Sequential reading flow (steps → code → rationale → deps + VC). No dead space. Footer collapses to single column on narrow viewports.

   ```css
   .quest-main { /* full-width main column */ }
   .quest-footer {
     display: grid;
     grid-template-columns: 1fr 1fr;
     gap: 20px;
     margin-top: 32px;
     padding-top: 24px;
     border-top: 1px solid var(--rule);
   }
   @media (max-width: 720px) {
     .quest-footer { grid-template-columns: 1fr; gap: 14px; }
   }
   ```

2. **Sticky sidebar (alternative)** — `position: sticky; align-self: start; top: 16px` on the sidebar so it follows the user as they scroll through the long main column. Empty space below is still visible at first paint, but the aside stays useful while reading. Acceptable when the sidebar layout intent is structural to the aesthetic.

**When to apply**: any quest decomposition where step counts vary substantially across quests (e.g., 3 steps in one, 10 in another). If every quest has roughly equal step counts the 2-column grid works fine.

### 5.14 — Inline `<code>` overflows narrow containers (generalization of §5.5)

**Bug**: §5.5 covers `<code>` inside `<td>` table cells. The same root cause hits *any* container narrower than ~400px that holds user-derived inline `<code>` — sidebar cards, callout boxes, footer cells, narrow grid items. Long identifiers (regex strings, command lines, file paths, fully-qualified type names) extend past the container's right edge and render as visible overflow into the paper-colored space beside the card.

**Symptom**: A Victory Condition like `grep -rE 'ready_for_planning\|needs_clarification\|...'` runs off the right edge of a 300px sidebar card. The text is visible but extends into adjacent grid space, breaking the card's visual containment.

**Fix**: Apply both the container reset *and* code-level wrapping. The container needs `min-width: 0` to override grid items' default `min-width: auto`; the inline code needs explicit break rules because `word-break: break-word` does not inherit through `<code>` boundaries reliably.

```css
.aside-card, .sidebar-card, .callout {
  min-width: 0;          /* override grid item default */
  /* ...rest of card styling... */
}
.aside-card code:not(pre code) {
  word-break: break-word;
  overflow-wrap: anywhere;
}
.aside-card ul li {
  word-break: break-word;
  overflow-wrap: anywhere;
}
```

**Generalized rule**: any container narrower than ~400px holding user-derived inline `<code>` needs the same three properties (`min-width: 0` on container, `word-break: break-word` + `overflow-wrap: anywhere` on code). Apply this proactively to every sidebar/footer/callout pattern, not only when the bug appears in a specific quest's content.

---

## 6. Anti-Patterns

These are markers of generic AI-slop output. The generator must actively avoid them, regardless of aesthetic direction.

- **Generic fonts**: Inter, Roboto, Arial, system-ui as the *only* font family (use distinctive system stacks instead — see typography pairings in section 2)
- **Purple-gradient hero on white**: the canonical AI-assistant aesthetic; visible from a mile away
- **Cookie-cutter Tailwind card layouts**: 12-column grid with rounded-2xl shadow-xl cards in a 3-column responsive grid
- **Emoji as decorative anchors**: 🎯, 🚀, ✨, 🔥 used as section markers or visual anchors
- **Centered everything**: a hero with centered text, centered metadata, centered TOC, centered cards — symmetrical to the point of personality vacuum
- **Gradient text on every heading**: linear-gradient(--from-purple-500 to-pink-500) on h1–h6
- **Generic shadow stack**: `box-shadow: 0 4px 6px rgba(0,0,0,0.1)` on every card, identical depth, no spatial logic
- **Dark mode by reflex**: defaulting to dark backgrounds for "modern" feel when the content tone doesn't call for it

---

## 7. Required Content Map

Every `plan.html` must contain these structural elements, regardless of aesthetic direction. *Where* they go and *how* they look is the direction's job; *whether* they exist is the contract's.

1. **Hero / masthead** with campaign title, slug, date, quest count, planning lens
2. **TOC** with anchor links to each quest section (anchors must work — see Pitfall 5.3). Each TOC entry shows a **difficulty badge** (`easy` / `medium` / `hard`) alongside dependency state.
3. **Per-quest sections**, each containing:
   - Quest title and purpose (1–2 sentences)
   - **Difficulty badge** (`easy` / `medium` / `hard`) visible in the quest header — same value as carried in `manifest.yaml`
   - Numbered steps with descriptions
   - Code blocks with file-path labels and syntax highlighting (per §9) where applicable
   - Brief rationale (1–2 sentences)
   - Dependencies (which quests must complete first, or "none")
   - Victory conditions (bulleted list)
4. **Campaign notes** with risks and open questions
5. **Footer** with generator attribution and timestamp

**Conditional:**

- A single **UI Layout Wireframe** section (§10) between the TOC and the first quest, included only for UI-bearing campaigns. Not required for backend / data / refactor campaigns.

---

## 8. Version & Provenance

- Contract version: 2.1
- Authored: 2026-05-27
- Owning skill: `liang-quest-planner`
- Companion script: `references/templates/assemble_plan.py` (deterministic assembly + structural validation)
- Revisions:
  - v1.1 — added §9 syntax highlighting; difficulty badge added to §7 required content; code_blocks / accessible / print_safe clauses in §1 extended to cover highlighting tokens.
  - v1.2 — added §5.8 (reading margins and desktop content width); codifies tech-blog default widths (`max-width: 1080–1200px`, `48–64px` side padding) after the planner shipped a cramped 880px / 32px default that the user flagged as too tight to read.
  - v1.3 — added §5.9 (don't uppercase identifier-bearing titles), §5.10 (pills need `white-space: nowrap`), §5.11 (multi-column tables don't fit auto-fit cards); revised §5.8 to bump the default range to `1280–1400px` after 1120px still felt cramped on 1920px+ displays with 2:1 quest-body grids.
  - v1.4 — added §5.12 (inline-`code` base styling leaks into `<pre><code>`); strengthened §9.1 with explicit `.ty ≠ --code-fg` and `.nm ≠ .kw` rules + an "identifier default" note treating `--code-fg` as a sixth syntax color; audited §9.2 palette starting points (NieR-monochrome re-tuned and verified, other directions annotated with required first-use bumps); added the `pre code` reset and `--code-fg` declaration to §9.3 skeleton. Driven by the interaction-system bug-sweep campaign where the NieR starting palette made types vanish into identifiers and numbers merge with keywords; lesson generalized so future palettes catch the same bugs before the user does.
  - v1.5 — added §5.13 (asymmetric content in 2-col grids leaves empty space — restructure-to-footer preferred over sticky sidebar); added §5.14 (inline `<code>` overflows narrow containers, generalizes §5.5 from tables to any narrow card); promoted Playwright screenshot loop from §9.2 syntax-palette-only mention to a mandatory §4.5 Visual Self-Audit with three viewports (1440/720/375), an extreme-sampling rule (longest-content quest + shortest-content quest, never middle), and an audit checklist mapped to §1 + §5. Also added `Run the Visual Self-Audit (§4.5)` as a §4.4 verification step. Driven by the finish-pipeline-cleanup campaign where q002's long step list left a 65% empty void in the right sidebar, q003's Victory Conditions regex strings overflowed the narrow aside card, and three rounds of screenshot inspection caught issues that the post-generation "ok the file exists" verification did not.
  - v1.6 — layered architecture: §4 becomes an Assembly Protocol (body generated per class-contract.md, base.css + skin-<name>.css inlined, CSS never regenerated per run); frontend-design delegation scoped to body-content only (§4.2); §4.5 collapses to a longest+shortest 375px spot-check plus decisions table (§4.4); §4a Templates Reference section added documenting the three-layer model and the skin naming convention; §5.1–5.14 marked baked-into-base.css (planner must not re-derive); §9.3 split between base.css (token rules + pre code reset) and skins (`:root` palette variables).
  - v1.7 — added §10 (UI Wireframe Mockup) + conditional Layer 4 `mockup.css`: optional skin-matched wireframe for UI-bearing campaigns, with inline-badge annotations. Lesson baked in (class-contract hard-rule 6): mockup colors come from skin vars on explicit surface backgrounds, and active/checked/selected states use accent borders + text, never fills behind text — making the dark-on-light fall-through bug that prompted this structurally impossible.
  - v1.8 — added §11 (Animated Flow Visualization): optional CSS-only `flow-visual-section` for loops, pipelines, retry/evaluation cycles, state machines, branching decisions, and orchestration flows. Flow graph styles live in `base.css`, use skin variables only, include responsive stacking and `prefers-reduced-motion`, and should be included only when they improve understanding rather than decorate.
  - v1.9 — **removed §11 (Animated Flow Visualization) entirely.** The trigger over-fired: because Phase 2a always orders quests by dependency topology, the "dependency DAG / chain / sequence" inclusion clause matched every multi-quest campaign, so the graph rendered on essentially every plan rather than only genuinely loop/pipeline/state-machine-shaped ones. Dropped the `flow-visual-*` styles from `base.css`, the skeleton + class table + hard-rule from `class-contract.md`, the SKILL.md Phase 2a decision step and 2c/2d references, and the §4.4 flow spot-check. Plans are now TOC → (optional UI wireframe) → quests.
  - v2.0 — **body drafting re-delegated from `frontend-design` to a body-drafter subagent; CSS assembly moved out of the model into `references/templates/assemble_plan.py`.** Rationale: by Phase 2c all design judgment is already spent (decomposition, difficulty, wireframe recipe, aesthetic land in 2a/2b), so body generation is contract-following transcription a cheaper, faster model handles reliably — while re-typing ~28KB of base + skin + mockup CSS as model output was pure token waste with a typo risk attached. §4 rewritten as the subagent + script protocol; §4.2 rescoped (delegation is transcription, never decisions); §4.3 anchor/structure/script checks marked script-enforced; §4a table gains the assembler row. Phase 3 full regens reuse the same machinery; edit-in-place stays with the planner and reads the affected section back before editing. Wireframe recipes are written by the planner in Phase 2a and handed to the subagent verbatim.
  - v2.1 — **body-drafter model made configurable via `project.yaml`.** Resolution chain: `models.body_drafter` → `models.execution_by_difficulty.medium` → harness default; missing `project.yaml` falls through silently (planning may precede the executor's first-run interview). §4 / §4.1 / §4.2 rephrased to use "body-drafter subagent" throughout — the skill family runs under pi with non-Claude hosts (GPT, DeepSeek), so vendor-pinned model names in skill prose are a portability bug. Companion change: `models.claude_mode` added for the executor's `--claude` tier overrides (schema docs in `liang-quest-core/references/project/project-yaml.md`).

---

## 9. Syntax Highlighting

Code blocks must include CSS-only token highlighting. No external libraries, no JavaScript — apply highlighting by wrapping tokens in `<span>` elements with the class taxonomy below. Each aesthetic direction tunes the palette against its dark code background; the class names stay stable across directions so the contract is portable.

### 9.1 — Token Class Taxonomy

| Class | Use for | Notes |
|-------|---------|-------|
| `.cm` | Single-line `//` comments, multi-line `/** */` blocks, inline `# ...` (YAML/shell), markdown `#` headings inside intel-doc snippets | Italic recommended; lowest visual weight |
| `.kw` | C++ control flow + modifiers: `if`, `else`, `for`, `while`, `return`, `continue`, `break`, `const`, `virtual`, `static`, `inline`, `auto`, `nullptr`, `true`, `false`, `this`, `class`, `struct`, `public`, `protected`, `private`, **and** primitive types: `void`, `bool`, `float`, `int32`, `uint32`, `int8` | Bold weight; warm/active accent color |
| `.ty` | UE engine types — anything matching prefix-conventions `U*`, `A*`, `F*`, `T*`, `I*`, `E*` (e.g., `USoEInteraction`, `TArray`, `TWeakObjectPtr`, `FSoEInteractionCooldown`, `EAllowShrinking`) | **Must differ perceptibly from `--code-fg`** (the unwrapped identifier color) — if `.ty` matches `--code-fg`, every type name reads as identifier-tone and the wrap might as well not exist. Distinct from `.kw`; medium weight |
| `.mc` | UE macros and all-caps preprocessor identifiers: `UCLASS`, `UFUNCTION`, `UPROPERTY`, `USTRUCT`, `GENERATED_BODY`, `DECLARE_*`, `SCOPE_CYCLE_COUNTER`, `TEXT`, `ensureMsgf`, `BlueprintCallable`, `BlueprintNativeEvent`, `Category`, **and** `#if`, `#endif`, `#include` directives | Highest visual weight after `.kw`; signal-color accent — push the hue or brightness *clearly* above `.kw`, not a 5% shift |
| `.st` | String literals — content inside `"..."`, `TEXT("...")`, single-quoted YAML values | Bright but legible against dark background |
| `.nm` | Numeric literals: integers, floats (`0.f`, `1.5`, `42`), hex (`0xFF00`) | **Must not share color with `.kw`** — numbers sit next to keywords constantly (`static const float x = 0.5f`) and matching colors makes the role read as one. Sharing with `.ty` or a muted bronze/sand is fine when the palette is constrained |

**Identifier default.** Unwrapped tokens — function names, variable names, parens, braces, semicolons, `::` scope operators — render in `--code-fg`, the de-facto "identifier" color. Treat `--code-fg` as a sixth syntax color: it must clear the 4.5:1 contrast bar against the code background AND differ from every wrapped role above (especially `.ty`). The contract does not introduce a `.fn` / `.id` class because wrapping every identifier inflates HTML for marginal gain; let `--code-fg` carry that role.

### 9.2 — Palette Guidance per Direction

The token colors should harmonize with the direction's accent palette (§2), not introduce a sixth foreign color. Concrete starting points below, but **every palette must be audited against the two rules in §9.1**: `.ty` ≠ `--code-fg` and `.nm` ≠ `.kw`. The starting palettes below were authored before those rules existed and several violate them — fix on first use rather than copy-pasting blindly. For each direction also pick a `--code-fg` (the unwrapped-identifier color) that differs perceptibly from `.ty`.

- **FF-gold** — `.cm` `#7a6f56`, `.kw` `#c49a3c`, `.ty` `#f7eccf`, `.mc` `#e8c060`, `.st` `#f3d58b`, `.nm` `#c49a3c`
  *Audit:* `.ty` parchment matches typical cream `--code-fg`; `.nm` matches `.kw`. Bump `.ty` to `#e8b860` (rich gold) and `.nm` to `#9a7a3c` (muted bronze) on first use.
- **Persona-blue** — `.cm` `#6a7da0`, `.kw` `#f0c64a`, `.ty` `#efe9d9`, `.mc` `#d94545`, `.st` `#f0c64a`, `.nm` `#f0c64a`
  *Audit:* `.ty` matches cream `--code-fg`; `.nm` matches `.kw` and `.st`. Bump `.ty` to `#a8c0e8` (soft cobalt-blue) and `.nm` to `#c0a040` (muted gold).
- **Octopath-watercolor** — `.cm` `#8a9c92`, `.kw` `#d99a6c`, `.ty` `#b8d2c4`, `.mc` `#a86850`, `.st` `#e3c89a`, `.nm` `#d99a6c`
  *Audit:* `.ty` sage is distinct from typical linen `--code-fg`. `.nm` matches `.kw`. Bump `.nm` to `#a87a50` (terra-bronze).
- **Chrono-pixel** — `.cm` `#7a7ca0`, `.kw` `#5fc6c2`, `.ty` `#f4e6a3`, `.mc` `#f0a1d4`, `.st` `#f4e6a3`, `.nm` `#5fc6c2`
  *Audit:* `.ty` amber is distinct from white code-fg. `.nm` matches `.kw`. Bump `.nm` to `#a8c4d0` (muted teal) so cyan keywords don't merge with cyan numbers.
- **Xenoblade-cosmic** — `.cm` `#5a6585`, `.kw` `#8c5fd9`, `.ty` `#b8d4ff`, `.mc` `#a8c8ff`, `.st` `#d4c5ff`, `.nm` `#8c5fd9`
  *Audit:* `.ty` and `.mc` are both pale-blue — too close; `.nm` matches `.kw`. Bump `.ty` to `#f0b8ff` (cosmic-rose, distinct from `.mc` accent), `.nm` to `#6a4ba8` (deep violet).
- **Dragon-Quest-classic** — `.cm` `#6a7faa`, `.kw` `#f5d442`, `.ty` `#ffffff`, `.mc` `#c44545`, `.st` `#f5d442`, `.nm` `#f5d442`
  *Audit:* `.ty` is literal white = white code-fg, vanishes. `.nm`, `.kw`, `.st` all share `#f5d442`. Bump `.ty` to `#a8c5ff` (heritage-blue-tint), `.nm` to `#c4a040` (muted slime-gold), and pick a `.st` shade like `#f0e6b0` to separate from `.kw`.
- **NieR-monochrome** — `.cm` `#7a7a7a`, `.kw` `#e36744`, `.ty` `#dcc89c`, `.mc` `#ff8159`, `.st` `#b8b5a8`, `.nm` `#a78a6e`
  *Verified palette (NieR bug-sweep campaign, 2026-05-27).* `.ty` warm sand pops against bone `--code-fg`; `.mc` hot orange visibly louder than `.kw` rust; `.nm` bronze keeps numbers distinct from keywords. Use these values as-is when picking NieR.
- **Tactics-Ogre-tactical** — `.cm` `#8b9aac`, `.kw` `#e89570`, `.ty` `#d8b365`, `.mc` `#e85f3c`, `.st` `#f5d442`, `.nm` `#d8b365`
  *Audit:* `.nm` matches `.ty`, which §9.1 permits — but verify against cream `--code-fg` first; gold `.ty` is distinct enough from cream identifiers to be safe.

Hex values are starting points, not prescriptions — tune for the 4.5:1 contrast bar against the chosen code background, and screenshot a representative code block (function declaration with macros + types + numbers + strings) before locking the palette. Playwright + `npx playwright install chromium` is a fast local-loop for this; one screenshot per palette tweak is enough to catch the vanishing-types / vanishing-numbers bug before the user does.

### 9.3 — CSS Skeleton

The token rules live in `base.css` (the `pre code` block and the six `pre code .cm/.kw/.ty/.mc/.st/.nm` rules, the `pre code` reset per §5.12, and the print collapse). Each `skin-*.css` defines the palette variables in `:root` — `--code-bg`, `--code-fg`, and the six `--syn-*` properties. The skin never touches the token rules themselves; the base never declares the variables it consumes. This is the layered split.

**Base.css skeleton** (do not copy-paste — read the file at generation time):

```css
:root {
  /* Declared by the skin, consumed here — base.css never sets these. */
  --code-bg: ;  /* from skin */
  --code-fg: ;  /* from skin — MUST differ from --syn-ty (§9.1) */
  --syn-cm: ; --syn-kw: ; --syn-ty: ;
  --syn-mc: ; --syn-st: ; --syn-nm: ;
}

pre {
  background: var(--code-bg);
  color: var(--code-fg);
  /* ...sizing, padding, overflow... */
}

/* §5.12 — CRITICAL reset: the bare code { } rule used for inline code
   in prose does NOT leak into pre code. Without this, unwrapped tokens
   (parens, braces, semicolons, identifiers) vanish into the background. */
pre code {
  color: var(--code-fg);
  background: transparent;
  border: none;
  padding: 0;
  font-size: inherit;
}

pre code .cm { color: var(--syn-cm); font-style: italic; }
pre code .kw { color: var(--syn-kw); font-weight: 600; }
pre code .ty { color: var(--syn-ty); }
pre code .mc { color: var(--syn-mc); font-weight: 600; }
pre code .st { color: var(--syn-st); }
pre code .nm { color: var(--syn-nm); }

@media print {
  pre code .cm, pre code .kw, pre code .ty,
  pre code .mc, pre code .st, pre code .nm {
    color: #333 !important;
    font-style: normal !important;
    font-weight: normal !important;
  }
}
```

**Skin `:root` block** (the variables base.css consumes for syntax highlighting):

```css
:root {
  --code-bg: #1a1a1a;
  --code-fg: #f0ede5;
  --syn-cm: #7a7a7a;
  --syn-kw: #e36744;
  --syn-ty: #dcc89c;
  --syn-mc: #ff8159;
  --syn-st: #b8b5a8;
  --syn-nm: #a78a6e;
}
```

The planner reads `base.css` verbatim, reads the chosen skin's `:root` block, and inlines both into `<style>` at generation time. The CSS cascade is automatic — base comes first (token rules reference variables), skin comes second (variables resolve into the token rules).

### 9.4 — Markup Shape

Within a `<pre><code>` block, wrap tokens inline:

```html
<pre><code><span class="mc">UPROPERTY</span>()
<span class="ty">TArray</span>&lt;<span class="ty">FSoEInteractionCooldown</span>&gt; ActiveCooldowns;</code></pre>
```

Long multi-line comments may be wrapped in a single `<span class="cm">...</span>` spanning newlines — the class applies to all enclosed text.

### 9.5 — Difficulty Badge Styling

Each quest carries a `difficulty` value (`easy` / `medium` / `hard`) visible in both the TOC and the quest header. Recommended visual treatment:

- A small pill or chip in the quest header, near the eyebrow / dependency badge
- Consistent color coding across directions:
  - `easy` — green-leaning accent or muted green text on a pale background
  - `medium` — gold or amber accent
  - `hard` — vermilion or signal-red accent
- Adapt the exact shade to the direction's palette; the *relative* ordering (cool → warm → hot) carries the meaning.

---

## 10. UI Wireframe Mockup

For UI-bearing campaigns, `plan.html` includes one skin-matched **UI Layout Wireframe** between the TOC and the first quest, composed from the `mockup.css` kit (Layer 4) — so the reader can picture the result before the build steps.

**Trigger (auto-detect in Phase 2).** Include when the campaign produces something a user looks at or interacts with; skip when it has no visual surface.

- **Include** — editor tools / panels (Slate, ImGui), app screens, dashboards, HUDs / in-game UI, forms, settings, CLIs with structured output, dialogs, browser extensions.
- **Skip** — backend, data pipelines, refactors, build / CI, library / API surfaces, algorithm work, migrations.

Read the signals already in the Decision Summary (Main Quest, Planning Lens, quest titles mentioning panels / screens / views / lists). Announce the choice in one sentence; the user can drop it in Phase 3. When ambiguous, lean toward including a lightweight one.

**Compose** one `ui-mock-section` from only the primitives the UI needs (full kit + skeleton in `class-contract.md`) — one representative state at a realistic size, not multiple screens or a flow. Show an `ui-mock-empty` state when it documents a real UX decision. Annotate with **inline numbered badges** (`ui-mock-badge`) in normal flow plus a `ui-mock-legend` below — never absolutely-positioned overlays (they misalign on reflow at narrow widths).

**Compliance.** The mockup obeys the `class-contract.md` skin hard-rule (colors from skin vars only; explicit surface backgrounds; accent borders + accent text, never fills behind text) — that rule is what makes the dark-on-light fall-through bug impossible. It also clears §1: responsive (grids scroll internally, panes stack at 560px), no JS, print-safe. The §4.4 spot-check at 375px covers it.
