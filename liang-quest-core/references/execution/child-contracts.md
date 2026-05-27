# Child Process Contracts

I/O contracts for child processes spawned by quest executors. Covers both the **canonical** `liang-quest-executor` (planner-native) and the **deprecated** `liang-quest-general-executor` / `liang-quest-tdd-executor` (cartographer/tactician chain).

## Common Child Rules

All children across all executors:

- Run in the **workspace root** as working directory
- Receive input via a YAML file path argument (Pi CLI / batch modes) or in-memory context (Claude mode)
- Write output to a YAML file path argument (Pi CLI / batch modes) or as a structured return value (Claude mode)
- Have **clean context isolation** — no parent AGENT.md, skill context, or conversation history
- Must not read secrets, `.env`, `.git/`, or credential files
- Communicate only via structured YAML / structured return — parent never parses child stdout for structured data

## Model Selection

| Child Type | Model Source | Used By |
|-----------|-------------|---------|
| Execute-child | `project.yaml` → `execution_by_difficulty[<quest|plan>.difficulty]` | All executors (planner-native + deprecated) |
| Verify-child (Tier 1 complex) | `project.yaml` → `models.verify` | Planner-native + deprecated General |
| Verify-child (Tier 2) | `project.yaml` → `models.verify` | Deprecated General only (planner-native defers Tier 2 to UAT batch with no child) |
| Verify-child (TDD) | `project.yaml` → `models.verify` | Deprecated TDD |
| Re-plan-child | `project.yaml` → `models.planning` | All executors |

In Claude mode (`--claude`), Pi CLI invocation is replaced by Claude Code Agent subagent dispatch with hardcoded tier mapping: easy → Haiku, medium → Sonnet, hard → Opus. Verify-children use Haiku; re-plan-children use Sonnet.

---

## Planner-Native Execute-Child (canonical)

**Purpose:** Implement one step from a quest `.md`'s `## Steps` section. The step has a title, a description, and zero or more code blocks (each with a `// file: <path>` or `# file: <path>` first line).

Used by `liang-quest-executor`.

### Input YAML

```yaml
child_type: "execute"
pipeline: "planner-native"
quest_id: string
quest_title: string
campaign_id: string
step_id: string                  # synthetic: s01, s02, ...
step_index: integer              # 1-based

step:
  title: string                  # from "### Step N: <title>"
  description: string            # text under the heading, before any code block
  code_blocks:                   # zero or more
    - file: string               # extracted from "// file: <path>" or "# file: <path>" first line
      language: string           # the fence info string (e.g. "yaml", "ts", "cpp")
      content: string            # the code block body (without the file: marker line)

quest_context:
  purpose: string                # from quest .md "## Purpose"
  difficulty: "easy" | "medium" | "hard"
  campaign_plan_path: string     # absolute path to plan.html for additional context
  dependencies: [string]         # quest IDs this quest depends on

# Retry context (only on re-execution)
is_retry: boolean
retry_attempt: integer
retry_tier: "lesson-only" | "replan"
revised_instructions: string | null     # set on retry 2+ from re-plan-child
revised_code_block:                     # set on retry 2+ if re-plan produced one
  file: string
  language: string
  content: string
previous_failure:
  error_summary: string
  stderr_tail: string
accumulated_lessons: [string]    # lessons from all prior attempts on this step

output_path: string              # Pi CLI / batch only
```

### Output YAML

```yaml
child_type: "execute"
pipeline: "planner-native"
quest_id: string
step_id: string
status: "success" | "error"

files_changed: [string]
implementation_summary: string
error_message: string            # only when status is "error"
```

The child is responsible for: reading existing files referenced by the step, applying the code blocks (write files specified by `// file:` markers), making any edits the step description calls for, and confirming the result with a brief implementation summary. No pre/postcondition validation — the planner-native format does not specify them per step.

---

## Planner-Native Verify-Child (canonical, Tier 1 complex only)

**Purpose:** Verify a single quest-level victory condition that the executor cannot resolve via simple pattern-matching (e.g., "the manifest's `quests` array has exactly 3 entries").

Used by `liang-quest-executor` only when the inline Tier 1 pattern-match cannot resolve the VC. Simple Tier 1 VCs (file exists, grep, valid YAML) are checked by the executor directly without spawning a child.

### Input YAML

```yaml
child_type: "verify"
pipeline: "planner-native"
quest_id: string
vc_index: integer                # which VC in the quest's checklist
vc_text: string                  # the full VC line from "## Victory Conditions"
workspace_root: string
files_changed: [string]          # union of files_changed across all steps in the quest
step_summaries:                  # one per step
  - step_id: string
    implementation_summary: string
output_path: string              # Pi CLI / batch only
```

### Output YAML

```yaml
child_type: "verify"
pipeline: "planner-native"
quest_id: string
vc_index: integer

pass: boolean
reasoning: string                # one sentence
evidence:                        # optional supporting evidence
  - check: string                # e.g. "grep pattern X in file Y"
    result: string
```

---

## Planner-Native Re-Plan-Child (canonical)

**Purpose:** Revise the failed step's instructions and (optionally) its code block, given failure context.

Used by `liang-quest-executor` on retry 2+.

### Input YAML

```yaml
child_type: "replan"
pipeline: "planner-native"
quest_id: string
quest_title: string
step_id: string

original_step:                   # the unmodified step content from the quest .md
  title: string
  description: string
  code_blocks:
    - file: string
      language: string
      content: string

quest_context:
  purpose: string
  difficulty: "easy" | "medium" | "hard"
  campaign_plan_path: string

failure_context:
  attempt: integer
  failure_type: string           # error | timeout | malformed_output | unexpected
  error_summary: string
  stdout_tail: string
  stderr_tail: string

previous_lessons: [string]       # all lesson entries for this step

output_path: string              # Pi CLI / batch only
```

### Output YAML

```yaml
child_type: "replan"
pipeline: "planner-native"
quest_id: string
step_id: string

revised_instructions: string     # revised step description (replaces original)
revised_code_block:              # optional; only when the code block needs replacement
  file: string
  language: string
  content: string
reasoning: string
confidence: "high" | "medium" | "low"
root_cause_hypothesis: string
```

The re-plan-child must NOT modify the source quest `.md` file. Its output lives in `step-<sid>.html`'s re-plan section and is consumed by the next execute-child attempt in-memory.

---

> **DEPRECATED COVERAGE BELOW.** The sections that follow describe the child contracts used by `liang-quest-general-executor` and `liang-quest-tdd-executor` — both deprecated in favor of the canonical `liang-quest-planner` → `liang-quest-executor` pair. Retained for in-flight campaigns and reference.

---

## TDD Execute-Child

**Purpose:** Implement one TDD cycle — write the failing test, make it pass, refactor.

### Input YAML

```yaml
child_type: "execute"
workflow: "tdd"
quest_id: string
quest_title: string
campaign_id: string
cycle_id: string
cycle_index: integer             # 1-based

test:
  name: string
  asserts: string

checklist:                       # 9-item spine (steps 1-8 are the child's job)
  - write_failing_test
  - run_tests
  - confirm_test_fails
  - confirm_fails_for_right_reason
  - implement_minimal
  - run_tests_and_confirm_passes
  - confirm_no_regression
  - refactor_and_confirm_still_green

extra_checks: [string]           # optional

# Enriched fields (optional)
implementation_guidance: string
test_command: string
target_files: [string]
reference_files: [string]
expected_outcome: string

# Retry context (only on re-execution)
is_retry: boolean
retry_attempt: integer
revised_guidance: string
previous_failure:
  error_summary: string
  failed_assertions: [string]
  stderr_tail: string

output_path: string
```

### Output YAML

```yaml
child_type: "execute"
workflow: "tdd"
quest_id: string
cycle_id: string
status: "completed" | "error"

files_changed: [string]
test_file: string
implementation_files: [string]
test_command_used: string

checklist_progress:
  write_failing_test: boolean
  run_tests: boolean
  confirm_test_fails: boolean
  confirm_fails_for_right_reason: boolean
  implement_minimal: boolean
  run_tests_and_confirm_passes: boolean
  confirm_no_regression: boolean
  refactor_and_confirm_still_green: boolean

extra_checks_completed: [string]
implementation_summary: string
error_message: string            # only when status is "error"
tests_passing: boolean
test_output_tail: string
```

---

## General Execute-Child

**Purpose:** Implement one general step following implementation-ready instructions.

### Input YAML

```yaml
child_type: "execute"
workflow: "general"
quest_id: string
quest_title: string
campaign_id: string
step_id: string
step_index: integer              # 1-based

step:
  name: string
  description: string
  files: [string]
  instructions: string
  preconditions: [string]
  postconditions: [string]

# Retry context (only on re-execution)
is_retry: boolean
retry_attempt: integer
revised_instructions: string
previous_failure:
  error_summary: string
  failed_criteria: [string]
  stderr_tail: string
accumulated_lessons: [string]    # lessons from all prior attempts

output_path: string
```

### Output YAML

```yaml
child_type: "execute"
workflow: "general"
quest_id: string
step_id: string
status: "completed" | "error"

files_changed: [string]
implementation_summary: string
preconditions_validated: boolean  # true if all preconditions were confirmed
postconditions_validated: boolean # true if all postconditions were confirmed
error_message: string            # only when status is "error"
```

---

## TDD Verify-Child

**Purpose:** Run a test command independently and report pass/fail.

### Input YAML

```yaml
child_type: "verify"
workflow: "tdd"
quest_id: string
cycle_id: string
test_command: string
test_file: string
expected_assertions: string
output_path: string
```

### Output YAML

```yaml
child_type: "verify"
workflow: "tdd"
quest_id: string
cycle_id: string

pass: boolean
exit_code: integer
stdout_tail: string              # last 50 lines
stderr_tail: string              # last 50 lines
failed_assertions: [string]
regression_detected: boolean
regression_details: string
test_count: integer
pass_count: integer
fail_count: integer
verification_summary: string
```

---

## General Verify-Child

**Purpose:** Verify a general step using either Tier 1 (command) or Tier 2 (yes/no checklist).

### Tier 1 Input YAML

```yaml
child_type: "verify"
workflow: "general"
verification_tier: 1
quest_id: string
step_id: string
verification_command: string
postconditions: [string]
output_path: string
```

### Tier 1 Output YAML

```yaml
child_type: "verify"
workflow: "general"
verification_tier: 1
quest_id: string
step_id: string

pass: boolean
exit_code: integer
stdout_tail: string
stderr_tail: string
postconditions_met: boolean
verification_summary: string
```

### Tier 2 Input YAML

```yaml
child_type: "verify"
workflow: "general"
verification_tier: 2
quest_id: string
step_id: string
acceptance_criteria: [string]    # each as a yes/no question
postconditions: [string]
files_changed: [string]          # from execute-child output
implementation_summary: string   # from execute-child output
output_path: string
```

### Tier 2 Output YAML

```yaml
child_type: "verify"
workflow: "general"
verification_tier: 2
quest_id: string
step_id: string

pass: boolean                    # true only if ALL criteria answered "yes"
criteria_results:
  - criterion: string
    answer: "yes" | "no"
    justification: string        # one sentence per criterion
postconditions_met: boolean
verification_summary: string
```

---

## Re-Plan-Child (Shared)

**Purpose:** Analyze failure context and produce revised guidance for a retry attempt.

### Input YAML

```yaml
child_type: "replan"
workflow: "tdd" | "general"
quest_id: string
quest_title: string
cycle_id: string | null          # cycle_id for TDD, null for general
step_id: string | null           # step_id for general, null for TDD

original:                        # the original cycle/step definition
  # TDD: test.name, test.asserts, implementation_guidance, test_command, etc.
  # General: name, description, instructions, files, preconditions, postconditions, etc.

failure_context:
  attempt: integer
  failure_type: string           # test_failure | build_error | timeout | verification_failed | unexpected
  error_summary: string
  stdout_tail: string
  stderr_tail: string
  failed_assertions: [string]    # TDD
  failed_criteria: [string]      # General (Tier 2)

previous_lessons: []             # all lesson entries for this cycle/step

output_path: string
```

### Output YAML

```yaml
child_type: "replan"
workflow: "tdd" | "general"
quest_id: string

# TDD-specific
revised_implementation_guidance: string
revised_test_approach: string

# General-specific
revised_instructions: string

# Shared
revised_target_files: [string]
reasoning: string
confidence: "high" | "medium" | "low"
root_cause_hypothesis: string
```

---

## .run/ Directory Structure

Per-quest working directory for child I/O during execution.

```
.run/
  <quest-id>/
    cycle-c01-execute-input.yaml     # TDD (scratch)
    cycle-c01-execute-output.yaml    # TDD (scratch)
    cycle-c01-verify-input.yaml      # TDD (scratch)
    cycle-c01-verify-output.yaml     # TDD (scratch)
    cycle-c01-result.yaml            # TDD (preserved)
    step-s01-execute-input.yaml      # General (scratch)
    step-s01-execute-output.yaml     # General (scratch)
    step-s01-verify-input.yaml       # General (scratch)
    step-s01-verify-output.yaml      # General (scratch)
    step-s01-result.yaml             # General (preserved)
    complete.yaml                    # completion marker (preserved)
```

### Preservation Rules

| Pattern | Preserved? |
|---------|-----------|
| `*-result.yaml` | Yes |
| `complete.yaml` | Yes |
| `*-input.yaml` | No (scratch) |
| `*-output.yaml` | No (scratch) |

---

## Error Handling (Shared)

### Child Spawn Failure
- Set cycle/step status to `failed`
- Create lesson with `failure_type: "unexpected"`
- Enter retry loop

### Malformed Output
- Treat as failure with `failure_type: "malformed_output"`
- Include raw output in `stdout_tail`

### Timeout
- Kill child process
- Failure with `failure_type: "timeout"`
- Re-planner may suggest simpler approach
