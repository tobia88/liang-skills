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
    manual: true             # OPTIONAL; human-in-editor quest, absent (false) for automated quests
    status: "ready"          # see Status Vocabulary; planner writes "ready"
```

`manual: true` marks a quest as human-in-editor work (UMG assembly, asset authoring, playtest UAT) that must never be dispatched to a headless child. The planner writes it for every quest whose title/purpose is labeled MANUAL. Consumed by both the executor (at §5 campaign intake) and the batch sweep orchestrator (sweep.py), which apply the same hold algorithm: such quests — and, transitively, their un-passed in-campaign dependents — are held at `status: skipped` with `skip_reason: manual_deferred` / `manual_dependency` instead of being dispatched; the campaign then counts as passed-with-manual-backlog. Hold semantics: `liang-quest-core/references/execution/status-transitions.md § Manual Holds`.

No `workflow` field. The planner-native pipeline has a single executor, so no workflow discriminator is needed.

Difficulty drives downstream model selection per `.liang/project.yaml`'s `execution_by_difficulty` mapping. The planner's `references/manifest-example.yaml` is the live worked example.

### Executor-Managed Fields (canonical)

`liang-quest-executor` adds/mutates these fields on quest entries during execution:

```yaml
quests[]:
  current_cycle: integer     # 1-based index of step currently executing (0 = not started)
  total_cycles: integer      # total step count parsed from the quest .md's ## Steps section
  skip_reason: string        # present when status is "skipped"; references failed dependency.
                             #   The executor (§5 intake) and sweep.py also write
                             #   "manual_deferred" / "manual_dependency" here to hold
                             #   manual quests out of headless dispatch
  started_at: string         # ISO 8601; set on in_progress transition
  completed_at: string       # ISO 8601; set on passed/failed/skipped transition
  usage:                     # child-process spend, harvested from pinned child session files;
    total_tokens: integer    #   sum across ALL children for this quest (execute attempts incl.
    cost_usd: float          #   retries, re-plan, verify). Absent when untracked (--claude mode
                             #   or harvest failure) — never written as zeros.
```

`usage.cost_usd` is the sum of per-message costs as priced by the Pi harness's model
registry at run time. Tokens are exact; dollars are as accurate as that registry
(subscription/OAuth providers may price at 0).

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
