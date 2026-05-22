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
Layer 2: Per-Quest Discussion (optional, via dialogue hub)
    |--- Dialogue Hub (numbered menu of all quests + Done)
    |--- Brainstorm-Lite (3-5 questions per selected quest)
    |
Per-Quest Scout & Planning Phase
```

## Layer 1: Crosscut Discussion

### When

After Campaign Intake, before any per-quest work.

### Format

Two sub-phases:

1. **Hybrid Shallow Scout** — read all quest contracts from the manifest + key codebase files to build campaign-wide context
2. **Scout-Present & Brainstorm-Lite** — present findings as context, immediately followed by 2-4 pointed questions about campaign-wide concerns. Single turn — no pause between findings and questions. The user corrects scout assumptions through their answers.

### Question Format

Each question uses 4 options + recommendation format (same as the brainstorm skill):

- 4 concrete options, each with a short description
- First option is the recommended one (marked with "(Recommended)")
- User can pick one or provide a custom answer

### Question Cap

Hard cap: **4 questions maximum** for the crosscut phase. Non-negotiable.

### Abbreviated Mode (1-Quest Campaigns)

When the campaign has exactly one quest, the crosscut phase is abbreviated:

- Run the Hybrid Shallow Scout and scout-present content normally
- Skip brainstorm-lite questions — no follow-up questions
- Proceed directly to per-quest planning

Rationale: with one quest, crosscut and per-quest concerns collapse into the same scope.

### Output

Crosscut constraints are written to `discussion.html` at the campaign root.
Each constraint has `scope: "crosscut"` and `source: "crosscut"`.

## Layer 2: Per-Quest Discussion

### When

After Crosscut Discussion (Layer 1) completes, before any per-quest planning
work begins. The hub runs once for the entire campaign — it is not interleaved
with individual quest planning.

### Hub Presentation

Present all eligible quests from the planning queue as a numbered menu. The last
option is always "Done — begin planning":

  Per-Quest Discussion Hub

    1. [quest-title-1]
    2. [quest-title-2]
    ...
    N+1. Done — begin planning

Discussed quests display a checkmark on the quest title when the menu is
re-displayed after each discussion.

### Discussion Loop

When the user selects a quest number:

1. Present a brief quest context: title, purpose, desired outcome, and key risks.
2. Run Brainstorm-Lite for that quest (see Question Format and Question Cap below).
3. Persist constraints to discussion.html (see Output below).
4. Re-display the hub menu with a checkmark on the just-discussed quest.

The user may then select another quest, re-enter a previously discussed quest,
or select Done.

### Re-entry

Discussed quests (marked with a checkmark) can be re-entered. When re-entering:

- New constraints are **appended** to discussion.html (append-only semantics).
- Existing constraints from the prior discussion of that quest are preserved
  unchanged.
- The checkmark remains on the quest in the menu.

### Hub Exit

When the user selects "Done — begin planning":

- The hub closes.
- The tactician proceeds to per-quest planning (scout then plan) for all quests
  in dependency order.
- No further discussion prompts occur during the planning phase.
- "Done" is the only way to exit the hub.

### Zero-Discussion Exit

Selecting "Done" immediately — without discussing any quests — proceeds to
planning with crosscut constraints only. No additional confirmation is required.

### Abbreviated Mode (1-Quest Campaigns)

When the campaign has exactly one quest, the per-quest dialogue hub is **skipped
entirely**. The tactician proceeds directly to planning with crosscut constraints
only.

Rationale: with one quest, crosscut and per-quest concerns collapse into the
same scope.

### Question Format

Each question uses 4 concrete options with the first marked as recommended:
- Option A (Recommended) — with short description
- Option B — with short description
- Option C — with short description
- Option D — with short description

Question categories are defined by each tactician's SKILL.md, not by this
protocol.

### Question Cap

Hard cap: **5 questions per quest**. Non-negotiable.

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
