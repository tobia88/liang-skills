# Plan Schema — Common Envelope

Shared fields and conventions for plan YAML across both TDD and general workflows.

Every `plan.html` opens with an HTML comment containing the full plan YAML. The HTML body renders it in JRPG dashboard style.

## Common Plan Envelope (Required Core)

These fields are present in every plan regardless of workflow type:

```yaml
plan_id: string              # e.g. "p001"; unique within the quest folder
quest_id: string             # matches the quest contract's quest_id
campaign_id: string          # matches the campaign's campaign_id
title: string                # human-readable plan title
workflow: string             # "tdd" | "general"
difficulty: string           # "easy" | "medium" | "hard"
difficulty_rationale: string # one-sentence explanation
readiness: string            # workflow-dependent; see below
created_at: string           # ISO 8601
schema_version: 1            # integer; bump when schema changes
```

### Workflow-Specific Content

After the common envelope, plans diverge by workflow:

- **TDD plans** contain `cycles[]` — see `tdd-cycles.md`
- **General plans** contain `steps[]` — see `general-steps.md`

## Difficulty Vocabulary

Fixed at v1. Use exactly these values:

| Value | Criteria |
|---|---|
| `easy` | Narrow scope, few risks, clear VCs, <=3 cycles/steps, low novelty |
| `medium` | Moderate scope, some risks or open questions, 3-6 cycles/steps, some novelty |
| `hard` | Broad scope, multiple risks or open questions, 6+ cycles/steps, high novelty or cross-cutting concerns |

Do not invent additional levels. New levels require a `schema_version` bump.

## Readiness Vocabulary (Plan-Level)

### TDD Plans

| Value | Meaning |
|---|---|
| `ready` | At least one testable victory condition exists; Readiness Gate passed normally |
| `foggy` | Zero testable VCs; user gave explicit one-shot override |
| `verify-only` | Quest type has no automated test command per registry |

### General Plans

| Value | Meaning |
|---|---|
| `ready` | Victory conditions are clear and achievable with the step plan |
| `scout-limited` | Scout phase revealed incomplete information; plan may need revision during execution |

## Optional Common Extensions

```yaml
foggy_reason: string         # required when readiness == "foggy" (TDD only)
inferred_quest_type: string  # quest type slug from inference

non_test_checks:             # plan-level legitimate non-test concerns
  - string
```

## YAML Conventions

- `snake_case` keys, lowercase, ASCII only
- Formal names (no JRPG metaphors in YAML keys)
- ISO 8601 for dates/timestamps
- VCS-neutral language: use "checkpoint", never commit/push/PR/branch/changelist/submit
- The word "Checkpoint" is VCS-neutral by design

## Schema Versioning Policy

- Current version: `schema_version: 1`
- Any new field requires a `schema_version` bump
- Emit new artifacts under the new version; never retroactively edit existing plans
- Executors must check `schema_version` before parsing and refuse gracefully if unsupported

## Layered Truth

- Plan YAML in the HTML comment is for tools/agents: structured, parseable, complete.
- Plan HTML body is for humans: visual, readable, JRPG-styled.
- Never split plan data across multiple files. One `plan.html` holds everything.
- The manifest carries pipeline state (`status`); the plan carries plan content. No duplication.
