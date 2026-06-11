# Tiered Retry Protocol (§7c detail)

Full protocol for the step-failure retry loop. SKILL.md §7c holds the summary; this file is the source of truth for retry payloads and lesson fields. Load on first step failure. Bounded by `max_step_retries` (default: 3).

## Retry 1 — Lesson-Only

1. **Extract lesson** — Create entry: `quest_id`, `step_id`, `attempt: 1`, `retry_tier: "lesson-only"`, `failure_type`, `error_summary`, `stdout_tail`, `stderr_tail`, `timestamp`. Append to `<campaign-root>/lessons.yaml`.
2. **Re-execute with lessons only** — Spawn execute-child with:
   - Original step content (unchanged).
   - `is_retry: true`, `retry_attempt: 1`, `retry_tier: "lesson-only"`.
   - `accumulated_lessons`: all lessons for this step so far.
   - `previous_failure`: error summary from the failed attempt.
   - `revised_instructions: null`.
3. **Pass:** Exit loop. Mark step passed. Checkpoint. Next step.
4. **Fail:** Proceed to Retry 2+.

## Retry 2+ — Re-Plan Escalation

1. **Extract lesson** — Append to `<campaign-root>/lessons.yaml` with `retry_tier: "replan"`.
2. **Spawn re-plan-child** — Provide: original step content, failure context, ALL accumulated lessons.
   - **Pi CLI mode:** `pi --model <planning-model> -p "Read the failed step envelope at .run/<quest-id>/step-<sid>.md and lessons.yaml. Produce revised instructions for the failed quest .md step. Write them to the step envelope's Re-plan fenced YAML block."`
   - **Claude mode:** Dispatch re-plan subagent (tier from `models.claude_mode.planning` or `models.claude_mode.medium` fallback) with same context. Returns in-memory.
3. **Read re-plan output** — Expect: `revised_instructions`, `revised_code_block` (optional), `reasoning`, `confidence`.
4. **Re-execute** — Spawn execute-child with `revised_instructions` replacing the original step description (and `revised_code_block` replacing the original code block if present), plus all accumulated lessons.
5. **Pass:** Exit loop. Mark step passed. Checkpoint. Next step.
6. **Fail, retries remaining:** Loop back (next retry is also Retry 2+ tier).
7. **Fail, retries exhausted:** Mark step `failed`. Extract final lesson with `outcome: "exhausted"`. Mark quest `failed`. Exit to §7e.

The original quest `.md` on disk is **never** modified. Re-plan revisions live only in the `step-<sid>.md` step envelope's Re-plan fenced YAML block and the in-memory step structure for the current attempt.

Source: extracted from liang-quest-executor/SKILL.md § 7c. Tiered Retry Loop
