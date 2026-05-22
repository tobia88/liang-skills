# Discussion Constraint Schema

Source of truth for the constraint data model used by the discussion stage across the JRPG quest planning family.

Constraints live inside the opening HTML comment of `discussion.html` within a `constraints` list.

## Required Core

```yaml
constraints:
  - id: string               # e.g. "dc001"; unique within the discussion; prefix "dc" + 3-digit zero-padded number
    description: string      # what the constraint mandates
    why: string              # rationale for the constraint
    source: string           # origin: "crosscut" or "per_quest:<quest-id>" (e.g. "per_quest:q003")
    applicable_quests: [string]  # quest IDs this applies to, or "*" for all quests
    scope: string            # "crosscut" or "quest_specific"
```

## Optional Extensions

```yaml
    priority: string         # "low" | "medium" | "high"
    confidence: string       # "low" | "medium" | "high"
    resolved_by: string      # "user" | "default"
    notes: string            # free-form supplementary notes
```

## Scope Vocabulary

| Value | Meaning |
|-------|---------|
| `crosscut` | Applies across multiple or all quests. Produced by crosscut discussion phase. |
| `quest_specific` | Applies to specific quests only. Produced by per-quest discussion phase. |

## ID Convention

Constraint IDs use prefix `dc` + 3-digit zero-padded number: `dc001`, `dc002`, etc.

IDs are unique within a single `discussion.html` file.

## Source Convention

The `source` field traces origin:

- `"crosscut"` — from the campaign-level crosscut discussion
- `"per_quest:q001"` — from per-quest discussion for quest `q001`

The format is `per_quest:<quest-id>` with no spaces.

## Validation Rules

- All Required Core fields must be present for every constraint
- `id` values must be unique within the discussion
- `scope` must be exactly `"crosscut"` or `"quest_specific"`
- `applicable_quests` must reference existing quest IDs or contain `"*"`
- When `scope` is `"crosscut"`, `applicable_quests` typically contains `"*"` or multiple quest IDs
- When `scope` is `"quest_specific"`, `applicable_quests` typically contains one quest ID
- `source` must match the convention: `"crosscut"` or `"per_quest:<valid-quest-id>"`

## YAML Conventions

Follow the family standard: snake_case keys, lowercase, ASCII only, formal names (no JRPG metaphors in YAML keys).

## Relationship to Other Schemas

- Constraints are consumed by the tactician during Decompose and Plan
- The `discussion_constraints_applied` field on plan steps references constraint IDs from this schema
- The discussion HTML template renders these constraints in JRPG dashboard style
- See `protocol.md` for the discussion flow that produces constraints
