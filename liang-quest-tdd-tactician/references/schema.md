# Tiered Schema — Plan and Project Config

This file is the source of truth for the schemas used by `liang-quest-tdd-tactician`.

Two artifacts:

- `plan.html` — opens with an HTML comment containing the full plan YAML.
- `.liang/project.yaml` — workspace-wide project config, bootstrapped once on first run.

YAML key style:

- snake_case
- lowercase
- ASCII only
- formal names (no JRPG metaphors in keys; JRPG flavor stays in the HTML views)

---

## Plan YAML

This lives inside the **opening HTML comment** of each `plan.html`.

### Required Core

```yaml
plan_id: string              # e.g. "p001"; unique within the quest folder
quest_id: string             # matches the quest contract's quest_id, e.g. "q001"
campaign_id: string          # matches the campaign's campaign_id
title: string                # human-readable plan title
difficulty: string           # see Difficulty Vocabulary below
difficulty_rationale: string # one-sentence explanation of the difficulty decision
readiness: string            # see Readiness Vocabulary below
created_at: string           # ISO 8601 date or datetime
schema_version: integer      # always 1 for v1

cycles:                      # ordered list; order is execution order
  - cycle_id: string         # e.g. "c01"; unique within the plan
    test:
      name: string           # short human-readable test name
      asserts: string        # what the test asserts (observable outcome)
    checklist:               # spine items; shape depends on readiness
      # When readiness is "ready" or "foggy" — 9-item TDD spine:
      - write_failing_test
      - run_tests
      - confirm_test_fails
      - confirm_fails_for_right_reason
      - implement_minimal
      - run_tests_and_confirm_passes
      - confirm_no_regression
      - refactor_and_confirm_still_green
      - checkpoint
      # When readiness is "verify-only" — 5-item verify-only spine:
      # - define_expected_outcome
      # - implement
      # - verify_against_plan
      # - refactor_if_needed
      # - checkpoint
```

### Optional Extensions

```yaml
foggy_reason: string         # required when readiness == "foggy"; why the override was used
inferred_quest_type: string  # quest type slug inferred from contract content; used for registry lookup

non_test_checks:             # plan-level; legitimate non-test concerns
  - string                   # free-form description of a non-test check

cycles[].extra_checks:       # per-cycle; genuinely important checks beyond the spine
  - string                   # free-form description of an extra check
```

---

## Checklist Spines

See the **Dual Checklist Spines** section above for both the 9-item TDD spine and the 5-item verify-only spine, including selection rules.

The word "Checkpoint" is VCS-neutral by design. Plan content must never contain VCS-specific wording (commit, push, PR, branch, changelist, submit).

---

## Project Config YAML

This lives at `.liang/project.yaml` in the workspace root.

### Required Core (v1, frozen)

```yaml
schema_version: 1            # integer; bump when schema changes
vcs: string                  # "git" | "perforce" | "none"
models:
  planning: string           # model ID for planning (this skill)
  execution_by_difficulty:
    easy: string             # model ID for easy-difficulty execution
    medium: string           # model ID for medium-difficulty execution
    hard: string             # model ID for hard-difficulty execution
created_at: string           # ISO 8601 date or datetime
```

There are no Optional Extensions for the project config at v1. All fields above are required.

> **v2 TODO:** Consider a reserved `models.executing` slot if the Executor needs its own model routing distinct from `execution_by_difficulty`.

---

## Difficulty Vocabulary

Fixed at v1. Use exactly these values:

- `easy` — narrow scope, few risks, clear VCs, ≤3 cycles, low novelty.
- `medium` — moderate scope, some risks or open questions, 3–6 cycles, some novelty.
- `hard` — broad scope, multiple risks or open questions, 6+ cycles, high novelty or cross-cutting concerns.

Do not invent additional difficulty levels. Adding new levels requires a `schema_version` bump.

---

## Readiness Vocabulary

Use exactly these values:

- `ready` — at least one testable victory condition exists; Readiness Gate passed normally.
- `foggy` — zero testable victory conditions; user gave an explicit one-shot override.
- `verify-only` — quest type has no automated test command; victory conditions cannot be verified by automated tests. Assigned when the test registry entry for the inferred quest type has `verify_only: true`.

Do not invent additional readiness states. Adding new levels requires a `schema_version` bump.

---

## Test Registry Schema — `.liang/test-approaches.yaml`

A project-global registry mapping quest types to their test approach. Created by the Tactician on first use; appended when new quest types are encountered. Lives at `.liang/test-approaches.yaml` in the workspace root.

YAML key style: snake_case, lowercase, ASCII only. Medium-detail entries only (no rich/layered extensions).

### Entry Shapes

The registry has two distinct entry shapes:

#### Automatable Entry

For quest types that have automated test commands:

```yaml
quest_types:
  <quest-type-slug>:
    framework: string              # test framework name (e.g. "jest", "pytest", "catch2")
    test_command: string           # exact command to run tests (e.g. "npm test", "pytest tests/")
    test_file_pattern: string      # glob pattern for test files (e.g. "**/*.test.ts", "tests/*_test.py")
```

#### Verify-Only Entry

For quest types with no automated test command:

```yaml
quest_types:
  <quest-type-slug>:
    verify_only: true              # boolean flag; always true for this shape
    verify_hint: string            # guidance for hybrid verification (what to check, expected artifacts)
```

### Rules

- Quest type slugs are open-ended (user defines freely); no predefined taxonomy.
- Each entry uses exactly one shape — never both.
- The `verify_only` flag distinguishes the two shapes; its absence implies automatable.
- `test_file_pattern` in automatable entries also serves as a mechanical check input for verify-only verification.
- The file is optional. When absent, the pipeline falls back to all-TDD behavior (backward compatibility).

---

## Dual Checklist Spines

The pipeline supports two checklist spines. Spine selection is determined by the quest's readiness level.

### 9-Item TDD Spine (unchanged)

Used when `readiness` is `ready` or `foggy`. This is the existing spine:

| # | Key | Description |
|---|-----|-------------|
| 1 | `write_failing_test` | Write the failing test for this cycle's assertion. |
| 2 | `run_tests` | Run the test suite. |
| 3 | `confirm_test_fails` | Confirm the new test fails. |
| 4 | `confirm_fails_for_right_reason` | Confirm the failure is for the expected reason, not a setup or config error. |
| 5 | `implement_minimal` | Write the minimal implementation to make the test pass. |
| 6 | `run_tests_and_confirm_passes` | Run the test suite and confirm the new test passes. |
| 7 | `confirm_no_regression` | Confirm no other tests broke. |
| 8 | `refactor_and_confirm_still_green` | Refactor if needed; confirm all tests still pass. |
| 9 | `checkpoint` | Mark a VCS-neutral checkpoint. |

### 5-Item Verify-Only Spine

Used when `readiness` is `verify-only`. For quests whose victory conditions cannot be verified by automated tests:

| # | Key | Description |
|---|-----|-------------|
| 1 | `define_expected_outcome` | State what the implementation should produce — the observable result this cycle delivers. |
| 2 | `implement` | Write the implementation to achieve the expected outcome. |
| 3 | `verify_against_plan` | Verify the implementation matches the expected outcome using hybrid mechanical+LLM checks. |
| 4 | `refactor_if_needed` | Refactor if needed; re-verify after changes. |
| 5 | `checkpoint` | Mark a VCS-neutral checkpoint. |

### Spine Selection Rule

| Readiness | Spine | Item Count |
|-----------|-------|------------|
| `ready` | 9-item TDD spine | 9 |
| `foggy` | 9-item TDD spine | 9 |
| `verify-only` | 5-item verify-only spine | 5 |

---

## Status Vocabulary (Manifest)

The Tactician is allowed exactly one manifest mutation. The relevant status values:

- `ready_for_planning` — quest contract is complete; no plan exists yet.
- `planned` — plan.html has been written for this quest.

The Tactician may only transition `ready_for_planning → planned`. All other statuses (`needs_clarification`, `blocked`, and any future Executor-owned statuses like `in_progress`, `done`) are outside this skill's authority.

---

## Validation Rules

Before any plan file is written:

- At least 1 cycle must exist.
- At least 1 testable victory condition must exist, unless `readiness` is `foggy` or `verify-only`.
- Every cycle must have a unique `cycle_id` within the plan.
- Every cycle must contain the correct checklist spine for its readiness level:
  - `ready` or `foggy`: the complete 9-item TDD spine in the exact order defined in the Dual Checklist Spines section.
  - `verify-only`: the complete 5-item verify-only spine in the exact order defined in the Dual Checklist Spines section.
- All cycles within a plan use the same spine (determined by plan-level `readiness`).
- `difficulty` must be one of: `easy`, `medium`, `hard`.
- `readiness` must be one of: `ready`, `foggy`, `verify-only`.
- `foggy_reason` must be present when `readiness` is `foggy`.
- `inferred_quest_type` should be present when the tactician has quest-type inference enabled.
- `schema_version` must be `1`.
- `plan_id`, `quest_id`, `campaign_id`, `title`, `difficulty`, `difficulty_rationale`, `readiness`, `created_at`, `schema_version` must all be present.
- All slugs and IDs must be lowercase ASCII with hyphens, no spaces or special characters.
- `created_at` must be a valid ISO 8601 date or datetime.
- Plan content must contain no VCS-specific wording (commit, push, PR, branch, changelist, submit).

If any rule fails, the skill must not write files.

---

## Schema Versioning Policy

- Current version: `schema_version: 1`.
- **Any new field** added to the plan schema or the project config schema **requires a `schema_version` bump**.
- Emit new artifacts under the new version; **never retroactively edit** existing plans or configs.
- The future Executor skill must check `schema_version` before parsing and refuse gracefully if unsupported.
- Hard Stop #11 in SKILL.md enforces this policy for the project config specifically.

---

## Layered Truth Reminder

- The plan YAML in the HTML comment is for **tools and agents**: structured, parseable, complete.
- The plan HTML body is for **humans**: visual, readable, JRPG-styled.
- Never split plan data across multiple files. One `plan.html` holds everything.
- The manifest carries pipeline state (`status`); the plan carries plan content. No duplication.
