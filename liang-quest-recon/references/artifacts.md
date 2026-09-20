# Recon Artifact Contract

Canonical file formats, statuses, and per-stage gates for `liang-quest-recon`. Workers and orchestrators of every harness conform to this document; the stage briefs and workflow scripts embed excerpts of it, but this file wins on conflict.

## Folder Layout

```
<prototype-stem>-breakdown/
  00-index.md            # stage 5 — the entry point everyone reads first
  NN-<system-id>.md      # stages 2–4 — one per system, NN = zero-padded order
  _chunkmap.json         # stage 1 — line-range partition of the prototype
  _features.json         # after stage 2 — merged per-system feature checklists
  _features/<id>.json    # optional per-system fragments (child-parallel profile), merged then kept or deleted
  _delta-<prev>.md       # stage 1, optional — structural delta vs a prior prototype version
  _consistency.md        # stage 5 — cross-doc audit
```

## Status Vocabulary (per feature, exactly one)

- **done** — the target codebase substantially implements the mechanic. Evidence: the core implementation `path:line`.
- **partial** — a counterpart exists but meaningful prototype behavior is absent. Evidence: what exists; note names what is absent.
- **missing** — no counterpart found after an honest search including alternative names/synonyms. Note lists the searches run.
- **divergent** — a counterpart exists but deliberately differs. Evidence cites both sides (prototype line ref + code `path:line`); note flags whether it matches a locked decision. **Locked-decision rule: a feature conflicting with a locked decision is `divergent`, never `missing` — the decision supersedes the prototype.**
- **prototype-only** — exists to serve the prototype medium itself (page chrome, localStorage persistence, embedded-asset handling, debug harness). Not ported.
- **oos-native** — the feature's natural home is a layer the scope directive excludes (e.g. Blueprint/UMG/flow-graph assets under a code-only directive). Not assessed; never used as an escape hatch for a lazy search.

**Evidence rules:** every done/partial/divergent verdict cites at least one repo-relative `path:line` the worker actually opened; a skeptic will re-open every citation and a citation that does not support its verdict fails the whole document. Comparison is by MECHANIC, not medium — a prototype CSS behavior counts as done if the equivalent mechanic exists in target code.

## Per-System Doc (`NN-<system-id>.md`)

Frontmatter:

```yaml
---
system: <kebab-id>
title: <Title>
prototype_lines: "<start-end, start-end, ...>"
depends_on: [<system ids>]
status: breakdown | compared | verified
---
```

`status` transitions strictly forward: `breakdown` (stage 2 wrote it) → `compared` (stage 3 appended) → `verified` (stage 4 passed, possibly after its one fix round). A doc flagged with residual errors stays `compared` and is listed in the index.

Stage-2 sections (in order): `## What the prototype does` · `## Data & formulas` · `## UI / presentation` · `## Dependencies & integration points` · `## Prototype-only` · `## Open questions`. Every claim carries a line ref like `(L4620)` or `(L4620-4655)`; constants/formulas verbatim; bulk content data (dialogue rows, item lists) documented as schema + row count + 2–3 representative rows, never transcribed wholesale.

Stage-3 appended sections: `## Current state` (one orienting paragraph — which modules/classes cover this system, plus an "ahead of prototype" note where code exceeds it — then the full table `| # | Feature | Status | Evidence | Note |`, one row per checklist feature, same order and numbering as `_features.json`) · `## Missing` (missing features grouped into coherent gap clusters referencing row numbers) · `## Modify (divergent)` (one bullet per divergent row: prototype behavior with line ref vs code behavior with `path:line`, locked-decision flag).

## `_chunkmap.json`

```json
{
  "total_lines": 15038,
  "systems": [{ "id": "kebab-id", "title": "...", "order": 1, "purpose": "one line",
                "ranges": [{ "start": 18, "end": 34 }], "depends_on": ["other-id"] }],
  "shared_core": [{ "start": 2585, "end": 2624, "label": "why it is load-bearing" }],
  "excluded":  [{ "start": 14137, "end": 15036, "reason": "why out of scope" }],
  "uncovered": [{ "start": 0, "end": 0 }],
  "notes": "mapper findings worth the orchestrator's attention"
}
```

Partition law: every line `1..total_lines` in exactly one bucket (a system range, shared_core, or excluded — boilerplate goes to excluded with reason "boilerplate"); ranges never overlap; `uncovered` lists leftovers > 20 lines (target: none). `total_lines` is the mapper's own authoritative count, not the orchestrator's seed. Shared core hard cap: 800 lines total.

## `_features.json`

```json
{
  "comment": "unit of assessment for stages 3-4",
  "systems": [{ "order": 1, "id": "kebab-id", "title": "...",
                "ranges": "18-34, 251-296",
                "features": ["10-25 SHORT atomic capability names"] }]
}
```

Features are atomic capabilities ("stamina ticks down per road segment"), not vague umbrellas ("travel works") — each is individually verdicted. Same id/order as the chunk map.

## `_delta-<prev>.md`

Sections: `New in <current>` · `Substantially grown` (rough old→new size) · `Roughly unchanged` · `Notes for the compare stage` (which systems should be presumed to have existing counterparts vs fresh). Under ~120 lines.

## `_consistency.md`

Five sections mirroring the mandates: **1 Dependency symmetry** (frontmatter/prose asymmetries between docs) · **2 Ownership** (each overlap candidate resolved to a single owning doc; double-counts and orphans flagged) · **3 Delta traceability** (every delta "new" item mapped to a doc's feature rows; orphans flagged) · **4 Cross-resolved open questions** · **5 Status sanity** (contradicting statuses for the same underlying mechanic across docs). Findings carry severity `info | warn | error`.

## `00-index.md`

Frontmatter: `title`, `source_prototype` (absolute path — the saga planner matches on this), `generated` (date), `pipeline` (run identifiers). Sections, in order:

1. `# Executive summary` — the port gap in one page; what exists, the big holes, where the codebase is ahead. No campaign decomposition (that is the saga planner's job).
2. `# System status table` — one row per system: feature count, per-status counts, verify outcome (`pass` / `fail(+n residual)` / `unverified`), plus a totals row.
3. `# Locked-decision divergences` — every divergent row attributable to a locked decision, gathered in one place, with "respect, don't re-litigate" framing.
4. `# Cross-cutting seams` — shared-state ownership map in target-codebase terms, ownership resolutions worth a planner's attention, unresolved warn/error consistency issues.
5. `# Open questions rollup` — deduplicated, cross-resolution applied, each tagged `[design]` vs `[code]`.
6. `# How to consume this folder` — reading order, what the support files are, and the planner contract: treat this folder (not the raw prototype) as intake; `divergent`/`prototype-only`/`oos-native` rows are not work; scope campaigns from Missing and Modify sections; build on code that is ahead of the prototype.

## Stage Gates (orchestrator acceptance checklist)

- **Stage 1**: partition law holds (verify arithmetically); system count 6–30 (12–20 target — merge trivia into owners); exclusions match the known-already-ported list; shared core ≤ 800 lines; boundaries were read-verified by the mapper.
- **Stage 2**: one doc per system, template-complete, `status: breakdown`; 10–25 features each; smoke-test two line refs from different docs by grepping the prototype yourself.
- **Stage 3**: every doc `status: compared`; table rows = checklist length; status counts sum correctly.
- **Stage 4**: every doc verdicted; failed docs got exactly one fix round; residuals flagged, not hidden.
- **Stage 5**: `_consistency.md` has all five sections; `00-index.md` has all six; read the index yourself before presenting it.
