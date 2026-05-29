# Child Process Contracts

I/O contracts for child processes spawned by the canonical `liang-quest-executor`.

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
| Execute-child | `project.yaml` → `execution_by_difficulty[quest.difficulty]` | Canonical executor |
| Verify-child (Tier 1 complex) | `project.yaml` → `models.verify` | Canonical executor |
| Re-plan-child | `project.yaml` → `models.planning` | Canonical executor |

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


