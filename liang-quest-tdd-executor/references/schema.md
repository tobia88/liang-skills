# Executor Schema — Plans, Project Config, Manifest, Lessons, and .run/

This file is the source of truth for all schemas consumed and produced by `liang-quest-tdd-executor`.

The Executor reads plans and project config; it writes manifest mutations, lessons, .run/ files, and run reports.

YAML key style: snake_case, lowercase, ASCII only, formal names (no JRPG metaphors).

---

## Plan YAML (Read-Only)

The Executor reads but **never writes** plan YAML. Plans are immutable inputs.

### Required Core (v1 — from Tactician)

```yaml
plan_id: string
quest_id: string
campaign_id: string
title: string
difficulty: "easy" | "medium" | "hard"
difficulty_rationale: string
readiness: "ready" | "foggy" | "verify-only"
created_at: string           # ISO 8601
schema_version: 1

inferred_quest_type: string  # optional; quest type slug from inference

cycles:
  - cycle_id: string         # e.g. "c01"
    test:
      name: string
      asserts: string
    checklist:               # spine items; shape depends on readiness
      # ready/foggy: 9-item TDD spine
      # verify-only: 5-item verify-only spine
      # (see tactician references/schema.md for canonical definitions)
    extra_checks: [string]   # optional
```

### Enriched Cycle Fields (v1 extension — from upgraded Tactician)

These fields are optional in v1 plans. When present, they enable self-contained cycle execution without codebase scouting.

```yaml
cycles[]:
  implementation_guidance: string   # file-level specifics for what to implement
  test_command: string              # exact test runner command for this cycle
  target_files: [string]            # files to create or modify
  reference_files: [string]         # existing files to read for context
  expected_outcome: string          # what success looks like after this cycle
```

### Schema Version Check

The Executor must check `schema_version` before parsing. Refuse gracefully if unsupported:

- `schema_version: 1` — supported.
- Any other value — skip quest with reason `unsupported_schema`.

---

## Project Config YAML (Read-Only)

Lives at `.liang/project.yaml`. Bootstrapped by the Tactician.

### Required Core (v1)

```yaml
schema_version: 1
vcs: "git" | "perforce" | "none"
models:
  planning: string               # model ID for planning/verification/re-planning
  execution_by_difficulty:
    easy: string                 # model ID for easy-difficulty execution
    medium: string               # model ID for medium-difficulty execution
    hard: string                 # model ID for hard-difficulty execution
created_at: string               # ISO 8601
```

### Executor Extensions (optional, added on first executor run if absent)

```yaml
executor:
  max_cycle_retries: integer     # default: 3; max retry attempts per cycle
  child_timeout_seconds: integer # default: 300; max time per child invocation
```

If the `executor` block is absent, use defaults silently (do not error). If `max_cycle_retries` is absent, default to `3`.

---

## Manifest YAML (Read-Write)

Lives at `.liang/campaigns/<campaign>/manifest.yaml`.

### Executor-Owned Fields

The Executor may mutate only these fields on quest entries:

```yaml
quests[]:
  status: string              # see Status Vocabulary below
  current_cycle: integer      # 1-based index of cycle currently executing (0 = not started)
  total_cycles: integer       # total cycle count from plan
  skip_reason: string         # present when status is "skipped"; references failed dependency
  started_at: string          # ISO 8601; set when status transitions to in_progress
  completed_at: string        # ISO 8601; set when status transitions to passed/failed/skipped
```

All other manifest fields (id, title, path, priority, readiness, depends_on, tags, notes, etc.) are **read-only** to the Executor.

### Status Vocabulary

| Status | Meaning | Set By |
|--------|---------|--------|
| `ready_for_planning` | Quest contract complete, no plan yet | Cartographer |
| `planned` | plan.html written | Tactician |
| `in_progress` | Execution underway | Executor |
| `passed` | All cycles passed | Executor |
| `failed` | A cycle exhausted retries | Executor |
| `skipped` | Dependency failed (cascade) | Executor |

### Allowed Transitions (Executor only)

```
planned       → in_progress
in_progress   → passed
in_progress   → failed
planned       → skipped        (cascade from dependency failure)
```

Any transition not in this table is a violation.

---

## Lesson YAML (Write-Only / Append-Only)

Lives at `.liang/campaigns/<campaign>/lessons.yaml`. Created on first failure; appended to on subsequent failures. Never deleted by the Executor.

### Lesson Entry Schema

```yaml
lessons:
  - quest_id: string
    cycle_id: string
    attempt: integer            # 1-based retry attempt number
    failure_type: string        # "test_failure" | "build_error" | "timeout" | "malformed_output" | "unexpected"
    error_summary: string       # concise human-readable description
    stdout_tail: string         # last 50 lines of child stdout (truncated)
    stderr_tail: string         # last 50 lines of child stderr (truncated)
    failed_assertions: [string] # list of specific assertions that failed
    attempted_fix: string       # what the re-plan-child suggested (empty on first attempt)
    outcome: string             # "retrying" | "passed_on_retry" | "exhausted"
    timestamp: string           # ISO 8601
```

---

## .run/ Directory Structure

Created per quest execution. Lives at `.liang/campaigns/<campaign>/.run/<quest-id>/`.

```
.run/
  <quest-id>/
    cycle-c01-execute-input.yaml     # input for execute-child (scratch)
    cycle-c01-execute-output.yaml    # output from execute-child (scratch)
    cycle-c01-verify-input.yaml      # input for verify-child (scratch)
    cycle-c01-verify-output.yaml     # output from verify-child (scratch)
    cycle-c01-replan-input.yaml      # input for re-plan-child (scratch, only on failure)
    cycle-c01-replan-output.yaml     # output from re-plan-child (scratch, only on failure)
    cycle-c01-result.yaml            # cycle outcome (preserved)
    cycle-c02-execute-input.yaml
    ...
    complete.yaml                    # completion marker (preserved)
```

### Preservation Rules

| File Pattern | Preserved After Cleanup? |
|-------------|-------------------------|
| `cycle-*-result.yaml` | Yes |
| `complete.yaml` | Yes |
| `cycle-*-input.yaml` | No (scratch) |
| `cycle-*-output.yaml` | No (scratch) |

### Cycle Result Schema

#### TDD Cycle Result

```yaml
cycle_id: string
spine_type: "tdd"
status: "passed" | "failed"
attempts: integer              # total attempts (1 = first try passed)
final_attempt_at: string       # ISO 8601
files_changed: [string]        # files modified by the execute-child
test_command: string            # command used for verification
```

#### Verify-Only Cycle Result

```yaml
cycle_id: string
spine_type: "verify-only"
status: "passed"               # verify-only cycles always "pass" — confidence indicates quality
confidence: "high" | "medium" | "low"
confidence_justification: string   # one-sentence justification from hybrid verification
mechanical_checks_passed: integer  # count of mechanical checks that passed
mechanical_checks_total: integer   # total mechanical checks attempted
llm_judgment: "pass" | "weak_pass" | "fail"
final_attempt_at: string       # ISO 8601
files_changed: [string]        # files modified by the execute-child
```

### Completion Marker Schema

```yaml
quest_id: string
status: "passed" | "failed"
spine_type: "tdd" | "verify-only"
cycles_completed: integer
cycles_total: integer
retries_used: integer          # total retry attempts across all cycles (0 for verify-only)
confidence_scores:             # present only for verify-only quests
  - cycle_id: string
    confidence: "high" | "medium" | "low"
started_at: string             # ISO 8601
completed_at: string           # ISO 8601
```

---

## Run Report (Write-Only)

Lives at `.liang/campaigns/<campaign>/run-report-<timestamp>.html`.

Contains an HTML comment with summary YAML:

```yaml
run_id: string                 # "run-<iso-8601-timestamp>"
campaign_id: string
started_at: string
completed_at: string
duration_seconds: integer
quests:
  - quest_id: string
    title: string
    difficulty: string
    spine_type: "tdd" | "verify-only"
    status: "passed" | "failed" | "skipped"
    cycles_completed: integer
    cycles_total: integer
    retries_used: integer
    skip_reason: string        # only when skipped
    confidence_scores:         # present only for verify-only quests
      - cycle_id: string
        confidence: "high" | "medium" | "low"
        justification: string
totals:
  passed: integer
  failed: integer
  skipped: integer
  verify_only_low_confidence: integer  # count of verify-only cycles scoring low
lessons_count: integer
```

See `references/run-report-template.html` for the HTML skeleton.

---

## Validation Rules

### Before executing a quest:

- `plan.html` exists and is readable.
- Plan YAML passes Required Core validation (all fields present, correct types).
- `schema_version` is `1`.
- `difficulty` is one of: `easy`, `medium`, `hard`.
- `readiness` is one of: `ready`, `foggy`, `verify-only`.
- `cycles[]` is non-empty.
- Each `cycle_id` is unique within the plan.
- All cycles carry the correct spine for the plan's readiness level.
- Quest status in manifest is `planned` (or `in_progress` for crash recovery resume).
- If `.liang/test-approaches.yaml` exists and plan has `inferred_quest_type`, validate spine type against registry (warn on mismatch, do not block).

### Before writing manifest mutations:

- The transition is in the Allowed Transitions table.
- The quest ID matches.
- No other fields are modified.

### Before writing lessons:

- All required lesson fields are present.
- `stdout_tail` and `stderr_tail` are truncated to 50 lines max.

---

## Hybrid Verification Schema (Verify-Only Cycles)

Internal to the Executor. Not part of the plan schema.

### Mechanical Check Result

```yaml
mechanical_checks:
  - check_type: "file_existence" | "pattern_match" | "structure_validation"
    target: string             # file path or pattern checked
    passed: boolean
    detail: string             # what was checked and result
```

### LLM Judgment Result

```yaml
llm_judgment:
  judgment: "pass" | "weak_pass" | "fail"
  justification: string       # one sentence
  expected_outcome: string     # verbatim from cycle define_expected_outcome
  model_used: string           # model ID from models.verify
```

### Confidence Score

```yaml
confidence:
  score: "high" | "medium" | "low"
  mechanical_passed: integer
  mechanical_total: integer
  llm_judgment: "pass" | "weak_pass" | "fail"
  justification: string       # one-sentence summary of combined result
  fail_criteria_triggered: [string]  # which anti-rubber-stamping rules fired, if any
```

---

## Schema Versioning Policy

- Current version: `schema_version: 1`.
- The Executor checks `schema_version` before parsing plans.
- New fields in child I/O contracts do not require a plan schema bump (they are internal to the Executor).
- New manifest status values require coordination with the Tactician's schema.
