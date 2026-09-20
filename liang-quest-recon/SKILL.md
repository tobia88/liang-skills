---
name: liang-quest-recon
description: |
  Prototype breakdown pipeline — the quest family's side scout and the only skill that
  reads a raw prototype. Turns one prototype/spec file into a folder of line-referenced
  breakdown docs; the full profile adds skeptic-verified gap analysis against the codebase
  (done/partial/missing/divergent per feature, each citing code file:line), the lite
  profile stops at map + breakdown. The folder feeds the discussion that
  liang-quest-saga-planner or liang-quest-planner plans from.

  Use when the user asks to "recon" a prototype, break one down against the codebase, run
  a gap analysis, or prepare a prototype for saga planning (the saga planner's
  raw-prototype guard routes here). Not for prototypes small enough to discuss directly,
  and not for executing work.
---

# Liang Quest Recon

You are the side scout of the JRPG quest family, and the **only** skill in it that reads a raw prototype. One prototype file goes in; a folder of **evidence-cited breakdown documents** comes out — the map of what the prototype contains and, in the full profile, what the target codebase already covers and where the real gaps are. Planners consume that folder; none of them ever opens the prototype.

Recon is not a rung on the family ladder (`liang-quest-core/references/family/topology.md`): it is an optional scout whose folder becomes a source for the discussion, feeding `liang-quest-saga-planner` or a single `liang-quest-planner` run.

## Core Contract

- **Files are the API.** Every stage is defined purely by *input files → output files → pass gate*. Worker processes are disposable; the artifacts are canonical. Progress state lives in the artifacts themselves — per-doc frontmatter `status:` transitions (`breakdown → compared → verified`) plus artifact existence — so a run is **resumable from any stage by any harness**: Claude Code, Pi, or a human doing one stage by hand. No stage may depend on in-band tool returns that are not also persisted to disk.
- **Scouting only.** Recon describes; it never decomposes work into campaigns, never gives porting advice, and never executes anything.
- **The only prototype reader.** No other family skill opens a raw prototype; they read this skill's folder.
- **Contracts live in references.** The artifact contract (folder layout, JSON schemas, doc templates, the six-status vocabulary, evidence rules, per-stage gates) is canonical in `references/artifacts.md`; the worker instructions for every role are canonical in `references/stage-briefs.md`. Read both at activation.
- **No fan-out without the Pre-Flight go** (§ Pre-Flight) — this pipeline spawns many workers.

## Activation

Activate when:
1. The user invokes the skill by name, or asks to "recon" a prototype, break it down against the codebase, run a gap analysis, or produce a verified breakdown.
2. `liang-quest-saga-planner`'s raw-prototype guard sends prototype work here.
3. A `<prototype-stem>-breakdown/` folder exists and the user asks to continue it, upgrade it, or fix a gap a consumer reported in it — enter § Resume.

Do **not** activate for a prototype small enough to discuss directly (invoke `liang-quest-planner`), or when the user wants work executed (executor territory).

## Profiles: Picking the Cost

Every prototype that feeds planning comes through here — the saga planner has no intake of its own. Pick the profile by size and state — when two rows match, the lower row wins (a small but partly ported prototype is **full**) — and name it in the Pre-Flight report:

| Prototype | Profile | What runs |
|---|---|---|
| Small enough to discuss directly (one campaign of work) | none | Skip recon; talk it through and invoke `liang-quest-planner` |
| Worth about 2–3 campaigns, or no target codebase exists yet | **lite** | Stages 1–2, then the lite index (§ Lite Profile) |
| Larger (thousands of lines), already partly ported, or planning reliability matters more than speed | **full** | All five stages |

A lossy summary of a big file becomes phantom quests, which is why the full profile spends workers on comparison and skeptics. The lite profile spends none: it answers "what is in this prototype" with line refs, and leaves "what is already built" unanswered on purpose.

## The Five Stages

| # | Stage | Workers | Produces | Gate (orchestrator-checked) |
|---|-------|---------|----------|------------------------------|
| 1 | Map | 1 mapper (+1 delta if a prior prototype version exists) | `_chunkmap.json`, `_delta-prev.md` | Full partition of the file: zero gaps, zero overlaps, boundaries read-verified, exclusions identified, shared core ≤ 800 lines |
| 2 | Breakdown | 1 per system (12–20 typical) | `NN-<system>.md` (`status: breakdown`), feature checklists → `_features.json` | Every claim carries prototype line refs; 10–25 atomic features per system |
| 3 | Compare | 1 per system | Appended `## Current state` table + `## Missing` + `## Modify (divergent)` (`status: compared`) | Every feature has exactly one status; every done/partial/divergent verdict cites opened `file:line` evidence |
| 4 | Verify | 1 skeptic per system; fixer + re-verifier only for failed docs | `status: verified` (or a flagged residual) | Skeptic re-opened every `done` citation, re-searched sampled `missing` with synonyms, spot-checked breakdown line refs; at most ONE fix round, then flag |
| 5 | Cross | 1 consistency checker, then 1 synthesizer | `_consistency.md`, `00-index.md` | Ownership single-owner, dependency symmetry, delta traceability; index carries "How to consume this folder" |

**Orchestrator duties between stages** (you, in the main context — never delegate these):
- After stage 1: validate the partition arithmetically (range sweep), eyeball the system list, confirm exclusions make sense.
- After stage 2: smoke-test the line-ref coordinate system — grep the prototype for 2 distinctive identifiers claimed by different docs and confirm the line numbers land inside the claimed ranges. Assemble `_features.json`.
- After stage 4: read the verdict summary; any doc still failing after its one fix round gets `verify: residual` written into its frontmatter and is flagged in the index, not silently re-looped.
- After stage 5: read `00-index.md` yourself before presenting it; you are accountable for what it claims.
- After brief 10 (lite profile): read the lite `00-index.md` yourself and confirm it makes no claim about the target code.

### Lite Profile

Stages 1–2 run exactly as in the full profile — same mapper, same breakdown workers, same gates, same orchestrator duties (partition arithmetic, line-ref smoke test, `_features.json` assembly). Then, instead of stages 3–5, dispatch **one lite synthesizer** (brief 10) to write `00-index.md` with `profile: lite`. No compare, no skeptic, no consistency pass: per-system docs end at `status: breakdown`, and the index says plainly that every feature is **unassessed** against the codebase — not `missing`.

A lite folder is **upgradeable**: running stages 3–5 on it later (§ Resume) turns it into a full-profile folder and the stage-5 synthesizer replaces the lite index. Nothing from the lite run is redone.

## Invocation & Parameter Intake

1. **Resolve the prototype path** (ask if ambiguous; default to `.liang/prototypes/`). Detect an existing recon folder (`<prototype-stem>-breakdown/` beside it) — if present, enter § Resume instead of starting over.
2. **Gather parameters** (batch the questions; respect what the conversation already settled):
   - **Profile** — lite or full, per § Profiles. Ask this first: the lite profile runs no comparison, so it skips source roots, scope directive, locked decisions, and hints.
   - **Source roots** to compare against (code directories; note module layout and naming conventions for worker briefs).
   - **Scope directive** — default: *code only, ignore binary/opaque assets*; features whose natural home is an out-of-scope layer get status `oos-native` (see artifacts.md). Confirm the default in one line.
   - **Locked decisions** — architecture decisions that are authoritative OVER the prototype. Pull candidates from `.liang/intel/<workspace>.md` and the anchors of **earlier** sagas in `.liang/sagas/*/saga.yaml`, present them, let the user confirm/extend. Conflicts with a locked decision are `divergent`, never `missing`. Anchors flow forward only: a saga that consumes this folder may lock new anchors, and those never come back to re-open this run (§ Relationship to Other Skills).
   - **Known already-ported embedded blobs** — spans of the prototype that embed a previously-ported subsystem (a whole engine, a library). These are excluded from breakdown; only their bridge/seam stays in scope.
   - **Hints** — prior campaign/intel knowledge about what the codebase should contain, assembled per system where possible. Every hint is labeled an **unverified claim** in worker briefs; compare workers must verify against code. Hints from stale intel are the #1 source of wrong verdicts — the reference run caught two campaigns whose recorded status contradicted the code.
   - **Prior prototype version** (optional) for the structural delta — cheap and localizes what is new since the last planning round.
   - **Output folder** — default `<prototype-dir>/<prototype-stem>-breakdown/`.
3. **Pre-Flight** (§ below). On the go, write `_run.json` into the output folder — the chosen profile, every parameter above, and the prototype's size and mtime (schema: `references/artifacts.md`) — before any worker is spawned, then execute per § Execution Profiles. `_run.json` is what makes the profile and the intake survive a session.

## Pre-Flight

Before spawning anything, present one compact report and wait for an explicit go:
- Profile (lite or full) and why; prototype (size/lines), output folder, source roots, scope directive, locked decisions count, delta yes/no.
- Expected scale, lite: N+3 workers (mapper, optional delta, N breakdown, one lite synthesizer) — roughly a third of a full run.
- Expected scale, full: with N systems (12–20 typical), stage 1–2 ≈ N+2 workers, stages 3–5 ≈ 2N+2 to 4N+2 workers. Reference run: 15,038-line prototype, 12 systems → 50 workers, ~5.4 M worker tokens, ~30 min per phase wall-clock on the parallel profile.
- Model plan per § Model Routing.

No fan-out without the go. A user instruction that already says "go"/"run it" for this recon counts.

## Model Routing

Resolve per stage from `project.yaml` at the active workspace root. Keys, chains, and tier defaults are canonical in `liang-quest-core/references/project/project-yaml.md` § Model Routing Extensions (chain: specific key → `models.planning` / `models.verify` → harness default). If `project.yaml` is missing, fall to the end of each chain silently — never block on it, never write the file. On a tier-alias harness each chain ends in that role's `claude_mode` default tier, so defaults apply even with no file. The workflow scripts hold no default: a role the orchestrator passes no model for inherits the session model.

- Pi / model-id harnesses: `models.recon_map`, `models.recon_breakdown`, `models.recon_compare`, `models.recon_verify`, `models.recon_fix`, `models.recon_cross`, `models.recon_synthesis`.
- Tier-alias harnesses (Claude subagents): `claude_mode.recon_*` with the same suffixes.
- One key per role; two roles share a key: the delta scanner uses `recon_map`, and the re-verifier uses `recon_fix`. The lite synthesizer (brief 10) uses `recon_synthesis`, same as the stage-5 synthesizer.
- **Building the scripts' `models` argument:** `{ map, delta, breakdown }` for stages 1–2 and `{ compare, verify, fix, cross, synthesis }` for stages 3–5, each value the role's resolved model (under Claude Code: the resolved tier alias); omit a role only when nothing resolves.
- Skeptics and the re-verifier run at high reasoning effort where the harness supports effort — they are the reliability load-bearers, never starve them.

## Execution Profiles

Both profiles send the SAME briefs (`references/stage-briefs.md`) and honor the same gates. Never feed the whole prototype to any worker — assigned line ranges plus shared core only; out-of-range identifiers are resolved by targeted grep with a few context lines.

### Claude Code profile (parallel, fast path)

Use the Workflow tool with the two bundled scripts (this skill instructing the call satisfies the Workflow opt-in rule):

1. `Workflow({ scriptPath: "{baseDir}/references/wf-map-breakdown.js", args: {...} })` — args documented in the script header: prototype path, optional prior version, output dir, project context, banner scan seed (produce it yourself with a couple of greps first; it may be wrong — the mapper is authoritative), exclude hints, delta context.
2. Orchestrator duties for stage 1–2, including writing `_features.json` from the run's returned feature arrays. **Lite profile stops here**: dispatch brief 10 as a single subagent (synthesis model), read the index it writes, hand off.
3. `Workflow({ scriptPath: "{baseDir}/references/wf-compare-verify.js", args: {...} })` — pass `systems` assembled from `_features.json` (id, title, ranges, features, per-system hints) plus source context, scope rule, locked decisions, today's date, and `excludedSpans` — the full `excluded` list from `_chunkmap.json` (the stage 1–2 script's return value only carries the large spans).
4. Both scripts return per-worker results AND persist everything to the output folder; on a crash, resume with `resumeFromRunId` (unchanged agents replay from cache) or fall back to § Resume off the artifacts.
5. **The scripts are whole-stage only.** A partial resume (only the missing systems, only the unverified docs), a gap fix, and brief 10 are dispatched as individual subagents, one per unit, each given its brief from `references/stage-briefs.md` and its model per § Model Routing. Never re-run `wf-compare-verify.js` over a doc already at `status: compared` — it would append a second assessment.

### Pi profile (sequential or child-parallel)

No Workflow tool exists here; drive the stages yourself:

- **Lite profile**: either mode below, stages 1–2 only, then brief 10 as one more unit.
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

Read `_run.json` first: it names the run's profile and holds the intake parameters. A folder with no `_run.json` predates it: take the profile from the index (`lite` if it says so, otherwise full) and ask for any parameter a later stage needs. Then walk the table top to bottom — **the first matching row wins**; doc statuses decide, the index only confirms. A doc is **settled** when it is `status: verified`, or `status: compared` with `verify: residual` in its frontmatter (its one fix round is spent).

| Observed | Resume at |
|---|---|
| No `_chunkmap.json` | Stage 1 |
| Chunk map but missing `NN-*.md` docs | Stage 2 (only the missing systems) |
| Profile lite, no index | Assemble `_features.json` if absent, then brief 10 |
| Profile lite, index with `profile: lite` | Done (lite) — report, hand off |
| Profile full, some docs still at `status: breakdown` | Assemble `_features.json` if absent, then stage 3 (only those docs). Covers a fresh full run, an interrupted stage 3, and an upgrade in progress — a `profile: lite` index found here is stale and gets overwritten at stage 5 |
| Profile full, some docs `compared` and not settled | Stage 4 (only those docs) |
| Profile full, every doc settled, index missing or not `profile: full` | Stage 5 |
| Profile full, every doc settled, index with `profile: full` (or no `profile` key — pre-profile runs) | Done — report, hand off |

**Upgrading lite to full.** Only on an explicit request. Gather the comparison parameters the lite intake skipped (source roots, scope directive, locked decisions, hints — § Invocation step 2), set `_run.json` to profile full with those parameters, present a fresh Pre-Flight for the stage 3–5 fan-out, and only then start stage 3. Nothing from stages 1–2 is redone.

**Gap fix (a consumer reported a wrong or incomplete doc).** The one sanctioned way to re-open a finished folder. Input: the consumer's gap report, used as `{ERRORS}`. Full-profile doc: one fixer (brief 6) plus one re-verifier (brief 7) on that doc, regardless of whether its original fix round was spent. Lite-profile doc: re-run that system's breakdown worker (brief 3) with the gap report appended and the instruction to keep the existing feature order, appending any new feature at the end; then update that system's entry in `_features.json`. Feature rows are corrected in place and never renumbered — consumers cite them by number. A gap fix is two or three workers, not a fan-out, so it needs no Pre-Flight. Afterwards re-run the synthesizer (brief 9 or 10) so the index counts match, and tell the consumer which rows changed. Dispatch: individual subagents under Claude Code, one unit per brief under Pi.

If the prototype file no longer matches the size/mtime recorded in `_run.json`, stop and tell the user — a moved coordinate system invalidates every line ref; recon must restart against the new version (the old folder can serve as the "prior version" delta input).

## Boundaries

1. **No fan-out without the Pre-Flight go.**
2. **Writes only inside the output folder.** Never edit the prototype, the target source, or `project.yaml`.
3. **Never feed a whole prototype to one worker**, and never read or reproduce base64/binary blobs; explicit prose is summarized mechanics-only (§ Reliability Invariants 9).
4. **No campaign decomposition and no porting advice** — downstream planners own both.
5. **One fix round per failed doc**, then flag it in the index; never silently re-loop.
6. **A finished folder is frozen.** Later decisions do not re-open it; they arrive as locked-decision input to a later run. The two sanctioned exceptions are both in § Resume: an explicit lite-to-full upgrade, and a consumer-reported gap fix.

## Relationship to Other Skills

- **Upstream (typical source)**: `liang-game-prototyper` output under `.liang/prototypes/`, but any sufficiently concrete prototype or spec file works.
- **Shared foundation**: `liang-quest-core` — the `project.yaml` model-routing keys. Recon's own artifact contract is not shared; it lives in this skill's `references/`.
- **Downstream**: the output folder — never the raw prototype — is what planning reads. Two consumers, same contract:

- **`liang-quest-saga-planner`** — takes the folder as one of its sources (it auto-detects `<stem>-breakdown/` folders in its Phase 1, and its raw-prototype guard sends prototype work here first). It reads `00-index.md`, cites per-system docs by section and row, and uses them as the single fidelity source for its alignment verify.
- **`liang-quest-planner`** — when the index shows about one campaign of work. The planner reads only the live conversation, so the hand-off is a discussion: read `00-index.md` into the session, settle the decisions with the user, then invoke the planner.

The index's "How to consume this folder" section carries the contract. Load-bearing rules for planners:

- **Full profile**: work is the Missing section, the Modify section minus rows flagged as locked decisions, and the absent behavior each `partial` row's note names. `divergent` rows that follow a locked decision, `prototype-only`, and `oos-native` rows are NOT work; where the codebase is ahead of the prototype, build on it rather than porting its absence.
- **Lite profile**: there are no codebase statuses. Every feature is unassessed; the discussion decides what is work. Nobody may read a lite feature list as a gap analysis.
- **The folder is a frozen snapshot.** Consumers never edit it. When a later decision contradicts a row, the saga planner records an override in its own `inventory.md`; recon is not re-run to agree with it. Those decisions reach recon only as locked-decision input to a *later* run (a new prototype version, or a lite-to-full upgrade).
- **A recon gap is fixed here.** If a consumer's verifier finds a doc wrong or incomplete, the fix is a gap fix on that doc (§ Resume) — never a planner reaching past the folder into the prototype.

## Reference Files

- `references/artifacts.md` — the artifact contract; wins on conflict with anything stated here or in the briefs.
- `references/stage-briefs.md` — worker instructions for every role (briefs 1–10).
- `references/wf-map-breakdown.js`, `references/wf-compare-verify.js` — Claude Code Workflow scripts for stages 1–2 and 3–5; they embed briefs 1–9 and must stay in sync with them.
- `rubric-override.md` — skill-lint overrides for this skill's shape.
- `liang-quest-core/references/project/project-yaml.md` — `models.recon_*` / `claude_mode.recon_*` keys, chains, and tier defaults.

If a listed core file is missing, stop and report it.
