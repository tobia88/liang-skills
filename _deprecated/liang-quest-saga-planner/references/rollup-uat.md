# Phase 5 — Deferred-UAT Rollup

Load when running --uat; source of truth for this mode.

**Generation is the executor's job; this mode only collects.** `liang-quest-executor` §8b
regenerates `uat-checklist.md` at each campaign root on every run (manual quests held out,
dependency-blocked skips, Tier-2 deferrals). This mode aggregates those per-campaign files into
one saga-ordered checklist. The saga context never re-derives UAT items from manifests, run
reports, or quest markdowns itself — a missing checklist is backfilled by dispatching §8b
standalone workers (step 1); a stale one is fixed by re-running the executor on that campaign.

Run when the user asks for the saga's deferred UAT / manual backlog, or after a sweep reports the
saga's headless portion done. Read-only against campaign folders; the single output is
`<saga-dir>/uat-checklist.md`.

1. **Collect.** For each campaign in `saga.yaml` (by recorded `campaign_id`), look for
   `<campaign-dir>/uat-checklist.md`:
   - **Present** → take its sections as-is (the executor wrote VCs verbatim and tagged
     `[MANUAL]`/`[AGENT]`).
   - **Absent, manifest all-passed** → campaign is clean; contributes nothing.
   - **Absent, manifest has unpassed quests** → the campaign ran before executor §8b existed (or
     never ran). **Backfill:** spawn one worker subagent per such campaign (model per § Model
     Routing), all in **parallel** — workers write disjoint campaign folders, so no waves needed.
     Brief each with: the campaign folder path, and the instruction to execute
     `liang-quest-executor/references/completion-flow.md` **§8b standalone-backfill** exactly —
     manifest is authoritative, latest run report by frontmatter `completed_at`, VCs verbatim from
     quest markdowns, write `uat-checklist.md` (or nothing if clean), no other writes. Verify each
     file exists on disk before consuming it. If a worker fails or the file is malformed, fall
     back to listing that campaign in a **"No checklist on disk"** section with its unpassed quest
     ids and the remedy (re-run the executor on it) — never reconstruct in this context.
2. **Order and group.** Campaigns in `campaign_depends_on` topological order, each campaign's
   sections in the order its checklist already has. Merge into numbered **sessions**: consecutive
   `[MANUAL]` blocks that one editor session can cover (respect any "one session covers quests
   X–Y" note carried in from the executor) collapse together — session grouping across campaigns
   is the one judgment this layer adds. Promote any blocker named by multiple campaigns (a missing
   asset, a broken tool) to a single **Blockers** section up top; verify it still exists on disk
   before listing.
3. **Write** `<saga-dir>/uat-checklist.md`: header with the saga's pass count and generation date;
   the sessions; a final **Wrap-up** section covering manifest status flips (user marks completed
   quests `passed`), `saga.yaml` status sync, and workspace-standard pre-submit steps (e.g. `p4
   reconcile`). Announce the path.
4. **Never** flip quest statuses, edit campaign folders, or execute anything from this mode. On
   completion suggest — never invoke — `skill:liang-quest-executor` for the `[AGENT]` sessions.

Regeneration is cheap and expected: as manual work lands and executors re-run, per-campaign
checklists shrink or disappear, and re-running `--uat` shrinks the rollup to match.
