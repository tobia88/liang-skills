# Run Report

Each sweep leaves `.liang/queue/_runs/YYYYMMDD_HHMM/` holding `report.md`, `sweep-data.js` and `dashboard.html`.

## Dashboard

The user's main way to follow a sweep and review it afterwards. Build it as a page, not a fixed template: start from the newest earlier sweep's `dashboard.html` (or `../assets/dashboard.html` for a project's first sweep), keep what works, and improve what this sweep's data calls for.

The page must:
- **Answer, in this order of prominence:** what needs the user; what is running, stalled or waiting; for each task, did every check pass and where is the proof; which decisions were made without the user.
- **Layer:** a summary is always visible; one task or view is open at a time; long material (evidence, paths, notes) sits behind a tab or a click. Nothing is shown in full by default when a count or one line will do.
- **Read `sweep-data.js`, and nothing else, for data.** Never paste data into the HTML. While `running` is true, re-load that script about every 30 seconds without losing the user's place or typing.
- **Open from disk** (`file://`) with no server and no build step; web fonts may fall back offline.
- **Keep review marks in browser storage:** done ticks on "needs you" items, approve / revisit per decision with a note, and a button that copies every revisit as a `liang-queue-feedback` item.
- **Look like a JRPG quest board:** menu windows, quests, objectives, a debrief. The theme lives in the frame and labels; task names, paths and log text stay plain and readable.

Check the page renders with the current data (a headless-browser screenshot is enough) before the sweep's first task starts, and again at wrap-up.

## report.md

The plain-text record, for reading without a browser.

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
Board: .liang/queue/_runs/20260926_2230/dashboard.html
```
