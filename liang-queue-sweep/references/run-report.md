# Run Report

One file per sweep: `.liang/queue/_runs/YYYYMMDD_HHMM.md`.

```markdown
# Sweep 20260926_2230

Started 22:30, ended 01:12. Done 2 · Blocked 1 · Waiting 1 · Skipped 1 (pending)

## Needs you
- 20260926_02_ForgeOutsideTableGrow: blocked — <what the user must do>
- 20260926_04_ForgeTableDressing: waiting on 20260926_02_ForgeOutsideTableGrow
- Suggested `after:` for 20260926_03_ForgeSparks: 20260926_01_ForgeReveal — <why>

## Plan
| Task | Runs | Model | Why |
| --- | --- | --- | --- |
| 20260926_01_ForgeReveal | first, alone | sonnet | builds C++ |
| 20260926_03_ForgeSparks | after 01 (inferred) | sonnet | needs 01's reveal actor |
| 20260926_05_ForgeNotes | alongside 01 | haiku | text only, no shared files |

## Tasks
| Task | Result | Model | Evidence | Judgement calls |
| --- | --- | --- | --- | --- |
| 20260926_01_ForgeReveal | done | sonnet | evidence/sim_rise_bbu.png | 2, see Log |
| 20260926_05_ForgeNotes | done | sonnet (stepped up from haiku) | evidence/notes_diff.txt | 1, see Log |

## Changed paths
Per task, for a named-path version-control reconcile.
- 20260926_01_ForgeReveal: <paths>
```

## Push Message

Three lines at most, for a phone:

```text
Queue sweep done: 2 done, 1 blocked.
Needs you: ForgeOutsideTableGrow — <one-line reason>.
Report: .liang/queue/_runs/20260926_2230.md
```
