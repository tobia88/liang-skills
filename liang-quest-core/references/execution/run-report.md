# Run Report Schema

Shared run report format produced by the canonical `liang-quest-executor`. Includes step-level results, tiered retry history, `.run/` child I/O references, and a deferred Tier 2 UAT section.

## File Location

```
.liang/campaigns/<campaign>/run-report-<iso-8601-timestamp>.html
```

## Run Report YAML (in opening HTML comment)

```yaml
run_id: string                 # "run-<iso-8601-timestamp>"
campaign_id: string
started_at: string             # ISO 8601
completed_at: string           # ISO 8601
duration_seconds: integer

quests:
  - quest_id: string
    title: string
    difficulty: string
    status: "passed" | "failed" | "skipped"

    # TDD-specific
    spine_type: "tdd" | "verify-only"        # present for TDD quests
    cycles_completed: integer                 # present for TDD quests
    cycles_total: integer                     # present for TDD quests
    retries_used: integer                     # present for TDD quests
    lesson_only_retries: integer              # count of lesson-only (tier 1) retries across all cycles
    replan_retries: integer                    # count of re-plan escalation (tier 2+) retries across all cycles
    confidence_scores:                        # present for verify-only TDD quests
      - cycle_id: string
        confidence: "high" | "medium" | "low"
        justification: string

    # General / planner-native specific
    steps_completed: integer                  # present for general + planner-native quests
    steps_total: integer                      # present for general + planner-native quests
    step_retries_used: integer                # present for general + planner-native quests
    lesson_only_retries: integer              # count of lesson-only (tier 1) retries across all steps
    replan_retries: integer                    # count of re-plan escalation (tier 2+) retries across all steps
    step_results:                             # present for general + planner-native quests
      - step_id: string
        status: "passed" | "failed"
        attempts: integer

    # Planner-native specific (quest-level VC verification)
    victory_conditions_checked: integer       # count of VCs in the quest's checklist
    victory_conditions_passed: integer        # count of VCs that passed (Tier 1 + post-UAT Tier 2)
    tier_2_deferred_count: integer            # count of VCs deferred to UAT
    vc_results:                               # present for planner-native quests
      - vc_index: integer
        vc_text: string
        tier: 1 | 2
        status: "passed" | "failed" | "tier_2_deferred"
        verification_method: "inline_pattern" | "verify_child" | "uat_batch"

    # Shared
    skip_reason: string                       # only when skipped

totals:
  passed: integer
  failed: integer
  skipped: integer
  tier2_failures: integer                     # count of Tier 2 verification failures

lessons_count: integer
```

## Lesson Schema

Shared across both executors. Lives at `.liang/campaigns/<campaign>/lessons.yaml`.

```yaml
lessons:
  - quest_id: string
    cycle_id: string             # TDD
    step_id: string              # General
    attempt: integer
    retry_tier: "lesson-only" | "replan"  # which retry strategy was used for this attempt
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
retry_tiers_used: ["lesson-only", "replan"]  # which tiers were used across attempts
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
status: "passed" | "failed"
verification_tier: 1 | 2
attempts: integer
retry_tiers_used: ["lesson-only", "replan"]  # which tiers were used across attempts
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
