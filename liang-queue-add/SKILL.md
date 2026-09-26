---
name: liang-queue-add
description: "Capture a pending task from the current discussion into the project's task queue (.liang/queue/YYYYMMDD_NN_TaskName/task.md) so it can run later without the user in the loop. Records only the goal, the user's decisions, the finish line and the boundaries — never a step-by-step plan — and saves any assets the discussion produced (picked textures, tuned values, reference code) into the task folder. Use when the user says \"queue this\", \"add to the queue\", \"save this as a pending task\", \"keep this for later\", or asks to park agreed work for an unattended run. Not for running tasks (liang-queue-sweep) or for planning a design that is still open."
---

# Liang Queue Add

Turn agreed work into a task folder a future session can run on its own. The task says what and why; the runner decides how.

## Core Contract

- **Capture, don't plan:** write Goal, Decisions, Done When and Boundaries. Leave the how to the runner; a stronger model on run day plans better than a script written today.
- **Decisions are the user's:** record picks, tuned values and rejected options exactly as the user settled them. Never add a decision the user did not make.
- **Assets survive the session:** copy every file the discussion produced and the task needs (images, tuned values, generator or preview code) into `assets/`. Scratch and temp folders do not survive a reboot.
- **Status starts at `pending`:** set `ready` only when the user says the task may run.
- **Queue files only:** create or update files under `.liang/queue/`. Touch nothing else in the project.
- **Format:** follow `references/task-format.md` exactly; `liang-queue-sweep` parses it.

## Activation

Run when the user asks to queue, park or save agreed work for later, or approves an existing queued task to run. Do not run while the goal is still under discussion; ask what remains open instead.

## Startup Flow

1. Find the project root and `.liang/queue/`. Create the folder if it is missing, and tell the user whether it is excluded from version control.
2. List existing task folders and pick the next `YYYYMMDD_NN` for today.
3. Draft the task from the discussion:
   - **Goal:** one to three sentences.
   - **Decisions:** every user call the runner must honour, with pointers into `assets/`.
   - **Done When:** checks the runner can observe and save as evidence.
   - **Boundaries:** limits specific to this task.
   - **`after`:** a dependency on another queued task, if any.
4. Show the draft and the asset list. Name any decision you inferred rather than heard, and ask the user to confirm or correct it.
5. On confirmation, write the folder and copy the assets in. Report the folder path and the status.
6. To mark a task ready later, change only its `status` line and confirm which task you changed.

## Boundaries

- Do not start the work itself, even partially.
- Do not write step lists, tool choices or implementation plans into `task.md`.
- Do not store secrets, credentials or personal data in a task or its assets.
- Do not edit files outside `.liang/queue/`.

## Failure Modes

- **Decision unclear:** ask one focused question; never pick for the user.
- **Asset missing** (the preview or file is already gone): say so, record in Decisions how to recreate it, and keep the task `pending`.
- **Task too big to check in one sweep:** propose splitting it into tasks linked with `after:`.
- **Queue folder tracked by version control:** warn the user before writing; queued tasks are local notes.

## Visual Tone

Plain and short. Show the draft `task.md` in a code block, then one line per asset. No tables unless comparing tasks.

## Relationship to Other Skills

- `liang-queue-sweep` runs `ready` tasks and writes the Log. This skill writes everything above the Log.

## Reference Files

- `references/task-format.md`: queue layout, `task.md` sections and fields, status values, log entry shape. Shared with `liang-queue-sweep`.
