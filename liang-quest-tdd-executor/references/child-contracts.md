# Child Process I/O Contracts

This file defines the input YAML, output YAML, and prompt templates for all three child types spawned by `liang-quest-tdd-executor`.

All children:

- Run in the **workspace root** as working directory.
- Receive input via a YAML file path argument.
- Write output to a YAML file path argument.
- Have **clean context isolation** — no parent AGENT.md, skill context, or conversation history.
- Must not read secrets, `.env`, `.git/`, or credential files.

---

## 1. Execute-Child

**Purpose:** Implement one TDD cycle — write the failing test, make it pass, refactor.

**Model:** `project.yaml` → `execution_by_difficulty[plan.difficulty]`

### Input YAML

```yaml
child_type: "execute"
quest_id: string
quest_title: string
campaign_id: string
cycle_id: string
cycle_index: integer             # 1-based position in the plan

test:
  name: string
  asserts: string

checklist:                       # the 9-item spine (steps 1-8 are the child's job)
  - write_failing_test
  - run_tests
  - confirm_test_fails
  - confirm_fails_for_right_reason
  - implement_minimal
  - run_tests_and_confirm_passes
  - confirm_no_regression
  - refactor_and_confirm_still_green

extra_checks: [string]           # optional per-cycle checks

# Enriched fields (optional — present in upgraded plans)
implementation_guidance: string  # file-level specifics
test_command: string             # exact test runner command
target_files: [string]           # files to create or modify
reference_files: [string]        # existing files to read for context
expected_outcome: string         # what success looks like

# Retry context (only present on re-execution after re-plan)
is_retry: boolean                # false on first attempt
retry_attempt: integer           # 1-based attempt number
revised_guidance: string         # from re-plan-child (replaces implementation_guidance on retry)
previous_failure:                # only present when is_retry is true
  error_summary: string
  failed_assertions: [string]
  stderr_tail: string

output_path: string              # where to write the output YAML
```

### Output YAML

```yaml
child_type: "execute"
quest_id: string
cycle_id: string
status: "completed" | "error"

files_changed: [string]          # list of file paths created or modified
test_file: string                # path to the test file written/modified
implementation_files: [string]   # paths to implementation files written/modified
test_command_used: string        # the test command the child ran (discovered or from input)

checklist_progress:              # which spine steps were completed
  write_failing_test: boolean
  run_tests: boolean
  confirm_test_fails: boolean
  confirm_fails_for_right_reason: boolean
  implement_minimal: boolean
  run_tests_and_confirm_passes: boolean
  confirm_no_regression: boolean
  refactor_and_confirm_still_green: boolean

extra_checks_completed: [string] # which extra_checks were performed

implementation_summary: string   # brief description of what was implemented
error_message: string            # only present when status is "error"

tests_passing: boolean           # true if all tests pass at end of cycle
test_output_tail: string         # last 30 lines of test output
```

### Prompt Template

```
You are executing one TDD cycle for a quest. Follow the 9-item TDD checklist spine strictly, in order. You own steps 1 through 8.

CYCLE: {{cycle_id}} — {{test.name}}
ASSERTION: {{test.asserts}}

{{#if implementation_guidance}}
IMPLEMENTATION GUIDANCE:
{{implementation_guidance}}
{{/if}}

{{#if target_files}}
TARGET FILES: {{target_files | join ", "}}
{{/if}}

{{#if reference_files}}
REFERENCE FILES (read for context): {{reference_files | join ", "}}
{{/if}}

{{#if test_command}}
TEST COMMAND: {{test_command}}
{{/if}}

{{#if expected_outcome}}
EXPECTED OUTCOME: {{expected_outcome}}
{{/if}}

{{#if is_retry}}
THIS IS A RETRY (attempt {{retry_attempt}}).
PREVIOUS FAILURE: {{previous_failure.error_summary}}
FAILED ASSERTIONS: {{previous_failure.failed_assertions | join "; "}}
REVISED GUIDANCE: {{revised_guidance}}
{{/if}}

STEPS:
1. Write a failing test that asserts: {{test.asserts}}
2. Run the test suite. Confirm the new test fails.
3. Confirm it fails for the RIGHT reason (not a setup/config error).
4. Write the MINIMAL implementation to make the test pass.
5. Run the test suite. Confirm the new test passes.
6. Confirm no other tests broke (no regressions).
7. Refactor if needed. Confirm all tests still pass.

{{#if extra_checks}}
EXTRA CHECKS (perform after step 7):
{{#each extra_checks}}
- {{this}}
{{/each}}
{{/if}}

When done, write your output YAML to: {{output_path}}

RULES:
- Write the MINIMUM code needed. Do not gold-plate.
- Do not modify files outside the scope of this cycle.
- Do not read .env, .git/, secrets, or credential files.
- If you cannot complete a step, set status to "error" and describe what went wrong.
```

---

## 2. Verify-Child

**Purpose:** Run the cycle's test command independently and report pass/fail with structured output.

**Model:** `project.yaml` → `models.planning`

### Input YAML

```yaml
child_type: "verify"
quest_id: string
cycle_id: string
test_command: string             # exact command to run
test_file: string                # path to the test file (for context)
expected_assertions: string      # what should pass (from plan)
output_path: string
```

### Output YAML

```yaml
child_type: "verify"
quest_id: string
cycle_id: string

pass: boolean                    # true if all tests pass
exit_code: integer               # process exit code
stdout: string                   # full stdout (truncated to 200 lines)
stderr: string                   # full stderr (truncated to 200 lines)
stdout_tail: string              # last 50 lines of stdout
stderr_tail: string              # last 50 lines of stderr

failed_assertions: [string]      # specific assertions that failed (parsed from output)
regression_detected: boolean     # true if previously-passing tests now fail
regression_details: string       # which tests regressed (if any)

test_count: integer              # total tests run (if parseable)
pass_count: integer              # tests passed (if parseable)
fail_count: integer              # tests failed (if parseable)

verification_summary: string     # one-sentence summary of the result
```

### Prompt Template

```
You are verifying the result of a TDD cycle. Your ONLY job is to run the test command, observe the result, and report it accurately.

CYCLE: {{cycle_id}}
TEST COMMAND: {{test_command}}
TEST FILE: {{test_file}}
EXPECTED: {{expected_assertions}}

STEPS:
1. Run the test command exactly as specified.
2. Capture stdout and stderr completely.
3. Determine if the test(s) passed or failed.
4. If failed, identify which specific assertions failed.
5. Check for regressions — did any previously-passing tests break?
6. Parse test counts if the output format allows.

Write your output YAML to: {{output_path}}

RULES:
- Run the EXACT test command provided. Do not modify it.
- Do not fix failing tests. Do not modify any files.
- Do not read .env, .git/, secrets, or credential files.
- Report honestly. If tests fail, report failure. Do not fabricate pass results.
- If the test command itself fails to run (missing binary, syntax error), report exit_code and the error.
```

---

## 3. Re-Plan-Child

**Purpose:** Given failure context, produce revised implementation guidance for a retry attempt. Delegates to planner-core's re-planning interface.

**Model:** `project.yaml` → `models.planning`

### Input YAML

```yaml
child_type: "replan"
quest_id: string
quest_title: string
cycle_id: string
cycle_index: integer

original_cycle:                  # the cycle definition from the plan
  test:
    name: string
    asserts: string
  implementation_guidance: string
  test_command: string
  target_files: [string]
  reference_files: [string]
  expected_outcome: string

failure_context:
  attempt: integer               # which attempt just failed (1-based)
  failure_type: string           # test_failure | build_error | timeout | unexpected
  error_summary: string
  stdout_tail: string            # last 50 lines
  stderr_tail: string            # last 50 lines
  failed_assertions: [string]

previous_lessons: []             # all lesson entries for this cycle from lessons.yaml
  # Each entry has: attempt, failure_type, error_summary, attempted_fix, outcome

output_path: string
```

### Output YAML

```yaml
child_type: "replan"
quest_id: string
cycle_id: string

revised_implementation_guidance: string  # new file-level specifics
revised_test_approach: string            # optional — only if the test itself needs adjustment
revised_target_files: [string]           # optional — updated file list if approach changed
reasoning: string                        # why this approach should work where the previous failed

confidence: "high" | "medium" | "low"    # self-assessed confidence in the fix
root_cause_hypothesis: string            # what the re-planner thinks went wrong
```

### Prompt Template

```
You are re-planning a failed TDD cycle. A previous attempt to implement this cycle failed. Your job is to analyze the failure and produce REVISED implementation guidance that addresses the root cause.

CYCLE: {{cycle_id}} — {{original_cycle.test.name}}
ASSERTION: {{original_cycle.test.asserts}}

ORIGINAL GUIDANCE:
{{original_cycle.implementation_guidance}}

FAILURE (attempt {{failure_context.attempt}}):
Type: {{failure_context.failure_type}}
Summary: {{failure_context.error_summary}}
Failed assertions: {{failure_context.failed_assertions | join "; "}}

STDERR (last 50 lines):
{{failure_context.stderr_tail}}

{{#if previous_lessons.length}}
PREVIOUS ATTEMPTS:
{{#each previous_lessons}}
- Attempt {{this.attempt}}: {{this.error_summary}} → Fix tried: {{this.attempted_fix}} → Result: {{this.outcome}}
{{/each}}
{{/if}}

TARGET FILES: {{original_cycle.target_files | join ", "}}
REFERENCE FILES: {{original_cycle.reference_files | join ", "}}
TEST COMMAND: {{original_cycle.test_command}}

STEPS:
1. Analyze the failure output to identify the root cause.
2. Review what previous attempts tried (if any) to avoid repeating the same fix.
3. Produce revised implementation guidance that specifically addresses the root cause.
4. If the test itself has a bug (not the implementation), note this in revised_test_approach.
5. Assess your confidence in the fix.

Write your output YAML to: {{output_path}}

RULES:
- Do not implement the fix yourself. Only produce guidance.
- Do not modify any files. You are a planner, not an executor.
- Do not suggest changes outside the scope of this cycle.
- Be specific — "fix the bug" is not guidance. Name files, functions, and expected behavior.
- If you see the same failure pattern across multiple attempts, escalate confidence to "low" to signal this cycle may need human intervention.
```

---

## Invocation Syntax

The parent Executor spawns children via Pi CLI. The exact syntax should be validated per q001 findings. Expected pattern:

```
pi --model <model-id> --prompt "<prompt-text>" < input.yaml > output.yaml
```

Or with file arguments:

```
pi --model <model-id> --input <input-path> --output <output-path> --prompt-file <prompt-path>
```

Adapt based on the actual Pi CLI capabilities validated in q001. The invariants:

- Model is specified per child type (see Model Selection table in SKILL.md).
- Input and output are structured YAML files.
- The child runs in the workspace root directory.
- The child has no access to parent context.

---

## Error Handling

### Child Spawn Failure

If a child process cannot be spawned (binary not found, permission error):

- Set cycle status to `failed`.
- Create a lesson with `failure_type: "unexpected"` and the spawn error message.
- Enter retry loop (a different error may be transient).

### Malformed Output

If child output YAML cannot be parsed:

- Treat as cycle failure.
- Create a lesson with `failure_type: "malformed_output"`.
- Include whatever raw output was produced in `stdout_tail`.
- Enter retry loop.

### Timeout

If a child exceeds `child_timeout_seconds`:

- Kill the child process.
- Set cycle status to `failed`.
- Create a lesson with `failure_type: "timeout"`.
- Enter retry loop (the re-planner may suggest a simpler approach).
