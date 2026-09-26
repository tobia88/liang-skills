---
name: liang-queue-add
description: "Capture a pending task from the current discussion, or from feedback items, into the project's task queue (.liang/queue/YYYYMMDD_NN_TaskName/task.md) so it can run later without the user in the loop. Records only the goal, the user's decisions, the finish line and the boundaries — never a step-by-step plan — and saves any assets the discussion produced (picked textures, tuned values, reference code) into the task folder. Use when the user says \"queue this\", \"add to the queue\", \"save this as a pending task\", \"keep this for later\", \"promote this feedback\", or asks to park agreed work for an unattended run. Not for running tasks (liang-queue-sweep), raw notes (liang-queue-feedback), or planning a design that is still open."
---

# Liang Queue Add

Turn agreed work into a task folder a future session can run on its own. The task says what and why; the runner decides how.

## Core Contract

- **Family rules:** follow `../liang-queue-core/SKILL.md` and its `references/format.md`; sweep and tidy parse what you write.
- **Capture, don't plan:** write Goal, Decisions, Done When and Boundaries. Leave the how to the runner; a stronger model on run day plans better than a script written today.
- **Decisions are the user's:** record picks, tuned values and rejected options exactly as the user settled them. Never add a decision the user did not make.
- **Assets survive the session:** copy every file the discussion produced and the task needs (images, tuned values, generator or preview code) into `assets/`. Scratch and temp folders do not survive a reboot.
- **From feedback:** when the task grows out of feedback items, list them in `from:` and mark each one `promoted`, naming the task in its Resolution.
- **Status starts at `pending`:** set `ready` only when the user says the task may run.

## Activation

Run when the user asks to queue, park or save agreed work for later, promotes feedback to a task, or approves an existing queued task to run. Do not run while the goal is still under discussion; ask what remains open instead.

## Startup Flow

1. Find `.liang/queue/`, creating it if missing, and pick the next `YYYYMMDD_NN` for today.
2. Draft the task from the discussion or the feedback: Goal, Decisions, Done When, Boundaries, and `after:` if it depends on another task.
3. Show the draft and the asset list. Name any decision you inferred rather than heard, and ask the user to confirm or correct it.
4. On confirmation, write the folder, copy the assets in, update any source feedback, and report the path and status.
5. To mark a task ready later, or to accept an `after:` a sweep suggested, change only that line and confirm which task you changed.

## Boundaries

- Do not start the work itself, even partially.
- Do not write step lists, tool choices or implementation plans into `task.md`.

## Failure Modes

- **Decision unclear:** ask one focused question; never pick for the user.
- **Asset missing** (the preview or file is already gone): say so, record in Decisions how to recreate it, and keep the task `pending`.
- **Task too big to check in one sweep:** propose splitting it into tasks linked with `after:`.

## Visual Tone

Plain and short. Show the draft `task.md` in a code block, then one line per asset. No tables unless comparing tasks.

## Relationship to Other Skills

- `liang-queue-core` owns the format and the family rules.
- `liang-queue-feedback` writes the notes this skill can promote.
- `liang-queue-sweep` runs `ready` tasks and writes the Log. This skill writes everything above the Log.
