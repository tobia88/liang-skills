# plan.html Class Contract

The interface between the three generation layers. **Read this before authoring any `base.css`, any `skin-*.css`, or the Phase 2 body generator.** All three layers target the same class names defined here. Change a name here and you must update `base.css` + all skins + the generator in lockstep — that is why this is pinned first.

## The three layers

1. **Fixed semantic body (theme-agnostic).** Phase 2 generates *only* this — the variable per-campaign content. The HTML structure and class names are identical regardless of which aesthetic direction is chosen. No theme needs bespoke markup.
2. **`base.css`** — all structure + all 14 pitfall fixes (§5.1–5.14 of the design contract). Written and visually audited *once*. Contains **zero hardcoded colors** — every color, font, and the radius/shadow is a `var(--x)` resolved by the skin.
3. **`skin-<name>.css`** — the `:root` variable block (palette, fonts, syntax colors, geometry) **plus** motif rules. Motifs are pure CSS on the fixed structure: pseudo-elements, backgrounds, borders, `clip-path`, CSS counters, `::first-letter`. ~40–80 lines.
4. **Visual kits (conditional, Layer 4).** Three generic plan-visual kits — `mockup.css` (UI wireframe), `diagram.css` (flow/state diagram), `timeline.css` (sequence timeline). **At most one** is inlined per plan, only when Phase 2a planned a visual and the body contains the matching section class (design-contract §10). Like `base.css` they contain **zero hardcoded colors** — every value is a `var(--x)` from the skin interface below, or a `color-mix()` of those vars, so the visual **matches the plan's skin** rather than mimicking a real screenshot. Campaigns with no visual (the skip-biased default for backend / data / refactor / library work) omit this layer entirely.

At generation time `assemble_plan.py` (same directory) inlines `base.css` + the chosen `skin-*.css` (+ the matching visual kit when the body contains a plan-visual section) into a single `<style>` block in `plan.html`, in that order — no model re-types the CSS. **These `.css` files are authoring sources inside the skill — they never ship beside `plan.html`.** The output remains a self-contained single file (`self_contained` clause, §1 of the design contract).

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

## Optional plan-visual block (Layer 4)

When Phase 2a plans a visual (design-contract §10), the planner inserts **at most one** plan-visual section between the `</nav>` (TOC) and `<main class="quests">` — a `ui-mock-section`, a `diagram-section`, or a `timeline-section`. Each is composed from its kit's primitives — the planner picks only the pieces the deliverable needs. Annotations are **inline numbered badges** in normal flow, mirrored by a legend below the frame — never absolutely-positioned overlays.

### UI wireframe (`ui-mock-section`, kit: `mockup.css`)

For screen/panel/form-shaped deliverables. A tool panel uses tabs + list + grid; a web form uses fields + buttons; a CLI uses the terminal chrome.

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

### Flow / state diagram (`diagram-section`, kit: `diagram.css`)

For system-structure / control-flow deliverables: pipelines, subsystems talking to each other, state machines, branching logic. One bounded slice — 5–12 nodes, not an exhaustive map.

```html
<section class="diagram-section">
  <h2>System Flow — Parry Resolution</h2>

  <div class="diagram">
    <div class="diagram-flow">
      <div class="diagram-row">
        <div class="diagram-node is-start"><span class="diagram-node-label">Input pressed</span></div>
      </div>
      <div class="diagram-arrow"><span class="diagram-arrow-label">OnParryPressed</span></div>
      <div class="diagram-row">
        <div class="diagram-node is-decision"><span class="diagram-badge">1</span><span class="diagram-node-label">In parry window?</span><span class="diagram-node-sub">0.18s after guard raise</span></div>
      </div>
      <div class="diagram-branch">
        <div class="diagram-lane">
          <span class="diagram-lane-label">yes</span>
          <div class="diagram-node is-active"><span class="diagram-badge">2</span><span class="diagram-node-label">Riposte state</span></div>
        </div>
        <div class="diagram-lane">
          <span class="diagram-lane-label">no</span>
          <div class="diagram-node"><span class="diagram-node-label">Guard hold</span></div>
        </div>
      </div>
      <div class="diagram-arrow is-return"><span class="diagram-arrow-label">on recover</span></div>
      <div class="diagram-row">
        <div class="diagram-node is-end"><span class="diagram-node-label">Neutral</span></div>
      </div>
    </div>
  </div>

  <ol class="diagram-legend">
    <li><span class="diagram-badge">1</span><span><strong>Parry window</strong> — what it is and where it's checked.</span></li>
  </ol>
</section>
```

Node variants: `.is-start` / `.is-end` (pills), `.is-state` (persistent state), `.is-decision` (chamfered), `.is-active` (accent + pulse), `.is-muted` (external/out-of-scope, dashed). Arrows: vertical by default, `.is-h` horizontal inside a row, `.is-return` loop-back, `.is-flowing` animated dashes on a hot path. `.diagram-branch` lanes stack at 560px. No inline styles needed.

### Sequence timeline (`timeline-section`, kit: `timeline.css`)

For behavior-over-time deliverables: animation sequences, camera moves, travel/tween motion, handshakes, turn phases, cutscene beats. One sequence, not the whole game loop.

```html
<section class="timeline-section">
  <h2>Sequence Timeline — Travel Mode</h2>

  <div class="timeline">
    <div class="timeline-scroll">
      <div class="timeline-grid" style="--tl-cols: 8;">
        <div class="timeline-ruler">
          <span class="timeline-ruler-corner">track</span>
          <div class="timeline-ruler-ticks">
            <span class="timeline-tick">0s</span><span class="timeline-tick">1s</span><!-- one per column -->
          </div>
        </div>
        <div class="timeline-track">
          <span class="timeline-track-label">Camera</span>
          <div class="timeline-lane">
            <span class="timeline-seg" style="--tl-start: 1; --tl-span: 3;"><span class="timeline-badge">1</span>zoom to map</span>
            <span class="timeline-marker" style="--tl-start: 4;"></span>
          </div>
        </div>
        <div class="timeline-track">
          <span class="timeline-track-label">Token</span>
          <div class="timeline-lane">
            <span class="timeline-seg is-muted" style="--tl-start: 3; --tl-span: 5;">node-to-node travel</span>
            <span class="timeline-token"></span>   <!-- animated; rests mid-lane when motion is off -->
          </div>
        </div>
      </div>
    </div>

    <div class="timeline-beats">   <!-- optional storyboard strip; numbered via CSS counter -->
      <div class="timeline-beat"><span class="timeline-beat-title">Confirm route</span><span class="timeline-beat-desc">planner panel collapses</span></div>
      <div class="timeline-beat is-active"><span class="timeline-beat-title">Travel</span><span class="timeline-beat-desc">token follows spline</span></div>
    </div>
  </div>

  <ol class="timeline-legend">
    <li><span class="timeline-badge">1</span><span><strong>Camera move</strong> — what happens and what drives it.</span></li>
  </ol>
</section>
```

Grid placement uses the whitelisted inline custom props only: `--tl-cols` on `.timeline-grid` (column count, default 8), `--tl-start` / `--tl-span` on segments and markers. The tracks grid scrolls internally at narrow widths. Use the tracks grid, the beat strip, or both — whichever the sequence calls for.

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
| `.diagram-section` / `.diagram` | Diagram section + frame (Layer 4) | explicit `var(--surface)` bg; one bounded slice, 5–12 nodes |
| `.diagram-flow` / `.diagram-row` / `.diagram-branch` / `.diagram-lane` / `.diagram-lane-label` | Diagram layout | branch lanes stack at 560px |
| `.diagram-node` (+ `is-start/is-end/is-state/is-decision/is-active/is-muted`) / `.diagram-node-label` / `.diagram-node-sub` | Diagram nodes | `.is-active` = accent border + accent label + pulse; animation off under reduced-motion/print |
| `.diagram-arrow` (+ `is-h/is-return/is-flowing`) / `.diagram-arrow-label` | Connectors + edge labels | `.is-flowing` dash motion is additive emphasis only |
| `.diagram-badge` / `.diagram-legend` | Annotation marker + legend | same rules as `.ui-mock-badge` |
| `.timeline-section` / `.timeline` / `.timeline-scroll` / `.timeline-grid` | Timeline section + frame (Layer 4) | grid scrolls internally at narrow widths; columns via `--tl-cols` |
| `.timeline-ruler` / `.timeline-ruler-corner` / `.timeline-ruler-ticks` / `.timeline-tick` | Shared ruler | one tick per column |
| `.timeline-track` / `.timeline-track-label` / `.timeline-lane` | Labeled tracks | lane is the positioning context for the token |
| `.timeline-seg` (+ `is-muted/is-pulse`) / `.timeline-marker` | Positioned bars + event markers | placed via whitelisted `--tl-start`/`--tl-span` inline props |
| `.timeline-token` | Traveling dot (animated) | rests mid-lane — the informative frame — when motion is disabled |
| `.timeline-beats` / `.timeline-beat` / `.timeline-beat-title` / `.timeline-beat-desc` | Storyboard beat strip | numbered via CSS counter; wraps at narrow widths |
| `.timeline-badge` / `.timeline-legend` | Annotation marker + legend | same rules as `.ui-mock-badge` |

## Hard rules for skin authors

1. **Never add `text-transform: uppercase` to `.quest-title`, `.toc-item a`, or any identifier-bearing heading** (§5.9). Uppercase is allowed on `.eyebrow`, `.footer-heading`, `.note-card-title`, `.toc-heading`, `.notes-heading`, and pill/badge text — short prose with no identifiers. `.campaign-title` may be uppercased *only* if you are certain the title carries no class/function names.
2. **Define every variable** in the interface above. A missing variable silently resolves to nothing and breaks contrast.
3. **Audit the two §9.1 rules per skin**: `--syn-ty` ≠ `--code-fg`, and `--syn-nm` ≠ `--syn-kw`.
4. **Motifs are pure CSS only** — pseudo-elements, backgrounds, borders, `clip-path`, CSS counters, gradients, `::first-letter`. No new markup, no JS, no external assets.
5. **Don't reintroduce a 2-column quest body** (sidebar pattern). The footer pattern in `base.css` is the §5.13 fix; overriding it back to `grid-template-columns: 2fr 1fr` on `.quest` reopens the void bug.
6. **Visual-kit colors come only from the skin interface.** The Layer-4 kits (`mockup.css`, `diagram.css`, `timeline.css`) and any per-campaign visual markup must use `var(--x)` or `color-mix()` of those vars — never raw hex. Every text-bearing visual container must set an explicit `var(--surface)`/`var(--surface-alt)` background so content can't fall through to a mismatched page color (the dark-on-light contrast bug). Active/checked/selected states use accent **borders + accent text on a surface background**, never an accent fill behind text.
7. **Kit animation is CSS-only and additive.** Keyframes live in the kit files only — never inline, never per-campaign, no JS. The static resting style must carry the full meaning by itself; animation may emphasize but never encode information that disappears when it stops. `prefers-reduced-motion: reduce` and `@media print` must disable every kit animation, and resting positions are chosen to be the informative frame (e.g., the timeline token rests mid-lane, not at the origin).
```
