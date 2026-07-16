# Phase 6 — Feature Walkthrough

Load when running --tour; source of truth for this mode.

**Generation is the executor's job; this mode only collects.** `liang-quest-executor` §8c writes
`walkthrough.md` at a campaign root — the tutorial covering **every** quest including passed ones
(how it works / what changed / where it lives / see-it-run blocks) — on demand only, never during
a completion flow. This mode aggregates those per-campaign tours into one saga-ordered walkthrough so the user
can learn what the saga built and exercise it feature by feature. The saga context never writes
tour content about a campaign itself.

Run when the user asks to be walked through what was built. Read-only against campaign folders;
the single output is `<saga-dir>/walkthrough.md`.

1. **Collect.** For each campaign in `saga.yaml`, look for `<campaign-dir>/walkthrough.md`:
   - **Present** → take it as-is.
   - **Absent** → spawn one §8c standalone worker per such campaign (model per § Model Routing,
     same chain as UAT-backfill workers), all in **parallel** — disjoint campaign folders. Brief
     each with: the campaign folder path, and the instruction to execute
     `liang-quest-executor/references/completion-flow.md` **§8c** exactly — manifest authoritative,
     latest run report by frontmatter `completed_at`, all quests covered including passed, verify
     named paths exist on disk, write `walkthrough.md`, no other writes. Verify each file exists
     before consuming; on worker failure list the campaign under **"No walkthrough on disk"** with
     the remedy — never reconstruct in this context.
   - A **stale** campaign walkthrough (quests changed since generation) is refreshed by deleting
     it and re-running `--tour`.
2. **Order and interleave.** Campaigns in `campaign_depends_on` topological order, each campaign's
   quest sections in the order its walkthrough already has. The one judgment this layer adds:
   where a tour stop is `[PENDING]`, point at the Phase 5 rollup session that unlocks it (never
   duplicate debt items); where a shared blocker gates several stops, note it once up front.
3. **Write** `<saga-dir>/walkthrough.md`: header with a one-paragraph saga summary, generation
   date, pass count; the campaign tours in order; a closing pointer to `uat-checklist.md` for the
   outstanding debt. Announce the path.
4. **Never** flip quest statuses, edit campaign folders, or execute anything from this mode.

`--uat` and `--tour` are companions: the checklist retires debt (checkbox items drive manifest
flips), the walkthrough teaches and exercises (its checkboxes are observation steps, never
verification records). Run both after a sweep: tour to learn, checklist to close out. For one
browsable page combining both, Phase 7 (`--handover`) renders them into `handover.html`.
