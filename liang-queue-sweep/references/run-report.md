# Run Report

One file per sweep: `.liang/queue/_runs/YYYYMMDD_HHMM.md`.

```markdown
# Sweep 20260926_2230

Started 22:30, ended 01:12. Done 2 · Blocked 1 · Skipped 1 (pending)

## Needs you
- 20260926_02_ForgeOutsideTableGrow: blocked — <what the user must do>

## Tasks
| Task | Result | Evidence | Judgement calls |
| --- | --- | --- | --- |
| 20260926_01_ForgeReveal | done | evidence/sim_rise_bbu.png | 2, see Log |

## Changed paths
- <every path touched, for a named-path version-control reconcile>
```

## Push Message

Three lines at most, for a phone:

```text
Queue sweep done: 2 done, 1 blocked.
Needs you: ForgeOutsideTableGrow — <one-line reason>.
Report: .liang/queue/_runs/20260926_2230.md
```
