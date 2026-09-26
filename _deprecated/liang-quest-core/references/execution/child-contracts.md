# Child Process Contracts

I/O contracts for child processes spawned by the canonical `liang-quest-executor`.

## Common Child Rules

All children across all executors:

- Run in the **workspace root** as working directory
- Receive input via a YAML file path argument or YAML section inside an executor-generated step envelope (Pi CLI / batch modes), or in-memory context (Claude mode)
- Write output to a YAML file path argument or YAML section inside the same step envelope (Pi CLI / batch modes), or as a structured return value (Claude mode)
- Have **clean context isolation** — no parent AGENT.md, skill context, or conversation history
- Must not read secrets, `.env`, `.git/`, or credential files
- Communicate only via structured YAML / structured return — parent never parses child stdout for structured data

## Model Selection

| Child Type | Model Source | Used By |
|-----------|-------------|---------|
| Execute-child | `project.yaml` → `execution_by_difficulty[quest.difficulty]` | Canonical executor |
| Verify-child (Tier 1 complex) | `project.yaml` → `models.verify` | Canonical executor |
| Re-plan-child | `project.yaml` → `models.planning` | Canonical executor |

In Claude mode (`--claude`), Pi CLI invocation is replaced by Claude Code Agent subagent dispatch. Execute-child tiers come from `project.yaml` → `models.claude_mode` (Claude tier aliases only — Claude Code cannot spawn non-Claude children). Verify-children resolve from `models.claude_mode.verify`; re-plan-children from `models.claude_mode.planning`. Defaults for absent keys are defined once (`liang-quest-core/references/project/project-yaml.md` § Model Routing Extensions), never restated here.

---

## Step Envelope Transport

For planner-native execution, the quest `.md` is the executable source-of-truth. The executor parses its `## Steps` section and creates one `step-<sid>.md` step envelope per step under `.run/<quest-id>/`.

A Markdown step envelope is a transport/ledger file with stable fenced YAML sections:

## Input
~~~yaml
child_type: "execute"
pipeline: "planner-native"
quest_id: "q001"
step_id: "s01"
~~~

## Output
~~~yaml
status: "success"
files_changed: []
implementation_summary: ""
~~~

## Re-plan
~~~yaml
revised_instructions: null
~~~

## Verification
~~~yaml
vc_results: []
~~~

## Usage
~~~yaml
attempts: []
~~~

### Usage Section (executor-written)

Children never write this section — a child cannot observe its own token usage. After
each child exits, the executor harvests per-message `usage` records (tokens + cost as
priced by the Pi harness) from the child's pinned session file and appends one entry:

```yaml
attempts:
  - attempt: integer             # 1-based; counts execute attempts including retries
    child_type: "execute" | "replan"
    model: string                # model id the child ran with (as resolved at spawn)
    input_tokens: integer
    output_tokens: integer
    cache_read_tokens: integer
    cache_write_tokens: integer
    cost_usd: float
```

Verify-children are quest-level, not step-level — their usage is harvested the same way
but lands only in the quest rollup (`complete.yaml`), not in any step envelope. If a
session file is missing or unparseable, omit the entry (never fabricate zeros) and note
the gap in the run report. Claude mode (`--claude`) writes no usage section: subagent
dispatch exposes no usage data to the executor.

---

## Planner-Native Execute-Child (canonical)

**Purpose:** Implement one step from a quest `.md`'s `## Steps` section. The step has a title, a description, and zero or more code blocks (each with a `// file: <path>` or `# file: <path>` first line). The child may receive that step through a step envelope, but it must treat the quest `.md` step content embedded in the YAML input as the load-bearing contract.

Used by `liang-quest-executor`.

### Input YAML

When embedded in a step envelope, this mapping appears directly under the `## Input` fenced YAML block (no `input:` wrapper key — the heading itself provides the section context).

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

output_path: string              # Pi CLI / batch only; path to the YAML output target or step envelope
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
plan_contradictions:             # facts the step asserts that the workspace contradicts; [] when none
  - claimed: string              # what the step says, quoted
    observed: string             # what the workspace shows
    evidence: string             # file:line, command + output, or measurement that shows it
    blocks_step: boolean         # true when the step cannot be completed as written
```

`plan_contradictions` is the child's only channel for "the plan is wrong". A child never asks the caller a question and never decides a contradiction on its own when `blocks_step` is true — it stops, reports, and lets the executor route it to a re-plan-child. When `blocks_step` is false the child may complete the step on the observed facts and still report the contradiction, so the run report records the drift.

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
output_path: string              # Pi CLI / batch only; path to the YAML output target
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
  dependencies: [string]         # quest IDs this quest depends on
failure_context:
  attempt: integer
  failure_type: string           # error | timeout | malformed_output | plan_contradiction | vc_failed | unexpected
  failed_vcs:                    # present when failure_type is vc_failed (a §7d repair round)
    - vc_text: string
      evidence: string           # the verifier's evidence, file:line where it has one
  playbook_hints: [string]       # notes of matched failure-playbook hint rules; [] when none
  error_summary: string
  stdout_tail: string
  stderr_tail: string
  plan_contradictions:           # present when failure_type is plan_contradiction; verbatim from the execute-child
    - claimed: string
      observed: string
      evidence: string
      blocks_step: boolean

previous_lessons: [string]       # all lesson entries for this step

output_path: string              # Pi CLI / batch only; path to the YAML output target or step envelope
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
resolvable: boolean              # false when a contradiction needs a decision the plan never made
                                 # (a changed deliverable count, a different file to overwrite, a
                                 # public name); the executor then fails the quest and reports it
                                 # under "Decisions needed" instead of re-executing
```

The re-plan-child decides plan contradictions itself, from the quest purpose, the campaign `plan.md`, and the evidence. It has no user to ask; `resolvable: false` is the only way to hand a decision back, and it goes to the run report, not to a prompt.

The re-plan-child must NOT modify the source quest `.md` file. Its output lives in the `step-<sid>.md` step envelope's re-plan section and is consumed by the next execute-child attempt in-memory.


