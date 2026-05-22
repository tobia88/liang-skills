# Plan Schema — General Steps

Schema for general (non-TDD) plan content. Read in conjunction with `common.md` for the shared envelope.

## General Plan YAML

After the common envelope fields, general plans contain `steps[]`:

```yaml
# ... common envelope (see common.md) ...
workflow: "general"
readiness: "ready" | "scout-limited"

scout_summary: string        # summary of codebase state from the mandatory scout phase
inferred_quest_type: string   # quest type slug from registry/inference; optional

steps:                       # ordered list; order is execution order
  - id: string              # e.g. "s01"; unique within the plan
    name: string             # short human-readable step name
    description: string      # what this step accomplishes
    files: [string]          # file paths this step creates or modifies
    instructions: string     # implementation-ready instructions (the core content)
    preconditions:           # conditions that must be true before this step executes
      - string               # natural language; executor validates mechanically
    postconditions:          # conditions that must be true after this step executes
      - string               # natural language; executor validates mechanically
    verification_tier: 1 | 2 # which verification approach to use
    verification_command: string | null  # Tier 1: shell command (exit 0 = pass); null for Tier 2
    acceptance_criteria:     # Tier 2: forced yes/no questions; also used as human-readable summary for Tier 1
      - string               # each criterion as an explicit yes/no question for Tier 2
    discussion_constraints_applied: [string]  # optional; constraint IDs from discussion.html honored by this step
```

## Step Schema Design Principles

### Flat Schema

All fields live at the step level — no nesting or sub-objects. Simple, scannable, easy for the executor model to parse.

### Implementation-Ready Instructions

The tactician (smart model) front-loads all thinking into prescriptive `instructions`. The executor (cheap model) follows them mechanically. This is the "plan heavy, execute cheap" principle.

Instructions must include:
- Exact file paths
- Specific changes to make
- Concrete content to write
- Any patterns to follow from existing code

### Pre/Postconditions

Replace TDD's self-contained test cycles as the drift-detection mechanism. The executor validates preconditions before acting and postconditions after.

**Preconditions** answer: "What must be true before this step can safely execute?"
- File/directory existence checks
- Required content patterns in files
- Dependencies from earlier steps

**Postconditions** answer: "What must be true after this step succeeds?"
- Files created/modified
- Content patterns present
- Structural properties satisfied

### Discussion Constraint Traceability

When a campaign has a `discussion.html` (produced by the discussion stage), the tactician populates `discussion_constraints_applied` on each step with the IDs of constraints that influenced the step's design. This enables mechanical traceability from discussion to plan.

- Field is optional — steps in plans without a discussion stage omit it
- Values are constraint IDs (e.g. `"dc001"`, `"dc003"`) matching the `id` field in the constraint schema (see `liang-quest-core/references/discussion/constraint-schema.md`)
- A constraint may appear on multiple steps
- Every constraint from `discussion.html` should appear on at least one step

### Two-Tier Verification

| Tier | When Used | How It Works |
|------|-----------|-------------|
| **1 (Command)** | Step has a deterministic shell check | Tactician provides `verification_command`; executor runs it; exit 0 = pass |
| **2 (Yes/No Checklist)** | No mechanical verification possible | Tactician writes `acceptance_criteria` as explicit yes/no questions; verify-child answers each; any "no" = fail |

The tactician should prefer Tier 1 whenever possible. Tier 2 is the fallback for inherently non-mechanical verification (documentation quality, design consistency, etc.).

### Registry-Informed Verification

When `.liang/test-approaches.yaml` exists and contains an entry for the
quest's inferred type, the registry informs Tier selection:

| Registry State | Step Type | Verification Behavior |
|---|---|---|
| Automatable (`test_command` present) | Code-touching step | Tier 1 with `test_command` as default `verification_command` |
| Automatable (`test_command` present) | Non-code step | Independent per-step verification (unchanged) |
| Verify-only (`verify_only: true`) | Domain-relevant step | Tier 2 with `verify_hint`-derived `acceptance_criteria` |
| Verify-only (`verify_only: true`) | Non-domain step | Independent per-step verification (unchanged) |
| No entry / registry absent | Any step | Per-step ad-hoc verification (existing behavior) |

The registry is a default, not an override. The tactician may choose a more
specific verification command when one exists for a particular step.

See `test-approaches.md` for the complete registry schema.

## Mandatory Scout Phase

Before planning, the general tactician must:

1. Read all files in the quest contract's scope
2. Examine existing patterns and conventions
3. Build a `scout_summary` that grounds the plan in codebase reality

The scout summary is stored in the plan YAML and available to the executor for context.

## Composite Difficulty Auto-Decision

The general tactician auto-decides difficulty using three signals:

| Signal | Easy | Medium | Hard |
|--------|------|--------|------|
| Step count | 1-3 | 4-6 | 7+ |
| Tier 2 proportion | 0-20% | 20-50% | 50%+ |
| Codebase impact | Single dir/file | Multiple dirs | Cross-cutting |

Combined with a one-sentence rationale.

## Example Step

```yaml
steps:
  - id: "s01"
    name: "Create logging config"
    description: "Create the logging configuration file with structured JSON output format"
    files: ["src/config/logging.json"]
    instructions: |
      Create src/config/logging.json with the following content:
      {
        "format": "structured",
        "level": "info",
        "outputs": ["stdout"],
        "timestamp": true
      }
    preconditions:
      - "directory src/config/ exists"
    postconditions:
      - "file src/config/logging.json exists"
      - "file src/config/logging.json contains \"structured\""
    verification_tier: 1
    verification_command: "test -f src/config/logging.json && grep -q structured src/config/logging.json"
    acceptance_criteria:
      - "Logging config exists at src/config/logging.json"
      - "Output format is set to structured JSON"
    discussion_constraints_applied: []

  - id: "s02"
    name: "Write migration guide"
    description: "Document the migration steps from v1 to v2 logging format"
    files: ["docs/migration-v2.md"]
    instructions: |
      Create docs/migration-v2.md covering:
      - All v1 config keys that changed
      - Before/after examples for each key
      - Migration checklist
    preconditions:
      - "file src/config/logging.json exists"
    postconditions:
      - "file docs/migration-v2.md exists"
    verification_tier: 2
    verification_command: null
    acceptance_criteria:
      - "Does the guide cover all v1 config keys that changed? (yes/no)"
      - "Does the guide include a before/after example? (yes/no)"
      - "Is the guide self-contained without requiring external references? (yes/no)"
```

## Validation Rules (General-Specific)

In addition to common validation:

- At least 1 step exists.
- Every step has a unique `id`.
- `verification_tier` must be `1` or `2`.
- When `verification_tier` is `1`, `verification_command` must be a non-empty string.
- When `verification_tier` is `2`, `verification_command` must be `null` and `acceptance_criteria` must contain at least one item.
- `acceptance_criteria` items should be phrased as yes/no questions when `verification_tier` is `2`.
- `preconditions` and `postconditions` must each have at least one entry.
- `instructions` must be non-empty.
- `files` must list at least one file path.
- When present, `discussion_constraints_applied` must be a list of strings. Each string should match a constraint ID format (`dc` + 3-digit number).
