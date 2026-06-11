# Manifest Schema

Source of truth for `manifest.yaml` and quest Markdown contracts used across the JRPG quest planning family.

## Canonical Schema (Planner → Executor)

This is the **canonical** manifest schema for new campaigns. Produced by `liang-quest-planner`, consumed by `liang-quest-executor`. The campaign manifest `schema_version: 4` is distinct from `.liang/project.yaml`'s `schema_version: 1`.

```yaml
schema_version: 4            # campaign manifest schema version (canonical); distinct from project.yaml
campaign_id: string          # e.g. "campaign-2026-05-27-planner-executor-pivot"
title: string                # human-readable campaign title
created_at: string           # ISO 8601
source: string               # e.g. "brainstorm" | "in-session conversation"
quest_count: integer

quests:
  - id: string               # e.g. "q001"
    title: string
    file: string             # relative path to quest-NNN-<name>.md
    depends_on: [string]     # quest IDs; may be empty
    difficulty: "easy" | "medium" | "hard"
    status: "ready"          # see Status Vocabulary; planner writes "ready"
```

No `workflow` field. The planner-native pipeline has a single executor, so no workflow discriminator is needed.

Difficulty drives downstream model selection per `.liang/project.yaml`'s `execution_by_difficulty` mapping. The planner's `references/manifest-example.yaml` is the live worked example.

### Executor-Managed Fields (canonical)

`liang-quest-executor` adds/mutates these fields on quest entries during execution:

```yaml
quests[]:
  current_cycle: integer     # 1-based index of step currently executing (0 = not started)
  total_cycles: integer      # total step count parsed from the quest .md's ## Steps section
  skip_reason: string        # present when status is "skipped"; references failed dependency
  started_at: string         # ISO 8601; set on in_progress transition
  completed_at: string       # ISO 8601; set on passed/failed/skipped transition
```

## Cross-Campaign Dependencies

`campaign_depends_on` is an optional list of `campaign_id` values declaring that a campaign requires another campaign to complete before it can be safely run. Consumed by the batch sweep orchestrator.

## Validation Rules

Before writing any campaign files:

- All Required Core keys must be present in the manifest.
- `quest_id` values must be unique within the Campaign.
- Each `quests[].id` must have a matching quest `.md` file at `quests[].file`.
- `depends_on` references must point to existing quest IDs in the same Campaign.
- The `depends_on` graph must be acyclic.
- All slugs must be lowercase ASCII with hyphens, no spaces or special characters.
- `created_at` must be valid ISO 8601.
