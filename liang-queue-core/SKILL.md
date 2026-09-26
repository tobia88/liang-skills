---
name: liang-queue-core
description: "Shared contract of the liang-queue-* family: where queue tasks and feedback live, their file format and status values, who may write what, and the limits every queue skill obeys. Read by liang-queue-add, liang-queue-feedback, liang-queue-sweep and liang-queue-tidy; not a task to run on its own. Load it directly only to answer questions about the queue format or to change it."
---

# Liang Queue Core

What the queue skills agree on, so each of them can stay short and leave the how to the model running it.

## The Family

| Skill | Job |
| --- | --- |
| `liang-queue-feedback` | Write down what the user noticed, in their words. |
| `liang-queue-add` | Turn agreed work, or feedback, into a task the user can approve. |
| `liang-queue-sweep` | Run approved tasks unattended and leave evidence. |
| `liang-queue-tidy` | Find tasks and feedback already done or no longer relevant, and close them. |

## Rules for Every Queue Skill

- **Format:** read and write queue files exactly as `references/format.md` describes, and only the parts it assigns to you.
- **The user's words are fixed:** never rewrite a task's Goal, Decisions, Done When or Boundaries, or a feedback item's text. Add to the Log or Resolution instead.
- **Close, never delete:** a finished or unwanted item moves to its `_done/` folder with the reason written down.
- **Stay in the queue:** only a sweep's task run changes project files. Every other queue skill writes only under `.liang/queue/`.
- **Local notes:** queue files hold no secrets, credentials or personal data. If `.liang/queue/` is tracked by version control, warn the user before writing.
- **Project rules win:** the project's agent instructions and `.liang/queue/_rules.md` come first; a task's Boundaries add to them and never loosen them.

## Reference Files

- `references/format.md`: queue layout, `task.md` and feedback formats, status values, Log entry shapes, and who writes which part.
