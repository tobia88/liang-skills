# Manifest Schema

Source of truth for `manifest.yaml` and Quest Contract YAML used across the JRPG quest planning family.

## Manifest YAML

Lives at `.liang/campaigns/<campaign>/manifest.yaml`.

### Required Core

```yaml
campaign_id: string          # e.g. "camp-2026-05-17-example"
slug: string                 # filesystem-safe; matches folder name suffix
title: string                # human-readable campaign title
created_at: string           # ISO 8601
source_report: string        # path to the originating Brainstorm/Strategy Report
lens: string                 # planning lens, e.g. "Skill Creation"
summary: string              # short campaign-level summary; one paragraph

quests:                      # ordered list; order communicates recommended progression
  - id: string               # e.g. "q001"
    title: string
    path: string             # relative path to quest's index.html
    priority: string         # "low" | "medium" | "high"
    readiness: string        # "low" | "medium" | "medium-high" | "high"
    status: string           # see Status Vocabulary
    depends_on: [string]     # quest IDs; may be empty
```

### Downstream-Stamped Fields (campaign-level)

These fields are NOT written by the cartographer. They are stamped by the downstream skill (tactician or quick) that first processes the campaign.

```yaml
workflow: string             # "tdd" | "general" | "quick" — stamped once at campaign level
```

The workflow field is a campaign-wide property, not a per-quest property. Whichever skill first processes the campaign stamps its workflow. Executors check this field at startup and refuse to run if the workflow does not match.

### Optional Extensions

```yaml
notes: string
tags: [string]
generated_by: string
schema_version: string
campaign_depends_on: [string]  # campaign_id values (per dc001) that must complete before this campaign runs; optional; empty list or absence = no cross-campaign dependencies
```

### Cross-Campaign Dependencies

`campaign_depends_on` is an optional list of `campaign_id` values declaring that this campaign requires another campaign to complete (all quests `passed`) before it can be safely run.

- Format: list of `campaign_id` strings (per crosscut decision dc001 in `camp-2026-05-24-batch-campaign-sweep`). NOT slugs (slugs can drift on rename) and NOT paths (paths shift on directory moves).
- Default semantics: absence of the field OR an empty list means "no cross-campaign dependencies."
- Validation: each referenced `campaign_id` should match an existing campaign's `campaign_id` within the same workspace. The cartographer is responsible for ensuring referenced campaigns exist at write time. Consumers (e.g., a sweep orchestrator script) should toposort by these edges and detect cycles.
- Backward compatibility: campaigns generated before this field existed (`schema_version` < 4) continue to validate. Missing field is interpreted as empty list.

### Executor-Managed Fields (on quest entries)

These are added/mutated only by executors during execution:

```yaml
quests[]:
  current_cycle: integer     # 1-based index of cycle/step currently executing (0 = not started)
  total_cycles: integer      # total cycle/step count from plan
  skip_reason: string        # present when status is "skipped"
  started_at: string         # ISO 8601; set on in_progress transition
  current_step_started_at: string  # ISO 8601; updated at each step/cycle start for progress polling
  completed_at: string       # ISO 8601; set on passed/failed/skipped transition
```

The `current_step_started_at` field is updated at the start of each step (general) or cycle (TDD). In batch mode, Claude polls this field to calculate elapsed time and detect potential hangs. In Claude mode, it serves as an audit timestamp.

## Quest Contract YAML

Lives inside the opening HTML comment of each `quest-NNN-<slug>/index.html`.

### Required Core

```yaml
quest_id: string             # matches manifest quests[].id
campaign_id: string          # matches manifest campaign_id
title: string
purpose: string              # why this quest exists
desired_outcome: string      # what successful completion produces
victory_conditions: [string] # observable success criteria
scope_boundary: string       # what this quest covers
depends_on: [string]         # other quest IDs
risks: [string]              # known risks
open_questions: [string]     # Fog of War items
planner_handoff: string      # explicit note to the planner skill
readiness: string            # "low" | "medium" | "medium-high" | "high"
status: string               # see Status Vocabulary
```

### Optional Extensions

```yaml
non_goals: [string]
constraints: [string]
required_inputs: [string]
expected_output: string
source_evidence: [string]
notes: string
```

## Priority Vocabulary

- `low`
- `medium`
- `high`

## Readiness Vocabulary (Quest-Level)

- `low`
- `medium`
- `medium-high`
- `high`

## Validation Rules

Before writing any campaign files:

- All Required Core keys must be present in the manifest and every Quest Contract.
- `quest_id` values must be unique within the Campaign.
- Each `quests[].id` must have a matching quest HTML file at `quests[].path`.
- `depends_on` references must point to existing quest IDs in the same Campaign.
- The `depends_on` graph must be acyclic.
- All slugs must be lowercase ASCII with hyphens, no spaces or special characters.
- `created_at` must be valid ISO 8601.
- When `campaign_depends_on` is present, each entry must be a non-empty string. Cross-campaign target existence is the cartographer's responsibility, not a manifest validation rule.
