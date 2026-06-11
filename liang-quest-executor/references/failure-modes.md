# Failure Modes

Load when handling any failure or ambiguous error state.

- **Child process fails to spawn:** Report, mark step failed, enter retry loop.
- **Child output malformed:** Treat as failure with `failure_type: "malformed_output"`.
- **Child timeout (Pi CLI / batch only):** Kill, failure with `failure_type: "timeout"`. Claude mode has no kill mechanism — the executor waits for the subagent to return.
- **Tier 1 VC fails inline:** Mark quest `failed` (no step retry — the steps already passed). Extract a lesson with `failure_type: "vc_failed"`.
- **Tier 1 verify-child returns malformed result:** Treat as VC failure with `failure_type: "verify_malformed"`. Mark quest `failed`.
- **Tier 2 "no" answer in UAT batch §8a:** Quest status downgraded from `passed` to `failed`. Lesson extracted with `failure_type: "uat_rejected"`. Cascade-skip dependents not yet processed.
- **Lesson-only retry fails (retry 1):** Expected for conceptual failures. Automatic escalation to re-plan-child on retry 2.
- **Re-plan-child returns malformed output:** Treat as failure of the retry attempt. Continue retry loop until exhausted.
- **Quest `.md` file unreadable or missing `## Steps` section:** Skip quest with a warning. Mark `failed` with a lesson.
- **Quest `.md` Steps section parses to zero steps:** Skip quest with a warning. Mark `failed`.
- **Manifest write fails:** Warn, continue. Manifest is stale but execution is valid.
- **All quests skipped or failed:** Produce run report anyway.
- **Mid-run interruption:** Manifest state + `.run/` step envelopes enable crash recovery.
- **`project.yaml` missing or incomplete:** Stop with exit code 2.
- **Pi CLI invocation fails:** Report spawn error with exact command. Offer to retry or skip the step.
- **`pi` CLI not on PATH in default mode:** Hard-stop at §6 Mode Selection, before any manifest mutation, with guidance to rerun with `--claude`. Exit code 2 under `--no-confirm`.
- **`--no-confirm` fallback failure:** If a gate's documented default cannot be applied (e.g., crash-recovery Resume but state is unrecoverable), exit with code 3 and write a structured failure message to stderr.

Source: extracted from liang-quest-executor/SKILL.md Failure Modes section.
