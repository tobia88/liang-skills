# Queue Format

The files every `liang-queue-*` skill reads and writes. Change the format here only.

## Queue Layout

```text
.liang/queue/
  _rules.md                  optional: project rules for unattended runs, such as what cannot run at once and minimum models
  _runs/YYYYMMDD_HHMM.md     one summary per sweep
  .lock                      present only while a sweep runs
  YYYYMMDD_NN_TaskName/      one folder per task
    task.md
    assets/                  inputs the task needs: files, values, reference code
    evidence/                proof saved by whoever closed it: screenshots, logs, build output
  _done/                     closed tasks (done or dropped)
  _feedback/
    YYYYMMDD_NN_Slug.md      one file per feedback item
    assets/                  screenshots and files, named after their item: YYYYMMDD_NN_*
    _done/                   closed feedback items, with their assets
```

- `YYYYMMDD` is the day the item was created; `NN` counts up from `01` within that day, separately for tasks and feedback.
- Task names are PascalCase; feedback slugs are short and readable. No spaces in either.
- Name order is the default run order. Use `after:` for anything else; never rename to reorder.
- Status lives inside the file, never in the name. Only closed items move, into the matching `_done/`.

## task.md

```markdown
---
status: pending
after: none
from: none
created: 2026-09-26
---

# TaskName

## Goal
What the user wants and why, in one to three sentences.

## Decisions
The user's own calls the runner must honour: picks, tuned values, rejected options.
Point to files in assets/ for anything longer than a line.

## Done When
Observable checks that can be performed and saved as evidence.

## Boundaries
What the runner must not do for this task, beyond the project rules.

## Log
Appended by sweep and tidy. Leave empty when creating the task.
```

| Field | Values | Meaning |
| --- | --- | --- |
| `status` | `pending` | Captured, not approved to run. Sweep skips it. |
| | `ready` | Approved by the user. The next sweep runs it. |
| | `running` | A sweep is working on it now, or died while doing so. |
| | `blocked` | Stopped; the Log says why and what the user must do. |
| | `done` | Done When is met, with evidence. Moves to `_done/`. |
| | `dropped` | No longer wanted or superseded, with the user's agreement. Moves to `_done/`. |
| `after` | `none` or a task folder name | Run only after that task is `done`. |
| `from` | `none` or feedback item names | The feedback this task came from. |
| `created` | ISO date | Day the task was written. |

### What Belongs in a Task

- **Write:** the goal, the user's decisions, the finish line, the limits.
- **Leave out:** step lists, tool choices and implementation plans. The runner plans fresh with whatever model and tools it has on the day.
- **Exception:** a hard-won fact the runner cannot rediscover (a file-format quirk, a known trap) goes in Decisions as one line with its source.

### Log Entries

Appended, never rewritten. A sweep entry:

```markdown
### 2026-09-26 22:40 — sweep 20260926_2230
- Model: <model that ran it; if stepped up, from which and why>
- Did: <what changed, with paths>
- Judgement calls: <each decision made without the user, and why>
- Evidence: evidence/<file>
- Result: done | blocked — <reason and what the user must do>
- Next: <the next unfinished part, so a later session can resume>
```

A tidy entry:

```markdown
### 2026-09-26 23:50 — tidy
- Found: <what shows the task is done, dropped, or still partly open>
- Evidence: <paths, changelists, or evidence/<file>>
- Result: done | dropped | open — <reason>
```

## Feedback Item

```markdown
---
status: open
created: 2026-09-26
---

# Short title

## Feedback
The user's own words.

## Context
Where and when it was noticed: map, build or changelist, screen, what led to it.
Point to files in assets/.

## Resolution
Written when the item closes: what closed it, with evidence. Leave empty when capturing.
```

| Field | Values | Meaning |
| --- | --- | --- |
| `status` | `open` | Noted, not acted on. |
| | `promoted` | Turned into a task; Resolution names the task. Stays in `_feedback/` until that task is done. |
| | `done` | Addressed, with evidence. Moves to `_feedback/_done/`. |
| | `dropped` | No longer relevant, with the user's agreement. Moves to `_feedback/_done/`. |
| `created` | ISO date | Day the feedback was written. |

## Who Writes What

| Part | Written by |
| --- | --- |
| Task Goal, Decisions, Done When, Boundaries, `after`, `from` | `liang-queue-add` |
| Task `status` | `liang-queue-add` (`pending` → `ready` on the user's word), `liang-queue-sweep`, `liang-queue-tidy` |
| Task Log | `liang-queue-sweep`, `liang-queue-tidy` |
| Feedback title, Feedback, Context | `liang-queue-feedback` |
| Feedback `status` and Resolution | `liang-queue-add` (promoted), `liang-queue-sweep` (done via `from`), `liang-queue-tidy` |
