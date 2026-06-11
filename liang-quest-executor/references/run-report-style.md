# Run Report — Markdown Style Contract

Run reports use native Markdown structure only — no HTML, CSS, JavaScript, images, or external dependencies.

## Headings

- `# Run Report` — top-level title.
- `## Quest Results` — summary table (see below).
- `## Quest Details` — per-quest breakdown with step tables.
- `## Lessons` — structured failure records.
- `## Deferred UAT` — Tier 2 victory condition items.
- Sub-headings under quest details use `### <Quest ID>: <Title>`.

## Tables

- **Quest Results table:** columns for Quest ID, Title, Difficulty, Steps, Retries, Status.
- **Step Details table** (per quest): columns for Step ID, Description, Retries, Status.
- Use plain pipe-delimited Markdown tables with header separator.

## Checklists

- **Tier 1 VC results:** `[x]` for pass, `[ ]` for fail, rendered as a flat checklist per quest.
- No custom icons or images — rely on Markdown task list syntax (`- [x]` / `- [ ]`).

## Text Status Badges

Use inline code or pipe-delimited text — no colored spans:

- `[PASS]` — quest or step passed.
- `[FAIL]` — quest or step failed.
- `[SKIP]` — quest cascade-skipped.
- `[PENDING UAT]` — quest passed provisionally with deferred Tier 2 VCs.
- `[RETRY N]` — step succeeded after N retries.

## YAML Front Matter

- Structured machine-readable run data lives in the YAML front matter block.
- All keys are neutral and formal (no JRPG labels).

## General Rules

- No HTML tags, CSS classes, style attributes, or inline styles.
- No JavaScript, images, or external resources of any kind.
- Escape all source-derived content (file paths, user input) appropriately.
- JRPG-flavored labels appear only in the human-readable Markdown body; YAML keys remain neutral and formal.
