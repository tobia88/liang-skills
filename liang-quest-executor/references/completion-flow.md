# Completion Flow — §8–12 Full Protocol

Run after the quest queue is exhausted, in **every** execution mode (Pi CLI, `--claude`, `--batch`), in order. SKILL.md holds the summary; this file is the source of truth. Load it when the queue empties.

## 8. Run Report

Generate a Markdown run report at campaign root: `run-report-<timestamp>.md`, where `<timestamp>` is local time formatted `YYYY-MM-DD-HHMM` (e.g. `run-report-2026-06-11-0930.md`) so reports sort lexically. Include YAML front matter for machine-readable run data and a Markdown body for human review. Schema: `liang-quest-core/references/execution/run-report.md`. Style: `references/run-report-style.md`.

**Spend totals.** When usage was tracked (Pi CLI / batch children with pinned sessions), sum per-quest `usage` rollups into front-matter `totals.total_tokens` / `totals.total_cost_usd`, set `usage_tracked: true`, and render the `## Spend` body section (per-quest table + campaign total). Label the figures as **child-process spend** — the orchestrator's own session is not included. If any quest's usage is missing (harvest failure, `--claude` run, mixed-mode resume), list the gaps in `## Spend` rather than presenting an incomplete sum as complete; if nothing was tracked at all, set `usage_tracked: false` and omit the section.

## 8a. UAT Batch Prompt

After the run report, present all deferred Tier 2 VCs as a consolidated UAT checklist.

1. **Check the deferred UAT queue.** If empty, skip this section.
2. **Present the UAT Checklist** — Display:
   - Quest ID, quest title.
   - VC text (the yes/no question).
   - Files changed by the quest.
   - Step summaries (from `implementation_summary` of each step).
3. **For each item, ask:** "Does this quest's outcome satisfy this victory condition?" Yes / No.
4. **Record results.** Update the quest's step envelopes and the run report with per-VC yes/no answers.
5. **Handle failures.** If any VC receives "no":
   - Extract a lesson with `failure_type: "uat_rejected"`.
   - Update the quest's manifest status from `passed` to `failed`.
   - Cascade-skip any quests that depend on the now-failed quest (if they haven't been processed yet — typically too late at this stage, so note the cascade impact for the next run).
   - No re-plan loop post-UAT. The failure is recorded for the next run.

**Under `--no-confirm`:** skip the interactive UAT checklist. All deferred items remain `tier_2_deferred` in step envelopes and the run report. The parent process decides how to handle Tier 2 review.

## 9. Cleanup

- **Preserve:** `lessons.yaml`, `run-report-*.md`, `.run/<quest-id>/complete.yaml`, `.run/<quest-id>/step-*.md`, and any run metadata recording shared helper references/snapshots.
- **Optional cleanup:** Old-format scratch files from prior runs (if any). Ask before deleting.

**Under `--no-confirm`:** skip the cleanup prompt. Preserve all files.

## 10. VCS Artifact Policy

Apply the `vcs_artifacts.execution` value from `.liang/project.yaml` once after the
chain completes — canonical value semantics and write-back rule:
`liang-quest-core/references/project/project-yaml.md § VCS Artifact Policy (optional)`.

**Under `--no-confirm`:** if `"ask"` or absent, treat as `"ignore"` silently. Do not write the choice back.

## 11. Commit Suggestion

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

## 12. Open Prompt

Offer to:

- Open `run-report-<timestamp>.md` in the default browser.
- Open the campaign folder.
- Do nothing.

Do not open anything automatically.

Source: extracted from liang-quest-executor/SKILL.md § Completion Flow (§8–12, All Modes)
