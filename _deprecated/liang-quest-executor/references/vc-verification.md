# Victory Condition Verification (§7d detail)

Full classification rules and verify-child prompts for quest-level VC verification. The SKILL.md summary is in § 7d. Quest-Level Victory Condition Verification; load this file when classifying VCs.

If the quest already failed at the step loop: skip VC verification entirely — the lesson and step failures are recorded; proceed to §7e with `passed: false`.

Otherwise, for each VC checkbox in `## Victory Conditions`:

## Auto-Classification

- **Tier 1 (mechanical):** matches a known pattern.
  - "file X exists" → check file existence.
  - "file X does not exist" → check file absence.
  - "file X contains Y" → grep for pattern.
  - "directory X exists" → check directory.
  - "file X is valid JSON/YAML" → parse and check.
  - VC begins with a verifiable phrase (`grep`, `test -f`, etc., or a shell-like check) → run the implied check with host-appropriate tooling (the phrase names the intent, not a literal command — e.g. use PowerShell equivalents on Windows).
- **Tier 1 complex:** mentions a check that needs reasoning over file contents (e.g., "the manifest's `quests` array has 3 entries"). Spawn a verify-child:
  - **Pi CLI mode:** `pi --model <verify-model> --session .run/<quest-id>/sessions/verify-vc<n>.jsonl -p "Read the final step envelope at .run/<quest-id>/step-<sid>.md. Verify this victory condition: <VC text>. Workspace root: <path>. Files touched by this quest: <files_changed across all steps>. Write pass: true|false and reasoning to the step envelope's Verification fenced YAML block."`
  - **Claude mode:** Verify-child subagent (tier from `models.claude_mode.verify`; default per `liang-quest-core/references/project/project-yaml.md` § Model Routing Extensions) with same context. The executor writes the structured result into the final step envelope's Verification fenced YAML block.
- **Tier 2 (judgmental):** VC describes subjective acceptance ("feels right", "renders correctly", "the code is idiomatic"). Add to the **deferred UAT queue**: quest ID, VC text, files changed across all steps, list of step summaries.

## Inline Result Aggregation

- All Tier 1 VCs pass → quest passes provisionally (pending UAT for any Tier 2 VCs).
- Any Tier 1 VC fails → run VC repair rounds (below). Still failing after the last round → quest fails. Mark `failed`. Extract a lesson with `failure_type: "vc_failed"` and `failed_criteria: [<VC text>]`; write `failed_vcs` to `complete.yaml`. Proceed to §7e.
- **Tier 2 VCs are NOT verified inline.** They sit in the deferred queue. The quest's provisional pass survives or falls based on §8a UAT review.

## VC Repair Rounds

The steps already passed, so re-running them cannot help; a failed Tier 1 VC usually names the exact gap (a file:line, a missing call). Up to `executor.max_vc_repair_rounds` rounds (default 2; 0 restores fail-at-once):

1. **Lesson.** Append a lesson with `failure_type: "vc_failed"`, `retry_tier: "vc_repair"`, `failed_criteria` and the verifier evidence.
2. **Re-plan-child** (planning model), `failure_context.failure_type: "vc_failed"` with `failed_vcs` (VC text + evidence per failing VC), the quest's `## Purpose`, all step summaries and `files_changed`. It returns `revised_instructions` for one repair: the smallest code change that makes the failing VCs true, plus the quest's own build/test commands to re-run (taken from its steps). `resolvable: false` (the VC is wrong or contradicts the plan) ends the rounds: the quest fails and the VC goes to `## Decisions needed`.
3. **Execute-child** applies the repair. Envelope `.run/<quest-id>/step-fix<r>.md`, title `Repair: <first failing VC, shortened>`; same Input/Output/Re-plan sections as a step.
4. **Re-verify every Tier 1 VC**, not only the failed ones — a repair must not break a VC that passed. Record the results in the repair envelope's Verification block.
5. **All pass** → quest passes; `complete.yaml` gets `vc_repair_rounds: <r>`. **Any fail** → next round, or fail the quest after the last.

**Guardrails.** A repair may not delete or skip a test, loosen an assertion, or edit a quest `.md` or VC. When the only way to pass is to change a test's expected value or read a VC more loosely, the repair-child says so in `plan_contradictions` with `blocks_step: false`; the executor applies it, passes the quest, and adds the reason to `complete.yaml` `needs_review` — the batch sweep lists it under "Needs you" in its morning report and keeps going.

Source: extracted from liang-quest-executor/SKILL.md § 7d. Quest-Level Victory Condition Verification
