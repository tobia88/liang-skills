# Hybrid Strategy Report Template

Use this reference when finalizing a `liang-brainstorm-relentless` session.

The final report must be a single self-contained `.html` file:

- CSS only
- no JavaScript
- no external fonts, images, or dependencies
- no embedded JSON state in v1
- native `<details>`/`<summary>` for collapsible Quest Log entries
- HTML-escape all user/project-provided text
- formal artifact name: `Strategy Report`
- JRPG terms are functional labels, not full roleplay

## Required Report Shape

Use a Two-Layer Strategy Report:

1. **Hero Header**
   - report title
   - date/time generated
   - planning lens
   - qualitative readiness
   - badges for status/lens/report type
2. **Quick Read**
   - shareable summary
   - final recommendation
   - one immediate next move
   - top risks
3. **Main Strategy Report**
   - Main Quest / Project Brief
   - Decision Memo
   - Decision Table
   - Victory Conditions
   - Scope Boundary
   - Boss Board / Risks
   - Fog of War / Open Questions
4. **Context and Checks**
   - Scouted Project Context
   - Referenced Paths
   - Universal Clarity Checklist
   - Domain-Specific Checklist
5. **Private Appendix**
   - collapsible Quest Log
   - notes, recommendations, pushbacks, rejected/deferred paths

## HTML Skeleton

Replace bracketed placeholders with final content. Remove empty sections that are irrelevant, but keep the overall two-layer structure.

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>[REPORT_TITLE] — Brainstorm Strategy Report</title>
  <style>
    :root {
      --bg: #f6f1e8;
      --paper: #fffaf0;
      --paper-2: #fffdf8;
      --ink: #252338;
      --muted: #6f6984;
      --line: rgba(45, 40, 70, 0.14);
      --deep: #17182e;
      --deep-2: #232245;
      --gold: #d6a84f;
      --gold-2: #f3d58b;
      --blue: #4b7bd8;
      --violet: #7b5cc8;
      --danger: #b85757;
      --ok: #3f8f6b;
      --warn: #b8872c;
      --shadow: 0 18px 50px rgba(31, 27, 49, 0.12);
      --radius: 18px;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      background:
        radial-gradient(circle at top left, rgba(214, 168, 79, 0.18), transparent 30rem),
        radial-gradient(circle at top right, rgba(75, 123, 216, 0.16), transparent 28rem),
        var(--bg);
      color: var(--ink);
      font: 16px/1.65 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    a { color: var(--blue); }

    .page {
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 32px 0 56px;
    }

    .hero {
      position: relative;
      overflow: hidden;
      border-radius: 28px;
      padding: 34px;
      background:
        linear-gradient(135deg, rgba(214,168,79,0.16), transparent 28%),
        linear-gradient(145deg, var(--deep), var(--deep-2));
      color: #fff8e8;
      box-shadow: var(--shadow);
    }

    .hero::after {
      content: "";
      position: absolute;
      inset: auto -80px -120px auto;
      width: 280px;
      height: 280px;
      border-radius: 999px;
      background: rgba(123, 92, 200, 0.22);
      filter: blur(4px);
    }

    .eyebrow {
      margin: 0 0 10px;
      color: var(--gold-2);
      font-size: 0.8rem;
      font-weight: 800;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }

    h1, h2, h3 {
      margin: 0;
      line-height: 1.2;
    }

    h1 {
      position: relative;
      z-index: 1;
      max-width: 820px;
      font-size: clamp(2rem, 4vw, 4rem);
      letter-spacing: -0.045em;
    }

    .subtitle {
      position: relative;
      z-index: 1;
      max-width: 780px;
      margin: 14px 0 0;
      color: rgba(255, 248, 232, 0.82);
      font-size: 1.05rem;
    }

    .meta-grid {
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-top: 26px;
    }

    .meta-card {
      padding: 14px 16px;
      border: 1px solid rgba(255,255,255,0.14);
      border-radius: 16px;
      background: rgba(255,255,255,0.07);
      backdrop-filter: blur(8px);
    }

    .meta-label {
      display: block;
      color: rgba(255,248,232,0.62);
      font-size: 0.72rem;
      font-weight: 800;
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }

    .meta-value {
      display: block;
      margin-top: 4px;
      font-weight: 800;
    }

    .badges {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 22px;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(255,255,255,0.11);
      border: 1px solid rgba(255,255,255,0.16);
      color: rgba(255,248,232,0.9);
      font-size: 0.8rem;
      font-weight: 750;
    }

    .section {
      margin-top: 24px;
    }

    .section-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin: 34px 0 14px;
    }

    .section-title h2 {
      font-size: 1.45rem;
      letter-spacing: -0.02em;
    }

    .section-title .label {
      color: var(--muted);
      font-size: 0.78rem;
      font-weight: 800;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 16px;
    }

    .card {
      grid-column: span 6;
      padding: 22px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: linear-gradient(180deg, var(--paper-2), var(--paper));
      box-shadow: 0 12px 28px rgba(31, 27, 49, 0.07);
    }

    .card.full { grid-column: 1 / -1; }
    .card.third { grid-column: span 4; }
    .card.two-third { grid-column: span 8; }

    .card h3 {
      margin-bottom: 10px;
      color: var(--deep-2);
      font-size: 1.05rem;
    }

    .card p:first-child { margin-top: 0; }
    .card p:last-child { margin-bottom: 0; }

    .callout {
      border-left: 5px solid var(--gold);
    }

    .danger { border-left: 5px solid var(--danger); }
    .ok { border-left: 5px solid var(--ok); }
    .warn { border-left: 5px solid var(--warn); }

    ul, ol { padding-left: 1.25rem; }

    .pill-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding: 0;
      list-style: none;
    }

    .pill-list li {
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(75, 123, 216, 0.09);
      border: 1px solid rgba(75, 123, 216, 0.16);
      color: #283b70;
      font-size: 0.88rem;
      font-weight: 700;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      overflow: hidden;
      border-radius: 14px;
      background: #fffefa;
      font-size: 0.94rem;
    }

    th, td {
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
      text-align: left;
    }

    th {
      background: rgba(23, 24, 46, 0.94);
      color: #fff8e8;
      font-size: 0.78rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    tr:last-child td { border-bottom: 0; }

    .status {
      display: inline-flex;
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 800;
      white-space: nowrap;
    }

    .status.recommended { background: rgba(63, 143, 107, 0.13); color: #2d6d52; }
    .status.deferred { background: rgba(184, 135, 44, 0.15); color: #805d1d; }
    .status.rejected { background: rgba(184, 87, 87, 0.13); color: #8d3f3f; }
    .status.open { background: rgba(75, 123, 216, 0.13); color: #315aa5; }
    .status.weak { background: rgba(123, 92, 200, 0.12); color: #5d45a0; }

    details {
      border: 1px solid var(--line);
      border-radius: 14px;
      background: rgba(255,255,255,0.66);
      margin: 10px 0;
      overflow: hidden;
    }

    summary {
      cursor: pointer;
      padding: 14px 16px;
      font-weight: 850;
      color: var(--deep-2);
      background: rgba(23, 24, 46, 0.045);
    }

    .details-body {
      padding: 14px 16px 18px;
    }

    .qa {
      display: grid;
      grid-template-columns: 130px 1fr;
      gap: 8px 14px;
      margin: 0;
    }

    .qa dt {
      color: var(--muted);
      font-size: 0.78rem;
      font-weight: 850;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .qa dd { margin: 0; }

    .footer {
      margin-top: 34px;
      padding: 20px 0 0;
      color: var(--muted);
      font-size: 0.9rem;
      text-align: center;
    }

    @media (max-width: 860px) {
      .meta-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .card, .card.third, .card.two-third { grid-column: 1 / -1; }
    }

    @media (max-width: 560px) {
      .page { width: min(100% - 20px, 1120px); padding-top: 16px; }
      .hero { padding: 24px; border-radius: 22px; }
      .meta-grid { grid-template-columns: 1fr; }
      .qa { grid-template-columns: 1fr; }
    }

    @media print {
      body { background: #fff; }
      .page { width: 100%; padding: 0; }
      .hero, .card { box-shadow: none; }
      .hero { border-radius: 0; }
      details { break-inside: avoid; }
    }
  </style>
</head>
<body>
  <main class="page">
    <header class="hero">
      <p class="eyebrow">Brainstorm Strategy Report</p>
      <h1>[REPORT_TITLE]</h1>
      <p class="subtitle">[ONE_SENTENCE_SUMMARY]</p>

      <section class="meta-grid" aria-label="Report metadata">
        <div class="meta-card">
          <span class="meta-label">Generated</span>
          <span class="meta-value">[DATE]</span>
        </div>
        <div class="meta-card">
          <span class="meta-label">Planning Lens</span>
          <span class="meta-value">[LENS]</span>
        </div>
        <div class="meta-card">
          <span class="meta-label">Readiness</span>
          <span class="meta-value">[READINESS]</span>
        </div>
        <div class="meta-card">
          <span class="meta-label">Status</span>
          <span class="meta-value">[FINAL_OR_FOGGY]</span>
        </div>
      </section>

      <div class="badges">
        <span class="badge">Main Quest</span>
        <span class="badge">Decision Memo</span>
        <span class="badge">Private Working Notes</span>
      </div>
    </header>

    <section class="section">
      <div class="section-title">
        <h2>Quick Read</h2>
        <span class="label">Shareable Layer</span>
      </div>

      <div class="grid">
        <article class="card full callout">
          <h3>Shareable Summary</h3>
          <p>[SHAREABLE_SUMMARY]</p>
        </article>

        <article class="card two-third ok">
          <h3>Final Recommendation</h3>
          <p>[FINAL_RECOMMENDATION]</p>
        </article>

        <article class="card third">
          <h3>Immediate Next Move</h3>
          <p>[ONE_IMMEDIATE_NEXT_MOVE]</p>
        </article>

        <article class="card full warn">
          <h3>Top Risks</h3>
          <ul>
            <li>[TOP_RISK_1]</li>
            <li>[TOP_RISK_2]</li>
            <li>[TOP_RISK_3]</li>
          </ul>
        </article>
      </div>
    </section>

    <section class="section">
      <div class="section-title">
        <h2>Main Strategy Report</h2>
        <span class="label">Decision Layer</span>
      </div>

      <div class="grid">
        <article class="card full">
          <h3>Main Quest / Project Brief</h3>
          <p>[MAIN_QUEST_BRIEF]</p>
          <ul>
            <li><strong>Target user/stakeholder:</strong> [TARGET_USER]</li>
            <li><strong>Core problem:</strong> [CORE_PROBLEM]</li>
            <li><strong>Constraints:</strong> [CONSTRAINTS]</li>
          </ul>
        </article>

        <article class="card full">
          <h3>Decision Memo</h3>
          <p>[DECISION_MEMO]</p>
        </article>

        <article class="card full">
          <h3>Decision Table</h3>
          <table>
            <thead>
              <tr>
                <th>Path</th>
                <th>Status</th>
                <th>Reason</th>
                <th>Tradeoff</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>[PATH]</td>
                <td><span class="status recommended">Recommended</span></td>
                <td>[REASON]</td>
                <td>[TRADEOFF]</td>
                <td>[CONFIDENCE]</td>
              </tr>
              <tr>
                <td>[ALTERNATIVE_PATH]</td>
                <td><span class="status deferred">Deferred Side Quest</span></td>
                <td>[REASON]</td>
                <td>[TRADEOFF]</td>
                <td>[CONFIDENCE]</td>
              </tr>
            </tbody>
          </table>
        </article>

        <article class="card">
          <h3>Victory Conditions</h3>
          <ul>
            <li>[SUCCESS_CRITERION_1]</li>
            <li>[SUCCESS_CRITERION_2]</li>
            <li>[SUCCESS_CRITERION_3]</li>
          </ul>
        </article>

        <article class="card">
          <h3>Scope Boundary</h3>
          <p><strong>In scope:</strong></p>
          <ul>
            <li>[IN_SCOPE_ITEM]</li>
          </ul>
          <p><strong>Out of scope / Side Quests:</strong></p>
          <ul>
            <li>[OUT_OF_SCOPE_ITEM]</li>
          </ul>
        </article>

        <article class="card danger">
          <h3>Boss Board / Risks</h3>
          <ul>
            <li>[RISK_AND_MITIGATION]</li>
          </ul>
        </article>

        <article class="card">
          <h3>Fog of War / Open Questions</h3>
          <ul>
            <li>[OPEN_QUESTION]</li>
          </ul>
        </article>
      </div>
    </section>

    <section class="section">
      <div class="section-title">
        <h2>Context and Checks</h2>
        <span class="label">Traceability Layer</span>
      </div>

      <div class="grid">
        <article class="card full">
          <h3>Scouted Project Context</h3>
          <p>[SCOUTED_CONTEXT_SUMMARY]</p>
          <p><strong>Referenced paths:</strong></p>
          <ul>
            <li><code>[PATH]</code></li>
          </ul>
        </article>

        <article class="card">
          <h3>Universal Clarity Checklist</h3>
          <table>
            <thead>
              <tr>
                <th>Gate</th>
                <th>Status</th>
                <th>Note</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Main Quest</td>
                <td><span class="status recommended">Satisfied</span></td>
                <td>[NOTE]</td>
              </tr>
              <tr>
                <td>Success Criteria</td>
                <td><span class="status weak">Weak</span></td>
                <td>[NOTE]</td>
              </tr>
            </tbody>
          </table>
        </article>

        <article class="card">
          <h3>Domain-Specific Checklist</h3>
          <table>
            <thead>
              <tr>
                <th>Item</th>
                <th>Status</th>
                <th>Note</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>[DOMAIN_ITEM]</td>
                <td><span class="status recommended">Satisfied</span></td>
                <td>[NOTE]</td>
              </tr>
            </tbody>
          </table>
        </article>
      </div>
    </section>

    <section class="section">
      <div class="section-title">
        <h2>Private Appendix</h2>
        <span class="label">Working Notes</span>
      </div>

      <article class="card full">
        <h3>Quest Log</h3>
        <p>This section preserves the private reasoning trail: questions, options, recommendations, user choices, pushbacks, and decisions.</p>

        <details>
          <summary>[Q1_TITLE]</summary>
          <div class="details-body">
            <dl class="qa">
              <dt>Question</dt>
              <dd>[QUESTION]</dd>
              <dt>Options</dt>
              <dd>[OPTIONS_SUMMARY]</dd>
              <dt>Recommended</dt>
              <dd>[RECOMMENDATION_WITH_TRADEOFF_CONFIDENCE]</dd>
              <dt>User Answer</dt>
              <dd>[USER_ANSWER]</dd>
              <dt>Result</dt>
              <dd>[NORMALIZED_DECISION_OR_NOTE]</dd>
            </dl>
          </div>
        </details>
      </article>
    </section>

    <footer class="footer">
      Generated by liang-brainstorm-relentless. Treat this full report as private working notes unless intentionally shared.
    </footer>
  </main>
</body>
</html>
```

## Content Guidance

### Shareable Summary

Write this as if it may be pasted into a README, issue, design note, or collaborator message. Keep it concise and avoid private rambling.

Include:

- what is being planned
- what decision was made
- why that direction is recommended
- the main remaining risk or open question

### Private Quest Log

The Quest Log should preserve reasoning without dumping unnecessary chat filler.

For each meaningful question/decision, include:

- question asked
- options summary
- recommendation, tradeoff, confidence
- user answer
- normalized decision
- pushback/contradiction note if any

Use `<details>` entries so the report remains comfortable to read.

### Decision Table

Use statuses such as:

- `Recommended`
- `Rejected for v1`
- `Deferred Side Quest`
- `Still Viable`
- `Fog of War`

Keep the table concise. The goal is to remember why choices were made, not to recreate the whole conversation.

### Checklist Statuses

Use:

- `Satisfied`
- `Weak`
- `Unresolved`

Do not use numeric readiness scores.

### Incomplete / Foggy Reports

If the user finalized early, make it obvious:

- Hero status: `Incomplete / Foggy`
- Quick Read includes missing gates
- Fog of War lists unresolved critical items
- Checklist marks weak/unresolved gates honestly

### HTML Safety

Escape user/project text before inserting into HTML:

- `&` → `&amp;`
- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;` when inside attributes

Do not include raw secrets, tokens, `.env` contents, credentials, or large file excerpts.
