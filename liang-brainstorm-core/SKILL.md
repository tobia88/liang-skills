---
name: liang-brainstorm-core
description: Shared reference library for liang-brainstorm-* skills. Contains behavioral contracts for question cadence, terminology, VCS policy, and scout rules consumed via reference inclusion at activation time. Not directly invocable.
---

# Liang Brainstorm Core

You are the shared reference foundation for the liang-brainstorm-* skill family.

This skill contains **no behavioral logic**. It exists solely as a structured library of reference documents consumed by brainstorm variant skills via reference inclusion.

## What This Skill Provides

| Reference | Contents | Consumers |
|---|---|---|
| `references/question-cadence.md` | 4-option ABCD format spec with Recommended/Tradeoff/Confidence/Manual | All brainstorm variants |
| `references/terminology.md` | Neutral formal terms and JRPG label mappings | All brainstorm variants |
| `references/vcs-policy.md` | VCS artifact policy lookup and prompt logic | All brainstorm variants |
| `references/scout-rules.md` | Project scout rules: allowed/avoided paths, timing, report context | All brainstorm variants |

## Composition Mechanism

Brainstorm variant skills consume core references via **reference inclusion** — they read the relevant files at activation time. Each variant reads all 4 reference files and may override or extend with variant-specific behavior.

## Boundaries

- This skill never brainstorms, plans, or produces artifacts.
- This skill is never invoked directly by the user — it is consumed silently by other skills.
- All behavioral logic belongs in the variant skills, not here.
