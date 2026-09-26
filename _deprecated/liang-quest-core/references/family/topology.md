# Quest Family Topology

The canonical statement of how the quest family fits together. Skills cite this file
instead of restating it (criterion C9). Maintainers and the audit only — no skill reads
it at activation.

## The Ladder

| Rung | What it is | Size | Produced by |
|---|---|---|---|
| **discussion** | Locked decisions in the live conversation, optionally a brainstorm Strategy Report | — | the user, `liang-brainstorm-*` |
| **saga** | A body of work too big for one campaign | 2–8 campaigns | `liang-quest-saga-planner` |
| **campaign** | One planner run | 2–8 quests | `liang-quest-planner` |
| **quest** | One executable unit | steps inside one quest file | `liang-quest-planner` (written), `liang-quest-executor` (run) |

A saga is optional: work that fits one campaign goes from discussion straight to the
planner.

## The Side Scout

`liang-quest-recon` is not a rung. It is the only family skill that reads a raw
prototype. Its breakdown folder (lite or full profile) becomes a **source for the
discussion** and is consumed through `00-index.md` by the saga planner, or read into the
conversation ahead of a single planner run. Consumers treat the folder as a frozen
snapshot.

## Feed Graph

```
discussion ──────────────┬──> saga-planner ──(one handoff per campaign: --quick same-context | --headless batch subagent)──> planner
recon folder (optional) ─┘                                                    │
discussion ──(fits one campaign)────────────────────────────────────────────> planner
                                                                              │
planner ──campaign folder──> executor ──run artifacts──> saga-planner rollups (--uat / --tour / --handover)
                                ▲
batch-sweep ──dispatches one executor per eligible campaign, in campaign_depends_on order
saga-planner ──saga.yaml──> batch-sweep (--saga scope), archiver (open-saga hold)   [read-only]
status   ── reads manifests, writes nothing
archiver ── moves finished campaigns under archive/, out of every other skill's glob
core     ── shared references, read by all, invoked by none
```

## Direction Rules

- **Files are the API.** Every arrow is a folder or file on disk, never an in-band return.
- **Decisions flow forward only.** Saga anchors reach recon only as locked-decision input
  to a *later* recon run; a saga disagreeing with a recon row records an override in its
  own `inventory.md`.
- **Finalized is frozen.** A planned campaign is immutable to the saga layer, except the
  single `campaign_depends_on` manifest patch; a recon folder is immutable to its
  consumers, and re-opened only by recon's own upgrade and gap-fix flows.
- **Campaigns land flat** in `.liang/campaigns/`; a saga groups them through its
  `saga.yaml` campaign list, the shared title prefix, and `campaign_depends_on` — never by
  nesting.
