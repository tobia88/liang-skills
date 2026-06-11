---
description: Audit/refine the liang-quest-* and liang-brainstorm-* skill families against criteria C1-C6. audit = read-only report, refine = tiered apply, enhance = named behavioral change.
argument-hint: "[audit|refine|enhance \"<goal>\"] [skill-glob]"
---

# /goal — skill family maintenance

Arguments: `$ARGUMENTS`. First token is the mode (default `audit`); remainder is the
target glob (default: `liang-quest-*` and `liang-brainstorm-*`).

At activation, read these from the liang-skills root. **Stop and report failure if
any read fails.**

- `.liang/goal/criteria.md` — the invariants (C1–C6), edit classes, and findings
  schema. Sole source of what to check; never invent checks beyond it.
- `.liang/goal/drift-ledger.md` — intentional divergences. Anything matching a
  ledger entry is not a finding; cite the dv ID when skipping.

## Flow

1. **Preflight (zero model tokens).** Run
   `python .liang/goal/preflight.py --targets "<glob>"`. It writes `findings.yaml`
   into a fresh run dir under `.liang/goal/runs/`. Exit 2 = config error: stop and
   report. Do not re-derive in context anything the script already checked.
   Then record a tree snapshot: `git status --porcelain` plus the mtimes of all
   scanned files. If any scanned file changed within the last 5 minutes, warn that
   another writer may be active — continue in audit mode, but do not let
   refine/enhance apply anything without explicit user confirmation.
2. **Judgment sweep.** For each criterion preflight flagged `judgment-needed`
   (C1 restatement-vs-orchestration, C3 delegation paths, C5 conventions), spawn one
   child per dimension — Claude harness: subagent; pi harness: `pi --print`
   sub-process. Build each child's input from `.liang/goal/envelopes/check-brief.yaml`
   with ONLY the flagged excerpts and the relevant criteria section — never whole
   SKILL.md bodies. Child model: `project.yaml models.verify` if the current harness
   can run it, else the harness default.
3. **Classify.** Tag every finding `mechanical` / `structural` / `behavioral` per
   criteria.md §C6. Dedup against the drift ledger; move suppressed findings to the
   `suppressed` list with their dv ID.
4. **Apply** (refine mode only). First re-take the tree snapshot and diff it
   against preflight's: if anything changed that this run did not change itself,
   STOP and report — never apply into a moving tree.
   - `mechanical` — apply directly; list each applied edit in the report.
   - `structural` — have children draft the diffs (model:
     `models.execution_by_difficulty.medium`, same harness fallback rule), then
     present ALL diffs for one batch approve/reject. Apply lockstep, all-or-nothing.
     Hash-check each target against its preflight-time state; refuse stale files.
   - `behavioral` — refuse; report the finding with a note that it requires
     `enhance "<goal>"`.
5. **Verify.** Re-run preflight on touched files plus a scoped re-check of the
   criteria the changeset addressed. Clean state (exit 0) required; otherwise report
   exactly what remains.
6. **Report.** Write `report.md` into the run dir — markdown only (headings, tables,
   text badges; run-report style): findings keyed by criterion ID with severity,
   class, and applied/pending/refused status. Summarize counts in chat.

## Boundaries

- `audit` writes nothing outside the run dir.
- Never change skill behavior outside `enhance`, and there only edits serving the
  named goal.
- Never edit files outside the target glob plus `liang-*-core` references and
  `liang-quest-core/references/project/project-yaml.md` (for additive optional-key
  documentation).
- Never add or remove drift-ledger entries — propose candidates as `open-question`
  findings instead.
- Never restate criteria into this command file — criteria.md is the source of truth.
