# Task Format

The contract between `liang-queue-add` (writer) and `liang-queue-sweep` (runner).
Both skills read this file; change it here only.

## Queue Layout

```text
.liang/queue/
  _rules.md                  optional: project rules for unattended runs
  _runs/YYYYMMDD_HHMM.md     one summary per sweep, written by the runner
  .lock                      present only while a sweep runs
  YYYYMMDD_NN_TaskName/      one folder per task
    task.md
    assets/                  inputs the task needs: files, values, reference code
    evidence/                proof the runner saved: screenshots, logs, build output
  _done/                     finished tasks, moved here by the runner
```

- `YYYYMMDD` is the day the task was created; `NN` counts up from `01` within that day.
- `TaskName` is PascalCase, no spaces.
- Name order is the default run order. Use `after:` for anything else; never rename a folder to reorder it.
- Status lives inside `task.md`, never in the folder name. Only `done` tasks move, into `_done/`.

## task.md

```markdown
---
status: pending
after: none
created: 2026-09-26
---

# TaskName

## Goal
What the user wants and why, in one to three sentences.

## Decisions
The user's own calls the runner must honour: picks, tuned values, rejected options.
Point to files in assets/ for anything longer than a line.

## Done When
Observable checks the runner can perform and save as evidence.

## Boundaries
What the runner must not do for this task, beyond the project rules.

## Log
Written by the runner. Leave empty when creating the task.
```

## Fields

| Field | Values | Meaning |
| --- | --- | --- |
| `status` | `pending` | Captured, not approved to run. The runner skips it. |
| | `ready` | Approved by the user. The next sweep runs it. |
| | `running` | A sweep is working on it now, or died while doing so. |
| | `blocked` | Stopped; the Log says why and what the user must do. |
| | `done` | Done When is met; the runner moves the folder to `_done/`. |
| `after` | `none` or a task folder name | Run only after that task is `done`. |
| `created` | ISO date | Day the task was written. |

## What Belongs in a Task

- **Write:** the goal, the user's decisions, the finish line, the limits.
- **Leave out:** step lists, tool choices, and implementation plans. The runner plans the work fresh with whatever model and tools it has on the day; a scripted plan ages as models improve.
- **Exception:** a hard-won fact the runner cannot rediscover (a file-format quirk, a known trap) goes in Decisions as one line with its source.

## Log Entries

The runner appends, never rewrites:

```markdown
### 2026-09-26 22:40 — sweep 20260926_2230
- Did: <what changed, with paths>
- Judgement calls: <each decision the runner made on its own, and why>
- Evidence: evidence/<file>
- Result: done | blocked — <reason and what the user must do>
- Next: <the next unfinished part, so a later session can resume>
```
