# Status Transitions

Shared status vocabulary and transition rules for manifest quest entries.

## Canonical: Planner → Executor Transitions

The canonical pipeline (`liang-quest-planner` → `liang-quest-executor`) uses a compact vocabulary — the planner is the planner and the executor is the executor, so there's no `ready_for_planning → planned` intermediate.

| Status | Meaning | Set By |
|--------|---------|--------|
| `ready` | Quest is planned and ready to execute | Planner |
| `in_progress` | Execution underway | Executor |
| `passed` | All steps completed and Tier 1 VCs verified (Tier 2 VCs may still be pending UAT) | Executor |
| `failed` | A step exhausted retries, a Tier 1 VC failed, or a Tier 2 VC failed in post-run UAT | Executor |
| `skipped` | Dependency failed (cascade) | Executor |

### Allowed Transitions

```
ready         → in_progress        (executor begins quest)
in_progress   → passed             (all steps passed and all Tier 1 VCs passed)
in_progress   → failed             (a step exhausted retries OR a Tier 1 VC failed)
passed        → failed             (a Tier 2 VC failed in §8a post-run UAT review)
ready         → skipped            (cascade from dependency failure)
```

Any transition not listed above is a violation.

### Tiered Retry (Canonical)

`liang-quest-executor` uses tiered retry per step (matching the deprecated general-executor's pattern):

| Retry | Strategy | Details |
|-------|----------|---------|
| Retry 1 | Lesson-only | Execute-child receives `accumulated_lessons` + `previous_failure`. No re-plan-child. Original step content unchanged. |
| Retry 2+ | Re-plan escalation | Re-plan-child invoked with planning model. Produces `revised_instructions` (and optionally `revised_code_block`). Execute-child receives revised content + all accumulated lessons. |
| Max retries exhausted | Hard fail | Step → `failed`. Quest → `failed`. Final lesson extracted. Transitive dependents cascade-skipped. |

Retry tier does not affect status transitions — both tiers stay in `in_progress`. The tier distinction is recorded in the lesson schema for post-run analysis. Retry limit is `executor.max_step_retries` in `project.yaml` (default: 3).

---

## Deprecated: Cartographer → Tactician → Executor Vocabulary

> **DEPRECATED.** The cartographer/tactician chain is deprecated. Retained for in-flight campaigns.

### Full Status Vocabulary (Deprecated)

| Status | Meaning | Set By |
|--------|---------|--------|
| `ready_for_planning` | Quest contract complete; no plan yet | Cartographer (deprecated) |
| `planned` | plan.html written | Tactician (deprecated) |
| `in_progress` | Execution underway | Legacy Executor |
| `passed` | All cycles/steps completed successfully | Legacy Executor |
| `failed` | A cycle/step exhausted retries | Legacy Executor |
| `skipped` | Dependency failed (cascade) | Legacy Executor |
| `needs_clarification` | Meaningful gaps; planner should not start | Cartographer (deprecated) |
| `blocked` | Depends on resolution outside the Campaign | Cartographer (deprecated) |

### Allowed Transitions (Deprecated)

```
ready_for_planning → planned       (tactician writes plan.html)
planned       → in_progress        (legacy execution begins)
in_progress   → passed             (all cycles/steps pass)
in_progress   → failed             (a cycle/step exhausts retries)
planned       → skipped            (cascade from dependency failure)
```

`liang-quest-quick` also uses the `ready_for_planning → in_progress` shortcut transition (it bypasses the tactician but consumes cartographer-format campaigns). Quick stays alive; only the cartographer/tactician/general/tdd-executor chain is deprecated.

### Tiered Retry Behavior

Both TDD and general executors use tiered retry escalation when a cycle/step fails:

| Retry | Strategy | Details |
|-------|----------|---------|
| Retry 1 | Lesson-only | Execute-child receives `accumulated_lessons` + `previous_failure`. No re-plan-child invoked. Original instructions/guidance unchanged. |
| Retry 2+ | Re-plan escalation | Re-plan-child invoked with planning model. Produces `revised_instructions` (general) or `revised_implementation_guidance` (TDD). Execute-child receives revised content + all accumulated lessons. |
| Max retries exhausted | Hard fail | Quest status set to `failed`. Final lesson extracted. All transitive dependents cascade-skipped. |

The tiered model applies identically in both Claude mode (subagents) and batch mode (Pi CLI children). The retry limit is governed by `max_step_retries` (general) or `max_cycle_retries` (TDD) in `project.yaml` (default: 3).

Retry tier does not affect status transitions — both tiers produce the same `in_progress` state. The tier distinction is recorded in the lesson schema (see run-report.md) for post-run analysis.

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

All other manifest fields (id, title, path, priority, readiness, depends_on, tags, notes) are read-only to executors.

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
