# Run Report Schema

Shared run report format for both TDD and general executors.

## File Location

```
campaigns/<campaign>/run-report-<iso-8601-timestamp>.html
```

## Run Report YAML (in opening HTML comment)

```yaml
run_id: string                 # "run-<iso-8601-timestamp>"
campaign_id: string
workflow: "tdd" | "general" | "mixed"   # "mixed" when campaign has both types
started_at: string             # ISO 8601
completed_at: string           # ISO 8601
duration_seconds: integer

quests:
  - quest_id: string
    title: string
    workflow: "tdd" | "general"
    difficulty: string
    status: "passed" | "failed" | "skipped"

    # TDD-specific
    spine_type: "tdd" | "verify-only"        # present for TDD quests
    cycles_completed: integer                 # present for TDD quests
    cycles_total: integer                     # present for TDD quests
    retries_used: integer                     # present for TDD quests
    confidence_scores:                        # present for verify-only TDD quests
      - cycle_id: string
        confidence: "high" | "medium" | "low"
        justification: string

    # General-specific
    steps_completed: integer                  # present for general quests
    steps_total: integer                      # present for general quests
    step_retries_used: integer                # present for general quests
    step_results:                             # present for general quests
      - step_id: string
        status: "passed" | "failed"
        verification_tier: 1 | 2
        attempts: integer

    # Shared
    skip_reason: string                       # only when skipped

totals:
  passed: integer
  failed: integer
  skipped: integer
  verify_only_low_confidence: integer         # count of verify-only cycles scoring low (TDD)
  tier2_failures: integer                     # count of Tier 2 verification failures (general)

lessons_count: integer
```

## Lesson Schema

Shared across both executors. Lives at `campaigns/<campaign>/lessons.yaml`.

```yaml
lessons:
  - quest_id: string
    workflow: "tdd" | "general"
    cycle_id: string             # TDD
    step_id: string              # General
    attempt: integer
    failure_type: string         # test_failure | build_error | timeout | verification_failed | malformed_output | unexpected
    error_summary: string
    stdout_tail: string          # last 50 lines
    stderr_tail: string          # last 50 lines
    failed_assertions: [string]  # TDD
    failed_criteria: [string]    # General (Tier 2)
    attempted_fix: string
    outcome: string              # "retrying" | "passed_on_retry" | "exhausted"
    timestamp: string            # ISO 8601
```

## Completion Marker Schema

Per-quest completion marker at `.run/<quest-id>/complete.yaml`.

### TDD Quest

```yaml
quest_id: string
workflow: "tdd"
status: "passed" | "failed"
spine_type: "tdd" | "verify-only"
cycles_completed: integer
cycles_total: integer
retries_used: integer
confidence_scores:               # verify-only only
  - cycle_id: string
    confidence: "high" | "medium" | "low"
started_at: string
completed_at: string
```

### General Quest

```yaml
quest_id: string
workflow: "general"
status: "passed" | "failed"
steps_completed: integer
steps_total: integer
step_retries_used: integer
step_results:
  - step_id: string
    status: "passed" | "failed"
    verification_tier: 1 | 2
    attempts: integer
started_at: string
completed_at: string
```

## Step/Cycle Result Schemas

### TDD Cycle Result

```yaml
cycle_id: string
spine_type: "tdd"
status: "passed" | "failed"
attempts: integer
final_attempt_at: string
files_changed: [string]
test_command: string
```

### Verify-Only Cycle Result

```yaml
cycle_id: string
spine_type: "verify-only"
status: "passed"
confidence: "high" | "medium" | "low"
confidence_justification: string
mechanical_checks_passed: integer
mechanical_checks_total: integer
llm_judgment: "pass" | "weak_pass" | "fail"
final_attempt_at: string
files_changed: [string]
```

### General Step Result

```yaml
step_id: string
workflow: "general"
status: "passed" | "failed"
verification_tier: 1 | 2
attempts: integer
final_attempt_at: string
files_changed: [string]
verification_command: string     # Tier 1; null for Tier 2
criteria_results:                # Tier 2 only
  - criterion: string
    answer: "yes" | "no"
```

## Visual Conventions

Run reports share the family visual style:

- Dark hero/header with campaign title, run timestamp, overall duration
- Quest result cards with status prominently displayed
- Green for passed, red for failed, amber for skipped
- **TDD verify-only confidence:** `high` = green, `medium` = amber, `low` = red warning
- **General Tier 2 failures:** visually flagged with amber/red indicators
- Low-confidence cycles and Tier 2 failures must be visually unmissable
- Per-quest cycle/step progress indicators
- Lessons section at the bottom
- Overall counts bar
- Native HTML/CSS only; no JavaScript; no external dependencies
