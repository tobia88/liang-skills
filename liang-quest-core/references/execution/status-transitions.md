# Status Transitions

Shared status vocabulary and transition rules for manifest quest entries.

## Canonical: Planner → Executor Transitions

The canonical pipeline (`liang-quest-planner` → `liang-quest-executor`) uses a compact vocabulary — the planner is the planner and the executor is the executor, so there's no `ready_for_planning → planned` intermediate.

| Status | Meaning | Set By |
|--------|---------|--------|
| `ready` | Quest is ready to execute | Planner |
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
ready         → skipped            (manual hold, applied at executor intake §5)
failed        → skipped            (manual hold re-applied at intake — manual quests and their
                                    un-passed dependents are held regardless of a prior failure)
skipped       → ready              (stale manual-hold release, applied at executor intake §5)
```

Any transition not listed above is a violation.

### Tiered Retry (Canonical)

`liang-quest-executor` uses tiered retry per step:

| Retry | Strategy | Details |
|-------|----------|---------|
| Retry 1 | Lesson-only | Execute-child receives `accumulated_lessons` + `previous_failure`. No re-plan-child. Original step content unchanged. |
| Retry 2+ | Re-plan escalation | Re-plan-child invoked with planning model. Produces `revised_instructions` (and optionally `revised_code_block`). Execute-child receives revised content + all accumulated lessons. |
| Max retries exhausted | Hard fail | Step → `failed`. Quest → `failed`. Final lesson extracted. Transitive dependents cascade-skipped. |

Retry tier does not affect status transitions — both tiers stay in `in_progress`. The tier distinction is recorded in the lesson schema for post-run analysis. Retry limit is `executor.max_step_retries` in `project.yaml` (default: 3).

## Executor-Owned Manifest Fields

The canonical executor manages these additional fields on quest entries:

```yaml
quests[]:
  status: string              # see transitions above
  current_cycle: integer      # 1-based index of cycle/step currently executing (0 = not started)
  total_cycles: integer       # total cycle/step count parsed from quest .md ## Steps
  skip_reason: string         # present when status is "skipped"; references failed dependency,
                               # or a manual hold ("manual_deferred" / "manual_dependency")
  started_at: string          # ISO 8601; set on in_progress transition
  completed_at: string        # ISO 8601; set on passed/failed/skipped transition
```

All other manifest fields (id, title, file, difficulty, depends_on) are read-only to executors.

## Cascade Skip

When a quest fails:

1. Find all quests whose `depends_on` includes the failed quest (transitively).
2. Set their status to `skipped` with `skip_reason: "dependency_failed: <quest-id>"`.
3. Remove them from the execution queue.

## Manual Holds (Executor Intake)

`manual: true` quests are human-in-editor work that must never be dispatched to a child process.
At campaign intake (executor §5), before the queue is built, the executor applies the same hold
algorithm as `liang-quest-batch-sweep`'s `apply_manual_holds`:

1. Release stale holds: any quest at `status: skipped` with `skip_reason: manual_deferred` or
   `manual_dependency` reverts to `ready` — recomputed from scratch on every intake.
2. Hold every `manual: true` quest with `status != passed` at `status: skipped`,
   `skip_reason: manual_deferred`.
3. Transitively hold any un-passed quest whose `depends_on` includes a held quest, at
   `status: skipped`, `skip_reason: manual_dependency`.

Held quests never enter the execution queue — the queue is built solely from `status: ready`.

## Crash Recovery

The canonical executor supports crash recovery:

1. Detect `status: in_progress` quests in the manifest.
2. Inspect `.run/<quest-id>/` for checkpoint state.
3. Offer the user: **Resume** from last checkpoint, or **Restart** (reset to ready, clean .run/).
4. Never silently resume when invoked interactively — always ask. Documented exception: under the executor's `--no-confirm` flag, default to **Resume** without prompting (non-interactive behavior per the executor's `--no-confirm` contract).
