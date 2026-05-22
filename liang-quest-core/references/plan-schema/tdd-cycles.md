# Plan Schema — TDD Cycles

Schema for TDD plan content. Read in conjunction with `common.md` for the shared envelope.

## TDD Plan YAML

After the common envelope fields, TDD plans contain `cycles[]`:

```yaml
# ... common envelope (see common.md) ...
workflow: "tdd"
readiness: "ready" | "foggy" | "verify-only"

cycles:                      # ordered list; order is execution order
  - cycle_id: string         # e.g. "c01"; unique within the plan
    test:
      name: string           # short human-readable test name
      asserts: string        # what the test asserts (observable outcome)
    checklist:               # spine items; shape depends on readiness
      - ...                  # see Checklist Spines below
    extra_checks: [string]   # optional; genuinely important per-cycle checks beyond the spine
```

### Enriched Cycle Fields (Optional)

When present, these enable self-contained cycle execution without codebase scouting:

```yaml
cycles[]:
  implementation_guidance: string   # file-level specifics for what to implement
  test_command: string              # exact test runner command for this cycle
  target_files: [string]            # files to create or modify
  reference_files: [string]         # existing files to read for context
  expected_outcome: string          # what success looks like after this cycle
  discussion_constraints_applied: [string]  # constraint IDs from discussion.html honored by this cycle
```

The `discussion_constraints_applied` field works identically to its counterpart in general steps — it lists constraint IDs from `discussion.html` that influenced the cycle's design. See `liang-quest-core/references/discussion/constraint-schema.md` for the constraint ID format.

## Dual Checklist Spines

Spine selection is determined by the plan's `readiness` field.

### 9-Item TDD Spine (readiness: ready or foggy)

| # | Key | Description |
|---|-----|-------------|
| 1 | `write_failing_test` | Write the failing test for this cycle's assertion |
| 2 | `run_tests` | Run the test suite |
| 3 | `confirm_test_fails` | Confirm the new test fails |
| 4 | `confirm_fails_for_right_reason` | Confirm failure is for the expected reason, not setup/config |
| 5 | `implement_minimal` | Write the minimal implementation to make the test pass |
| 6 | `run_tests_and_confirm_passes` | Run test suite and confirm the new test passes |
| 7 | `confirm_no_regression` | Confirm no other tests broke |
| 8 | `refactor_and_confirm_still_green` | Refactor if needed; confirm all tests still pass |
| 9 | `checkpoint` | Mark a VCS-neutral checkpoint |

### 5-Item Verify-Only Spine (readiness: verify-only)

| # | Key | Description |
|---|-----|-------------|
| 1 | `define_expected_outcome` | State what the implementation should produce |
| 2 | `implement` | Write the implementation to achieve the expected outcome |
| 3 | `verify_against_plan` | Verify via hybrid mechanical+LLM checks |
| 4 | `refactor_if_needed` | Refactor if needed; re-verify after changes |
| 5 | `checkpoint` | Mark a VCS-neutral checkpoint |

### Spine Selection Rule

| Readiness | Spine | Items |
|-----------|-------|-------|
| `ready` | 9-item TDD | 9 |
| `foggy` | 9-item TDD | 9 |
| `verify-only` | 5-item verify-only | 5 |

All cycles within a plan use the same spine (determined by plan-level readiness).

## Test Registry

See `test-approaches.md` for the complete `.liang/test-approaches.yaml` registry schema (entry shapes, rules, validation).

## TDD Readiness Gate

The TDD tactician's hybrid readiness check:

1. **Registry-driven** — If registry entry has `verify_only: true`, set readiness to `verify-only`.
2. **Victory conditions check** — Require at least one objectively testable VC. If zero exist, refuse unless user gives one-shot `foggy` override.

## Validation Rules (TDD-Specific)

In addition to common validation:

- At least 1 cycle exists.
- Every cycle has a unique `cycle_id`.
- Every cycle contains the correct checklist spine for the plan's readiness level.
- All cycles within a plan use the same spine.
- `foggy_reason` must be present when `readiness` is `foggy`.
- When present, `discussion_constraints_applied` must be a list of strings matching the constraint ID format (`dc` + 3-digit number).
