---
name: liang-quest-saga-planner
description: "DEPRECATED, use liang-queue-add / liang-queue-sweep instead. Saga-level orchestrator: turns a discussion's worth of work into 2–8 related campaigns via repeated liang-quest-planner handoffs. Sources are the conversation's locked decisions, a brainstorm Strategy Report, and optional liang-quest-recon folders — it never reads a raw prototype. Locks cross-campaign anchors, splits the work with a dependency topology, hands each campaign to the planner (same-context or batch subagents), and gates each on a source-alignment verify. Resumable: state lives in .liang/sagas/. Post-execution modes --uat, --tour and --handover roll per-campaign UAT checklists and walkthroughs into one saga view. Use when asked to break work into multiple campaigns or to continue a saga; not for a single campaign (liang-quest-planner) or for running campaigns (executor / batch-sweep)."
---

# Liang Quest Saga Planner

Some bodies of work are too big for one campaign. This skill sits **above** `liang-quest-planner` as the upper orchestrator: it gathers the tasks and decisions a discussion produced, splits them into an ordered set of campaigns, and hands each campaign to the planner one at a time — in the same context, the only place the planner reads from.

The saga is the rung between discussion and campaign on the family ladder (`liang-quest-core/references/family/topology.md`). `liang-quest-recon` is an optional **side scout**, not a rung: when the work involves a prototype, recon breaks it down and its folder becomes one of the saga's sources.

## Core Contract

- **Planning only.** Like the planner, this skill stops at planning artifacts. It never executes quests, runs builds, or touches VCS.
- **Never reads a raw prototype.** Breaking a prototype down — systems, schemas, constants, codebase comparison — is `liang-quest-recon`'s job, lite or full profile. The saga planner reads a recon folder through its `00-index.md`, treats the folder as a frozen snapshot, and never edits it.
- **Division of labor is fixed.** The saga planner owns: the work inventory, the campaign-level split, cross-campaign dependency topology, and per-campaign Decision Summaries. `liang-quest-planner` owns everything inside a campaign: quest decomposition, `plan.md`, quest markdowns, `manifest.yaml`, and the optional `plan.html` render. The saga planner's **only** write into a campaign folder is patching `campaign_depends_on` into `manifest.yaml` after the planner finalizes.
- **Campaigns land flat** in `.liang/campaigns/` exactly as the planner writes them — never nested under a saga folder. Grouping is by the shared title prefix and the saga state file, matching how `sweep.py` discovers campaigns.
- **Resumable.** Saga state lives in `.liang/sagas/<saga-id>/saga.yaml` (+ `inventory.md`). A saga typically spans multiple sessions; re-invoking the skill resumes from the state file.
- **`saga.md` is the saga dossier.** Required in every saga, whatever the surface: the split rationale, the anchors, and each campaign's purpose, scope, dependencies, and victory conditions. It carries **no status** — `saga.yaml` owns status, and the status table is shown in chat.
- **`saga.html` is an optional render.** Produced only when `planner.html` is true in `.liang/project.yaml`, from `saga.md` + `saga.yaml` through `liang-quest-planner`'s HTML machinery (body contract + `assemble_plan.py` + skins), regenerated whole — never edited in place. Status text and diagram states are merged in from `saga.yaml` at render time.
- **`.liang/project.yaml` must exist before planning.** Phase 1 step 0 bootstraps the file, or just its `planner.html` key, when absent.
- **Planned campaigns are immutable at the saga layer.** The planner's one-shot rule applies; the saga planner never re-plans or edits a finalized campaign.
- **Planned means verified.** A campaign's status flips to `planned` only after the Phase 4.5 alignment verify passes it against the saga's sources; until then it sits at `review` and blocks its dependents.

## Output Layout

```
.liang/sagas/saga-<YYYY-MM-DD>-<slug>/
  saga.yaml        # state: anchors, campaign list, statuses — the resume point and the only status surface
  inventory.md     # work inventory built in-context in Phase 1: one row per task, with its origin
  saga.md          # REQUIRED saga dossier — split rationale, anchors, per-campaign scope; no status
  saga.html        # OPTIONAL render of saga.md + saga.yaml; only when planner.html is true
  align/c##.md     # per-campaign source-alignment reports (Phase 4.5)
  uat-checklist.md # deferred-UAT rollup (Phase 5, post-execution, regenerable)
  walkthrough.md   # feature-walkthrough rollup (Phase 6, post-execution, regenerable)
  handover.html    # OPTIONAL render of the two rollups above (Phase 7); only when planner.html is true

.liang/campaigns/campaign-<date>-<HHMM>-<sagaprefix>-<slug>/   # planner output, flat, one per campaign
```

`saga.yaml` schema (inline, no external reference file):

```yaml
schema_version: 2
saga_id: saga-2026-07-08-battle-simulator-port
title: "Battle Simulator Port"
short_name: "BattleSim"        # prefixes every campaign's Main Quest title
skin: persona-blue             # planner skin slug; used by saga.html AND every campaign plan.html (planner.html true only)
sources:                        # what this saga was planned from; never a raw prototype
  - kind: discussion            # discussion | brainstorm-report | recon
    ref: "2026-07-08 session — battle simulator port scoping"
  - kind: recon
    ref: ".liang/prototypes/ShadesOfElysium-battle-simulator_v2.21-breakdown/"   # folder holding 00-index.md
    profile: full               # full | lite — copied from the index frontmatter
created_at: "2026-07-08T14:00:00+08:00"
status: intake | discussion | decomposed | planning | complete
anchors:                        # locked in Phase 2, injected into every Decision Summary
  - id: a001
    label: "Skill data storage"
    decision: "Primary DataAsset per skill; effects as instanced structs"
campaigns:
  - id: c01                     # saga-local id
    title: "BattleSim — Data Model Port"   # becomes the planner's Main Quest title
    purpose: "One-sentence outcome"
    scope: ["stat schema", "skill definitions", "config values"]
    depends_on: []              # saga-local c## ids; must be acyclic
    status: pending | review | planned   # review = finalized but alignment verify found blocking drift
    campaign_id: ""             # folder name recorded after planner finalization
```

A `schema_version: 1` saga (it carries `source_prototype` and an intake-subagent `inventory.md`) resumes as-is, never migrated mid-saga. Read its `inventory.md` this way: it stands in for the recon folder wherever this document says "recon docs" (including as the Phase 4.5 fidelity source); a system row is a task row; `port` means `do`; and it has no override column, so it carries no overrides. A v1 saga still at `status: intake` with no `inventory.md` cannot resume — its intake no longer exists; start a new saga through recon.

## Activation

Activate when:
1. User invokes by name (`skill:liang-quest-saga-planner`), optionally with a recon folder path.
2. User explicitly asks to turn the discussed work into **multiple** plans/campaigns ("break this into campaigns", "saga-plan this").
3. An in-progress saga exists in `.liang/sagas/` and the user asks to continue it.
4. User asks for a saga's deferred UAT / manual backlog / verification checklist, or invokes with `--uat` — run **only** Phase 5 (Deferred-UAT Rollup); no planning phases.
5. User asks for a saga's feature walkthrough / guided tour ("show me what was built", "walk me through the features"), or invokes with `--tour` — run **only** Phase 6 (Feature Walkthrough); no planning phases.
6. User asks for a single readable page of the saga's tour + outstanding UAT ("one page I can read in the browser"), or invokes with `--handover` — run **only** Phase 7 (Handover View), which triggers Phase 5/6 first when their outputs are missing; no planning phases.

Do **not** activate from generic "plan this" (that is `liang-quest-planner`'s territory) or "run/sweep campaigns" (executor / batch-sweep territory). If the work looks small enough for a single campaign (≲8 quests), say so and recommend invoking `liang-quest-planner` directly instead — a one-campaign saga is pure overhead.

**Raw-prototype guard.** If the invocation names a prototype file, or the work is "port this prototype" and no recon folder exists for it, stop before Phase 1 and route to `liang-quest-recon`, which picks the lite or full profile by its own § Profiles table. Re-invoke this skill once the folder's `00-index.md` exists. There is no intake path that reads the prototype here.

**On every invocation, check `.liang/sagas/` first.** If an in-progress saga matches the user's intent, show its status table (campaigns, statuses, next pending) and resume at the right phase instead of starting over. Never run two sagas over the same sources concurrently.

## Model Routing & `--claude`

The saga planner delegates in five places: Phase 4 batch-mode campaign planners, Phase 4.5 alignment verifiers, Phase 5/6 executor-artifact workers (UAT backfill and walkthrough), and the body-drafter for `saga.html` (Phase 3.5) and `handover.html` (Phase 7). The two body-drafter spawns follow the planner's 2c rules unchanged, including its inline fallback. The other three resolve through `models.saga_planner`, `models.saga_align`, and `models.saga_uat` — chains, the unspawnable-step rule, and the `claude_mode.saga_*` tier defaults are canonical in `liang-quest-core/references/project/project-yaml.md` § Model Routing Extensions. Announce the resolved model in one line before spawning.

**Both harness paths, every delegation point.** Under Claude Code a child is a general-purpose subagent. Under Pi it is a `pi --print --model <resolved>` sub-process; like every family child it is briefed with file paths, communicates only through the files it writes, and takes single-line arguments. Where no child can be spawned at all: batch mode degrades to the same-context loop, the alignment verifier runs in this context as a read-only pass over the same inputs (say so in the `align/` report), and a rollup with no artifact to collect follows the fallback its own reference file states.

**`--claude`** forces resolution through the `claude_mode` namespace and dispatches children as Claude Agent subagents — the executor's flag semantics, reused. Without the flag, auto-detect applies: a harness that can only spawn tier aliases resolves through `claude_mode` anyway (same rule as the planner's body-drafter). When the saga runs with `--claude`, propagate it downstream — every Next Move suggestion carries `--claude`. `project.yaml` is required (Phase 1 bootstraps it when missing), so these chains always resolve against a real file; a missing **key** falls through its chain as documented.

## Phase 1 — Source Intake (in-context)

No subagent: the sources are already decisions, or a recon index written to be read in one sitting.

0. **Resolve `.liang/project.yaml` first.** It is required. If the file is missing, run the shared interview (`liang-quest-core/references/project/project-yaml.md` § First-Run Interview), then write the file. If the file exists but has no `planner.html` key, ask only that interview's **Plan render surface** question (a yes also turns on `saga.html`) and store the answer under `planner.html`. A `--html` / `--no-html` flag on the invocation overrides the key for this run only and is never written back, and is passed through to every planner handoff. In a headless context a missing file or missing key with no flag is a hard stop: report what is missing and exit without planning. Apart from that first-run bootstrap, `planner.html` is the only `project.yaml` key this skill ever writes.
1. **Gather the sources** and record them under `sources` in `saga.yaml`:
   - **Discussion** — the tasks and locked decisions in the live conversation. Respect what is already settled; do not re-ask it.
   - **Brainstorm report** — a `liang-brainstorm-relentless` Strategy Report in context (locked-decision table, Victory Conditions, Scope, Risks).
   - **Recon folder(s)** — named by the user, or auto-detected when the discussion names a prototype: a sibling `<prototype-stem>-breakdown/` containing `00-index.md`, or any folder whose `00-index.md` frontmatter `source_prototype` matches that path. A prototype with no recon folder trips the raw-prototype guard (§ Activation).
1b. **Reading a recon folder.** Read `00-index.md` first and follow its "How to consume this folder" section; copy its `profile` into `saga.yaml` (no key: record `full`). Open a per-system `NN-*.md` doc only when a row needs drill-down — never sweep the folder into context.
   - `profile: full` — apply the planner contract the index states (canonical: `liang-quest-recon/references/artifacts.md` § `00-index.md`). Rows it counts as work become inventory tasks; rows it counts as not-work get no task row unless a Phase 2 override adds one.
   - `profile: lite` — the folder has no codebase statuses: every feature is *unassessed*, not missing. The discussion decides what is work; say this to the user in one line so nobody reads the feature lists as a gap analysis.
2. Create the saga folder and a stub `saga.yaml` (`status: intake`). Derive `saga_id` from the local date + a slug of the work's title; pick a `short_name` (2–3 syllables, e.g. "BattleSim") and confirm it with the user in one line — it prefixes every campaign title.
3. **Write `inventory.md` — the work inventory.** Required shape:
   - **Work Inventory table**: one row per task — id (`w01`…), what it delivers, **origin** (the discussion decision, the report section, or the recon `NN-doc` rows it comes from), a `do | adapt | skip` call with a one-line reason, and an **override** column (empty until Phase 2 fills it).
   - **Integration points**: existing workspace code the tasks plug into, with file paths — from recon evidence when present; for discussion-only sagas confirm each with a targeted grep, never a sweep.
   - **Out of saga scope**: what the discussion explicitly parked.
   - **By reference, never by copy**: schemas, constants, and formulas stay in the recon docs; rows cite them as `NN-doc § section` or row numbers.
4. **Thin-discussion check.** If the sources leave more than about five open gaps at saga level (no clear outcome, no scope edge, no decisions to anchor), say so and recommend `liang-brainstorm-relentless` first — a saga planned from a vague discussion produces vague campaigns.

The main context works from `inventory.md` from here on.

## Phase 2 — Saga Discussion (once, not per campaign)

Present the inventory digest to the user and lock the **architecture anchors**: the decisions that cut across campaigns and would otherwise get re-asked N times. Typical anchors: data storage form (DataAsset vs DataTable vs config), how a recon'd prototype's effect/formula logic maps to the target architecture, UI framework approach, which existing systems are integration boundaries, what is explicitly out of saga scope.

- Drive this like a focused review of the inventory's `do | adapt | skip` calls plus the cross-cutting decisions. Batch questions; respect what the conversation already settled.
- Record each locked anchor in `saga.yaml` under `anchors` (`status: discussion` while in progress).
- Anchors are **LOCKED** once written: downstream Decision Summaries cite them verbatim; per-campaign planner discussion may refine details inside a campaign but never silently contradicts an anchor. If the user changes an anchor mid-saga, update `saga.yaml` and flag which pending campaigns it affects (planned campaigns stay as-is — note the drift to the user).
- **Anchors flow forward only.** When an anchor contradicts a recon row (a `missing` feature the user now rules out, a `done` mechanic the user wants redone), the saga overrides that row **in `inventory.md`**: re-call the task that cites the row — or add a task row when the recon row had none, as for a `done` mechanic — and fill its override column with the anchor id and the reason. The recon folder stays untouched — a frozen, verified snapshot — and recon is never re-run to agree with an anchor. New anchors become locked-decision input only for a *later* recon run.

## Phase 3 — Campaign Decomposition

1. Split the work into campaigns. Each campaign must be a cohesive, independently-plannable outcome sized for the planner's 2–8 quest range. Typical seams: data model → core logic → state machine/flow → UI → integration/routing → tuning pass. Merge fragments; split anything that would exceed ~8 quests.
2. Order by dependency topology; record saga-local `depends_on` (acyclic). Producer campaigns must land before consumer campaigns.
3. Title every campaign `"<short_name> — <Campaign Title>"` so planner-derived slugs sort and group in `.liang/campaigns/`.
4. Tag each campaign with a saga-level `difficulty` (`easy`/`medium`/`hard` — carried into `saga.md` and, when rendered, `saga.html`'s diff badges; informational, distinct from per-quest difficulty the planner assigns later).
5. Present the decomposition for user confirmation — as a table in chat, or (when `planner.html` is true) by writing `saga.md` and rendering `saga.html` first and letting the user review the page in the browser. Adjust until confirmed, then write the full campaign list to `saga.yaml` with all statuses `pending` (`status: decomposed`).
6. Pick the saga skin (planner slug, e.g. `persona-blue`) if not already chosen, record it in `saga.yaml`. One skin per saga: `saga.html` and every campaign `plan.html` use it, so the saga reads as one visual family when `planner.html` is true.

## Phase 3.5 — Saga Dossier (`saga.md`) and optional dashboard

### `saga.md` — always

Write `saga.md` from `references/saga-template.md` as soon as the decomposition exists (even pre-confirmation — it is the best review artifact). It carries the split rationale, the anchors, and per campaign: purpose, scope, saga-local dependencies, victory conditions, and the sibling scopes it must not reach into.

**No status lives in `saga.md`.** `saga.yaml` is the only status surface; show the status table in chat. `saga.md` changes only when the decomposition or an anchor changes — not when a campaign flips to `planned` or `review`.

Schemas and formulas stay in the recon docs, integration tables in `inventory.md`; never duplicate either into `saga.md`.

### `saga.html` — only when `planner.html` is true

With `planner.html` false there is no `saga.html`: the status table in chat plus `saga.md` are the whole surface, and the rest of this section does not run.

**Rendering reuses the planner's 2c machinery verbatim** — same body-drafter subagent pattern (model resolution per the planner's rules), same `liang-quest-planner/references/templates/class-contract.md` contract, same `assemble_plan.py` validation + CSS assembly. The drafter reads `saga.md` and `saga.yaml` **from disk**: `saga.md` supplies the content, `saga.yaml` supplies the status text and diagram states at render time. No bespoke CSS, ever. The saga-shaped mapping onto the contract:

- One `section.quest` per **campaign** (`id="c01"`…), TOC heading "Campaigns", eyebrows "Campaign NN · <Status>".
- `diff-badge` = the campaign's saga-level difficulty (required by the validator in both TOC and section headers).
- `span.dep-state` in each TOC item carries `<status> · depends: <ids>`.
- Exactly one `diagram-section` between TOC and main: the campaign dependency graph (nodes = campaigns; `.is-active` = next up, `.is-muted` = pending, plain = planned; lanes for parallel tracks; legend explains the topology).
- Steps = campaign scope items (no code blocks — lean overview); rationale = why this split; footer = Dependencies + campaign-level Victory Conditions.
- Notes section = saga risks + open questions cards; the wide decisions table lists the **locked anchors** (pill text `locked`).
- Content depth is LEAN: purpose/scope/deps/victory per campaign — exactly what `saga.md` carries.

Assemble with the saga skin: `python <skills-root>/liang-quest-planner/references/templates/assemble_plan.py <saga-dir>/_body.html <skin> <saga-dir>/saga.html --title "<Saga Title> — Saga"`, delete `_body.html` on success, auto-open in the browser (same per-OS commands as the planner), announce the path.

**Poisoned-context guard.** If saga text anywhere in context renders with `â€`-style glyphs (UTF-8 punctuation laundered through a Windows-1252 decode), that copy of the text is poisoned — never retype or transcribe it into briefs, bodies, or edit strings; re-Read `saga.md` / `saga.yaml` from disk and compose from what the files actually contain. `assemble_plan.py` auto-repairs laundered runs and prints a `MOJIBAKE:` warning as a last line of defense — treat that warning as proof the drafting context was poisoned upstream, not as noise.

**Keeping it live.** `saga.html` is re-rendered **whole** — never edited in place — when a campaign flips to `planned` or `review`, and at session stop. Announce in one line ("saga.html re-rendered — refresh browser"). A decomposition or anchor change edits `saga.md` first, then re-renders. A campaign section's footer gains a relative link to its plan when the campaign is planned — `../../campaigns/<campaign-dir>/plan.html` (works on `file://`), or `plan.md` when that campaign was planned with `planner.html` false.

## Phase 4 — Per-Campaign Planner Handoff (resumable)

Set `status: planning`. Two handoff modes — pick once per session and say which is running:

- **Same-context loop** — the planner executes in this context, one campaign at a time. Default when ≤2 campaigns remain or the user wants to steer each plan's Phase 3 discussion live. Ceiling: 2–3 campaigns per session.
- **Batch mode** — one fresh-context subagent per campaign runs the planner to full finalization; the orchestrator stays thin. Offer it (recommended) when 3+ campaigns are pending. Degradation comes from one long context, not from batching: each subagent starts clean and reads `saga.yaml` / `inventory.md` / predecessor campaign folders from disk.

Both modes share the Decision Summary step. For each campaign, in topological order:

1. **Assemble its Decision Summary in-context** — the planner's exact 9-field shape (Main Quest, Planning Lens, Target User, Locked Decisions, Victory Conditions, Scope Boundary, Risks, Open Questions, Decision Table), built from `inventory.md` + the saga anchors + this campaign's scope row. Two saga-specific rules:
   - **Scope Boundary must name sibling campaigns' scopes as explicit non-goals** ("enemy AI is campaign c04, not here") — this is what keeps N plans related-but-disjoint.
   - **Cross-campaign contracts**: when this campaign consumes something a dependency campaign produces (a type, an asset, an interface), state that interface in Locked Decisions as this campaign's consumption contract. Read the dependency campaign's manifest/quest titles if needed to phrase it accurately.
   - **Formulas and schemas by reference**: cite `inventory.md` rows and the recon doc sections they point at instead of pasting bulk constants or field lists into the summary — the planner (or its subagent) reads them from disk. An inventory override wins over the recon row it overrides.
   Leave no 9-field gap — a complete summary is what makes `--quick` gap-fill a no-op.

### Same-context loop

2. **Invoke the planner**: read `liang-quest-planner/SKILL.md` (a sibling of this skill's folder) and execute it in this same context in **`--quick` mode**, presenting the Decision Summary as the conversation's decisions. Pass through the saga's `--html` / `--no-html` flag when the saga was invoked with one; otherwise the planner reads `planner.html` from `.liang/project.yaml` itself. Let the planner run its own Phases 2–4 untouched — with `planner.html` true that is `plan.md` + the quest files and the rendered `plan.html` in its Phase 2, then Phase 3 discussion, then `manifest.yaml` at finalization; with `planner.html` false it is the quest table in chat and all three artifacts at finalization. One saga override: the aesthetic direction is the saga `skin` from `saga.yaml`, not the planner's per-lens auto-pick. Do not shortcut its machinery otherwise.
3. **After planner finalization**, in the new campaign folder's `manifest.yaml`, add top-level `campaign_depends_on: [<campaign_id>, ...]` mapping this campaign's saga-local `depends_on` to the recorded `campaign_id` values of the already-planned dependency campaigns. Omit the field when there are no dependencies. This is the saga planner's only write inside a campaign folder.
4. **Run the Phase 4.5 source-alignment verify.** On pass, update `saga.yaml` (set the campaign's `status: planned`, record its `campaign_id` — the folder name) and, when `planner.html` is true, **re-render `saga.html`** per Phase 3.5 (status flip, diagram node, plan link, counts). On blocking drift, `status: review` — see Phase 4.5.
5. **Context budget check.** After each campaign, assess remaining context. A planner handoff is expensive (summary + body-drafter round + discussion + files); 2–3 campaigns per session is the realistic ceiling. When context is getting thin, stop cleanly: report the saga status table and tell the user to re-invoke the skill to resume. Never start a handoff you likely can't finish.

### Batch mode (fresh-context subagent per campaign)

2. **Launch one subagent per campaign** (model per § Model Routing), in topological waves — a campaign launches only when every dependency is `planned`; independent campaigns may run in parallel. The brief contains: the campaign's full Decision Summary, the saga folder path (subagent reads `saga.yaml` + `inventory.md` from disk, plus the recon docs its inventory rows cite), the `campaign_id` folder names of its dependency campaigns (subagent reads their manifests/quests for contract phrasing), the saga `skin` override, the resolved surface (`--html` or `--no-html`, so the subagent never has to ask), and the instruction to execute `liang-quest-planner --headless` (implies `--quick`; skips Phase 3 discussion, the visual spot-check, and the browser auto-open — no user is present in a subagent) to **full finalization**. The finished folder must carry `plan.md`, the quest markdowns, `manifest.yaml`, `plan.html` when the surface is on, and the `campaign_depends_on` patch (in batch mode the subagent writes it; the orchestrator verifies). Which phase writes which artifact is the planner's business, not the saga's.
3. **Verify each returned campaign on disk** before launching its dependents: the campaign folder exists and is flat, and it contains `plan.md`, the quest files, and `manifest.yaml`, with the manifest carrying the correct `campaign_depends_on`. Only when `planner.html` is true, also check that `plan.html` exists and contains exactly **one** `<div class="page">`. Then run the Phase 4.5 alignment verify; on pass flip `status: planned` in `saga.yaml` and, with `planner.html` true, re-render `saga.html`.
4. **Watch for cross-campaign ownership collisions** between parallel subagents — two campaigns claiming the same new type/asset/interface. Steer the live agent mid-flight when possible; otherwise serialize the pair and note the contract owner in the later campaign's Decision Summary.
5. **Review model**: the user reviews all the finished plans after the batch — the `plan.html` pages when `planner.html` is true, otherwise the `plan.md` dossiers. Collected notes are applied in a single revision session, per campaign, by editing the markdown (and re-rendering when a page exists) — not by the saga layer.

When all campaigns are `planned`, run the saga-level coverage audit before closing: in-context, from `inventory.md` + the campaign manifests, confirm (a) every inventory task marked `do` or `adapt` is claimed by exactly one campaign, and (b) every cross-campaign contract is named consistently by its producer and consumer. Report any gap to the user; then set `status: complete` and present the final saga table with every campaign path.

## Phase 4.5 — Source Alignment Verify (gate)

A campaign is never marked `planned` on the planner's word alone. After finalization (either mode), spawn one **read-only verifier subagent** (model per § Model Routing) briefed with: the campaign's `inventory.md` rows (with their overrides), the saga anchors, its scope row + Decision Summary, the recon docs those rows cite when the saga has a recon source, and the finalized `plan.md` + quest markdowns (the verifier reads markdown; it never reads `plan.html`, and it never opens a raw prototype). It checks four things and returns a structured verdict:

- **Coverage** — every scope item maps to at least one quest.
- **Fidelity** — depends on where the campaign's rows come from:
  - *Rows backed by recon docs*: load-bearing constants and formulas in the quest markdowns match the recon docs verbatim; cite the `NN-doc` section or row on every mismatch. The recon docs are the single fidelity source — if one looks wrong or incomplete, report it as a **recon gap** for the user to fix in recon; never reach past it into the prototype. An inventory override beats the row it overrides.
  - *Discussion-only rows*: there are no constants to match; check instead that every locked decision in the Decision Summary is honoured by the quests that touch it, citing the decision on every miss.
- **Boundary** — no quest reaches into a sibling campaign's scope.
- **Anchors** — nothing silently contradicts a locked anchor.

Write the report to `<saga-dir>/align/<c##>.md`. Triage:

- **Pass or minor drift** (cosmetic; no constant, decision, contract, or scope item affected): note the minor items in the report, flip `status: planned`, proceed.
- **Blocking drift** (wrong constant, dishonoured locked decision, missed scope item, boundary violation, anchor contradiction): set `status: review`, do **not** launch dependent campaigns, and surface the drift list to the user. The fix belongs to the user-driven revision session, not to silent saga-layer edits — the immutability rule stands. After revision, re-run the verifier; flip to `planned` on pass.

- **Recon gap** (a cited recon doc is wrong or incomplete): set `status: review` and hold dependents, exactly as for blocking drift. The user runs a gap fix in `liang-quest-recon` (its § Resume); recon corrects rows in place without renumbering and reports which rows changed. Re-check the inventory tasks citing those rows, then re-run the verifier.

The verifier is evidence-precise, not creative: it reports mismatches with citations; it never proposes redesigns.

## Phase 5 — Deferred-UAT Rollup (post-execution, `--uat`)

Run when the user asks for the saga's deferred UAT / manual backlog, or after a sweep reports the saga's headless portion done. Generation is the executor's job (`liang-quest-executor` §8b writes each campaign's `uat-checklist.md`); this mode only collects — merging per-campaign checklists into one topo-ordered, session-grouped rollup, backfilling missing ones via parallel §8b workers, never re-deriving UAT items itself. Read-only against campaign folders; the single output is `<saga-dir>/uat-checklist.md`. Full protocol: `references/rollup-uat.md` — load when this mode runs.

## Phase 6 — Feature Walkthrough (post-execution, `--tour`)

Run when the user asks to be walked through what was built. Generation is the executor's job (`liang-quest-executor` §8c writes each campaign's `walkthrough.md`, covering every quest including passed ones); this mode only collects — merging per-campaign tours into one saga-ordered walkthrough, backfilling missing ones via parallel §8c workers, never writing tour content itself. Read-only against campaign folders; the single output is `<saga-dir>/walkthrough.md`. Companion to `--uat`; Phase 7 (`--handover`) renders both into one page. Full protocol: `references/rollup-tour.md` — load when this mode runs.

## Phase 7 — Handover View (post-execution, `--handover`)

**Runs only when `planner.html` is true.** With it false there is no HTML surface: `--handover` says the two markdown rollups (`uat-checklist.md`, `walkthrough.md`) are the deliverable, names their paths, and stops — running Phase 5/6 first if either is missing.

**Presentation layer only.** Renders the two saga-level rollups — `uat-checklist.md` (Phase 5) and `walkthrough.md` (Phase 6) — into a single self-contained `<saga-dir>/handover.html`, via the planner's 2c HTML machinery (body-drafter, class contract, `assemble_plan.py`, saga skin); runs Phase 5/6 first if either source is missing. The markdown files stay the source of truth — the HTML is a disposable, regenerate-whole view, never edited by hand, never a state surface. Single output: `<saga-dir>/handover.html`. Full protocol: `references/rollup-handover.md` — load when this mode runs.

## Next Move

After completion (or at any session stop with 2+ planned campaigns), suggest — never invoke:

```
skill:liang-quest-batch-sweep — sweep saga <saga-dir-name>   # scoped: THIS saga's campaigns only (sweep.py --saga), in campaign_depends_on order
skill:liang-quest-executor .liang/campaigns/<campaign-dir>   # or run one campaign directly
```

Always suggest the saga-scoped form — an unscoped sweep is workspace-global and re-dispatches every non-passed campaign in the workspace's history. When the saga ran with `--claude`, append `--claude` to both suggestions. Remind the user that quests flagged `manual: true` are held out of the headless queue by the sweep and become a post-sweep in-editor backlog — after the sweep finishes, `skill:liang-quest-saga-planner --uat <saga-dir-name>` (Phase 5) rolls that backlog plus all deferred Tier-2 VCs into `<saga-dir>/uat-checklist.md`, and `--handover` (Phase 7) renders it with the walkthrough into one browsable `handover.html` when `planner.html` is true.

## Boundaries

1. **No execution, no VCS** beyond writing saga state (`saga.yaml`, `inventory.md`, `saga.md`, `align/c##.md`, `uat-checklist.md`, `walkthrough.md`, and the optional `saga.html` / `handover.html` renders), the `project.yaml` first-run bootstrap and `planner.html` write-back in Phase 1, and the single manifest patch.
2. **Never author campaign content** — no quest markdowns, no `plan.md` or `plan.html` edits. That is planner territory, reached only through the planner handoff (same-context or batch subagent).
3. **Never nest campaigns** under `.liang/sagas/` or any subfolder; sweep discovery depends on flat `.liang/campaigns/`.
4. **Never re-plan a planned campaign.** Corrections to a finalized campaign are out of scope for the saga layer.
5. **No secrets, credentials, or binary assets** in saga artifacts; the inventory references recon docs by section and row, never by embedding their content.
6. **Never read a raw prototype, never edit a recon folder.** Prototype questions go back to `liang-quest-recon`; disagreements with a recon row are recorded as inventory overrides.

## Relationship to Other Skills

- **Downstream (handoff)**: `liang-quest-planner` — invoked once per campaign: `--quick` in the same-context loop, `--headless` in batch subagents; sole producer of campaign folders. Its 2c HTML machinery (class contract, `assemble_plan.py`, skins) is also reused for `saga.html` (Phase 3.5) and `handover.html` (Phase 7), both only when `planner.html` is true.
- **Downstream (suggested)**: `liang-quest-batch-sweep` / `liang-quest-executor` — consume the planned campaigns; sweep toposorts via the `campaign_depends_on` fields this skill patches in. The executor's §8b per-campaign `uat-checklist.md` artifacts are Phase 5's sole input; its §8c `walkthrough.md` artifacts are Phase 6's.
- **Shared foundation**: `liang-quest-core` — manifest schema (`campaign_depends_on` semantics live in `liang-quest-core/references/campaign/manifest-schema.md`).
- **Upstream (sources)**: the live discussion and, typically, a `liang-brainstorm-relentless` Strategy Report — the same inputs `liang-quest-planner` takes, one level up.
- **Side scout (optional source)**: `liang-quest-recon` — the only skill that reads a prototype. Its breakdown folder (lite or full profile) enters the saga through `00-index.md` in Phase 1; anchors flow forward into later recon runs as locked decisions, never back into the run the saga consumed.

## Reference Files
- `references/saga-template.md` — `saga.md` dossier skeleton (Phase 3.5). Required in every saga, whatever the surface.
- `liang-quest-core/references/project/project-yaml.md` — first-run interview, `planner.html`, and the `models.saga_*` / `claude_mode.saga_*` routing keys.
- `liang-quest-core/references/campaign/manifest-schema.md` — `campaign_depends_on` semantics for the one manifest patch.
- `references/rollup-uat.md` (Phase 5, `--uat`), `references/rollup-tour.md` (Phase 6, `--tour`), `references/rollup-handover.md` (Phase 7, `--handover`) — full protocols; load when the matching mode runs.
- `liang-quest-planner/SKILL.md` — executed per campaign in Phase 4; `liang-quest-planner/references/templates/class-contract.md` and `assemble_plan.py` — the render machinery reused for `saga.html` and `handover.html`.
- `liang-quest-recon/references/artifacts.md` — the `00-index.md` consume contract and the `profile` key (Phase 1b).
- `liang-quest-executor/references/completion-flow.md` — §8b / §8c, the per-campaign artifacts Phases 5–6 collect.

If a listed core file is missing, stop and report it.
