# Batch Mode — Future Script Contract

**Status: the batch executor script is not yet shipped.** When `--batch` is invoked and no script exists at `references/batch-executor.*` in the skill directory, the executor falls back to Pi CLI mode with a one-line warning. This document specifies the contract the future script must honor.

When `--batch` is active and the script exists, the executor does not dispatch children directly. Instead it launches the batch executor script and monitors progress.

## Script Launch (when script exists)

1. Verify the batch executor script exists in the skill directory.
2. Launch as a background process, passing the campaign path.
3. Store the process handle for alive/dead detection.
4. Report: "Batch executor launched for `<campaign-title>`. Polling for progress..."

## Polling Loop

Poll at regular intervals (default: 30 seconds):

1. **Check process alive** — If exited, check exit code and proceed to Completion Detection.
2. **Read manifest** — Check `current_cycle` for each `in_progress` quest; use step-envelope mtime for freshness/elapsed polling instead of deprecated per-step timestamp fields.
3. **Scan step envelopes** — Check `.run/<quest-id>/` for new or updated `step-*.md` envelope files.
4. **Report progress** — Display active quest/step, elapsed time, completed/total, new step results, overall progress.

## Completion Detection

1. **Exit code 0:** Batch completed. Read final manifest. Report outcomes.
2. **Non-zero exit:** Batch failed/interrupted. Read manifest for partial results.
3. **All quests resolved but process still running:** Warn, continue waiting for exit.

After batch completion, proceed to §8 Run Report in SKILL.md. The run report reads `.run/` step envelopes identically for all execution modes.

## Model Routing

The batch script spawns Pi CLI children with the same model routing as default mode: `project.yaml.models.execution_by_difficulty[<quest.difficulty>]` for execute-children, `models.verify` for verify-children, `models.planning` for re-plan-children.
