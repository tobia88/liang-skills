# Discussion Protocol

Shared protocol for the discussion stage that runs inside tacticians before quest planning begins. Defines the two-layer discussion flow, question format, caps, skip mechanics, and output artifact.

## Two-Layer Discussion Flow

The discussion stage has two layers that run sequentially before any quest is planned.

Layer 1 (Crosscut) establishes campaign-wide constraints. Layer 2 (Per-Quest) captures quest-specific preferences. Both layers produce constraints that are persisted in `discussion.html` at the campaign root.

```
Campaign Intake
    |
Layer 1: Crosscut Discussion (mandatory)
    |--- Hybrid Shallow Scout
    |--- Scout-Present (show findings, user reacts)
    |--- Brainstorm-Lite (2-4 questions)
    |
Layer 2: Per-Quest Discussion (optional, per quest)
    |--- Binary Gate ("Discuss this quest?")
    |--- Brainstorm-Lite (3-5 questions)
    |
Per-Quest Scout & Planning Phase
```

## Layer 1: Crosscut Discussion

### When

After Campaign Intake, before any per-quest work.

### Format

Three sub-phases:

1. **Hybrid Shallow Scout** — read all quest contracts from the manifest + key codebase files to build campaign-wide context
2. **Scout-Present** — present findings to user in a structured summary; user reacts, corrects, or confirms
3. **Brainstorm-Lite** — ask 2-4 pointed questions about campaign-wide concerns (architecture, conventions, constraints, priorities)

### Question Format

Each question uses 4 options + recommendation format (same as the brainstorm skill):

- 4 concrete options, each with a short description
- First option is the recommended one (marked with "(Recommended)")
- User can pick one or provide a custom answer

### Question Cap

Hard cap: **4 questions maximum** for the crosscut phase. Non-negotiable.

### Abbreviated Mode (1-Quest Campaigns)

When the campaign has exactly one quest, the crosscut phase is abbreviated:

- Run the Hybrid Shallow Scout and Scout-Present sub-phases normally
- Skip the Brainstorm-Lite sub-phase (no follow-up questions)
- Proceed directly to per-quest planning

Rationale: with one quest, crosscut and per-quest concerns collapse into the same scope.

### Output

Crosscut constraints are written to `discussion.html` at the campaign root.
Each constraint has `scope: "crosscut"` and `source: "crosscut"`.

## Layer 2: Per-Quest Discussion

### When

Before each quest is planned, after the crosscut discussion.

### Gate

Single binary question per quest: "Would you like to discuss **[quest title]** before planning?"

- **Yes** → run brainstorm-lite for this quest
- **No** → skip; quest uses crosscut constraints only

### Format

Brainstorm-Lite: 3-5 pointed questions about quest-specific design decisions.
Same 4-option + recommendation format as crosscut.

### Question Cap

Hard cap: **5 questions per quest**. Non-negotiable.

### Skip Mechanics

- User can decline the gate question → quest is planned with crosscut constraints only
- User can decline all gate questions → no per-quest discussions happen
- Undiscussed quests are still planned normally

### Output

Per-quest constraints are appended to the existing `discussion.html`.
Each constraint has `scope: "quest_specific"` and `source: "per_quest:<quest-id>"`.

## discussion.html Artifact

### Location

Campaign root: `.liang/campaigns/<campaign>/discussion.html`

### Format

Uses the family YAML-in-HTML-comment convention:

- Opening HTML comment contains full constraint YAML (per `constraint-schema.md`)
- HTML body renders constraints in JRPG dashboard style (per `discussion-template.html`)

### Lifecycle

- Created during crosscut discussion (Layer 1)
- Appended during per-quest discussions (Layer 2)
- Read by the tactician during Decompose and Plan phase
- Read-only after planning begins

## Constraint Consumption Rules

- Tacticians read `discussion.html` before planning each quest
- Crosscut constraints (`scope: "crosscut"`) apply to all quests by default
- Per-quest constraints (`scope: "quest_specific"`) apply only to their `applicable_quests`
- The tactician populates `discussion_constraints_applied` on each plan step with applicable constraint IDs
- Every constraint should appear in at least one plan step's `discussion_constraints_applied`
