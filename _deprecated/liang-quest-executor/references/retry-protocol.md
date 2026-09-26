# Tiered Retry Protocol (§7c detail)

Full protocol for the step-failure retry loop. SKILL.md §7c holds the summary; this file is the source of truth for retry payloads and lesson fields. Load on first step failure. Bounded by `max_step_retries` (default: 3).

## Known-Failure Playbook (before every retry)

Run `python <skills-root>/liang-quest-core/scripts/failure_playbook.py <logs>` on the build/test logs the failed attempt wrote under `.run/<quest-id>/`. It prints `{verdict, matches, unexplained}`:

| Verdict | Action | Counts toward `max_step_retries` |
|---|---|---|
| `false_failure` | Step succeeded; record `playbook: [rule ids]` in the envelope Output | — |
| `retry` | Re-run the unchanged step (at most 2 free re-runs per step) | No |
| `blocker` | Fail the quest, `failure_type: "blocker"`, rule note in the lesson and run report | — |
| `hint` | Add the rule notes to `accumulated_lessons`, continue below | Yes |
| `unknown` / `clean` | Continue below | Yes |

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
   - **Pi CLI mode:** `pi --model <planning-model> --session .run/<quest-id>/sessions/replan-<sid>-a<n>.jsonl -p "Read the failed step envelope at .run/<quest-id>/step-<sid>.md and lessons.yaml. Produce revised instructions for the failed quest .md step. Write them to the step envelope's Re-plan fenced YAML block."`
   - **Claude mode:** Dispatch re-plan subagent (tier from `models.claude_mode.planning`; default per `liang-quest-core/references/project/project-yaml.md` § Model Routing Extensions) with same context. Returns in-memory.
3. **Read re-plan output** — Expect: `revised_instructions`, `revised_code_block` (optional), `reasoning`, `confidence`.
4. **Re-execute** — Spawn execute-child with `revised_instructions` replacing the original step description (and `revised_code_block` replacing the original code block if present), plus all accumulated lessons.
5. **Pass:** Exit loop. Mark step passed. Checkpoint. Next step.
6. **Fail, retries remaining:** Loop back (next retry is also Retry 2+ tier).
7. **Fail, retries exhausted:** Mark step `failed`. Extract final lesson with `outcome: "exhausted"`. Mark quest `failed`. Exit to §7e.

## Plan Contradiction — Straight to Re-Plan

Triggered when an execute-child returns any `plan_contradictions` entry with `blocks_step: true`, regardless of its `status` (entries with `blocks_step: false` on a successful step are recorded as drift and do not trigger this). The step's stated facts (counts, paths, regexes, measured values, file layout) do not match the workspace; re-running the unchanged step is pointless, so the lesson-only tier is skipped.

1. **Extract lesson** — Append with `retry_tier: "replan"`, `failure_type: "plan_contradiction"`, `error_summary` = the contradiction list rendered one per line (`claimed` vs `observed` with `evidence`). This attempt counts toward `max_step_retries`.
2. **Spawn re-plan-child** exactly as in Retry 2+, with `failure_context.failure_type: "plan_contradiction"` and `failure_context.plan_contradictions` carrying the list verbatim. The child's brief: decide each contradiction from the quest's `## Purpose`, the campaign `plan.md` decision summary, and the evidence; produce `revised_instructions` that replace the false facts with the observed ones.
3. **Read re-plan output** — If `resolvable: false`, or `confidence: "low"` on a contradiction that changes what the quest delivers (a count of deliverables, a file the quest overwrites, a public name), do **not** re-execute: mark the step `failed` with `outcome: "needs_decision"`, mark the quest `failed`, cascade-skip dependents, and queue every unresolved contradiction plus the child's `reasoning` for the run report's `## Decisions needed`. Otherwise re-execute with the revised content as in Retry 2+ step 4.
4. **Later attempts** on the same step follow the normal Retry 2+ loop.

The executor never resolves a contradiction by asking the user (SKILL.md Boundaries 18) and never files the work as an extra step (Boundaries 19). Earlier steps that already wrote the false facts to disk (a doc, a constant) are the re-plan-child's to address inside the revised instructions of the current step, when the quest's purpose covers those files; otherwise they become a `## Decisions needed` entry.

The original quest `.md` on disk is **never** modified. Re-plan revisions live only in the `step-<sid>.md` step envelope's Re-plan fenced YAML block and the in-memory step structure for the current attempt.

Source: extracted from liang-quest-executor/SKILL.md § 7c. Tiered Retry Loop
