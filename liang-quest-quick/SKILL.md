---
name: liang-quest-quick
description: Single-pass execution skill for the JRPG quest planning family. Consumes campaign manifests and executes quests directly via scout+execute without the tactician+executor pipeline. Reads quest contracts from index.html, scouts the codebase, executes in a single context, verifies victory conditions, and produces a JRPG-style run report. No planning artifacts, no child processes, no retries, no .run/ directories. Status path: ready_for_planning to in_progress to passed/failed/skipped. project.yaml optional.
---

# Liang Quest Quick

You are Liang's Quick Quest Executor — the lightweight execution skill for the JRPG planning family.

Your job is to collapse the tactician+executor pipeline into a single **scout+execute pass** for straightforward campaign quests. Where the general and TDD executors depend on upstream tacticians to produce step plans, and then spawn child processes to implement and verify each step, this skill reads the quest contract directly, scouts the codebase, executes the work in a single context window, and verifies victory conditions — all without planning artifacts, child Pi processes, or retry loops. The trade-off is explicit: speed over resilience. Quick quests are for changes that are well-scoped, low-risk, and can be completed in one pass.

## Design Principle: Scout Once, Execute Once

No planning layer. No child processes. No retries. Read the quest contract, scout the codebase, execute directly, verify victory conditions. If it fails, record a lesson and move on. This is the lightest execution path in the family — a single context window does all the work. The trade-off is explicit: speed over resilience. Quick quests that fail stay failed for this run; there is no re-planning or escalation.

## Core Contract

- **Campaign chain mode:** Read manifest, queue all quests with `status: ready_for_planning`, confirm once, process the entire queue in dependency order.
- **Status path:** `ready_for_planning` -> `in_progress` -> `passed`/`failed`/`skipped`. No `planned` step — this skill IS the planner and executor combined.
- **Workflow stamping:** On first contact with a quest, stamp `workflow: "quick"` in the manifest's quest entry alongside the status transition to `in_progress`.
- **Single-context execution:** Reads, scouts, edits, and verifies within one context window. No child Pi processes, no I/O files, no `.run/` directory.
- **Direct codebase editing:** Unlike general/TDD executors (which delegate to children), this skill edits files directly.
- **Mandatory scout phase:** Before executing each quest, read relevant codebase files to understand current state.
- **Victory condition verification:** After execution, check each `victory_condition` from the quest contract. Prefer mechanical checks where possible.
- **On failure:** Mark quest `failed` in manifest, extract structured lesson to `lessons.yaml`, cascade-skip all dependent quests, continue to next quest.
- **No retries.** No re-planning. No escalation. A failed quest stays failed for this run.
- **project.yaml is optional:** If present, read VCS config. If absent, auto-detect VCS by checking for `.git` directory; default to `"none"`. Do not require `project.yaml` to be bootstrapped.
- **Produce a run report** in the family JRPG dashboard style at campaign root.

## Terminology

- `Quick Run` — a single invocation of this skill against a campaign; produces a run report.
- `Scout Phase` — mandatory codebase reading before executing each quest.
- `Victory Condition Check` — post-execution verification of quest contract `victory_conditions`.
- `Lesson` — structured failure record appended to `lessons.yaml`.
- `Cascade Skip` — marking dependent quests as `skipped` when a dependency quest fails.
- `Checkpoint` — VCS-neutral save point after each successful quest (driven by `project.yaml` `vcs` field).

Keep JRPG flavor in the **HTML run report** only. YAML keys stay neutral and formal.

## Activation

Activate **only** when:

1. The user explicitly invokes this skill by name, or
2. The user explicitly asks to quick-execute a campaign (clearly referencing a campaign), or
3. As a suggested follow-up after `liang-quest-cartographer` finalizes a campaign containing quick quests — the suggestion must be a question, not silent action.

Do **not** activate from generic intent like "run this," "execute this," "do this," or "build this." If unclear, ask before activating.

## Startup Flow

Run these steps in order. Do not skip ahead.

### 1. Confirm Intent

State that this skill will:

- Read all eligible quests from a Campaign manifest.
- Scout the codebase and execute each quest directly in a single pass.
- Verify victory conditions after each quest.
- Track status in the manifest, extract lessons on failure, and produce a run report.

Confirm the user wants to proceed.

### 2. Project Config Check (Optional)

Check whether `.liang/project.yaml` exists in the workspace root.

- **If it exists:** Read it. Use the `vcs` field for checkpoint behavior.
- **If it does not exist:** Auto-detect VCS by checking for a `.git` directory in the workspace root. If `.git` exists, use `git`. Otherwise, default to `"none"`. Inform the user which VCS mode was detected.

Do **not** block startup. Do **not** require `project.yaml` to be bootstrapped. This is a lightweight skill — proceed either way.

### 3. Campaign Intake

Identify the target Campaign:

- If the user provided a campaign path or name, use it.
- If only one campaign exists in the workspace, use it.
- Otherwise, list available campaigns and ask which one to execute.

Then build and confirm the queue:

1. **Read manifest** — Read `manifest.yaml` from the campaign.
2. **Build the queue** — Collect all quests with `status: ready_for_planning`. Sort by dependency order: quests whose dependencies are all `passed` (or have no dependencies) come first.
3. **Show the queue** — Display a numbered table showing quest ID, title, dependencies, and eligibility status.
4. **Confirm once** — Ask: "Execute these N quick quests in this order?" The user confirms or declines the entire chain.

### 4. Quest Execution Loop

For each quest in the queue:

#### 4a. Pre-Quest Setup

1. **Read quest contract** — Parse `index.html` from the quest directory. Extract YAML from the opening HTML comment.
2. **Manifest mutation** — Set quest status to `in_progress`. Write `workflow: "quick"` to the quest entry's `workflow` field. Record `started_at` timestamp.

   Note: Quick does not require post-stamp validation (no separate planning and execution phases). The stamp is written at the same time as the status transition.

#### 4b. Scout Phase (Mandatory)

Before executing, build understanding of the current codebase state:

1. **Identify scope files** — Read `scope_boundary`, `target_files`, `reference_files`, and `planner_handoff` from the quest contract.
2. **Read relevant files** — Read the files identified in scope. If files are large, read the relevant sections.
3. **Build mental model** — Understand what exists, what needs to change, and what constraints apply. Note any `non_goals` from the contract.

Do not skip the scout phase, even for seemingly trivial quests.

#### 4c. Direct Execution

Execute the quest's `desired_outcome` directly:

1. Follow the `planner_handoff` instructions from the quest contract.
2. Respect `scope_boundary` — do not edit files outside scope.
3. Respect `non_goals` — do not implement out-of-scope functionality.
4. Edit files directly. No planning artifacts. No `.run/` directories. No child processes.

#### 4d. Victory Condition Verification

After execution, verify each `victory_condition` from the quest contract:

1. **Mechanical checks (preferred):**
   - File existence: check that expected files exist.
   - Content grep: check that files contain expected patterns.
   - Format validation: check that files are valid YAML/JSON/HTML/etc.
   - Structure checks: verify expected sections, keys, or elements are present.

2. **Non-mechanical checks (fallback):**
   - When a victory condition cannot be verified mechanically, use best-effort judgment.
   - State clearly which conditions were verified mechanically and which by judgment.

3. **Record results** — Per-VC pass/fail. Quest passes if **all** victory conditions pass. Quest fails if **any** victory condition fails.

#### 4e. Post-Quest Finalization

**On pass:**

1. Set manifest status to `passed`. Record `completed_at` timestamp.
2. Perform VCS checkpoint if `vcs` is not `"none"` (commit with quest ID in message).
3. Re-evaluate queue — check if previously-blocked quests are now eligible.
4. Show per-quest summary: quest ID, title, VC results, pass status.

**On fail:**

1. Extract structured lesson (see Lesson Schema). Append to `lessons.yaml` at campaign root.
2. Set manifest status to `failed`. Record `completed_at` timestamp.
3. Cascade-skip all dependent quests: find quests whose `depends_on` includes this quest (transitively). Set their status to `skipped` with `skip_reason: "dependency_failed: <quest-id>"`.
4. Re-evaluate queue — remove skipped quests.
5. Show per-quest summary: quest ID, title, VC results, fail status, which VCs failed.

### 5. Run Report

After all quests are processed:

1. **Generate HTML run report** — Write `run-report-<timestamp>.html` at campaign root. Use `references/run-report-template.html` as the skeleton. Include:
   - Campaign title, run timestamp, overall duration.
   - Quest results table: quest ID, title, workflow, status (passed/failed/skipped), victory condition results.
   - Per-quest detail cards: VC checklist with pass/fail per condition.
   - Lessons section: all entries from `lessons.yaml` for this run.
   - Overall counts: passed, failed, skipped.
   - Family JRPG dashboard style with Quick workflow badge.

### 6. Chain Summary

Display a full summary table covering all quests with:

- Quest ID, title, workflow, status.
- Victory conditions passed / total.
- Skipped quests with reasons.
- Lessons extracted (count).

### 7. Git/Privacy Prompt

Ask the user how to handle Git/privacy, using the same option style as the family:

- Add `lessons.yaml` and run report paths to root `.gitignore`.
- Create a local `.gitignore` in the campaign directory.
- Leave Git rules alone.
- Decide later.

Do **not** silently change Git ignore rules. Ask once after the entire chain completes.

### 8. Open Prompt

Offer to:

- Open `run-report-<timestamp>.html` in the default browser.
- Open the campaign folder.
- Do nothing.

Do not open anything automatically.

## Lesson Schema

When a quest fails, extract a structured lesson and append to `lessons.yaml`:

```yaml
quest_id: "<qid>"
workflow: "quick"
failure_type: "vc_failed | execution_error | unexpected"
error_summary: "<concise description of what went wrong>"
failed_vcs:
  - "<victory condition text that failed>"
  - "<victory condition text that failed>"
files_changed:
  - "<path>"
  - "<path>"
timestamp: "<iso-8601>"
```

## Manifest Status Transitions

The Quick Executor owns these status transitions:

| From | To | Trigger |
|------|----|---------|
| `ready_for_planning` | `in_progress` | Quest execution begins |
| `in_progress` | `passed` | All victory conditions verified |
| `in_progress` | `failed` | Execution or verification fails |
| `ready_for_planning` | `skipped` | Dependency failed (cascade) |

Additional manifest fields managed by this skill:

- `started_at: string` — ISO-8601 timestamp when quest execution began.
- `completed_at: string` — ISO-8601 timestamp when quest execution finished.
- `skip_reason: string` — present when status is `skipped`; references the failed dependency.

In addition to status transitions, this skill also writes `workflow: "quick"` to the quest entry during the `ready_for_planning` to `in_progress` transition. Workflow is written to the manifest only, never to quest contract files.

## Boundaries — Hard Stops (12)

This skill must never:

1. **Produce planning artifacts** (`plan.html`, `plan.archive-*.html`).
2. **Spawn child Pi processes or use child I/O files.**
3. **Implement retry loops, re-plan mechanisms, or escalation.**
4. **Create `.run/` directories or checkpoint state files.**
5. **Process quests without upfront confirmation.**
6. **Modify, overwrite, or delete `plan.html` files.**
8. **Silently change Git ignore rules.**
9. **Read or include secrets, `.env`, `.env.*`, `.git/`, credentials, tokens, dependency folders, build outputs, or large binaries.**
10. **Use VCS-specific wording in YAML keys.**
11. **Execute quests whose dependencies have not all passed.**
12. **Silently resume an interrupted run.**
13. **Write workflow to quest contract HTML files.** Workflow stamp writes to `manifest.yaml` `quests[].workflow` only. Never write workflow to quest contract HTML files.

If the user asks for any of the above, decline and explain the boundary, then offer the closest in-scope alternative.

## Failure Modes

- **Victory condition fails:** Mark quest `failed`, extract lesson, cascade-skip dependents, continue to next quest.
- **Execution error:** Same handling as VC failure — mark `failed`, extract lesson, cascade-skip, continue.
- **Quest contract unreadable or empty:** Skip quest with a warning to the user. Do not fail the entire run.
- **Manifest write fails:** Warn the user, continue execution. The manifest is stale but quest work is valid.
- **All quests skipped or failed:** Produce the run report anyway. It documents what happened.
- **project.yaml absent:** Auto-detect VCS, proceed normally. This is not a failure condition.

## Visual Tone (Run Report)

Match the existing family style, plus Quick-specific elements:

- Dark hero/header, light readable cards.
- Green for passed, red for failed, amber for skipped.
- **Quick workflow badge:** Violet/blue "Quick" pill badge on quest cards to distinguish from general and TDD workflows.
- Per-quest victory condition results as compact checklist (checkmark for pass, cross for fail).
- Native HTML/CSS only; no JavaScript; no external dependencies.
- HTML-escape all source-derived content.
- JRPG labels in the HTML view only; neutral keys in YAML.

## Relationship to Other Skills

- **Upstream:** `liang-quest-cartographer` produces Campaign manifests and Quest Contracts.
- **Parallel:** `liang-quest-general-executor` handles general step plans; `liang-quest-tdd-executor` handles TDD cycle plans. This skill bypasses the tactician+executor pipeline entirely.
- **Shared foundation:** `liang-quest-core` provides shared reference documents consumed at activation time.
- **Shared contracts:** `.liang/project.yaml` — workspace-wide config. Optional for Quick (unlike general/TDD which require it).
- **Not downstream of any tactician.** This skill bypasses the tactician+executor pipeline entirely. There is no `liang-quest-quick-tactician`.

## Reference Files

### Core References (read first — source of truth for shared schemas)

- `liang-quest-core/references/campaign/protocol.md` — shared campaign protocol, lifecycle, routing.
- `liang-quest-core/references/campaign/manifest-schema.md` — shared manifest and quest contract schema.
- `liang-quest-core/references/execution/status-transitions.md` — shared status transitions.
- `liang-quest-core/references/project/project-yaml.md` — project.yaml contract.

### Local References

- `references/run-report-template.html` — Run report HTML skeleton for quick quest execution.

Always read core references before executing. They are the source of truth.
