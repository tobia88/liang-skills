# Status Transitions

Shared status vocabulary and transition rules for manifest quest entries across both TDD and general executors.

## Full Status Vocabulary

| Status | Meaning | Set By |
|--------|---------|--------|
| `ready_for_planning` | Quest contract complete; no plan yet | Cartographer |
| `planned` | plan.html written | Tactician (TDD or General) |
| `in_progress` | Execution underway | Executor (TDD, General, or Quick) |
| `passed` | All cycles/steps completed successfully | Executor |
| `failed` | A cycle/step exhausted retries | Executor |
| `skipped` | Dependency failed (cascade) | Executor |
| `needs_clarification` | Meaningful gaps; planner should not start | Cartographer |
| `blocked` | Depends on resolution outside the Campaign | Cartographer |

## Allowed Transitions

### Cartographer → Tactician

```
ready_for_planning → planned       (tactician writes plan.html)
```

### Tactician → Executor

The tactician's only allowed mutation is `ready_for_planning → planned`.

### Executor Transitions

```
planned       → in_progress        (execution begins)
in_progress   → passed             (all cycles/steps pass)
in_progress   → failed             (a cycle/step exhausts retries)
planned       → skipped            (cascade from dependency failure)
```

Any transition not listed above is a violation.

### Quick Executor Transitions

The quick executor bypasses the `planned` status entirely, transitioning directly from `ready_for_planning` to `in_progress`.

```
ready_for_planning → in_progress    (quick execution begins; no plan step)
in_progress        → passed         (all victory conditions verified)
in_progress        → failed         (execution or verification fails; no retry)
ready_for_planning → skipped        (cascade from dependency failure)
```

## Executor-Owned Manifest Fields

Both TDD and general executors manage these additional fields on quest entries:

```yaml
quests[]:
  status: string              # see transitions above
  current_cycle: integer      # 1-based index of cycle/step currently executing (0 = not started)
  total_cycles: integer       # total cycle/step count from plan
  skip_reason: string         # present when status is "skipped"; references failed dependency
  started_at: string          # ISO 8601; set on in_progress transition
  completed_at: string        # ISO 8601; set on passed/failed/skipped transition
```

All other manifest fields (id, title, path, priority, readiness, depends_on, workflow, tags, notes) are read-only to executors.

## Cascade Skip

When a quest fails:

1. Find all quests whose `depends_on` includes the failed quest (transitively).
2. Set their status to `skipped` with `skip_reason: "dependency_failed: <quest-id>"`.
3. Remove them from the execution queue.

## Crash Recovery

Both executors support crash recovery:

1. Detect `status: in_progress` quests in the manifest.
2. Inspect `.run/<quest-id>/` for checkpoint state.
3. Offer the user: **Resume** from last checkpoint, or **Restart** (reset to planned, clean .run/).
4. Never silently resume. Always ask.

Quick executor does not support crash recovery. It has no `.run/` directory, no checkpoints, and no retry mechanism. A failed quick quest must be re-run from scratch.
