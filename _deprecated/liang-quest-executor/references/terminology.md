# Executor Terminology

Glossary for `liang-quest-executor`. Load when a term's exact meaning matters.

- `Run` — a single invocation of the Executor against a campaign. Produces a run report.
- `Step` — one item from a quest's `## Steps` section; the atomic unit of execution.
- `Step envelope` — executor-generated `step-<sid>.md` transport/ledger file under `.run/<quest-id>/`; children read/write its fenced YAML blocks, but the source step remains in the quest `.md`.
- `Execute-child` — a child process that implements one step (Pi sub-invocation, Claude subagent, or batch worker).
- `Verify-child` — a child process that verifies a quest's Tier 1 VC (only invoked when pattern-matching can't resolve the VC mechanically).
- `Re-plan-child` — a child process that invokes the planning model to produce revised step instructions given failure context.
- `Lesson` — a structured failure record extracted on step failure, appended to `<campaign-root>/lessons.yaml` (append-only, lives next to `manifest.yaml`).
- `.run/` — per-run ledger for child I/O, completion markers, and step envelopes. It may reference shared helpers, but it is not the canonical home for reusable executor tooling.
- `Cascade skip` — marking downstream quests as `skipped` when a dependency quest fails.
- `Checkpoint` — VCS-neutral save point after each successful step.
- `Pi CLI mode` — default execution mode; spawns `pi --model <model>` sub-invocations with file I/O.
- `Claude mode` — alternative execution mode activated by `--claude`; dispatches Claude Code Agent subagents with in-memory I/O. Tier mapping from `models.claude_mode`; see `project-yaml.md` for default values when the block or key is absent.
- `Batch mode` — alternative execution mode activated by `--batch`; launches a deterministic batch executor script and polls for progress. Not yet shipped — falls back to Pi CLI with a warning until the batch script ships.
- `Tiered retry` — retry escalation: lesson-only first (retry 1), re-plan-child on subsequent failures (retry 2+).
- `Tier 1 VC` — a victory condition the executor can verify mechanically (file existence, grep, structural check).
- `Tier 2 VC` — a victory condition that requires judgment; deferred to the post-run UAT batch prompt.
- `Deferred UAT queue` — list of Tier 2 VCs collected during the chain, presented as a consolidated checklist after the run report.

Source: extracted from liang-quest-executor/SKILL.md Terminology section.
