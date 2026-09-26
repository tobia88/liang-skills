# Child Brief

Hand this to the child session for each task, followed by the task folder path.

---

You are running one queued task while the user is away. Nobody will answer questions until the sweep ends.

**Read first:** the project's agent instructions (CLAUDE.md, AGENTS.md), `.liang/queue/_rules.md` if present, then everything in the task folder. If the Log has entries, resume from the last `Next:` line.

**Your job:** meet every Done When check within the Decisions and Boundaries. Plan the work yourself; the task deliberately gives no steps.

**Rules:**
- Honour every Decision exactly. They are the user's calls, not suggestions.
- When you face a choice the task does not settle, pick the option most consistent with the Goal and Decisions, and record it as a judgement call.
- Stop and mark the task `blocked` rather than do anything irreversible, anything that reaches outside the machine, or anything a Boundary or project rule forbids.
- Never discard or overwrite the user's uncommitted work. If you need a file they have changed, block.
- Save proof for each Done When check in `evidence/` (screenshots, logs, build output) and name each file after its check.

**Finish:** append one Log entry to `task.md` in the shape given by the task format, including `Next:` if anything is unfinished. Set `status` to `done` only if every check passed with evidence; otherwise `blocked`, with what the user must do.
