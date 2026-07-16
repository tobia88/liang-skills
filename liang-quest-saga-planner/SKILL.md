---
name: liang-quest-saga-planner
description: "Saga-level planner that turns a large prototype (e.g. an HTML game prototype under .liang/prototypes/) into multiple related campaigns via repeated liang-quest-planner handoffs. Four phases: subagent prototype intake (systems inventory + workspace integration map), saga discussion (lock architecture anchors once), campaign decomposition with cross-campaign dependency topology, and a resumable per-campaign handoff phase with two modes — same-context loop or batch fresh-context subagents — that invokes liang-quest-planner --quick with pre-baked Decision Summaries and patches campaign_depends_on into each finalized manifest. Every finalized campaign passes a prototype-alignment verify before it counts as planned. Subagent models route from project.yaml (models.saga_intake / saga_planner / saga_align, claude_mode tier aliases, --claude override). State lives in .liang/sagas/ so planning survives across sessions. Post-execution, a Deferred-UAT Rollup mode (--uat) collects the per-campaign uat-checklist.md artifacts that liang-quest-executor §8b generates and merges them into a single topo-ordered, session-grouped .liang/sagas/<id>/uat-checklist.md; campaigns missing their checklist get parallel §8b standalone-backfill worker subagents (models.saga_uat → models.verify, claude_mode.saga_uat medium tier) — the saga context itself never reconstructs. A companion --tour mode rolls per-campaign walkthrough.md tours the same way, and --handover renders both saga-level rollups into a single read-only handover.html (planner HTML machinery, saga skin); the markdown files stay the source of truth."
---

# Liang Quest Saga Planner

One prototype is often too big for one campaign. This skill sits **above** `liang-quest-planner`: it extracts the decisions embodied in a prototype, splits the port into an ordered set of campaigns, and hands each campaign to the planner one at a time — in the same context, the only place the planner reads from.

Metaphor ladder: **quest** (one executable unit) → **campaign** (2–8 quests, one planner run) → **saga** (2–8 campaigns, one prototype).

## Core Contract

- **Planning only.** Like the planner, this skill stops at planning artifacts. It never executes quests, runs builds, or touches VCS.
- **Division of labor is fixed.** The saga planner owns: the systems inventory, the campaign-level split, cross-campaign dependency topology, and per-campaign Decision Summaries. `liang-quest-planner` owns everything inside a campaign: quest decomposition, `plan.html`, quest markdowns, `manifest.yaml`. The saga planner's **only** write into a campaign folder is patching `campaign_depends_on` into `manifest.yaml` after the planner finalizes.
- **Campaigns land flat** in `.liang/campaigns/` exactly as the planner writes them — never nested under a saga folder. Grouping is by the shared title prefix and the saga state file, matching how `sweep.py` discovers campaigns.
- **Resumable.** Saga state lives in `.liang/sagas/<saga-id>/saga.yaml` (+ `inventory.md`). A saga typically spans multiple sessions; re-invoking the skill resumes from the state file.
- **Human-readable dashboard.** The saga maintains `saga.html` — a living overview page generated with `liang-quest-planner`'s HTML machinery (body contract + `assemble_plan.py` + skins), regenerated or edited-in-place at every saga state change. The user reads and steers the saga from this page; keep it current.
- **Planned campaigns are immutable at the saga layer.** The planner's one-shot rule applies; the saga planner never re-plans or edits a finalized campaign.
- **Planned means verified.** A campaign's status flips to `planned` only after the Phase 4.5 alignment verify passes it against the prototype; until then it sits at `review` and blocks its dependents.

## Output Layout

```
.liang/sagas/saga-<YYYY-MM-DD>-<slug>/
  saga.yaml        # state: anchors, campaign list, statuses — the resume point
  inventory.md     # systems inventory from the intake subagent
  saga.html        # living dashboard — self-contained, planner-machinery assembled
  align/c##.md     # per-campaign alignment-verify reports (Phase 4.5)
  uat-checklist.md # deferred-UAT rollup (Phase 5, post-execution, regenerable)
  walkthrough.md   # feature-walkthrough rollup (Phase 6, post-execution, regenerable)
  handover.html    # read-only HTML view of the two rollups above (Phase 7, disposable)

.liang/campaigns/campaign-<date>-<HHMM>-<sagaprefix>-<slug>/   # planner output, flat, one per campaign
```

`saga.yaml` schema (inline, no external reference file):

```yaml
schema_version: 1
saga_id: saga-2026-07-08-battle-simulator-port
title: "Battle Simulator Port"
short_name: "BattleSim"        # prefixes every campaign's Main Quest title
skin: persona-blue             # planner skin slug; used by saga.html AND every campaign plan.html
source_prototype: ".liang/prototypes/ShadesOfElysium-battle-simulator_v2.21.html"
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

## Activation

Activate when:
1. User invokes by name (`skill:liang-quest-saga-planner`), optionally with a prototype path.
2. User explicitly asks to turn a prototype into **multiple** plans/campaigns ("break this prototype into campaigns", "saga-plan this").
3. An in-progress saga exists in `.liang/sagas/` and the user asks to continue it.
4. User asks for a saga's deferred UAT / manual backlog / verification checklist, or invokes with `--uat` — run **only** Phase 5 (Deferred-UAT Rollup); no planning phases.
5. User asks for a saga's feature walkthrough / guided tour ("show me what was built", "walk me through the features"), or invokes with `--tour` — run **only** Phase 6 (Feature Walkthrough); no planning phases.
6. User asks for a single readable page of the saga's tour + outstanding UAT ("one page I can read in the browser"), or invokes with `--handover` — run **only** Phase 7 (Handover View), which triggers Phase 5/6 first when their outputs are missing; no planning phases.

Do **not** activate from generic "plan this" (that is `liang-quest-planner`'s territory) or "run/sweep campaigns" (executor / batch-sweep territory). If the prototype looks small enough for a single campaign (≲8 quests of work), say so and recommend invoking `liang-quest-planner` directly instead — a one-campaign saga is pure overhead.

**On every invocation, check `.liang/sagas/` first.** If an in-progress saga matches the user's intent, show its status table (campaigns, statuses, next pending) and resume at the right phase instead of starting over. Never run two sagas over the same prototype concurrently.

## Model Routing & `--claude`

The saga planner spawns subagents in four places: the Phase 1 intake, Phase 4 batch-mode campaign planners, Phase 4.5 alignment verifiers, and Phase 5/6 executor-artifact workers (UAT backfill and walkthrough — same routing). (Body-drafters resolve inside the planner per its own rules — nothing saga-specific there.) Resolution follows the planner's body-drafter convention exactly — walk the chain, treat unspawnable models as unresolved, announce the resolved model in one line before spawning; semantics in `liang-quest-core/references/project/project-yaml.md`:

- **Intake:** `models.saga_intake` → `models.planning` → harness default.
- **Batch campaign planner:** `models.saga_planner` → `models.planning` → harness default.
- **Alignment verifier:** `models.saga_align` → `models.verify` → harness default.
- **UAT-backfill / walkthrough worker:** `models.saga_uat` → `models.verify` → harness default.

Harnesses that spawn subagents by tier alias resolve through the `models.claude_mode` namespace instead: `claude_mode.saga_intake` (default: the `medium` tier), `claude_mode.saga_planner` (default: `hard`), `claude_mode.saga_align` (default: `medium`), `claude_mode.saga_uat` (default: `medium` — extraction and formatting, not judgment).

**`--claude`** forces resolution through the `claude_mode` namespace and dispatches children as Claude Agent subagents — the executor's flag semantics, reused. Without the flag, auto-detect applies: a harness that can only spawn tier aliases resolves through `claude_mode` anyway (same rule as the planner's body-drafter). When the saga runs with `--claude`, propagate it downstream — every Next Move suggestion carries `--claude`. If `project.yaml` is missing, all chains skip to the harness default silently; never block planning on it, never write the file.

## Phase 1 — Prototype Intake (subagent)

1. Resolve the prototype path (ask if ambiguous; default to looking under `.liang/prototypes/`).
2. Create the saga folder and a stub `saga.yaml` (`status: intake`). Derive `saga_id` from the local date + a slug of the prototype name; pick a `short_name` (2–3 syllables, e.g. "BattleSim") and confirm it with the user in one line — it prefixes every campaign title.
3. **Spawn one intake subagent** (general-purpose / Explore-equivalent; read-only; model per § Model Routing) briefed to produce `inventory.md`. The brief must include:
   - The prototype path, with instruction to **skip embedded binary/base64 asset blobs** and read the code and data definitions.
   - Instruction to also **grep the active workspace's source** for systems the prototype overlaps or must integrate with (existing combat/encounter/UI/save systems, game mode routing, etc.), so campaigns integrate rather than duplicate.
   - Required output shape — a markdown doc with:
     - **Systems Inventory table**: one row per system — name, what it does, key data/formulas (verbatim constants where load-bearing), and a `port | adapt | skip` recommendation with one-line reason.
     - **Data schemas**: the prototype's config/entity/skill/effect structures, field by field.
     - **Integration points**: existing workspace code the port must plug into, with file paths.
     - **Prototype-only list**: things that exist to serve the HTML prototype (debug editors, embedded assets, page chrome) and should not be ported.
4. Write the subagent's output to `inventory.md`. Sanity-skim it; if a system you can see in the prototype is missing, send the subagent back for that gap before proceeding.

The main context reads `inventory.md` — never the raw prototype — from here on.

## Phase 2 — Saga Discussion (once, not per campaign)

Present the inventory digest to the user and lock the **architecture anchors**: the decisions that cut across campaigns and would otherwise get re-asked N times. Typical anchors: data storage form (DataAsset vs DataTable vs config), how the prototype's effect/formula logic maps to the target architecture, UI framework approach, which existing systems are integration boundaries, what is explicitly out of saga scope.

- Drive this like a focused review of the inventory's `port | adapt | skip` calls plus the cross-cutting decisions. Batch questions; respect what the conversation already settled.
- Record each locked anchor in `saga.yaml` under `anchors` (`status: discussion` while in progress).
- Anchors are **LOCKED** once written: downstream Decision Summaries cite them verbatim; per-campaign planner discussion may refine details inside a campaign but never silently contradicts an anchor. If the user changes an anchor mid-saga, update `saga.yaml` and flag which pending campaigns it affects (planned campaigns stay as-is — note the drift to the user).

## Phase 3 — Campaign Decomposition

1. Split the port into campaigns. Each campaign must be a cohesive, independently-plannable outcome sized for the planner's 2–8 quest range. Typical seams: data model → core logic → state machine/flow → UI → integration/routing → tuning pass. Merge fragments; split anything that would exceed ~8 quests.
2. Order by dependency topology; record saga-local `depends_on` (acyclic). Producer campaigns must land before consumer campaigns.
3. Title every campaign `"<short_name> — <Campaign Title>"` so planner-derived slugs sort and group in `.liang/campaigns/`.
4. Tag each campaign with a saga-level `difficulty` (`easy`/`medium`/`hard` — the dashboard's diff badges; informational, distinct from per-quest difficulty the planner assigns later).
5. Present the decomposition for user confirmation — as a table in chat, or by generating the Phase 3.5 dashboard first and letting the user review `saga.html` in the browser. Adjust until confirmed, then write the full campaign list to `saga.yaml` with all statuses `pending` (`status: decomposed`).
6. Pick the saga skin (planner slug, e.g. `persona-blue`) if not already chosen, record it in `saga.yaml`. One skin per saga: the dashboard and every campaign `plan.html` use it, so the saga reads as one visual family.

## Phase 3.5 — Saga Dashboard (`saga.html`)

Generate the living dashboard as soon as the decomposition exists (even pre-confirmation — it is the best review artifact), and keep it current for the rest of the saga.

**Generation reuses the planner's Phase 2c machinery verbatim** — same body-drafter subagent pattern (model resolution per the planner's rules), same `../liang-quest-planner/references/templates/class-contract.md` contract, same `assemble_plan.py` validation + CSS assembly. No bespoke CSS, ever. The saga-shaped mapping onto the contract:

- One `section.quest` per **campaign** (`id="c01"`…), TOC heading "Campaigns", eyebrows "Campaign NN · <Status>".
- `diff-badge` = the campaign's saga-level difficulty (required by the validator in both TOC and section headers).
- `span.dep-state` in each TOC item carries `<status> · depends: <ids>`.
- Exactly one `diagram-section` between TOC and main: the campaign dependency graph (nodes = campaigns; `.is-active` = next up, `.is-muted` = pending, plain = planned; lanes for parallel tracks; legend explains the topology).
- Steps = campaign scope items (no code blocks — lean overview); rationale = why this split; footer = Dependencies + campaign-level Victory Conditions.
- Notes section = saga risks + open questions cards; the wide decisions table lists the **locked anchors** (pill text `locked`).
- Content depth is LEAN: purpose/scope/deps/victory per campaign. Schemas, formulas, and integration tables stay in `inventory.md` — never duplicate them into the page.

Assemble with the saga skin: `python <planner>/references/templates/assemble_plan.py <saga-dir>/_body.html <skin> <saga-dir>/saga.html --title "<Saga Title> — Saga"`, delete `_body.html` on success, auto-open in the browser (same per-OS commands as the planner), announce the path.

**Keeping it live** — after every saga state change, update `saga.html` and announce in one line ("dashboard updated — refresh browser"):

- Campaign planned (Phase 4): flip its status text in eyebrow + TOC dep-state, un-mute its diagram node, mark the new next-up node `.is-active`, and add a relative link to its plan — `../../campaigns/<campaign-dir>/plan.html` (works on `file://`) — in the campaign section's footer. Update the masthead planned/pending count.
- Decomposition or anchor change: full regen through the same machinery.
- Edit-in-place (Read the affected section first — the body was subagent-drafted, never edit from memory) for status flips and link additions; full regen for structural changes. Same judgment rule as the planner's Phase 3.

## Phase 4 — Per-Campaign Planner Handoff (resumable)

Set `status: planning`. Two handoff modes — pick once per session and say which is running:

- **Same-context loop** — the planner executes in this context, one campaign at a time. Default when ≤2 campaigns remain or the user wants to steer each plan's Phase 3 discussion live. Ceiling: 2–3 campaigns per session.
- **Batch mode** — one fresh-context subagent per campaign runs the planner to full finalization; the orchestrator stays thin. Offer it (recommended) when 3+ campaigns are pending. Degradation comes from one long context, not from batching: each subagent starts clean and reads `saga.yaml` / `inventory.md` / predecessor campaign folders from disk.

Both modes share the Decision Summary step. For each campaign, in topological order:

1. **Assemble its Decision Summary in-context** — the planner's exact 9-field shape (Main Quest, Planning Lens, Target User, Locked Decisions, Victory Conditions, Scope Boundary, Risks, Open Questions, Decision Table), built from `inventory.md` + the saga anchors + this campaign's scope row. Two saga-specific rules:
   - **Scope Boundary must name sibling campaigns' scopes as explicit non-goals** ("enemy AI is campaign c04, not here") — this is what keeps N plans related-but-disjoint.
   - **Cross-campaign contracts**: when this campaign consumes something a dependency campaign produces (a type, an asset, an interface), state that interface in Locked Decisions as this campaign's consumption contract. Read the dependency campaign's manifest/quest titles if needed to phrase it accurately.
   - **Formulas and schemas by reference**: cite `inventory.md` sections/rows instead of pasting bulk constants or field lists into the summary — the planner (or its subagent) reads the inventory from disk.
   Leave no 9-field gap — a complete summary is what makes `--quick` gap-fill a no-op.

### Same-context loop

2. **Invoke the planner**: read `../liang-quest-planner/SKILL.md` and execute it in this same context in **`--quick` mode**, presenting the Decision Summary as the conversation's decisions. Let the planner run its own Phases 2–4 untouched (body-drafter subagent, `assemble_plan.py`, Phase 3 open discussion, quest markdown writing) — with one saga override: the aesthetic direction is the saga `skin` from `saga.yaml`, not the planner's per-lens auto-pick. Do not shortcut its machinery otherwise.
3. **After planner finalization**, in the new campaign folder's `manifest.yaml`, add top-level `campaign_depends_on: [<campaign_id>, ...]` mapping this campaign's saga-local `depends_on` to the recorded `campaign_id` values of the already-planned dependency campaigns. Omit the field when there are no dependencies. This is the saga planner's only write inside a campaign folder.
4. **Run the Phase 4.5 alignment verify.** On pass, update `saga.yaml` (set the campaign's `status: planned`, record its `campaign_id` — the folder name) **and update `saga.html`** per Phase 3.5 (status flip, diagram node, plan.html link, counts). On blocking drift, `status: review` — see Phase 4.5.
5. **Context budget check.** After each campaign, assess remaining context. A planner handoff is expensive (summary + body-drafter round + discussion + files); 2–3 campaigns per session is the realistic ceiling. When context is getting thin, stop cleanly: report the saga status table and tell the user to re-invoke the skill to resume. Never start a handoff you likely can't finish.

### Batch mode (fresh-context subagent per campaign)

2. **Launch one subagent per campaign** (model per § Model Routing), in topological waves — a campaign launches only when every dependency is `planned`; independent campaigns may run in parallel. The brief contains: the campaign's full Decision Summary, the saga folder path (subagent reads `saga.yaml` + `inventory.md` from disk), the `campaign_id` folder names of its dependency campaigns (subagent reads their manifests/quests for contract phrasing), the saga `skin` override, and the instruction to execute `liang-quest-planner --quick` to **full finalization** — plan.html, quest markdowns, `manifest.yaml`, and the `campaign_depends_on` patch (in batch mode the subagent writes it; the orchestrator verifies).
3. **Verify each returned campaign on disk** before launching its dependents: campaign folder exists and is flat (plan.html + quest files + manifest.yaml), plan.html contains exactly **one** `<div class="page">`, manifest carries the correct `campaign_depends_on`. Then run the Phase 4.5 alignment verify; on pass flip `status: planned` in `saga.yaml` and update `saga.html`.
4. **Watch for cross-campaign ownership collisions** between parallel subagents — two campaigns claiming the same new type/asset/interface. Steer the live agent mid-flight when possible; otherwise serialize the pair and note the contract owner in the later campaign's Decision Summary.
5. **Review model**: the user reviews all plan.htmls after the batch; collected notes are applied in a single revision session (planner edit-in-place machinery, per campaign) — not by the saga layer.

When all campaigns are `planned`, run the saga-level coverage audit before closing: in-context, from `inventory.md` + the campaign manifests, confirm (a) every inventory system marked `port` or `adapt` is claimed by exactly one campaign, and (b) every cross-campaign contract is named consistently by its producer and consumer. Report any gap to the user; then set `status: complete` and present the final saga table with every campaign path.

## Phase 4.5 — Prototype Alignment Verify (gate)

A campaign is never marked `planned` on the planner's word alone. After finalization (either mode), spawn one **read-only verifier subagent** (model per § Model Routing) briefed with: the prototype path (skip embedded blobs), the campaign's `inventory.md` rows, the saga anchors, its scope row + Decision Summary, and the finalized plan.html + quest markdowns. It checks four things and returns a structured verdict:

- **Coverage** — every scope item maps to at least one quest.
- **Fidelity** — load-bearing constants and formulas in the quest markdowns match the prototype verbatim; cite the prototype/inventory value on every mismatch.
- **Boundary** — no quest reaches into a sibling campaign's scope.
- **Anchors** — nothing silently contradicts a locked anchor.

Write the report to `<saga-dir>/align/<c##>.md`. Triage:

- **Pass or minor drift** (cosmetic; no constant, contract, or scope item affected): note the minor items in the report, flip `status: planned`, proceed.
- **Blocking drift** (wrong constant, missed scope item, boundary violation, anchor contradiction): set `status: review`, do **not** launch dependent campaigns, and surface the drift list to the user. The fix belongs to the user-driven revision session, not to silent saga-layer edits — the immutability rule stands. After revision, re-run the verifier; flip to `planned` on pass.

The verifier is evidence-precise, not creative: it reports mismatches with citations; it never proposes redesigns.

## Phase 5 — Deferred-UAT Rollup (post-execution, `--uat`)

**Generation is the executor's job; this mode only collects.** `liang-quest-executor` §8b
regenerates `uat-checklist.md` at each campaign root on every run (manual quests held out,
dependency-blocked skips, Tier-2 deferrals). This mode aggregates those per-campaign files into
one saga-ordered checklist. The saga context never re-derives UAT items from manifests, run
reports, or quest markdowns itself — a missing checklist is backfilled by dispatching §8b
standalone workers (step 1); a stale one is fixed by re-running the executor on that campaign.

Run when the user asks for the saga's deferred UAT / manual backlog, or after a sweep reports the
saga's headless portion done. Read-only against campaign folders; the single output is
`<saga-dir>/uat-checklist.md`.

1. **Collect.** For each campaign in `saga.yaml` (by recorded `campaign_id`), look for
   `<campaign-dir>/uat-checklist.md`:
   - **Present** → take its sections as-is (the executor wrote VCs verbatim and tagged
     `[MANUAL]`/`[AGENT]`).
   - **Absent, manifest all-passed** → campaign is clean; contributes nothing.
   - **Absent, manifest has unpassed quests** → the campaign ran before executor §8b existed (or
     never ran). **Backfill:** spawn one worker subagent per such campaign (model per § Model
     Routing), all in **parallel** — workers write disjoint campaign folders, so no waves needed.
     Brief each with: the campaign folder path, and the instruction to execute
     `liang-quest-executor/references/completion-flow.md` **§8b standalone-backfill** exactly —
     manifest is authoritative, latest run report by frontmatter `completed_at`, VCs verbatim from
     quest markdowns, write `uat-checklist.md` (or nothing if clean), no other writes. Verify each
     file exists on disk before consuming it. If a worker fails or the file is malformed, fall
     back to listing that campaign in a **"No checklist on disk"** section with its unpassed quest
     ids and the remedy (re-run the executor on it) — never reconstruct in this context.
2. **Order and group.** Campaigns in `campaign_depends_on` topological order, each campaign's
   sections in the order its checklist already has. Merge into numbered **sessions**: consecutive
   `[MANUAL]` blocks that one editor session can cover (respect any "one session covers quests
   X–Y" note carried in from the executor) collapse together — session grouping across campaigns
   is the one judgment this layer adds. Promote any blocker named by multiple campaigns (a missing
   asset, a broken tool) to a single **Blockers** section up top; verify it still exists on disk
   before listing.
3. **Write** `<saga-dir>/uat-checklist.md`: header with the saga's pass count and generation date;
   the sessions; a final **Wrap-up** section covering manifest status flips (user marks completed
   quests `passed`), `saga.yaml` status sync, and workspace-standard pre-submit steps (e.g. `p4
   reconcile`). Announce the path.
4. **Never** flip quest statuses, edit campaign folders, or execute anything from this mode. On
   completion suggest — never invoke — `skill:liang-quest-executor` for the `[AGENT]` sessions.

Regeneration is cheap and expected: as manual work lands and executors re-run, per-campaign
checklists shrink or disappear, and re-running `--uat` shrinks the rollup to match.

## Phase 6 — Feature Walkthrough (post-execution, `--tour`)

**Generation is the executor's job; this mode only collects.** `liang-quest-executor` §8c writes
`walkthrough.md` at a campaign root — the tutorial covering **every** quest including passed ones
(how it works / what changed / where it lives / see-it-run blocks) — on demand only, never during
a completion flow. This mode aggregates those per-campaign tours into one saga-ordered walkthrough so the user
can learn what the saga built and exercise it feature by feature. The saga context never writes
tour content about a campaign itself.

Run when the user asks to be walked through what was built. Read-only against campaign folders;
the single output is `<saga-dir>/walkthrough.md`.

1. **Collect.** For each campaign in `saga.yaml`, look for `<campaign-dir>/walkthrough.md`:
   - **Present** → take it as-is.
   - **Absent** → spawn one §8c standalone worker per such campaign (model per § Model Routing,
     same chain as UAT-backfill workers), all in **parallel** — disjoint campaign folders. Brief
     each with: the campaign folder path, and the instruction to execute
     `liang-quest-executor/references/completion-flow.md` **§8c** exactly — manifest authoritative,
     latest run report by frontmatter `completed_at`, all quests covered including passed, verify
     named paths exist on disk, write `walkthrough.md`, no other writes. Verify each file exists
     before consuming; on worker failure list the campaign under **"No walkthrough on disk"** with
     the remedy — never reconstruct in this context.
   - A **stale** campaign walkthrough (quests changed since generation) is refreshed by deleting
     it and re-running `--tour`.
2. **Order and interleave.** Campaigns in `campaign_depends_on` topological order, each campaign's
   quest sections in the order its walkthrough already has. The one judgment this layer adds:
   where a tour stop is `[PENDING]`, point at the Phase 5 rollup session that unlocks it (never
   duplicate debt items); where a shared blocker gates several stops, note it once up front.
3. **Write** `<saga-dir>/walkthrough.md`: header with a one-paragraph saga summary, generation
   date, pass count; the campaign tours in order; a closing pointer to `uat-checklist.md` for the
   outstanding debt. Announce the path.
4. **Never** flip quest statuses, edit campaign folders, or execute anything from this mode.

`--uat` and `--tour` are companions: the checklist retires debt (checkbox items drive manifest
flips), the walkthrough teaches and exercises (its checkboxes are observation steps, never
verification records). Run both after a sweep: tour to learn, checklist to close out. For one
browsable page combining both, Phase 7 (`--handover`) renders them into `handover.html`.

## Phase 7 — Handover View (post-execution, `--handover`)

**Presentation layer only.** Renders the two saga-level rollups — `uat-checklist.md` (Phase 5) and
`walkthrough.md` (Phase 6) — into a single self-contained `<saga-dir>/handover.html` the user reads
in a browser. The two markdown files stay the source of truth: agents parse them, checkbox state
lives in them, executor re-runs regenerate them. The HTML is a disposable view — regenerated whole
from the markdown every time, never edited by hand, never a state surface (checked/unchecked
renders as static text), never collected or parsed by any downstream skill.

1. **Ensure fresh sources.** If `<saga-dir>/uat-checklist.md` is missing, run Phase 5 first; if
   `<saga-dir>/walkthrough.md` is missing, run Phase 6 first. If the user says either is stale,
   re-run that phase before rendering — never patch the HTML around stale markdown.
2. **Render with the planner's Phase 2c machinery** — same body-drafter pattern, same
   class contract, same `assemble_plan.py` + the saga `skin` (the page joins the `saga.html` /
   `plan.html` visual family). No bespoke CSS. The handover-shaped mapping onto the contract:
   - One `section.quest` per **tour stop** (campaign), topological order, `id="c01"`…; TOC heading
     "Tour Stops"; eyebrow "Stop NN · <passed>/<total>"; `diff-badge` = the campaign's saga-level
     difficulty; `dep-state` = `<passed>/<total> · depends: <ids>`.
   - Per stop: purpose = the walkthrough's stop summary; steps = its highlight and see-it-run
     observation items (static text — no live checkboxes); footer deps col = campaign
     dependencies, second col heading "Outstanding debt" = the UAT sessions gating this stop, each
     linking `uat-checklist.md` § that session. Fully-passed stops say "none".
   - Exactly one `diagram-section` between TOC and main: the **UAT session unlock chain** (nodes =
     sessions in order, `.is-active` = next actionable, `.is-muted` = blocked, plain = done;
     legend names each session's `[MANUAL]`/`[AGENT]` tag).
   - Notes section: cards for shared Blockers and the walkthrough's quick-start tour (if present);
     the `notes-wide` table = session index — one row per session, pill = its state
     (`pill-recommended` done / `pill-deferred` next / `pill-rejected` blocked), plus the wrap-up
     reminders from the checklist's final section.
   - Depth is LEAN: summaries and links into the two markdown files — never the full checklist
     item text duplicated into the page.
3. **Assemble** with `assemble_plan.py` to `<saga-dir>/handover.html` (title "<Saga Title> —
   Handover"), delete `_body.html`, auto-open in the browser, announce the path.
4. **Regenerate on demand** — after any `--uat`/`--tour` re-run, offer a one-line "re-render
   handover.html?"; regeneration is cheap and the file is safe to delete at any time. **Never**
   flip quest statuses, edit campaign folders, or write anything but `handover.html` from this
   mode.

## Next Move

After completion (or at any session stop with 2+ planned campaigns), suggest — never invoke:

```
skill:liang-quest-batch-sweep — sweep saga <saga-dir-name>   # scoped: THIS saga's campaigns only (sweep.py --saga), in campaign_depends_on order
skill:liang-quest-executor .liang/campaigns/<campaign-dir>   # or run one campaign directly
```

Always suggest the saga-scoped form — an unscoped sweep is workspace-global and re-dispatches every non-passed campaign in the workspace's history. When the saga ran with `--claude`, append `--claude` to both suggestions. Remind the user that quests flagged `manual: true` are held out of the headless queue by the sweep and become a post-sweep in-editor backlog — after the sweep finishes, `skill:liang-quest-saga-planner --uat <saga-dir-name>` (Phase 5) rolls that backlog plus all deferred Tier-2 VCs into `<saga-dir>/uat-checklist.md`, and `--handover` (Phase 7) renders it with the walkthrough into one browsable `handover.html`.

## Boundaries

1. **No execution, no VCS** beyond writing saga state (including `uat-checklist.md`, `walkthrough.md`, and `handover.html`) and the single manifest patch.
2. **Never author campaign content** — no quest markdowns, no plan.html edits. That is planner territory, reached only through the planner handoff (same-context or batch subagent).
3. **Never nest campaigns** under `.liang/sagas/` or any subfolder; sweep discovery depends on flat `.liang/campaigns/`.
4. **Never re-plan a planned campaign.** Corrections to a finalized campaign are out of scope for the saga layer.
5. **No secrets, credentials, or binary assets** in saga artifacts; the inventory references prototype internals by description and line ranges, not by embedding blobs.

## Relationship to Other Skills

- **Downstream (handoff)**: `liang-quest-planner` — invoked once per campaign in `--quick` mode, same-context or via a batch subagent; sole producer of campaign folders. Its Phase 2c HTML machinery (class contract, `assemble_plan.py`, skins) is also reused for `saga.html` (Phase 3.5) and `handover.html` (Phase 7).
- **Downstream (suggested)**: `liang-quest-batch-sweep` / `liang-quest-executor` — consume the planned campaigns; sweep toposorts via the `campaign_depends_on` fields this skill patches in. The executor's §8b per-campaign `uat-checklist.md` artifacts are Phase 5's sole input; its §8c `walkthrough.md` artifacts are Phase 6's.
- **Shared foundation**: `liang-quest-core` — manifest schema (`campaign_depends_on` semantics live in `references/campaign/manifest-schema.md`).
- **Upstream (typical source)**: `liang-game-prototyper` output under `.liang/prototypes/`, but any sufficiently concrete prototype or spec file works as intake material.
