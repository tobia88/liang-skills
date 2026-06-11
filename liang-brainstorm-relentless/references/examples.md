# Interaction Formats — Verbatim Examples

Load before producing each of these interactions for the first time in a session. These are the canonical formats; adapt content, keep structure.

## Opening Question

```text
Opening Scout:
- Current folder appears to be a Pi/coding-agent workspace.
- Relevant top-level paths noticed: README.md, docs/, .pi/
- Avoided secrets, dependency folders, build outputs, and old reports.

Detected Lens:
Skill Creation + Software Project Planning

Question:
Which planning lens should drive this session?

A. Skill Creation — focus on trigger behavior, interaction rules, outputs, boundaries, and failure modes.
B. Software Project — focus on users, architecture context, constraints, maintainability, and delivery decisions.
C. Game Dev — focus on player fantasy, core loop, production scope, platform, and playtest criteria.
D. General Project — focus on goals, decisions, risks, and next actions.

Recommended:
A — your initial idea appears to be a reusable skill design.

Tradeoff:
It may under-emphasize broader software architecture unless we deliberately include it.

Confidence:
Medium-high.

Manual:
Describe a different lens or combination.
```

## Normalized Manual Answer

```text
Normalized Decision:
Use functional JRPG planning structure with a professional tone; avoid full roleplay.

I will record that unless you correct it.
```

## Vague Answer Conversion

```text
That answer is still Fog of War. "Better workflow" does not tell us what changes, who benefits, or how we know it worked.

Choose the concrete meaning:

A. Faster — reduce time spent on planning.
B. Safer — reduce forgotten decisions and contradictions.
C. Higher quality — improve project briefs and decision memos.
D. More comfortable — make brainstorming less stressful and easier to resume mentally.

Recommended:
B — your report/notes requirement suggests decision memory is the core pain.

Tradeoff:
It may optimize for traceability more than speed.

Confidence:
Medium.

Manual:
Define "better workflow" in your own words.
```

## Contradiction (Boss Encounter)

```text
Boss Encounter: Contradiction Wraith

Earlier you chose a lightweight first version. Now you want analytics, templates, and automation in v1. These can conflict.

Choose how to reconcile:

A. Keep v1 lightweight; move analytics/templates/automation to Side Quests.
B. Expand v1 and accept a larger scope.
C. Keep only one advanced feature in v1.
D. Split into two separate projects or skills.

Recommended:
A — it protects the first version from scope creep while preserving the ideas.

Tradeoff:
You will not get the more impressive version immediately.

Confidence:
High.

Manual:
Explain your own reconciliation.
```

## Save Point

```text
Save Point

Locked:
- ...

Fog of War:
- ...

Next pressure point:
- ...
```

## Next Move Prompt (final interaction)

**Next Move**

Planning is the natural next step. Hand off to the planner with the same command either way:

```
skill:liang-quest-planner
```

- **Same session** (default) — run it now. The planner reads decisions directly from this conversation; no argument needed. Best when the brainstorm was focused and context has room.
- **Fresh session** — paste the command into a new session and point the planner at the saved report path when prompted (e.g., `.liang/brainstorm-reports/2026-05-21_1430-my-topic.md`). Best when the brainstorm was long and you want a clean context.

If you'd like to preview the report first, I can open it in your default browser — just say so.

Source: extracted from liang-brainstorm-relentless/SKILL.md example blocks.
