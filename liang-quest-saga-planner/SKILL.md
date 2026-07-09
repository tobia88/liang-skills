---
name: liang-quest-saga-planner
description: "Saga-level planner that turns a large prototype (e.g. an HTML game prototype under .liang/prototypes/) into multiple related campaigns via repeated liang-quest-planner handoffs. Four phases: subagent prototype intake (systems inventory + workspace integration map), saga discussion (lock architecture anchors once), campaign decomposition with cross-campaign dependency topology, and a resumable per-campaign handoff loop that invokes liang-quest-planner --quick with pre-baked Decision Summaries and patches campaign_depends_on into each finalized manifest. State lives in .liang/sagas/ so planning survives across sessions."
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

## Output Layout

```
.liang/sagas/saga-<YYYY-MM-DD>-<slug>/
  saga.yaml        # state: anchors, campaign list, statuses — the resume point
  inventory.md     # systems inventory from the intake subagent
  saga.html        # living dashboard — self-contained, planner-machinery assembled

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
    status: pending | planned
    campaign_id: ""             # folder name recorded after planner finalization
```

## Activation

Activate when:
1. User invokes by name (`skill:liang-quest-saga-planner`), optionally with a prototype path.
2. User explicitly asks to turn a prototype into **multiple** plans/campaigns ("break this prototype into campaigns", "saga-plan this").
3. An in-progress saga exists in `.liang/sagas/` and the user asks to continue it.

Do **not** activate from generic "plan this" (that is `liang-quest-planner`'s territory) or "run/sweep campaigns" (executor / batch-sweep territory). If the prototype looks small enough for a single campaign (≲8 quests of work), say so and recommend invoking `liang-quest-planner` directly instead — a one-campaign saga is pure overhead.

**On every invocation, check `.liang/sagas/` first.** If an in-progress saga matches the user's intent, show its status table (campaigns, statuses, next pending) and resume at the right phase instead of starting over. Never run two sagas over the same prototype concurrently.

## Phase 1 — Prototype Intake (subagent)

1. Resolve the prototype path (ask if ambiguous; default to looking under `.liang/prototypes/`).
2. Create the saga folder and a stub `saga.yaml` (`status: intake`). Derive `saga_id` from the local date + a slug of the prototype name; pick a `short_name` (2–3 syllables, e.g. "BattleSim") and confirm it with the user in one line — it prefixes every campaign title.
3. **Spawn one intake subagent** (general-purpose / Explore-equivalent; read-only) briefed to produce `inventory.md`. The brief must include:
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

## Phase 4 — Per-Campaign Planner Handoff (resumable loop)

Set `status: planning`. For the next `pending` campaign in topological order:

1. **Assemble its Decision Summary in-context** — the planner's exact 9-field shape (Main Quest, Planning Lens, Target User, Locked Decisions, Victory Conditions, Scope Boundary, Risks, Open Questions, Decision Table), built from `inventory.md` + the saga anchors + this campaign's scope row. Two saga-specific rules:
   - **Scope Boundary must name sibling campaigns' scopes as explicit non-goals** ("enemy AI is campaign c04, not here") — this is what keeps N plans related-but-disjoint.
   - **Cross-campaign contracts**: when this campaign consumes something a dependency campaign produces (a type, an asset, an interface), state that interface in Locked Decisions as this campaign's consumption contract. Read the dependency campaign's manifest/quest titles if needed to phrase it accurately.
   Leave no 9-field gap — a complete summary is what makes `--quick` gap-fill a no-op.
2. **Invoke the planner**: read `../liang-quest-planner/SKILL.md` and execute it in this same context in **`--quick` mode**, presenting the Decision Summary as the conversation's decisions. Let the planner run its own Phases 2–4 untouched (body-drafter subagent, `assemble_plan.py`, Phase 3 open discussion, quest markdown writing) — with one saga override: the aesthetic direction is the saga `skin` from `saga.yaml`, not the planner's per-lens auto-pick. Do not shortcut its machinery otherwise.
3. **After planner finalization**, in the new campaign folder's `manifest.yaml`, add top-level `campaign_depends_on: [<campaign_id>, ...]` mapping this campaign's saga-local `depends_on` to the recorded `campaign_id` values of the already-planned dependency campaigns. Omit the field when there are no dependencies. This is the saga planner's only write inside a campaign folder.
4. **Update `saga.yaml`** (set the campaign's `status: planned`, record its `campaign_id` — the folder name) **and update `saga.html`** per Phase 3.5 (status flip, diagram node, plan.html link, counts).
5. **Context budget check.** After each campaign, assess remaining context. A planner handoff is expensive (summary + body-drafter round + discussion + files); 2–3 campaigns per session is the realistic ceiling. When context is getting thin, stop cleanly: report the saga status table and tell the user to re-invoke the skill to resume. Never start a handoff you likely can't finish.

When all campaigns are `planned`, set `status: complete` and present the final saga table with every campaign path.

## Next Move

After completion (or at any session stop with 2+ planned campaigns), suggest — never invoke:

```
skill:liang-quest-batch-sweep — sweep saga <saga-dir-name>   # scoped: THIS saga's campaigns only (sweep.py --saga), in campaign_depends_on order
skill:liang-quest-executor .liang/campaigns/<campaign-dir>   # or run one campaign directly
```

Always suggest the saga-scoped form — an unscoped sweep is workspace-global and re-dispatches every non-passed campaign in the workspace's history. Remind the user that quests flagged `manual: true` are held out of the headless queue by the sweep and become a post-sweep in-editor backlog.

## Boundaries

1. **No execution, no VCS** beyond writing saga state and the single manifest patch.
2. **Never author campaign content** — no quest markdowns, no plan.html edits. That is planner territory, reached only through the in-context handoff.
3. **Never nest campaigns** under `.liang/sagas/` or any subfolder; sweep discovery depends on flat `.liang/campaigns/`.
4. **Never re-plan a planned campaign.** Corrections to a finalized campaign are out of scope for the saga layer.
5. **No secrets, credentials, or binary assets** in saga artifacts; the inventory references prototype internals by description and line ranges, not by embedding blobs.

## Relationship to Other Skills

- **Downstream (same-context)**: `liang-quest-planner` — invoked once per campaign in `--quick` mode; sole producer of campaign folders. Its Phase 2c HTML machinery (class contract, `assemble_plan.py`, skins) is also reused for `saga.html` (Phase 3.5).
- **Downstream (suggested)**: `liang-quest-batch-sweep` / `liang-quest-executor` — consume the planned campaigns; sweep toposorts via the `campaign_depends_on` fields this skill patches in.
- **Shared foundation**: `liang-quest-core` — manifest schema (`campaign_depends_on` semantics live in `references/campaign/manifest-schema.md`).
- **Upstream (typical source)**: `liang-game-prototyper` output under `.liang/prototypes/`, but any sufficiently concrete prototype or spec file works as intake material.
