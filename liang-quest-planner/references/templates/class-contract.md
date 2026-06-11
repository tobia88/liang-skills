# plan.html Class Contract

The interface between the three generation layers. **Read this before authoring any `base.css`, any `skin-*.css`, or the Phase 2 body generator.** All three layers target the same class names defined here. Change a name here and you must update `base.css` + all skins + the generator in lockstep — that is why this is pinned first.

## The three layers

1. **Fixed semantic body (theme-agnostic).** Phase 2 generates *only* this — the variable per-campaign content. The HTML structure and class names are identical regardless of which aesthetic direction is chosen. No theme needs bespoke markup.
2. **`base.css`** — all structure + all 14 pitfall fixes (§5.1–5.14 of the design contract). Written and visually audited *once*. Contains **zero hardcoded colors** — every color, font, and the radius/shadow is a `var(--x)` resolved by the skin.
3. **`skin-<name>.css`** — the `:root` variable block (palette, fonts, syntax colors, geometry) **plus** motif rules. Motifs are pure CSS on the fixed structure: pseudo-elements, backgrounds, borders, `clip-path`, CSS counters, `::first-letter`. ~40–80 lines.
4. **`mockup.css` (conditional, Layer 4).** The generic UI-wireframe kit. Inlined **only** when the campaign is UI-bearing and the planner composes a wireframe (see design-contract §10). Like `base.css` it contains **zero hardcoded colors** — every value is a `var(--x)` from the skin interface below, or a `color-mix()` of those vars. The mockup therefore **matches the plan's skin** rather than mimicking a real screenshot. Backend / data / refactor campaigns omit this layer entirely.

At generation time `assemble_plan.py` (same directory) inlines `base.css` + the chosen `skin-*.css` (+ `mockup.css` when the body contains a `ui-mock-section`) into a single `<style>` block in `plan.html`, in that order — no model re-types the CSS. **These `.css` files are authoring sources inside the skill — they never ship beside `plan.html`.** The output remains a self-contained single file (`self_contained` clause, §1 of the design contract).

## CSS variable interface (skins MUST define every one)

`base.css` consumes only these variables and never declares them. Each `skin-*.css` MUST set all of them in `:root` or `base.css` will resolve to nothing.

```css
:root {
  /* surfaces + text */
  --bg:            /* page background */
  --surface:       /* card / panel / toc background */
  --surface-alt:   /* table header, code-path label, inline-code bg */
  --ink:           /* primary text */
  --ink-muted:     /* secondary text, captions */
  --accent:        /* primary accent (eyebrows, links-hover, markers) */
  --accent-2:      /* secondary accent */
  --rule:          /* borders + dividers */

  /* code block */
  --code-bg:
  --code-fg:       /* unwrapped-identifier color; MUST differ from --syn-ty (§9.1) */

  /* six syntax tokens (§9.1 taxonomy; audit .ty != --code-fg, .nm != .kw) */
  --syn-cm:  --syn-kw:  --syn-ty:  --syn-mc:  --syn-st:  --syn-nm:

  /* difficulty badge — cool -> warm -> hot ordering carries meaning (§9.5) */
  --diff-easy:    --diff-medium:    --diff-hard:

  /* decision-table status pills */
  --pill-rec:     --pill-rej:       --pill-def:

  /* typography (system stacks only — no @import, no CDN) */
  --font-display:  --font-body:  --font-mono:

  /* feel */
  --radius:        /* 0 for sharp/brutalist (NieR), up to ~12px for rounded (Dragon-Quest) */
  --shadow:        /* a full box-shadow value, or "none" */
}
```

## Fixed body structure

The generator emits exactly this skeleton, filling content. Class names are the contract.

```html
<body>
  <div class="page">

    <header class="masthead">
      <div class="folio-bar">          <!-- optional readout strip; skins style or `display:none` -->
        <span>SLUG</span><span>DATE</span><span>N QUESTS</span><span>LENS</span>
      </div>
      <p class="eyebrow">PLANNING LENS</p>
      <h1 class="campaign-title">Campaign Title</h1>   <!-- NEVER text-transform if it may carry identifiers (§5.9) -->
      <dl class="masthead-meta">
        <div class="meta-item"><dt>Slug</dt><dd>...</dd></div>
        <div class="meta-item"><dt>Date</dt><dd>...</dd></div>
        <div class="meta-item"><dt>Quests</dt><dd>...</dd></div>
        <div class="meta-item"><dt>Lens</dt><dd>...</dd></div>
      </dl>
    </header>

    <nav class="toc">
      <h2 class="toc-heading">Quests</h2>
      <ol class="toc-list">
        <li class="toc-item">           <!-- ELEMENT CHILDREN ONLY, no bare text (flex layout, §5.1) -->
          <a href="#q001">Quest title</a>
          <span class="diff-badge diff-medium">medium</span>
          <span class="dep-state">depends: q-prev</span>
        </li>
      </ol>
    </nav>

    <main class="quests">
      <section class="quest" id="q001">
        <header class="quest-header">  <!-- element children only -->
          <span class="eyebrow quest-eyebrow">Quest 001</span>
          <span class="diff-badge diff-medium">medium</span>
          <h2 class="quest-title">Quest Title</h2>   <!-- NO uppercase (§5.9) -->
          <p class="quest-purpose">One or two sentences.</p>
        </header>

        <div class="quest-main">       <!-- full width; the §5.13 void-killer is structural here -->
          <ol class="steps">
            <li class="step">
              <h3 class="step-title">Step title</h3>
              <p class="step-desc">Description.</p>
              <figure class="code">
                <figcaption class="code-path">path/to/file.ext</figcaption>
                <pre><code><span class="mc">UPROPERTY</span>() <span class="ty">TArray</span>&lt;...&gt; X;</code></pre>
              </figure>
            </li>
          </ol>
          <p class="rationale">Brief why (1–2 sentences).</p>
        </div>

        <footer class="quest-footer">  <!-- 2-col strip, collapses at 720px -->
          <div class="quest-footer-col deps">
            <h4 class="footer-heading">Dependencies</h4>
            <ul class="dep-list"><li>q-prev — reason</li></ul>
          </div>
          <div class="quest-footer-col victory">
            <h4 class="footer-heading">Victory Conditions</h4>
            <ul class="vc-list"><li>condition</li></ul>
          </div>
        </footer>
      </section>
    </main>

    <section class="notes">
      <h2 class="notes-heading">Campaign Notes</h2>
      <div class="notes-grid">          <!-- narrative cards only; auto-fit (§5.11) -->
        <div class="note-card risk"><h3 class="note-card-title">Risks</h3><ul><li>...</li></ul></div>
        <div class="note-card question"><h3 class="note-card-title">Open Questions</h3><ul><li>...</li></ul></div>
      </div>
      <div class="notes-wide">          <!-- the wide table gets its OWN row (§5.11) -->
        <div class="note-card">
          <h3 class="note-card-title">Locked Decisions</h3>
          <table class="decisions">
            <thead><tr><th>Path</th><th>Status</th><th>Reason</th></tr></thead>
            <tbody>
              <tr><td>...</td><td><span class="pill pill-recommended">recommended</span></td><td>...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <footer class="page-footer">
      <p class="attribution">Generated by liang-quest-planner — TIMESTAMP</p>
    </footer>

  </div>
</body>
```

## Optional UI wireframe block (Layer 4)

When the campaign is UI-bearing (design-contract §10), the planner inserts **one** `ui-mock-section` between the `</nav>` (TOC) and `<main class="quests">`. It is composed from the generic `mockup.css` kit — the planner picks only the pieces the UI needs (a tool panel uses tabs + list + grid; a web form uses fields + buttons; a CLI uses the terminal chrome). Annotations are **inline numbered badges** in normal flow, mirrored by a legend below the frame.

```html
<section class="ui-mock-section">
  <h2>UI Layout Wireframe</h2>

  <div class="ui-mock">                          <!-- frame: explicit var(--surface) bg -->
    <div class="ui-mock-titlebar">
      <div class="ui-mock-tab is-active"><span class="ui-mock-badge">1</span>Tool Name</div>
    </div>

    <div class="ui-mock-toolbar">
      <div class="ui-mock-row">
        <span class="ui-mock-label">Field</span>
        <div class="ui-mock-field"><span class="ui-mock-badge">2</span><span class="ui-mock-swatch"></span>Value</div>
      </div>
      <div class="ui-mock-row">
        <span class="ui-mock-label">Mode</span>
        <div class="ui-mock-toggle-group">
          <span class="ui-mock-btn is-active"><span class="ui-mock-badge">3</span>Option A</span>
          <span class="ui-mock-btn">Option B</span>
        </div>
      </div>
    </div>

    <div class="ui-mock-body">                    <!-- explicit bg; never transparent -->
      <div class="ui-mock-group">Group Label <span class="ui-mock-count">(n)</span></div>
      <div class="ui-mock-list">
        <div class="ui-mock-item">
          <span class="ui-mock-check is-checked"></span>
          <span class="ui-mock-name">item_name</span>
          <span class="ui-mock-value">default</span>
        </div>
      </div>
    </div>

    <div class="ui-mock-divider"></div>

    <div class="ui-mock-gridwrap">
      <div class="ui-mock-grid" style="--mock-cols: 2fr 1fr 1fr;">
        <div class="ui-mock-grid-head">
          <span class="ui-mock-cell">Column A</span>
          <span class="ui-mock-cell">Column B</span>
          <span class="ui-mock-cell">Column C</span>
        </div>
        <div class="ui-mock-grid-row is-selected">
          <span class="ui-mock-cell">row_value</span>
          <span class="ui-mock-cell is-mono is-accent">0.85</span>
          <span class="ui-mock-cell is-mono is-muted">1.0</span>
        </div>
      </div>
    </div>

    <div class="ui-mock-statusbar"><span>n of m match</span><span>filter summary</span></div>
  </div>

  <ol class="ui-mock-legend">
    <li><span class="ui-mock-badge">1</span><span><strong>Region</strong> — what it is and how it behaves.</span></li>
  </ol>
</section>
```

Use only the pieces the UI calls for. An empty result area uses `<div class="ui-mock-empty">message</div>`. A sidebar+main layout wraps panes in `<div class="ui-mock-split">` with `.ui-mock-sidebar` + `.ui-mock-pane`. The grid column template is set per-instance via the `--mock-cols` inline custom property.

## Class registry

| Class | Role | Pitfall guardrails baked into base |
|-------|------|------------------------------------|
| `.page` | Main container | §5.8 widths (max 1360px, responsive padding) |
| `.masthead` / `.campaign-title` | Hero | §5.9 — base sets no uppercase on title |
| `.folio-bar` | Optional readout strip | skins style or `display:none` |
| `.masthead-meta` / `.meta-item` | Metadata grid | `min-width:0` on items (§5.2) |
| `.toc` / `.toc-list` / `.toc-item` | TOC | element-children-only for flex safety (§5.1); anchors must resolve (§5.3) |
| `.quest` | Quest section | `scroll-margin-top` for anchor jumps |
| `.quest-title` | Quest heading | §5.9 — no uppercase |
| `.quest-main` | Full-width content column | §5.13 — footer pattern instead of 2-col sidebar |
| `.quest-footer` / `.quest-footer-col` | 2-col strip | collapses at 720px (§5.4); `min-width:0` + code wrap (§5.14) |
| `.steps` / `.step` | Numbered steps | hanging counter via `::before` absolute, NOT grid (§5.1) |
| `.code` / `.code-path` / `pre` / `pre code` | Code block | `pre code` reset (§5.12); `overflow-x:auto`; file-path label |
| `pre code .cm/.kw/.ty/.mc/.st/.nm` | Syntax tokens | §9; print collapses to greyscale (§5.7) |
| `:not(pre) > code` | Inline code | `word-break`/`overflow-wrap` (§5.14); scoped so it can't leak into `pre code` (§5.12) |
| `.notes-grid` / `.note-card` | Narrative cards | auto-fit; `min-width:0` + code wrap (§5.11/5.14) |
| `.notes-wide` / `.decisions` | Wide table | own row, `table-layout:fixed`, cell `word-break` (§5.5/5.11) |
| `.pill` / `.pill-*` | Status pills | `white-space:nowrap` (§5.10) |
| `.diff-badge` / `.diff-easy/medium/hard` | Difficulty chip | `white-space:nowrap` (§5.10); §9.5 color ordering |
| `.eyebrow` | Small uppercase label | uppercase OK (short prose, no identifiers, §5.9) |
| `.rationale` | Brief why callout | left-accent-bar |
| `.page-footer` | Attribution | print-safe |
| `.ui-mock-section` / `.ui-mock` | Wireframe section + frame (Layer 4) | explicit `var(--surface)` bg — never transparent |
| `.ui-mock-titlebar` / `.ui-mock-tab` | Tab / window chrome | `.is-active` = accent stripe + surface bg, not a fill |
| `.ui-mock-toolbar` / `.ui-mock-row` / `.ui-mock-label` / `.ui-mock-field` / `.ui-mock-btn` | Form controls | `.is-active` btn = outlined accent (contrast-safe); fields wrap long strings (§5.14) |
| `.ui-mock-check` | Checkbox | `.is-checked` = accent border + accent check on surface |
| `.ui-mock-group` / `.ui-mock-list` / `.ui-mock-item` | Grouped list | `.is-collapsed` caret; `.is-selected` = accent left-border + color-mix tint |
| `.ui-mock-gridwrap` / `.ui-mock-grid` / `.ui-mock-cell` | Data grid | scrolls internally at narrow widths; cols via `--mock-cols` |
| `.ui-mock-split` / `.ui-mock-sidebar` / `.ui-mock-pane` / `.ui-mock-divider` | Split layout | collapses to stacked at 560px |
| `.ui-mock-statusbar` / `.ui-mock-empty` | Status strip / empty state | explicit surface bg |
| `.ui-mock-badge` / `.ui-mock-legend` | Inline annotation marker + legend | outlined accent badge, reflow-proof (no absolute overlays) |

## Hard rules for skin authors

1. **Never add `text-transform: uppercase` to `.quest-title`, `.toc-item a`, or any identifier-bearing heading** (§5.9). Uppercase is allowed on `.eyebrow`, `.footer-heading`, `.note-card-title`, `.toc-heading`, `.notes-heading`, and pill/badge text — short prose with no identifiers. `.campaign-title` may be uppercased *only* if you are certain the title carries no class/function names.
2. **Define every variable** in the interface above. A missing variable silently resolves to nothing and breaks contrast.
3. **Audit the two §9.1 rules per skin**: `--syn-ty` ≠ `--code-fg`, and `--syn-nm` ≠ `--syn-kw`.
4. **Motifs are pure CSS only** — pseudo-elements, backgrounds, borders, `clip-path`, CSS counters, gradients, `::first-letter`. No new markup, no JS, no external assets.
5. **Don't reintroduce a 2-column quest body** (sidebar pattern). The footer pattern in `base.css` is the §5.13 fix; overriding it back to `grid-template-columns: 2fr 1fr` on `.quest` reopens the void bug.
6. **Mockup colors come only from the skin interface.** `mockup.css` (Layer 4) and any per-campaign mockup markup must use `var(--x)` or `color-mix()` of those vars — never raw hex. Every text-bearing mockup container must set an explicit `var(--surface)`/`var(--surface-alt)` background so content can't fall through to a mismatched page color (the dark-on-light contrast bug). Active/checked/selected states use accent **borders + accent text on a surface background**, never an accent fill behind text.
```
