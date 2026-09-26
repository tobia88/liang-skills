# Failure Modes

Load when handling any failure or ambiguous error state.

- **Child process fails to spawn (Pi CLI invocation error included):** record the exact command in the lesson, mark the step failed, enter the retry loop. No mid-run prompt.
- **Child output malformed:** Treat as failure with `failure_type: "malformed_output"`.
- **Child timeout (Pi CLI / batch only):** Kill, failure with `failure_type: "timeout"`. Claude mode has no kill mechanism — the executor waits for the subagent to return.
- **Tier 1 VC fails inline:** Run VC repair rounds (`references/vc-verification.md § VC Repair Rounds`) — no step retry, the steps already passed. Still failing after the last round → mark quest `failed`, lesson `failure_type: "vc_failed"`.
- **Build/test log shows a known failure:** Classify with `liang-quest-core/scripts/failure_playbook.py` before retrying (SKILL.md §7c): `false_failure` passes the step, `retry` re-runs it for free (max 2), `blocker` fails the quest with `failure_type: "blocker"`, `hint` feeds the next attempt. New recurring failures get a rule in `failure-playbook.yaml`.
- **Tier 1 verify-child returns malformed result:** Treat as VC failure with `failure_type: "verify_malformed"`. Mark quest `failed`.
- **Tier 2 "no" answer in UAT batch §8a:** Quest status downgraded from `passed` to `failed`. Lesson extracted with `failure_type: "uat_rejected"`. Cascade-skip dependents not yet processed.
- **Lesson-only retry fails (retry 1):** Expected for conceptual failures. Automatic escalation to re-plan-child on retry 2.
- **Child reports a `plan_contradictions` entry with `blocks_step: true` (any `status`):** Failure with `failure_type: "plan_contradiction"`; enter the retry loop at the re-plan tier (`references/retry-protocol.md § Plan Contradiction`). Entries with `blocks_step: false` on a successful step are plan drift for the run report, not a failure. Never ask the user which fact is right.
- **Re-plan-child returns `resolvable: false` or low confidence on a deliverable-changing contradiction:** Step `failed` with `outcome: "needs_decision"`, quest `failed`, cascade-skip, entry in the run report's `## Decisions needed`. The run continues with the remaining eligible quests.
- **Child output contains a question addressed to the user** (in `implementation_summary`, `error_message`, or free text): treat as `failure_type: "malformed_output"` — the child contract has no question channel. The retry brief tells the child to decide from the step and quest purpose, or to report the blocker as a `plan_contradictions` entry.
- **Quest step says "stop and report if ...":** a planner-authored halt. When its condition holds, the child reports `status: "error"` with the finding; the executor marks the quest `failed` without retry (the condition is external, not a child mistake), cascade-skips, and carries the report into the run report. No dialogue.
- **Re-plan-child returns malformed output:** Treat as failure of the retry attempt. Continue retry loop until exhausted.
- **Quest `.md` file unreadable or missing `## Steps` section:** Skip quest with a warning. Mark `failed` with a lesson.
- **Quest `.md` Steps section parses to zero steps:** Skip quest with a warning. Mark `failed`.
- **Manifest write fails:** Warn, continue. Manifest is stale but execution is valid.
- **All quests skipped or failed:** Produce run report anyway.
- **Mid-run interruption:** Manifest state + `.run/` step envelopes enable crash recovery.
- **`project.yaml` missing or incomplete:** under `--no-confirm` or any headless run, stop with exit code 2; interactively, SKILL.md §2 bootstraps it first.
- **`pi` CLI not on PATH in default mode:** Hard-stop at §6 Mode Selection, before any manifest mutation, with guidance to rerun with `--claude`. Exit code 2 under `--no-confirm`.
- **`--no-confirm` fallback failure:** If a gate's documented default cannot be applied (e.g., crash-recovery Resume but state is unrecoverable), exit with code 3 and write a structured failure message to stderr.

Source: extracted from liang-quest-executor/SKILL.md Failure Modes section.
