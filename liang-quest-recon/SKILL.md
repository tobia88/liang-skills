---
name: liang-quest-recon
description: |
  Verified prototype-to-codebase breakdown pipeline — the scouting stage above the saga
  planner in the JRPG ladder (recon -> saga -> campaign -> quest). Turns one large
  prototype/spec file into a folder of adversarially-verified breakdown + gap-analysis
  markdown docs (per-system feature tables with done/partial/missing/divergent statuses,
  each verdict citing code file:line evidence that survived a skeptic re-check), which
  liang-quest-saga-planner then consumes as intake material instead of the raw prototype.

  Use when the user asks to "recon" a prototype, break down / analyze a big prototype
  against the existing codebase, run a "gap analysis", produce a "verified breakdown",
  or prepare a large prototype for saga planning. Do NOT use for small prototypes that
  fit one campaign (invoke liang-quest-planner directly) or when the user wants to
  execute work (executor territory).
---

# Liang Quest Recon

You are the reconnaissance stage of the JRPG quest family. One large prototype file goes in; a folder of **verified, evidence-cited breakdown documents** comes out — the map of what the prototype contains, what the target codebase already covers, and where the real gaps are. `liang-quest-saga-planner` consumes that folder instead of the raw prototype.

Metaphor ladder: **recon** (this skill, one prototype → one breakdown folder) → **saga** (2–8 campaigns) → **campaign** (2–8 quests) → **quest** (one executable unit).

## When Recon Earns Its Cost

Run recon when the prototype is large (thousands of lines), partially ported already, or when planning reliability matters more than speed — a single intake subagent summarizing a 5 MB file is lossy, and lossy intake becomes phantom quests. Skip recon when the prototype is small enough that the saga planner's own single-subagent intake can hold it faithfully, or when no target codebase exists yet (nothing to compare against — recon degenerates to stages 1–2 only, which is legitimate but say so).

This pipeline spawns many workers. **Never start the fan-out without the Pre-Flight go** (§ Pre-Flight).

## Core Principle: Files Are the API

Every stage is defined purely by *input files → output files → pass gate*. Worker processes are disposable; the artifacts are canonical. Progress state lives in the artifacts themselves — per-doc frontmatter `status:` transitions (`breakdown → compared → verified`) plus artifact existence — so a run is **resumable from any stage by any harness**: Claude Code, Pi, or a human doing one stage by hand. No stage may depend on in-band tool returns that are not also persisted to disk.

The full artifact contract (folder layout, JSON schemas, doc templates, the six-status vocabulary, evidence rules, and per-stage gates) is canonical in `references/artifacts.md`. The worker instructions for every role are canonical in `references/stage-briefs.md`. Read both at activation.

## The Five Stages

| # | Stage | Workers | Produces | Gate (orchestrator-checked) |
|---|-------|---------|----------|------------------------------|
| 1 | Map | 1 mapper (+1 delta if a prior prototype version exists) | `_chunkmap.json`, `_delta-<prev>.md` | Full partition of the file: zero gaps, zero overlaps, boundaries read-verified, exclusions identified, shared core ≤ 800 lines |
| 2 | Breakdown | 1 per system (12–20 typical) | `NN-<system>.md` (`status: breakdown`), feature checklists → `_features.json` | Every claim carries prototype line refs; 10–25 atomic features per system |
| 3 | Compare | 1 per system | Appended `## Current state` table + `## Missing` + `## Modify (divergent)` (`status: compared`) | Every feature has exactly one status; every done/partial/divergent verdict cites opened `file:line` evidence |
| 4 | Verify | 1 skeptic per system; fixer + re-verifier only for failed docs | `status: verified` (or a flagged residual) | Skeptic re-opened every `done` citation, re-searched sampled `missing` with synonyms, spot-checked breakdown line refs; at most ONE fix round, then flag |
| 5 | Cross | 1 consistency checker, then 1 synthesizer | `_consistency.md`, `00-index.md` | Ownership single-owner, dependency symmetry, delta traceability; index carries "How to consume this folder" |

**Orchestrator duties between stages** (you, in the main context — never delegate these):
- After stage 1: validate the partition arithmetically (range sweep), eyeball the system list, confirm exclusions make sense.
- After stage 2: smoke-test the line-ref coordinate system — grep the prototype for 2 distinctive identifiers claimed by different docs and confirm the line numbers land inside the claimed ranges. Assemble `_features.json`.
- After stage 4: read the verdict summary; any doc still failing after its one fix round gets flagged in the index, not silently re-looped.
- After stage 5: read `00-index.md` yourself before presenting it; you are accountable for what it claims.

## Invocation & Parameter Intake

1. **Resolve the prototype path** (ask if ambiguous; default to `.liang/prototypes/`). Detect an existing recon folder (`<prototype-stem>-breakdown/` beside it) — if present, enter § Resume instead of starting over.
2. **Gather parameters** (batch the questions; respect what the conversation already settled):
   - **Source roots** to compare against (code directories; note module layout and naming conventions for worker briefs).
   - **Scope directive** — default: *code only, ignore binary/opaque assets*; features whose natural home is an out-of-scope layer get status `oos-native` (see artifacts.md). Confirm the default in one line.
   - **Locked decisions** — architecture decisions that are authoritative OVER the prototype. Pull candidates from `.liang/intel/<workspace>.md` and `.liang/sagas/*/saga.yaml` anchors, present them, let the user confirm/extend. Conflicts with a locked decision are `divergent`, never `missing`.
   - **Known already-ported embedded blobs** — spans of the prototype that embed a previously-ported subsystem (a whole engine, a library). These are excluded from breakdown; only their bridge/seam stays in scope.
   - **Hints** — prior campaign/intel knowledge about what the codebase should contain, assembled per system where possible. Every hint is labeled an **unverified claim** in worker briefs; compare workers must verify against code. Hints from stale intel are the #1 source of wrong verdicts — the reference run caught two campaigns whose recorded status contradicted the code.
   - **Prior prototype version** (optional) for the structural delta — cheap and localizes what is new since the last planning round.
   - **Output folder** — default `<prototype-dir>/<prototype-stem>-breakdown/`.
3. **Pre-Flight** (§ below), then execute per § Execution Profiles.

## Pre-Flight

Before spawning anything, present one compact report and wait for an explicit go:
- Prototype (size/lines), output folder, source roots, scope directive, locked decisions count, delta yes/no.
- Expected scale: with N systems (12–20 typical), stage 1–2 ≈ N+2 workers, stages 3–5 ≈ 2N+2 to 4N+2 workers. Reference run: 15,038-line prototype, 12 systems → 50 workers, ~5.4 M worker tokens, ~30 min per phase wall-clock on the parallel profile.
- Model plan per § Model Routing.

No fan-out without the go. A user instruction that already says "go"/"run it" for this recon counts.

## Model Routing

Resolve per stage from `project.yaml` at the active workspace root, per the family convention (chain: specific key → `models.planning`-style fallback → harness default; if `project.yaml` is missing, harness default silently — never block on it, never write the file):

- Pi / model-id harnesses: `models.recon_map`, `models.recon_breakdown`, `models.recon_compare`, `models.recon_verify`, `models.recon_fix`, `models.recon_cross`, `models.recon_synthesis`.
- Tier-alias harnesses (Claude subagents): `claude_mode.recon_*` with the same suffixes.
- Proven defaults: everything mid-tier; **synthesis top-tier** (it writes the one document everyone reads). Verify runs at high reasoning effort where the harness supports effort — skeptics are the reliability load-bearers, never starve them.

## Execution Profiles

Both profiles send the SAME briefs (`references/stage-briefs.md`) and honor the same gates. Never feed the whole prototype to any worker — assigned line ranges plus shared core only; out-of-range identifiers are resolved by targeted grep with a few context lines.

### Claude Code profile (parallel, fast path)

Use the Workflow tool with the two bundled scripts (this skill instructing the call satisfies the Workflow opt-in rule):

1. `Workflow({ scriptPath: "{baseDir}/references/wf-map-breakdown.js", args: {...} })` — args documented in the script header: prototype path, optional prior version, output dir, project context, banner scan seed (produce it yourself with a couple of greps first; it may be wrong — the mapper is authoritative), exclude hints, delta context.
2. Orchestrator duties for stage 1–2, including writing `_features.json` from the run's returned feature arrays.
3. `Workflow({ scriptPath: "{baseDir}/references/wf-compare-verify.js", args: {...} })` — pass `systems` assembled from `_features.json` (id, title, ranges, features, per-system hints) plus source context, scope rule, locked decisions, today's date.
4. Both scripts return per-worker results AND persist everything to the output folder; on a crash, resume with `resumeFromRunId` (unchanged agents replay from cache) or fall back to § Resume off the artifacts.

### Pi profile (sequential or child-parallel)

No Workflow tool exists here; drive the stages yourself:

- **Sequential**: run each stage's units one at a time in scoped working passes, following the brief verbatim and writing the artifacts directly. Slower, cheapest, zero infrastructure.
- **Child-parallel**: dispatch stage units as `pi --print` child processes (one per system), each child briefed with the stage brief + its parameters and writing its artifact files itself. Follow the quest-family child conventions: children communicate ONLY through the files they write; keep every shim argument single-line (`.cmd` shims truncate argv at the first newline); reap on exit-code markers. Merge per-system feature fragments (`_features/<id>.json`, written by each breakdown child) into `_features.json` before stage 3.

## Reliability Invariants (non-negotiable, both profiles)

1. **Partition discipline** — the chunk map covers every line exactly once (systems ∪ shared core ∪ excluded); the mapper establishes the authoritative line count itself and read-verifies every boundary.
2. **Line-ref discipline** — every factual claim in a breakdown doc carries a prototype line ref; load-bearing constants and formulas are transcribed verbatim.
3. **Atomic feature checklists** — `_features.json` is the unit of assessment; compare assesses exactly those features, in order; verify audits coverage against it.
4. **Six-status vocabulary** with the locked-decision rule and evidence rules exactly as defined in `references/artifacts.md`.
5. **Skeptic gates** — re-open every `done` citation (cap 8, sampled across files), re-search ≥2 `missing` rows with synonyms, spot-check ≥6 breakdown claims including ≥2 verbatim constants.
6. **One fix round** — a failed doc gets one fixer + one re-verify; still failing → flagged in the index, never silently retried.
7. **Consistency mandates** — ownership single-owner, dependency symmetry, delta traceability, cross-resolved open questions, cross-doc status sanity.
8. **No silent caps** — any bounded coverage (sampling, skipped spans) is logged and lands in the index.
9. **Content safety** — explicit prose in the prototype is summarized mechanics-only; base64/binary blobs are never read or reproduced; no blobs in artifacts.
10. **Mojibake rule** — harness Read tools may render UTF-8 punctuation as mojibake; workers write proper punctuation and never transcribe mojibake bytes.

## Resume

Determine the furthest consistent state from the artifacts, then re-enter there:

| Observed | Resume at |
|---|---|
| No `_chunkmap.json` | Stage 1 |
| Chunk map but missing `NN-*.md` docs | Stage 2 (only the missing systems) |
| Docs at `status: breakdown`, no `_features.json` | Assemble `_features.json`, then stage 3 |
| Docs at `status: compared` | Stage 4 (only unverified docs) |
| All docs `status: verified`, no `00-index.md` | Stage 5 |
| `00-index.md` present | Done — report, hand off |

If the prototype file changed since the run started (size/mtime), stop and tell the user — a moved coordinate system invalidates every line ref; recon must restart against the new version (the old folder can serve as the "prior version" delta input).

## Downstream Handoff

The output folder — not the raw prototype — is the intake material for `liang-quest-saga-planner` (it auto-detects `<stem>-breakdown/` folders in Phase 1). The index's "How to consume this folder" section carries the contract; the load-bearing rule for planners: **`divergent` (locked decisions), `prototype-only`, and `oos-native` rows are NOT work** — campaigns are scoped from the Missing and Modify sections only, and where the codebase is ahead of the prototype, build on it rather than porting its absence.
