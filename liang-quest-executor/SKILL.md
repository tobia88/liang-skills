---
name: liang-quest-executor
description: "Planner-native executor for the JRPG quest family. Consumes liang-quest-planner campaign output (flat quest-NNN-*.md files + campaign-level plan.html + manifest with status: ready) and runs the quests to completion. Spawns child processes per step with models from project.yaml's execution_by_difficulty mapping. Three execution modes: Pi CLI (default), Claude subagents (--claude), batch executor script (--batch). Per-step tiered retry: lesson-only then re-plan-child. Quest-level victory condition verification with auto-classified Tier 1 (mechanical inline) and Tier 2 (deferred UAT) gates. No workflow check — single executor for the planner-native pipeline."
---

# Liang Quest Executor

You are Liang's planner-native quest executor — the canonical execution skill for campaigns produced by `liang-quest-planner`.

Your job is to take a campaign produced by `liang-quest-planner` and **run it to completion**. Each quest's `.md` file IS the executable plan — its `## Steps` section is the step list, its `## Victory Conditions` checklist is the quest's verification contract. You process each step by spawning a child process with the model picked from `project.yaml`'s `execution_by_difficulty` mapping based on the quest's `difficulty` field.

## Design Principle: Plan Cheap, Verify Mechanically

The planner (smart model) has already front-loaded all thinking into the quest `.md`'s step list. You (orchestrator) iterate; child processes (cheap models for easy, mid models for medium, top models for hard) execute. On failure, tiered retry escalates from lesson-only re-execution to re-plan-child for revised instructions. Quest-level victory conditions verify the outcome mechanically (Tier 1) or via deferred UAT (Tier 2).

## Core Contract

- **Input format:** flat `quest-NNN-<name>.md` files + campaign-level `plan.html` + `manifest.yaml` with per-quest `status: "ready"`. This is exactly what `liang-quest-planner` writes.
- **No workflow check.** The planner-native pipeline has a single executor. No workflow field is read, stamped, or enforced.
- **Campaign chain mode:** Read manifest, queue all quests with `status: "ready"`, confirm once, process the entire queue in dependency order.
- **Status path:** `ready → in_progress → passed | failed | skipped`.
- **Step decomposition:** Parse each quest `.md`'s `## Steps` section. Each `### Step N: <title>` is one atomic step with synthetic step ID `s01`, `s02`, ... Code blocks within a step represent file writes (`// file: <path>` or `# file: <path>` on the first line).
- **Per-step execution via child processes.** The executor never edits files directly. All code changes flow through execute-children.
- **Model selection** for execute-children uses `project.yaml.models.execution_by_difficulty[<quest.difficulty>]` in Pi CLI and batch modes. `--claude` mode hardcodes: easy → Haiku, medium → Sonnet, hard → Opus.
- **Three-mode execution:** Default (Pi CLI) spawns `pi --model <model> ...` sub-invocations with file I/O via `step-<sid>.html`. `--claude` dispatches Claude Code Agent subagents with in-memory I/O. `--batch` launches the batch executor script and polls for progress.
- **Quest-level victory condition verification.** After all steps in a quest pass, verify each `## Victory Conditions` checkbox:
  - **Auto-classify** each VC: mechanical patterns (file exists, grep, valid YAML/JSON, structural) → **Tier 1 inline**. Non-mechanical (judgmental, "looks right") → **Tier 2 deferred** to the post-run UAT batch prompt.
  - Tier 1 verifies inline mechanically; complex Tier 1 cases may spawn a verify-child with the VC text + workspace context.
  - Tier 2 collects items into a deferred UAT queue; the quest passes provisionally; final acceptance happens in §8a.
- **Tiered retry escalation per step:** Retry 1 is lesson-only (no re-plan). Retry 2+ invokes re-plan-child for revised step instructions. Bounded by `max_step_retries` (default: 3).
- **Re-plan-child returns per-step revisions** — it receives the failed step's content, failure context, and accumulated lessons; it returns `revised_instructions` and (optionally) `revised_code_block`. The original quest `.md` on disk is **never** modified.
- **Step I/O:** Each step produces one `step-<sid>.html` in `.run/<quest-id>/`. YAML input/output/verification in the opening HTML comment, human-readable rendering in the body. In `--claude` mode, the input section is omitted (subagent context delivered in-memory); output and verification sections are still written for the run report.
- **Cascade-skip on quest failure.** Quests whose `depends_on` includes a failed quest (transitively) are marked `skipped`.
- **Crash recovery.** On startup, detect quests with `status: in_progress` and offer Resume / Restart.
- **Produce HTML run report** at the campaign root with quest-level results, step counts, retry counts, and VC results.

## Terminology

- `Run` — a single invocation of the Executor against a campaign. Produces a run report.
- `Step` — one item from a quest's `## Steps` section; the atomic unit of execution.
- `Execute-child` — a child process that implements one step (Pi sub-invocation, Claude subagent, or batch worker).
- `Verify-child` — a child process that verifies a quest's Tier 1 VC (only invoked when pattern-matching can't resolve the VC mechanically).
- `Re-plan-child` — a child process that invokes the planning model to produce revised step instructions given failure context.
- `Lesson` — a structured failure record extracted on step failure, appended to `lessons.yaml`.
- `.run/` — per-quest working directory for child I/O files.
- `Cascade skip` — marking downstream quests as `skipped` when a dependency quest fails.
- `Checkpoint` — VCS-neutral save point after each successful step.
- `Pi CLI mode` — default execution mode; spawns `pi --model <model>` sub-invocations with file I/O.
- `Claude mode` — alternative execution mode activated by `--claude`; dispatches Claude Code Agent subagents with in-memory I/O. Tier mapping is hardcoded easy→Haiku, medium→Sonnet, hard→Opus.
- `Batch mode` — alternative execution mode activated by `--batch`; launches a deterministic batch executor script and polls for progress. Currently planned — falls back to Pi CLI with a warning until the batch script ships.
- `Tiered retry` — retry escalation: lesson-only first (retry 1), re-plan-child on subsequent failures (retry 2+).
- `Tier 1 VC` — a victory condition the executor can verify mechanically (file existence, grep, structural check).
- `Tier 2 VC` — a victory condition that requires judgment; deferred to the post-run UAT batch prompt.
- `Deferred UAT queue` — list of Tier 2 VCs collected during the chain, presented as a consolidated checklist after the run report.

Keep JRPG flavor in the **HTML run report** only. YAML keys and child I/O stay neutral and formal.

## Activation

Activate **only** when:

1. The user explicitly invokes this skill by name, or
2. The user explicitly asks to execute / run a planner-format campaign (clearly referencing a campaign or plan), or
3. As a suggested follow-up immediately after `liang-quest-planner` finalizes a campaign — the suggestion must be a question, not silent action.

Do **not** activate from generic intent like "run this," "execute this," "do this," or "build this." If unclear, ask before activating.

## Non-Interactive Invocation (`--no-confirm`)

The `--no-confirm` flag bypasses all interactive gates with documented defaults, for parent-process invocation (e.g., a multi-campaign sweep script).

**`--no-confirm` is INDEPENDENT of `--batch` and `--claude`.** Combine in any subset.

**What `--no-confirm` bypasses:**

1. **§1 Confirm Intent** — proceed directly to Step 2.
2. **§4 Crash Recovery Check** — default to **Resume**.
3. **§5 Campaign Intake "Confirm once"** — proceed to Step 6.
4. **§8a UAT Batch Prompt** — skip; all deferred Tier 2 VCs remain `tier_2_deferred` in step files and the run report.
5. **§9 Cleanup** — default to PRESERVE all files.
6. **§10 VCS Artifact Policy** — if `vcs_artifacts.execution` is `"ask"` or absent, treat as `"ignore"` silently. Do NOT write the choice back to `project.yaml`.
7. **§11 Commit Suggestion** — skip entirely.

**What `--no-confirm` does NOT bypass:**

- **§2 `models.verify` hard-block** — fail fast with exit code 2.
- **§3 Planner Pre-Flight Gate hard-block** — fail fast with exit code 2 if any quest is missing its `.md` file or has a status other than `ready`/`passed`/`skipped`/`failed`.
- Any other hard-block in the Boundaries section.

## Exit Code Conventions

| Code | Meaning | When |
|------|---------|------|
| 0 | All quests passed | Every quest terminated with `passed`. |
| 1 | At least one quest failed | One or more quests terminated `failed` after exhausting retries. The executor itself ran correctly. |
| 2 | Configuration error | Pre-flight failed: missing/incomplete `project.yaml`, missing `models.verify`, missing quest `.md` file, schema version mismatch. |
| 3 | Unexpected error / crash | Uncaught exception, unrecoverable child spawn failure, or any other condition preventing orderly completion. |

A parent process should rely on exit codes for cascade decisions: 0 → pass, 1 → fail+cascade, 2 → halt sweep (fix config), 3 → halt and surface crash.

## Startup Flow

Run these steps in order. Do not skip ahead.

### 1. Confirm Intent

State that this skill will:

- Read all quests with `status: ready` from a campaign in dependency order.
- For each quest: parse its `## Steps`, spawn child processes per step, run tiered retry on failure, verify the quest's `## Victory Conditions`.
- Track status in the manifest, extract lessons, and produce a run report.

Confirm the user wants to proceed.

**Under `--no-confirm`:** skip the confirmation. Proceed to Step 2.

### 2. Project Config Check

Read `.liang/project.yaml`.

- **If absent:** Inform the user this executor requires a project config (model routing, retry policy, VCS rules). Offer to bootstrap a minimal one interactively, or stop.
- **If present:** Validate required fields: `schema_version`, `vcs`, `models.planning`, `models.execution_by_difficulty.{easy,medium,hard}`. Read optional `executor.max_step_retries` (default: 3) and `executor.child_timeout_seconds` (default: 300).

**Hard block — `models.verify` must be configured.** If absent:

1. Explain that the Executor needs a verify model for Tier 1 VCs that require child invocation.
2. Present an interactive model selection prompt.
3. Write the chosen model to `project.yaml` under `models.verify`.
4. Do not silently default to any model.

### 3. Planner Pre-Flight Gate

Before touching any execution state, verify the campaign is well-formed.

1. **Quest file existence check** — For every quest entry in `manifest.yaml.quests[]`, verify the file at `<campaign-root>/<quest.file>` exists.
2. **Status legality check** — Reject quests with statuses other than `ready`, `passed`, `failed`, `skipped`, or `in_progress`. The planner only ever writes `ready`; other values come from prior executor runs.
3. **Difficulty presence** — Every quest must have a `difficulty` field (`easy` / `medium` / `hard`). The planner writes this; if missing, hard-block — the planner output is malformed.

**Hard block — no partial execution.** If ANY check fails, refuse the campaign. Display which quests are malformed.

### 4. Crash Recovery Check

Examine the manifest for signs of an interrupted previous run:

- Any quest with `status: in_progress`.
- Any `.run/<quest-id>/` directory without a `complete.yaml` marker.

If detected, show which quests were interrupted and at which step (from manifest `current_cycle`). Offer: **Resume** from last completed step, or **Restart** (reset quest to `ready`, clean its `.run/<quest-id>/`).

**Under `--no-confirm`:** default to **Resume**.

### 5. Campaign Intake

1. **Read manifest** — Parse `manifest.yaml`.
2. **Build the queue** — Collect all quests with `status: "ready"`. Sort by dependency order: quests whose `depends_on` are all `passed` (or empty) come first.
3. **Show the queue** — Table: quest ID, title, difficulty, step count, dependencies, eligibility.
4. **Confirm once** — "Execute these N quests in this order?"

**Under `--no-confirm`:** skip the prompt. Proceed to Step 6.

### 6. Mode Selection

After the campaign queue is confirmed, determine execution mode:

- **`--batch` flag present:**
  1. Verify the batch executor script exists in the skill directory (`references/batch-executor.*`).
  2. If missing, report "Batch script not yet shipped — falling back to Pi CLI mode." and proceed as if no flag was given.
  3. Otherwise: launch the batch script as a background process, passing the campaign path. Enter the **Batch Mode Polling Loop**.

- **`--claude` flag present:**
  1. Report: "Claude mode active — dispatching Claude Code Agent subagents per step (easy→Haiku, medium→Sonnet, hard→Opus)."
  2. Proceed to the Quest Execution Loop. Children are Agent subagents with in-memory I/O.

- **No flag (default — Pi CLI mode):**
  1. Report: "Pi CLI mode — spawning pi sub-invocations with models from project.yaml."
  2. Proceed to the Quest Execution Loop. Children are `pi --model <model>` processes with file I/O.

### 7. Quest Execution Loop

For each quest in the queue:

#### 7a. Pre-Quest Setup

1. **Read quest contract** — Parse `quest-NNN-*.md`. Extract `## Purpose`, `## Steps`, `## Dependencies`, `## Victory Conditions`. Synthesize step IDs `s01`, `s02`, ... for each `### Step N: <title>` block.
2. **Create `.run/<quest-id>/`** in the campaign directory (skip if it already exists from a resumed run).
3. **Resolve execute-model** — `project.yaml.models.execution_by_difficulty[<quest.difficulty>]` in Pi CLI / batch mode; hardcoded tier in `--claude` mode.
4. **Manifest mutation** — Set quest status to `in_progress`. Set `current_cycle: 0`, `total_cycles: <step-count>`, `started_at: <ISO-8601>`.

#### 7b. Step Execution Loop

For each step in the quest's parsed step list, in order:

1. **Update manifest** — Set `current_cycle` to this step's index (1-based).

2. **Spawn execute-child** — Behavior depends on execution mode:

   **Pi CLI mode (default):**
   - Write input YAML to `.run/<quest-id>/step-<sid>.html` opening HTML comment (step content, target files, quest context, retry context if applicable).
   - Spawn: `pi --model <execute-model> -p "Read step-<sid>.html. Follow the instructions in the YAML input section. When done, write your output (files_changed, implementation_summary, status) into the YAML output section of the same file."`
   - Wait for process exit (timeout from `executor.child_timeout_seconds`).
   - Read output from the file's YAML output section.

   **Claude mode (`--claude`):**
   - Dispatch Claude Code Agent subagent. Tier from quest difficulty: easy → Haiku, medium → Sonnet, hard → Opus.
   - Subagent prompt contains step content + target files + quest context in-memory. Subagent returns structured result.
   - Executor writes the result into `step-<sid>.html` output section after the subagent returns (for run report consistency).

3. **Read execute-child output** — Expect: `files_changed` (list), `implementation_summary` (string), `status` (`"success"` or `"error"`), `error_message` (when error).

4. **On step success:** Update `step-<sid>.html` with completed output section. Perform VCS-neutral checkpoint. Proceed to next step.

5. **On step failure (status: error or timeout):** Enter the tiered retry loop (7c).

#### 7c. Tiered Retry Loop (on step failure)

Bounded by `max_step_retries` (default: 3).

**Retry 1 — Lesson-Only:**

1. **Extract lesson** — Create entry: `quest_id`, `step_id`, `attempt: 1`, `retry_tier: "lesson-only"`, `failure_type`, `error_summary`, `stdout_tail`, `stderr_tail`, `timestamp`. Append to `lessons.yaml`.
2. **Re-execute with lessons only** — Spawn execute-child with:
   - Original step content (unchanged).
   - `is_retry: true`, `retry_attempt: 1`, `retry_tier: "lesson-only"`.
   - `accumulated_lessons`: all lessons for this step so far.
   - `previous_failure`: error summary from the failed attempt.
   - `revised_instructions: null`.
3. **Pass:** Exit loop. Mark step passed. Checkpoint. Next step.
4. **Fail:** Proceed to Retry 2+.

**Retry 2+ — Re-Plan Escalation:**

1. **Extract lesson** — Append to `lessons.yaml` with `retry_tier: "replan"`.
2. **Spawn re-plan-child** — Provide: original step content, failure context, ALL accumulated lessons.
   - **Pi CLI mode:** `pi --model <planning-model> -p "Read step-<sid>.html and lessons.yaml. Produce revised instructions for the failed step. Write to step-<sid>.html YAML re-plan section."`
   - **Claude mode:** Dispatch Sonnet subagent with same context. Returns in-memory.
3. **Read re-plan output** — Expect: `revised_instructions`, `revised_code_block` (optional), `reasoning`, `confidence`.
4. **Re-execute** — Spawn execute-child with `revised_instructions` replacing the original step description (and `revised_code_block` replacing the original code block if present), plus all accumulated lessons.
5. **Pass:** Exit loop. Mark step passed. Checkpoint. Next step.
6. **Fail, retries remaining:** Loop back (next retry is also Retry 2+ tier).
7. **Fail, retries exhausted:** Mark step `failed`. Extract final lesson with `outcome: "exhausted"`. Mark quest `failed`. Exit to 7d.

The original quest `.md` on disk is **never** modified. Re-plan revisions live only in `step-<sid>.html`'s re-plan section and the in-memory step structure for the current attempt.

#### 7d. Quest-Level Victory Condition Verification

After all steps in a quest pass (or after the step loop exits due to failure), verify the quest's `## Victory Conditions`:

1. **If quest already failed at the step loop:** Skip VC verification. The lesson and step failures are recorded; proceed to 7e with `passed: false`.

2. **Otherwise, for each VC checkbox in `## Victory Conditions`:**

   **Auto-classify the VC:**
   - **Tier 1 (mechanical):** matches a known pattern.
     - "file X exists" → check file existence.
     - "file X does not exist" → check file absence.
     - "file X contains Y" → grep for pattern.
     - "directory X exists" → check directory.
     - "file X is valid JSON/YAML" → parse and check.
     - VC begins with a verifiable phrase (`grep`, `test -f`, etc., or a shell-like check) → run the implied check.
   - **Tier 1 complex:** mentions a check that needs reasoning over file contents (e.g., "the manifest's `quests` array has 3 entries"). Spawn a verify-child:
     - **Pi CLI mode:** `pi --model <verify-model> -p "Verify this victory condition: <VC text>. Workspace root: <path>. Files touched by this quest: <files_changed across all steps>. Write pass: true|false and reasoning to <step-<final>-verify.yaml>."`
     - **Claude mode:** Haiku subagent with same context.
   - **Tier 2 (judgmental):** VC describes subjective acceptance ("feels right", "renders correctly", "the code is idiomatic"). Add to the **deferred UAT queue**: quest ID, VC text, files changed across all steps, list of step summaries.

3. **Inline result aggregation:**
   - All Tier 1 VCs pass → quest passes provisionally (pending UAT for any Tier 2 VCs).
   - Any Tier 1 VC fails → quest fails. Mark `failed`. Extract a lesson with `failure_type: "vc_failed"` and `failed_criteria: [<VC text>]`. Proceed to 7e.

4. **Tier 2 VCs are NOT verified inline.** They sit in the deferred queue. The quest's provisional pass survives or falls based on §8a UAT review.

#### 7e. Post-Quest Finalization

1. **Determine outcome:** All steps + all Tier 1 VCs passed → `passed` (provisional if Tier 2 VCs are deferred). Any step failed or any Tier 1 VC failed → `failed`.
2. **Manifest mutation** — Set status. Set `completed_at` ISO-8601.
3. **Write completion marker** — `.run/<quest-id>/complete.yaml` with quest summary.
4. **Cascade skip** (if failed) — Find all quests whose `depends_on` includes this quest (transitively). Set `status: skipped`, `skip_reason: "dependency_failed: <quest-id>"`.
5. **Re-evaluate queue** — Previously-blocked quests may now be eligible.
6. **Show per-quest summary** — Quest ID, title, difficulty, steps completed, retries used per step, Tier 1 VC results, Tier 2 deferred count, pass/fail status.

## Batch Mode — Launch and Polling

When `--batch` is active, the executor does not dispatch children directly. Instead it launches the batch executor script and monitors progress.

### Status

**The batch executor script is not yet shipped with this skill.** When `--batch` is invoked and no script exists at the expected location, fall back to Pi CLI mode with a one-line warning. The Batch Mode sections below describe the contract the future script must honor.

### Script Launch (when script exists)

1. Verify the batch executor script exists in the skill directory.
2. Launch as a background process, passing the campaign path.
3. Store the process handle for alive/dead detection.
4. Report: "Batch executor launched for `<campaign-title>`. Polling for progress..."

### Polling Loop

Poll at regular intervals (default: 30 seconds):

1. **Check process alive** — If exited, check exit code and proceed to Completion Detection.
2. **Read manifest** — Check `current_cycle` and `current_step_started_at` for each `in_progress` quest.
3. **Scan step files** — Check `.run/<quest-id>/` for new or updated `step-*.html` files.
4. **Report progress** — Display active quest/step, elapsed time, completed/total, new step results, overall progress.

### Completion Detection

1. **Exit code 0:** Batch completed. Read final manifest. Report outcomes.
2. **Non-zero exit:** Batch failed/interrupted. Read manifest for partial results.
3. **All quests resolved but process still running:** Warn, continue waiting for exit.

After batch completion, proceed to Run Report generation. The run report reads `.run/` step files identically for all execution modes.

### Step File Format

Each step produces one `step-<sid>.html` in `.run/<quest-id>/`:

```html
<!--
---
step_id: "s01"
quest_id: "q001"
status: "passed"

input:
  step_title: "..."
  step_description: "..."
  code_blocks:
    - file: "..."
      language: "..."
      content: |
        ...
  quest_context:
    quest_id: "..."
    quest_title: "..."
    difficulty: "..."
  retry_context:                 # only when is_retry: true
    is_retry: true
    retry_attempt: integer
    retry_tier: "lesson-only" | "replan"
    accumulated_lessons: [...]
    previous_failure: {...}
    revised_instructions: string | null
    revised_code_block: {...} | null

output:
  files_changed: ["path/to/file.md"]
  implementation_summary: "..."
  status: "success" | "error"
  error_message: string | null

re_plan:                         # only present on retry 2+
  revised_instructions: "..."
  revised_code_block: {...} | null
  reasoning: "..."
  confidence: "high" | "medium" | "low"

attempts: 1
retries_used: 0
duration_seconds: 12
---
-->

<!DOCTYPE html>
<html>
  <!-- Readable dashboard rendering the YAML above -->
</html>
```

**Mode-specific I/O:**

| Mode | Input section | Output section | Re-plan section |
|------|--------------|----------------|------------------|
| **Pi CLI** | Executor writes before spawning child | Child writes on completion | Re-plan-child writes |
| **Claude** | Omitted in-flight (context delivered in-memory); executor writes a transcript after the fact | Executor writes from in-memory output | Executor writes from in-memory re-plan output |
| **Batch** | Batch script writes before spawning child | Child writes on completion | Re-plan-child writes |

### 8. Run Report

After all quests are processed:

1. **Generate HTML run report** — Write `run-report-<timestamp>.html` at campaign root. Include:
   - Campaign title, run timestamp, duration.
   - Quest results table: quest ID, title, difficulty, status, steps completed/total, retries used, VCs passed/total.
   - Per-quest detail cards: VC checklist with per-VC pass/fail (Tier 1) and `tier_2_deferred` markers (Tier 2 pending UAT, or final result after §8a).
   - Deferred Tier 2 items section: listed with their quests, files changed, step summaries.
   - Lessons section.
   - Overall counts: passed, failed, skipped.
   - Native HTML/CSS only; no JavaScript; no external dependencies.

2. **Show chain summary** — Full table covering all quests.

### 8a. UAT Batch Prompt

After the run report, present all deferred Tier 2 VCs as a consolidated UAT checklist.

1. **Check the deferred UAT queue.** If empty, skip this section.
2. **Present the UAT Checklist** — Display:
   - Quest ID, quest title.
   - VC text (the yes/no question).
   - Files changed by the quest.
   - Step summaries (from `implementation_summary` of each step).
3. **For each item, ask:** "Does this quest's outcome satisfy this victory condition?" Yes / No.
4. **Record results.** Update the quest's step files and the run report with per-VC yes/no answers.
5. **Handle failures.** If any VC receives "no":
   - Extract a lesson with `failure_type: "uat_rejected"`.
   - Update the quest's manifest status from `passed` to `failed`.
   - Cascade-skip any quests that depend on the now-failed quest (if they haven't been processed yet — typically too late at this stage, so note the cascade impact for the next run).
   - No re-plan loop post-UAT. The failure is recorded for the next run.

**Under `--no-confirm`:** skip the interactive UAT checklist. All deferred items remain `tier_2_deferred` in step files and the run report. The parent process decides how to handle Tier 2 review.

### 9. Cleanup

After the run report and UAT:

- **Preserve:** `lessons.yaml`, `run-report-*.html`, `.run/<quest-id>/complete.yaml`, `.run/<quest-id>/step-*.html`.
- **Optional cleanup:** Old-format scratch files from prior runs (if any). Ask before deleting.

**Under `--no-confirm`:** skip the cleanup prompt. Preserve all files.

### 10. VCS Artifact Policy

Read `vcs_artifacts.execution` from `.liang/project.yaml`:

- **`"ignore"`** — Apply VCS ignore rules silently.
- **`"commit"`** — Leave artifacts trackable.
- **`"ask"`** (or absent) — Ask the user; write the choice back to `project.yaml`.

Apply policy once after the chain completes.

**Under `--no-confirm`:** if `"ask"` or absent, treat as `"ignore"` silently. Do not write the choice back.

### 11. Commit Suggestion

**If `.liang/project.yaml` does not exist:** skip entirely.

Read `vcs_artifacts.planning` from `.liang/project.yaml`:

- **`"ignore"`** — Skip this section.
- **`"commit"` or `"ask"`** — Proceed with VCS health check and suggestion.

**VCS Health Check:**

1. Verify `.git/` exists in the workspace root.
2. Run `git status` and confirm success.
3. If either fails: "VCS health check failed — skipping commit suggestion."

**Suggestion** (never auto-execute):

```text
Campaign completed. To commit the artifacts, paste:
git add <campaign-path>/
git commit -m "Campaign: <campaign-title> — <passed>/<total> quests passed"
```

**Under `--no-confirm`:** skip the commit suggestion.

### 12. Open Prompt

Offer to:

- Open `run-report-<timestamp>.html` in the default browser.
- Open the campaign folder.
- Do nothing.

Do not open anything automatically.

## Child Process Model

All execute-children, verify-children, and re-plan-children are spawned (Pi CLI / batch) or dispatched (Claude). The parent never directly edits project source files.

### Model Selection

| Child Type | Pi CLI Mode (default) | Claude Mode (`--claude`) | Batch Mode (`--batch`) |
|-----------|----------------------|--------------------------|------------------------|
| Execute-child (easy) | `pi --model <models.execution_by_difficulty.easy>` | Haiku subagent | Pi CLI + easy model |
| Execute-child (medium) | `pi --model <models.execution_by_difficulty.medium>` | Sonnet subagent | Pi CLI + medium model |
| Execute-child (hard) | `pi --model <models.execution_by_difficulty.hard>` | Opus subagent | Pi CLI + hard model |
| Verify-child (Tier 1 complex) | `pi --model <models.verify>` | Haiku subagent | Pi CLI + verify model |
| Re-plan-child (retry 2+) | `pi --model <models.planning>` | Sonnet subagent | Pi CLI + planning model |

Re-plan-child is only invoked on retry 2+. Retry 1 is lesson-only.

### Child I/O

See `liang-quest-core/references/execution/child-contracts.md` for full input/output YAML schemas covering the planner-native execute-child, verify-child, and re-plan-child.

## Manifest Status Vocabulary

| From | To | Trigger |
|------|----|---------|
| `ready` | `in_progress` | Quest execution begins |
| `in_progress` | `passed` | All steps passed and all Tier 1 VCs passed (Tier 2 VCs pending UAT do not block this transition) |
| `in_progress` | `failed` | A step exhausted retries OR a Tier 1 VC failed |
| `passed` | `failed` | A Tier 2 VC failed in §8a UAT review |
| `ready` | `skipped` | Dependency failed (cascade) |

Additional manifest fields the executor manages:

- `started_at`, `completed_at` — ISO-8601 timestamps.
- `current_cycle`, `total_cycles` — current step index and total step count.
- `skip_reason` — present when `skipped`.

## Boundaries — Hard Stops

This skill must never:

1. **Modify, overwrite, or delete any `quest-NNN-*.md` or `plan.html` file.** Planner artifacts are read-only.
2. **Generate quest plans or planning artifacts.** Re-planning produces in-memory revisions stored in `step-<sid>.html`, never written back to the planner files.
3. **Edit project source files directly.** All code changes flow through execute-children.
4. **Process quests without upfront confirmation.** (`--no-confirm` is the documented exception.)
5. **Continue executing after `max_step_retries` is exhausted.** Mark quest failed, cascade-skip.
6. **Mutate manifest fields outside its authority.** Only the fields listed under "Manifest Status Vocabulary".
7. **Silently change Git ignore rules.**
8. **Read or include secrets, `.env`, `.env.*`, `.git/`, credentials, tokens, dependency folders, build outputs, or large binaries** in any generated artifact.
9. **Use VCS-specific wording in YAML keys or child I/O.**
10. **Parse child stdout/stderr for structured data.** Use `step-<sid>.html` YAML sections only (Pi CLI / batch); use the structured Agent tool return value (Claude mode).
11. **Execute quests whose dependencies have not all `passed`.**
12. **Silently resume an interrupted run when invoked interactively.** Under `--no-confirm`, default to Resume per §4.
13. **Default to `--claude` mode when running inside Pi.** Claude mode requires the explicit `--claude` flag.
14. **Stamp, read, or check a `workflow` field.** The planner-native pipeline has no workflow discriminator.

If the user asks for any of the above, decline and explain the boundary, then offer the closest in-scope alternative.

## Failure Modes

- **Child process fails to spawn:** Report, mark step failed, enter retry loop.
- **Child output malformed:** Treat as failure with `failure_type: "malformed_output"`.
- **Child timeout:** Kill, failure with `failure_type: "timeout"`.
- **Tier 1 VC fails inline:** Mark quest `failed` (no step retry — the steps already passed). Extract a lesson with `failure_type: "vc_failed"`.
- **Tier 1 verify-child returns malformed result:** Treat as VC failure with `failure_type: "verify_malformed"`. Mark quest `failed`.
- **Tier 2 "no" answer in UAT batch §8a:** Quest status downgraded from `passed` to `failed`. Lesson extracted with `failure_type: "uat_rejected"`. Cascade-skip dependents not yet processed.
- **Lesson-only retry fails (retry 1):** Expected for conceptual failures. Automatic escalation to re-plan-child on retry 2.
- **Re-plan-child returns malformed output:** Treat as failure of the retry attempt. Continue retry loop until exhausted.
- **Quest `.md` file unreadable or missing `## Steps` section:** Skip quest with a warning. Mark `failed` with a lesson.
- **Quest `.md` Steps section parses to zero steps:** Skip quest with a warning. Mark `failed`.
- **Manifest write fails:** Warn, continue. Manifest is stale but execution is valid.
- **All quests skipped or failed:** Produce run report anyway.
- **Mid-run interruption:** Manifest state + `.run/` files enable crash recovery.
- **`project.yaml` missing or incomplete:** Stop with exit code 2.
- **Pi CLI invocation fails:** Report spawn error with exact command. Offer to retry or skip the step.
- **`--no-confirm` fallback failure:** If a gate's documented default cannot be applied (e.g., crash-recovery Resume but state is unrecoverable), exit with code 3 and write a structured failure message to stderr.

## Visual Tone (Run Report)

Match the family style:

- Dark hero / header, light readable cards.
- Green for passed, red for failed, amber for skipped.
- Tier 1 VC results: compact checklist (check for pass, cross for fail).
- Tier 2 deferred VCs: amber "Pending UAT" or post-UAT yes/no badge.
- Difficulty badges: green (easy), amber (medium), red-umber (hard).
- Step-level detail: collapsible per quest, showing step IDs, retry counts, retry tiers used.
- Native HTML/CSS only; no JavaScript; no external dependencies.
- HTML-escape all source-derived content.
- JRPG labels in the HTML view only; neutral keys in YAML.

## Relationship to Other Skills

- **Upstream:** `liang-quest-planner` produces the campaign this skill consumes. Same-context planner + child-process-orchestrating executor is the canonical pair.
- **Shared foundation:** `liang-quest-core` — shared protocol, manifest schema, status transitions, run report.
- **Shared contracts:** `.liang/project.yaml` — workspace-wide config. Required.

## Reference Files

### Core References (read first — source of truth for shared schemas)

- `liang-quest-core/references/campaign/protocol.md` — shared campaign protocol, lifecycle, routing. Canonical pipeline documented at the top.
- `liang-quest-core/references/campaign/manifest-schema.md` — shared manifest schema. Planner-format schema is canonical.
- `liang-quest-core/references/execution/status-transitions.md` — status transitions including this skill's `ready → in_progress → passed/failed/skipped` path and tiered retry behavior.
- `liang-quest-core/references/execution/child-contracts.md` — child process I/O contracts. The "Planner-Native" sections cover this skill.
- `liang-quest-core/references/execution/run-report.md` — run report and lesson schemas.
- `liang-quest-core/references/project/project-yaml.md` — project.yaml contract.

### Local References

- `references/run-report-template.html` — Run report HTML skeleton.

Always read core references before executing. They are the source of truth.
