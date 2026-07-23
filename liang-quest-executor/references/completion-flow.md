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

## 8b. UAT Checklist Artifact (all modes — including `--no-confirm`)

Regenerate `uat-checklist.md` at campaign root from the manifest and envelopes this run just wrote.
This is the campaign's live verification-debt artifact: §8a is a prompt that vanishes with the
session (and is skipped entirely under `--no-confirm`); this file is what persists.

Collect, in quest `depends_on` order:

1. **`manual: true` quests with `status != passed`** — tag `[MANUAL]`. Copy the quest markdown's
   `## Victory Conditions` checkboxes verbatim, plus any in-play observation checklist embedded in
   its steps (playtest checklists are the actual test items).
2. **Quests skipped with a dependency-shaped `skip_reason`** (`manual_dependency`,
   `dependency_failed:*`) — tag `[AGENT]`: re-dispatchable to this executor
   once the named blocker clears. State the blocker explicitly (the manual quest, the missing
   asset, the failed dependency).
3. **Tier-2 VCs still deferred after §8a** (under `--no-confirm`: all of them) — the VC rows plus
   the resolution path as recorded in the run report.

Per entry: quest id + title, relative link to the quest markdown (never duplicate step bodies),
the tag, the blocker if any, and the checkbox items. Header: campaign title, generation timestamp,
passed/total count, and the instruction to flip the quest's manifest `status:` to `passed` when
its items are done. If the collection is **empty, delete** any existing `uat-checklist.md` — the
file's presence is the signal that verification debt exists.

**Standalone backfill invocation.** §8b may also run detached from a completion flow, against a
campaign that already executed before this step existed — typically as a subagent spawned by
`liang-quest-saga-planner` Phase 5. With no fresh run in context, the sources are:

- `manifest.yaml` — authoritative on every quest's status, `manual` flag, and `skip_reason`;
- the **latest** run report (newest `run-report-*.md` by frontmatter `completed_at`, NOT by
  filename — stale duplicate reports exist) — for Tier-2 deferred VC rows and their resolution
  paths; on manifest/report disagreement, the manifest wins;
- the quest markdowns — for verbatim Victory Conditions and in-step observation checklists.

Same collection rules, same output rules (write at campaign root, or delete when nothing
qualifies), and no other writes — a backfill worker never touches the manifest, run reports, or
quest files.

Downstream: `liang-quest-saga-planner --uat` (Phase 5) collects these per-campaign files across a
saga and orders them by `campaign_depends_on`. Keep the format stable: `## ` section per quest,
`- [ ]` items, `[MANUAL]`/`[AGENT]` tags in the section heading.

## 8c. Feature Walkthrough Artifact (on demand only — never part of the completion flow)

Where §8b is the debt report (only what automation could NOT verify), the walkthrough is a
**tutorial**: **every quest in the campaign, passed ones included**, written to teach a human who
didn't watch the execution how each new system works, what changed and what got fixed along the
way, and how to exercise it. The stance is teacher-to-student ("here is what your codebase can do
now and how it does it"), never auditor ("here is where to verify my claims"). Generate
only when explicitly invoked standalone — typically as a worker spawned by
`liang-quest-saga-planner --tour` (Phase 6). Absence of a walkthrough signals nothing; do not
create one during a normal completion flow.

Sources — same rules as §8b standalone backfill: `manifest.yaml` authoritative on status; the
latest run report by frontmatter `completed_at` (manifest wins on disagreement); quest markdowns
for intent and steps; `lessons.yaml`, run-report deviation notes, and the `.run/<quest-id>/` step
envelopes (`implementation_summary`) for what deviated, what broke and got fixed mid-execution,
and judgment calls made; plus the live source/assets on disk — **read the implementation itself**,
not just confirm paths exist: the narrative below teaches mechanism, and that cannot be written
from file names (note drift instead of guessing).

Per quest, in `depends_on` order, a `## ` section: quest id + title + status marker in the heading
(`[DONE]` for `passed`, `[PENDING]` otherwise), then four blocks. **Link, never restate:** every
reference to verification debt is a plain link to the quest's `uat-checklist.md` section — never
copy, paraphrase, or summarize its checkbox items (an item-count teaser like "11 items covering
tabs, locks, …" is restating too). The two files must not drift apart because one quoted the
other. A `[PENDING]` quest's section stays short: what was built, current on-disk state, one link.

- **How it works** — a guided narrative that follows the data through the system in execution
  order, plain language, functions as waypoints: "a fight starts when `Init()` builds …; each
  action enters `SubmitPlayerSkill()`, which first …, then …". Explain the *why* behind the shape
  (ordering contracts, seams left for later campaigns, design intent from the quest markdown /
  brainstorm), not just the part names. Point at code (`path:line` anchors, verified on disk) —
  never paste multi-line excerpts; pasted code goes stale, pointers survive drift.
- **What changed** — before/after: what was deleted, replaced, or refactored; where execution
  deviated from the plan; bugs found and fixed mid-quest; judgment calls made. Sourced from the
  run report, `lessons.yaml`, and step `implementation_summary` fields. This is the "what's new /
  what got fixed" record — omit the block only when a quest genuinely changed nothing pre-existing
  (greenfield additions), and say so in one clause rather than leaving it silently absent.
- **Where it lives** — file/asset paths, verified to exist on disk.
- **See it run** — `- [ ]` steps that let the human *experience* the feature, then understand it:
  lead with doing (a console command, a PIE sequence, an editor inspection), follow with a
  directed reading path ("open `BeginTurn()` and notice the tick order — this is what c03 plugs
  into"). These are learning steps, not Victory Conditions — they never drive manifest flips, and
  re-verification checkboxes stay in `uat-checklist.md` only. **No audit steps:** greps that
  "confirm it's still clean" or check that a claim held are verification, not teaching — they
  don't belong here. If the feature can't be exercised yet, one sentence naming what unlocks it
  plus the checklist link — no preview of the checklist's items.

Header: campaign title, generation date, and a one-paragraph summary of the capability this
campaign added. Write `walkthrough.md` at campaign root; **no other writes** — never touch the
manifest, run reports, quest files, or `uat-checklist.md`.

Downstream: `liang-quest-saga-planner --tour` (Phase 6) collects these per-campaign files. Keep
the format stable: `## ` section per quest, status marker in the heading, the four named blocks.

## 9. Cleanup

- **Preserve:** `lessons.yaml`, `run-report-*.md`, `.run/<quest-id>/complete.yaml`, `.run/<quest-id>/step-*.md`, and any run metadata recording shared helper references/snapshots.
- **Optional cleanup:** Old-format scratch files from prior runs (if any). Ask before deleting.

**Under `--no-confirm`:** skip the cleanup prompt. Preserve all files.

## 10. VCS Artifact Policy

Apply the `vcs_artifacts.execution` value from `.liang/project.yaml` once after the
chain completes — canonical value semantics and write-back rule:
`liang-quest-core/references/project/project-yaml.md § VCS Artifact Policy (optional)`.

**Under `--no-confirm`:** if `"ask"` or absent, treat as `"ignore"` silently. Do not write the choice back.

## 10a. VCS Source Reconcile (all modes — including `--no-confirm`)

Skip when `.liang/project.yaml` is missing or its `vcs` is not `"perforce"`, or when this run wrote no step envelopes.

1. **Collect touched files** — union of `output.files_changed` across the step envelopes THIS run wrote (`.run/<quest-id>/step-*.md` of every quest processed this run — not envelopes left by earlier runs). Resolve relative paths against the workspace root. Drop anything under `.liang/` (planning/execution bookkeeping is never reconciled), anything with an `Intermediate`, `Binaries`, `Saved`, or `DerivedDataCache` path segment (build/derived output — compile-step children have been observed dumping the build log's rebuilt-file list into `files_changed`, which is not an edit list), and anything §Boundaries item 8 excludes (secrets, large binaries).
2. **Verify existence** — a collected path that does not exist on disk is suspect (build-log noise or a wrong path), and handing it to `p4 reconcile` would open the depot file **for delete**. Exclude missing paths from the reconcile; list them separately as "recorded but absent on disk — verify manually (deliberate deletion vs envelope noise)". Only reconcile a deletion when the envelope's `implementation_summary` explicitly says the child deleted that file.
3. **Nothing collected** → state "no source files to reconcile" and continue to §11.
4. **Reconcile, scoped** — run `p4 reconcile <file> <file> ...` with exactly the surviving list; this opens adds/edits in the default changelist. **NEVER run a bare or workspace-wide `p4 reconcile`** — the workspace may carry deliberate local drift (config edits, held-back deletions) that must not be opened for submit. **NEVER `p4 submit`, `p4 revert`, or any other Perforce write** beyond this one scoped reconcile.
5. **Report** — echo p4's output, and append the opened-file list to this run's report under a `## Reconcile` body section (front-matter keys stay VCS-neutral per Boundaries item 9). If `p4` is missing from PATH or exits non-zero, print the file list with a ready-to-paste `p4 reconcile <files>` command for manual handling and continue — a reconcile failure never changes quest statuses or the exit code.

Idempotent by design: when a wrapper (e.g. `liang-quest-batch-sweep`'s `sweep-afk.py`) reconciles again afterwards, the second pass finds the files already opened and no-ops.

**Under `--no-confirm`:** run without prompting — the AFK path is exactly where automatic reconcile matters most.

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
