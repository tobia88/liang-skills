# Recon Artifact Contract

Canonical file formats, statuses, and per-stage gates for `liang-quest-recon`. Workers and orchestrators of every harness conform to this document; the stage briefs and workflow scripts embed excerpts of it, but this file wins on conflict.

## Folder Layout

```
<prototype-stem>-breakdown/
  00-index.md            # stage 5 (full) or brief 10 (lite) — the entry point everyone reads first
  NN-<system-id>.md      # stages 2–4 — one per system, NN = zero-padded order
  _run.json              # written at the Pre-Flight go — profile + intake parameters; what Resume reads first
  _chunkmap.json         # stage 1 — line-range partition of the prototype
  _features.json         # after stage 2 — merged per-system feature checklists
  _features/<id>.json    # optional per-system fragments (child-parallel profile), merged then kept or deleted
  _delta-prev.md         # stage 1, optional — structural delta vs a prior prototype version
  _consistency.md        # stage 5 — cross-doc audit (full profile only)
```

A **lite-profile** folder holds `_run.json`, `00-index.md` (`profile: lite`), the `NN-*.md` docs at `status: breakdown`, `_chunkmap.json`, `_features.json`, and the optional delta — nothing from stages 3–5.

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
verify: residual            # optional — set by the orchestrator when the doc still fails after its one fix round
---
```

`status` transitions strictly forward: `breakdown` (stage 2 wrote it) → `compared` (stage 3 appended) → `verified` (stage 4 passed, possibly after its one fix round). A doc flagged with residual errors stays `compared`, gains `verify: residual`, and is listed in the index; Resume treats it as settled. In a lite-profile folder `breakdown` is the terminal status until an upgrade runs stage 3.

Stage-2 sections (in order): `## What the prototype does` · `## Data & formulas` · `## UI / presentation` · `## Dependencies & integration points` · `## Prototype-only` · `## Open questions`. Every claim carries a line ref like `(L4620)` or `(L4620-4655)`; constants/formulas verbatim; bulk content data (dialogue rows, item lists) documented as schema + row count + 2–3 representative rows, never transcribed wholesale.

Stage-3 appended sections: `## Current state` (one orienting paragraph — which modules/classes cover this system, plus an "ahead of prototype" note where code exceeds it — then the full table `| # | Feature | Status | Evidence | Note |`, one row per checklist feature, same order and numbering as `_features.json`) · `## Missing` (missing features grouped into coherent gap clusters referencing row numbers) · `## Modify (divergent)` (one bullet per divergent row: prototype behavior with line ref vs code behavior with `path:line`, locked-decision flag).

## `_run.json`

Written by the orchestrator at the Pre-Flight go, before any worker runs; rewritten only by a lite-to-full upgrade.

```json
{
  "profile": "lite",
  "upgraded_from": null,
  "prototype": "<absolute path>", "prototype_bytes": 0, "prototype_mtime": "<ISO 8601>",
  "prior_version": null,
  "output_dir": "<absolute path>",
  "source_roots": [], "scope_rule": "", "locked_decisions": [], "hints": {},
  "exclude_hints": "",
  "started": "<ISO 8601>"
}
```

The comparison fields (`source_roots`, `scope_rule`, `locked_decisions`, `hints`) stay empty in a lite run and are filled by the upgrade, which also sets `profile: "full"` and `upgraded_from: "lite"`. A folder without `_run.json` predates it: its profile is whatever its index says (`lite`, otherwise full).

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

## `_delta-prev.md`

Sections: `New in <current>` · `Substantially grown` (rough old→new size) · `Roughly unchanged` · `Notes for the compare stage` (which systems should be presumed to have existing counterparts vs fresh). Under ~120 lines.

## `_consistency.md`

Five sections mirroring the mandates: **1 Dependency symmetry** (frontmatter/prose asymmetries between docs) · **2 Ownership** (each overlap candidate resolved to a single owning doc; double-counts and orphans flagged) · **3 Delta traceability** (every delta "new" item mapped to a doc's feature rows; orphans flagged) · **4 Cross-resolved open questions** · **5 Status sanity** (contradicting statuses for the same underlying mechanic across docs). Findings carry severity `info | warn | error`.

## `00-index.md`

Frontmatter: `title`, `source_prototype` (absolute path — consumers match on this), `profile` (`full` | `lite`; an index without the key is a pre-profile full run), `generated` (date), `pipeline` (run identifiers). Full-profile sections, in order:

1. `# Executive summary` — the port gap in one page; what exists, the big holes, where the codebase is ahead. No campaign decomposition (that is the saga planner's job).
2. `# System status table` — one row per system: feature count, per-status counts, verify outcome (`pass` / `fail(+n residual)` / `unverified`), plus a totals row.
3. `# Locked-decision divergences` — every divergent row attributable to a locked decision, gathered in one place, with "respect, don't re-litigate" framing.
4. `# Cross-cutting seams` — shared-state ownership map in target-codebase terms, ownership resolutions worth a planner's attention, unresolved warn/error consistency issues.
5. `# Open questions rollup` — deduplicated, cross-resolution applied, each tagged `[design]` vs `[code]`.
6. `# How to consume this folder` — reading order, what the support files are, and the planner contract: treat this folder (not the raw prototype) as the source; work is the Missing sections, the Modify sections minus rows flagged as locked decisions, and the absent behavior each `partial` row's note names; `divergent` rows that follow a locked decision, `prototype-only`, and `oos-native` rows are not work; build on code that is ahead of the prototype; the folder is a frozen snapshot consumers never edit.

### Lite index (`profile: lite`)

Same frontmatter, four sections, ≤ ~150 lines:

1. `# Executive summary` — what the prototype contains, in one page. First sentence states the profile: "Lite recon — no codebase comparison was run; every feature below is unassessed." No claims about what exists in the target code.
2. `# System table` — one row per system: doc, line ranges, feature count, depends_on. No status columns.
3. `# Seams and open questions` — cross-system dependencies and shared state in prototype terms, plus the docs' open questions, deduplicated, each tagged `[design]` vs `[code]`.
4. `# How to consume this folder` — reading order, the support files, and the lite contract: this folder is the source, not the raw prototype; features are **unassessed, not missing** — the discussion decides what is work; the folder is frozen; upgrade path = run stages 3–5 on this folder.

## Stage Gates (orchestrator acceptance checklist)

- **Stage 1**: partition law holds (verify arithmetically); system count 6–30 (12–20 target — merge trivia into owners); exclusions match the known-already-ported list; shared core ≤ 800 lines; boundaries were read-verified by the mapper.
- **Stage 2**: one doc per system, template-complete, `status: breakdown`; 10–25 features each; smoke-test two line refs from different docs by grepping the prototype yourself.
- **Stage 3**: every doc `status: compared`; table rows = checklist length; status counts sum correctly.
- **Stage 4**: every doc verdicted; failed docs got exactly one fix round; residuals flagged, not hidden.
- **Stage 5**: `_consistency.md` has all five sections; `00-index.md` has all six and `profile: full`; read the index yourself before presenting it.
- **Lite index** (brief 10, replaces stages 3–5): stage 1 and 2 gates passed; `00-index.md` has `profile: lite` and all four lite sections; no status vocabulary appears anywhere in it; read it yourself before presenting it.
