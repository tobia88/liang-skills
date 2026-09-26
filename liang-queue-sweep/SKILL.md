---
name: liang-queue-sweep
description: "Run the project's ready tasks from .liang/queue/ unattended: pre-flight check and a run plan (order, what runs together, model per task), one fresh child session per task, judgement calls logged instead of asked, evidence saved, a run summary written and pushed to the user. Also --check (pre-flight only) and --status (list tasks). Use when the user says \"sweep the queue\", \"run the queue\", \"go queue\", \"run my pending tasks\", is about to go AFK, or starts it headless. Not for capturing tasks (liang-queue-add) or closing work already done (liang-queue-tidy)."
---

# Liang Queue Sweep

Work through the queue while the user is away, and leave a record they can review in minutes.

## Core Contract

- **Only `ready` runs:** skip every other status. The user's "go" for this sweep approves every `ready` task, and nothing else.
- **Plan first:** decide order, what runs together and each task's model per `references/run-plan.md`. No task runs before its `after:` task, or a dependency the plan found, is `done`.
- **One child session per task:** give each task a fresh context holding the task folder, the project rules and `references/child-brief.md`. The orchestrator only plans, dispatches, reads the Log and writes the run summary. Without child sessions, run tasks one by one on the default model and re-read only the task folder at each start.
- **Decide, don't ask:** the user is away. Make each judgement call, record it and its reason in the Log, and continue.
- **Stop only for:** an action that is irreversible or reaches outside the machine, a hard blocker, or a Boundary. Mark the task `blocked` with what the user must do, then continue with tasks that do not depend on it.
- **Project rules first:** read the project's agent instructions (CLAUDE.md, AGENTS.md) and `.liang/queue/_rules.md` before anything else.
- **Evidence or it didn't happen:** a task is `done` only when every Done When check passed and its proof is saved in `evidence/`.
- **Family rules:** follow `../liang-queue-core/SKILL.md` and its `references/format.md`.

## Activation

- `liang-queue-sweep`: pre-flight, then run.
- `liang-queue-sweep --check`: pre-flight only; report what would block.
- `liang-queue-sweep --status`: list tasks with status, `after` and the last Log result, plus the count of open feedback. Change nothing.

Headless start, without an open chat, from the project root:

```bash
claude -p "/liang-queue-sweep"
```

With pi, pass the same request as the prompt. Either can also start from a scheduled task.

## Startup Flow

1. **Lock:** if `.liang/queue/.lock` exists and is younger than 12 hours, stop and report its owner and time. Otherwise write it with the time and session id.
2. **Pre-flight**, for every runnable task:
   - Read the project rules and the whole `task.md`.
   - Confirm its assets exist.
   - Confirm the tools it needs are available and not held by another process or session: apps, simulators, build tools, version-control access.
   - List anything that needs the user's hands.
   - Make the run plan.
   - In `--check` mode, report the plan and what would block, and stop here.
3. **Run**, per the plan:
   - Set `status: running` and dispatch the child session on the planned model.
   - The child plans and does the work, saves evidence and appends one Log entry.
   - Read the entry. Set `done` and move the folder to `_done/`, or set `blocked`.
   - When a task is `done`, close the feedback named in its `from:` as `done`, pointing its Resolution at the task.
4. **Resume:** each task found `running` at startup was left by a sweep that died. Continue it from the Log's `Next:` line; do not start it over.
5. **Wrap up:**
   - Write `_runs/YYYYMMDD_HHMM.md` per `references/run-report.md`.
   - Remove the lock.
   - Push a short summary to the user: done, blocked, and what needs them. Send it the moment a task blocks, too, if a push channel exists.

## Boundaries

- Do not publish, submit, push, deploy, send messages or spend money.
- Do not delete user data. Do not revert, overwrite or discard the user's uncommitted work; if a task needs a file the user has changed, mark it `blocked`.
- When reconciling version control after a run, name the changed paths; never reconcile the whole workspace.
- Do not run `pending` tasks, even if they look finished.

## Failure Modes

- **Pre-flight fails:** mark the affected tasks `blocked` with the fix, then run the rest.
- **Check fails after the work:** try another approach within the task's Boundaries, stepping up the model once per `references/run-plan.md`. When out of ideas, mark `blocked` with what was tried.
- **A child needs what the plan kept from it** (a build, the editor, version control): it stops and logs why; re-run it in sequence with the tasks that use the same thing.
- **Child session dies or runs out of context:** the task stays `running`; resume from `Next:` in a new child.
- **A task is far slower than expected:** stop it, log progress and `Next:`, mark `blocked` with "needs more time", and move on.
- **Lock held by a live sweep:** stop without touching anything.

## Visual Tone

Terse, scannable, phone-friendly. The run summary leads with counts (done / blocked / waiting / skipped), then "needs you" items, then one line per task.

## Relationship to Other Skills

- `liang-queue-core` owns the format and the family rules.
- `liang-queue-add` writes tasks; `liang-queue-tidy` closes ones already done before a sweep reaches them.

## Reference Files

- `references/run-plan.md`: how to plan order, what runs together, and the model per task.
- `references/child-brief.md`: the brief handed to each task's child session.
- `references/run-report.md`: the `_runs/` summary shape and the push message.
- `../liang-queue-core/references/format.md`: queue layout, task and feedback formats.
