---
name: liang-queue-tidy
description: "Check open feedback and unfinished queue tasks against the project as it is now, find the ones already done or no longer relevant, and close them with evidence once the user agrees. Use when the user says \"tidy the queue\", \"clean up feedback\", \"what's already done\", \"is X still open\", \"prune the queue\", or before a sweep so finished work is not redone. Not for doing the work (liang-queue-sweep) or capturing it (liang-queue-add, liang-queue-feedback)."
---

# Liang Queue Tidy

Keep the queue honest: nothing already done waits to be redone, and nothing still open is closed by mistake.

## Contract

- **Family rules:** follow `../liang-queue-core/SKILL.md` and its `references/format.md`.
- **Scope:** open or promoted feedback, and tasks that are not closed. The user may narrow it to feedback, tasks, or named items. Leave `running` tasks and a locked queue alone.
- **Look, don't touch:** judge each item against the project as it is now, by whatever means suits it. Change nothing in the project to find out.
- **Evidence behind every verdict:** say what shows an item is done, partly done, still open, or no longer relevant. When the proof is out of reach, say so instead of guessing.
- **Report, then close:** show the verdicts first. Close items only after the user agrees; an item partly done stays open with a note on what is left.

## Relationship to Other Skills

- `liang-queue-sweep` does the work; tidy only records what is already true.
- `liang-queue-add` and `liang-queue-feedback` write the items tidy checks.
