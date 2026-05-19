# Manifest Schema

Source of truth for `manifest.yaml` and Quest Contract YAML used across the JRPG quest planning family.

## Manifest YAML

Lives at `campaigns/<campaign>/manifest.yaml`.

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
    workflow: string          # "tdd" | "general" | "quick"
```

### Optional Extensions

```yaml
notes: string
tags: [string]
generated_by: string
schema_version: string
```

### Executor-Managed Fields (on quest entries)

These are added/mutated only by executors during execution:

```yaml
quests[]:
  current_cycle: integer     # 1-based index of cycle/step currently executing (0 = not started)
  total_cycles: integer      # total cycle/step count from plan
  skip_reason: string        # present when status is "skipped"
  started_at: string         # ISO 8601; set on in_progress transition
  completed_at: string       # ISO 8601; set on passed/failed/skipped transition
```

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
workflow: string              # "tdd" | "general" | "quick"
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
- `workflow` must be exactly `"tdd"`, `"general"`, or `"quick"`.
