# Tiered Schema — Manifest and Quest Contract

This file is the source of truth for the Campaign schema used by `liang-quest-cartographer`.

Two artifacts, **Layered Truth**:

- `manifest.yaml` — campaign metadata + per-quest summary index.
- `quest-NNN-<slug>/index.html` — opens with an HTML comment containing the full Quest Contract YAML.

Do not duplicate full Quest Contracts into the manifest. Do not move campaign metadata into quest files.

YAML key style:

- snake_case
- lowercase
- ASCII only
- formal names (no JRPG metaphors in keys; JRPG flavor stays in the HTML views)

## Manifest YAML

### Required Core

```yaml
campaign_id: string          # e.g. "camp-2026-05-17-example-campaign"
slug: string                 # filesystem-safe; matches the folder name suffix
title: string                # human-readable campaign title
created_at: string           # ISO 8601 date or datetime
source_report: string        # path to the originating Brainstorm/Strategy Report
lens: string                 # planning lens of the source, e.g. "Skill Creation"
summary: string              # short campaign-level summary; one paragraph

quests:                      # ordered list; order communicates recommended progression
  - id: string               # e.g. "q001"
    title: string
    path: string             # relative path to the quest's index.html
    priority: string         # "low" | "medium" | "high"
    readiness: string        # "low" | "medium" | "medium-high" | "high"
    status: string           # see Status Vocabulary below
    depends_on: [string]     # list of quest ids this quest depends on; may be empty
```

### Downstream-Stamped Fields (v3)

These fields are NOT written by the cartographer. They are stamped by the downstream skill (tactician or quick) that first processes the campaign.

```yaml
workflow: string             # "tdd" | "general" | "quick" — stamped once at campaign level, not per quest
```

In schema v3, workflow is a campaign-level field stamped by the downstream skill that first processes the campaign. It is not a per-quest property. For v1/v2 campaigns where workflow was per-quest, the per-quest values are ignored; the downstream skill stamps campaign-level workflow on first contact.

### Optional Extensions

```yaml
notes: string                # campaign-level free-form notes
tags: [string]               # arbitrary tags
generated_by: string         # skill name + version
schema_version: string       # bumped when this schema changes
```

## Quest Contract YAML

This lives inside the **opening HTML comment** of each `quest-NNN-<slug>/index.html`.

### Required Core

```yaml
quest_id: string             # matches manifest quests[].id, e.g. "q001"
campaign_id: string          # matches manifest campaign_id
title: string                # human-readable quest title
purpose: string              # why this quest exists; strategic intent
desired_outcome: string      # what successful completion produces
victory_conditions: [string] # observable success criteria
scope_boundary: string       # what this quest covers
depends_on: [string]         # other quest ids this quest depends on
risks: [string]              # known risks specific to this quest
open_questions: [string]     # Fog of War items the planner will need to resolve
planner_handoff: string      # explicit note to the future planner skill
readiness: string            # "low" | "medium" | "medium-high" | "high"
status: string               # see Status Vocabulary below
```

### Downstream-Stamped Fields (v3)

Quest contracts are workflow-agnostic. Workflow is stamped at campaign level in the manifest by the downstream skill, not in quest contracts.

### Optional Extensions

```yaml
non_goals: [string]          # explicit out-of-scope items
constraints: [string]        # technical, time, or context constraints
required_inputs: [string]    # what the planner will need before planning starts
expected_output: string      # what the planner is expected to produce
source_evidence: [string]    # short excerpts/refs from the source report
notes: string                # free-form supplementary notes
```

## Status Vocabulary

Use these values for `status`:

- `ready_for_planning` — Quest Contract is complete enough for the planner skill to consume.
- `needs_clarification` — meaningful gaps exist; planner should not start yet.
- `blocked` — depends on resolution of something outside the Campaign.

Do not invent additional statuses.

## Priority Vocabulary

Use:

- `low`
- `medium`
- `high`

## Readiness Vocabulary

Use:

- `low`
- `medium`
- `medium-high`
- `high`

Do not use numeric scores.

## Workflow Vocabulary

Use exactly these values:

- `tdd` — quests with testable code deliverables and automated test commands (Red/Green/Refactor cycles)
- `general` — config, docs, assets, spikes, glue, prompt work, skill creation, or any quest without meaningful test-first cycles
- `quick` — simple, narrowly-scoped quests that bypass the tactician+executor pipeline for single-pass scout+execute

Downstream skills (tacticians and quick) assign workflow when they first process a campaign. The workflow value reflects the planning approach used for the entire campaign:
- `tdd` — the TDD tactician planned the campaign
- `general` — the general tactician planned the campaign
- `quick` — the quick skill executed the campaign directly

## Validation Rules

Before any file is written:

- All Required Core keys must be present in the manifest and in every Quest Contract.
- `quest_id` values must be unique within the Campaign.
- Each `quests[].id` in the manifest must have a matching quest HTML file at `quests[].path`.
- `depends_on` references must point to existing `quest_id` values in the same Campaign.
- The `depends_on` graph must be acyclic.
- All slugs must be lowercase ASCII with hyphens, no spaces or special characters.
- `created_at` must be a valid ISO 8601 date or datetime.
- `workflow`, when present at campaign level, must be exactly `"tdd"`, `"general"`, or `"quick"`. In v3, workflow is campaign-level only (stamped downstream). Per-quest workflow fields from v1/v2 are ignored.

If any rule fails, the skill must not write files.

## Layered Truth Reminder

- The manifest is for **orientation**: campaign metadata + quest index.
- The quest HTML is for the **full contract**: everything a future planner needs to plan that quest.
- Never duplicate full quest fields into the manifest.
- Never split campaign-level metadata into quest files.

## Schema Versioning

If this schema changes:

- Bump `schema_version` in new manifests.
- Do not retroactively edit existing campaigns; generate new ones instead.

### Backward Compatibility

v1 campaigns have workflow per quest in Required Core, assigned by the cartographer. v2 campaigns have workflow per quest as Downstream-Stamped. v3 campaigns have workflow at campaign level only. When a v3 tool encounters a v1/v2 campaign with per-quest workflow values, it ignores them and stamps campaign-level workflow on first contact. The schema_version field in the manifest (Optional Extensions) indicates which version generated the campaign. Absence of schema_version implies v1.
