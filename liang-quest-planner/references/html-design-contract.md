# HTML Design Contract

This document governs the `plan.html` generation phase of `liang-quest-planner`. It defines the **quality floor every output must clear**, the **aesthetic catalog** the planner picks from, the **selection heuristics** for matching direction to campaign, the **delegation protocol** for soft-handing-off to `frontend-design`, the **CSS pitfall guardrails** to avoid common AI-generated layout bugs, and the **anti-patterns** that mark generic AI-slop output.

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

## 4. Delegation Protocol

The planner soft-delegates HTML generation to the `frontend-design:frontend-design` skill when available.

### 4.1 Detection

Check whether `frontend-design:frontend-design` (or the bare alias `frontend-design`) appears in the current environment's skill list. If neither is present, fall back to inline generation.

### 4.2 Delegation Prompt Composition

When delegating, the prompt to `frontend-design:frontend-design` must include:

1. **Output path**: the absolute path to `plan.html` in the campaign folder
2. **Chosen aesthetic direction**: name, palette hex anchors, typography pairing, decorative motif, layout direction (copy verbatim from the catalog entry above)
3. **Content map**: the full Decision Summary content to render — hero metadata, TOC, per-quest sections, campaign notes, footer attribution
4. **HTML Quality Contract**: all nine clauses verbatim from section 1 above
5. **CSS Pitfall Guardrails**: all clauses verbatim from section 5 below
6. **Anti-patterns**: section 6 below verbatim
7. **Required Content Map**: the structural elements every output must contain

### 4.3 Fallback

If delegation is unavailable, fails, or produces output that obviously violates the quality contract (e.g., the file isn't written, or a quick visual check fails), the planner generates the HTML inline using the same direction, palette, contract, and pitfall guardrails. The fallback path produces correct HTML — just with less of the specialist polish frontend-design adds.

### 4.4 Verification

Regardless of path, after generation:

- Confirm the file exists at the expected path
- Spot-check that anchor IDs match `href` values for the TOC
- Confirm no `<script>` tags appear in the output
- Confirm the output is a single self-contained file

---

## 5. CSS Pitfall Guardrails

These are common AI-generated CSS bugs the generator must actively avoid. Codify them here so both delegated and fallback paths know to watch for them.

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

---

## 8. Version & Provenance

- Contract version: 1.4
- Authored: 2026-05-27
- Owning skill: `liang-quest-planner`
- Companion skill (soft dependency): `frontend-design:frontend-design`
- Revisions:
  - v1.1 — added §9 syntax highlighting; difficulty badge added to §7 required content; code_blocks / accessible / print_safe clauses in §1 extended to cover highlighting tokens.
  - v1.2 — added §5.8 (reading margins and desktop content width); codifies tech-blog default widths (`max-width: 1080–1200px`, `48–64px` side padding) after the planner shipped a cramped 880px / 32px default that the user flagged as too tight to read.
  - v1.3 — added §5.9 (don't uppercase identifier-bearing titles), §5.10 (pills need `white-space: nowrap`), §5.11 (multi-column tables don't fit auto-fit cards); revised §5.8 to bump the default range to `1280–1400px` after 1120px still felt cramped on 1920px+ displays with 2:1 quest-body grids.
  - v1.4 — added §5.12 (inline-`code` base styling leaks into `<pre><code>`); strengthened §9.1 with explicit `.ty ≠ --code-fg` and `.nm ≠ .kw` rules + an "identifier default" note treating `--code-fg` as a sixth syntax color; audited §9.2 palette starting points (NieR-monochrome re-tuned and verified, other directions annotated with required first-use bumps); added the `pre code` reset and `--code-fg` declaration to §9.3 skeleton. Driven by the interaction-system bug-sweep campaign where the NieR starting palette made types vanish into identifiers and numbers merge with keywords; lesson generalized so future palettes catch the same bugs before the user does.

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

```css
:root {
  /* Code-block surface + the de-facto identifier color (see §9.1) — both
     must be picked per-direction. --code-fg must differ perceptibly from
     --syn-ty or every type name reads as identifier-tone. */
  --code-bg: #1a1a1a;
  --code-fg: #f0ede5;

  /* Six syntax-token colors. Tune per-direction; see §9.2. */
  --syn-cm: #7a7a7a;
  --syn-kw: #e36744;
  --syn-ty: #dcc89c;
  --syn-mc: #ff8159;
  --syn-st: #b8b5a8;
  --syn-nm: #a78a6e;
}

pre {
  background: var(--code-bg);
  color: var(--code-fg);
  /* ...sizing, padding, overflow... */
}

/* CRITICAL: reset every inherited property on pre code so the bare `code`
   rule used for inline code in prose does NOT leak into the dark code
   block. Without this reset, unwrapped tokens (parens, braces, semicolons,
   plain identifiers) vanish into the background. See Pitfall §5.12. */
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

Declare both `--code-fg` and the `--syn-*` custom properties in `:root` so they can be tuned per-direction without touching the highlighting CSS itself. The `pre code` reset is the load-bearing line — every inline `code { color: ...; background: ...; border: ...; padding: ...; }` rule for prose elsewhere in the stylesheet *will* match `pre code` unless this reset short-circuits it.

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
