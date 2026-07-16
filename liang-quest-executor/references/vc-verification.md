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
  - **Pi CLI mode:** `pi --model <verify-model> -p "Read the final step envelope at .run/<quest-id>/step-<sid>.md. Verify this victory condition: <VC text>. Workspace root: <path>. Files touched by this quest: <files_changed across all steps>. Write pass: true|false and reasoning to the step envelope's Verification fenced YAML block."`
  - **Claude mode:** Verify-child subagent (tier from `models.claude_mode.verify`, default `haiku`) with same context. The executor writes the structured result into the final step envelope's Verification fenced YAML block.
- **Tier 2 (judgmental):** VC describes subjective acceptance ("feels right", "renders correctly", "the code is idiomatic"). Add to the **deferred UAT queue**: quest ID, VC text, files changed across all steps, list of step summaries.

## Inline Result Aggregation

- All Tier 1 VCs pass → quest passes provisionally (pending UAT for any Tier 2 VCs).
- Any Tier 1 VC fails → quest fails. Mark `failed`. Extract a lesson with `failure_type: "vc_failed"` and `failed_criteria: [<VC text>]`. Proceed to §7e.
- **Tier 2 VCs are NOT verified inline.** They sit in the deferred queue. The quest's provisional pass survives or falls based on §8a UAT review.

Source: extracted from liang-quest-executor/SKILL.md § 7d. Quest-Level Victory Condition Verification
