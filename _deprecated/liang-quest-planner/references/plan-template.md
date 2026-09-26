<!--
  plan.md template for liang-quest-planner.
  SKELETON: Replace [BRACKETED_TOKENS] with real values.
  - This is the "why" doc; the quest files are the "do" docs.
  - REQUIRED in every campaign folder, whatever `planner.html` is set to.
  - Holds rationale, difficulty, dependencies, risks, and the decision table.
    No steps, no code blocks — those live only in the quest files.
  - Victory conditions are the one deliberate overlap with the quest file:
    repeat them verbatim so the dossier reads on its own.
  - The Skin line appears only when `planner.html` is true; the Visual line
    only when Phase 2a planned a plan visual.
  - Repeat the Quest block for each quest, in dependency order.
-->

# [CAMPAIGN_TITLE]

- Campaign: `campaign-[YYYY-MM-DD]-[HHMM]-[SLUG]`
- Generated: [ISO_8601_LOCAL]
- Planning lens: [PLANNING_LENS]
- Skin: [SKIN_SLUG]
- Visual: [ONE_SENTENCE_VISUAL_RECIPE]

## Decision Summary

### Main Quest
[GOAL_AND_CORE_PROBLEM]

### Planning Lens
[LENS]

### Target User
[TARGET_USER]

### Locked Decisions

| Label | Chosen path | Key tradeoff | Confidence |
|---|---|---|---|
| [LABEL] | [CHOSEN_PATH] | [TRADEOFF] | [Low/Medium/Medium-high/High] |

### Victory Conditions
- [CAMPAIGN_VICTORY_CONDITION]

### Scope Boundary
- In scope: [IN_SCOPE_ITEMS]
- Non-goals: [NON_GOALS]

### Risks
- [RISK] — mitigation: [MITIGATION]

### Open Questions
- [OPEN_QUESTION]

### Decision Table

| Path | Status | Reason |
|---|---|---|
| [PATH] | [Recommended/Rejected/Deferred] | [REASON] |

## Quests

### Quest 001: [QUEST_TITLE]  `[easy|medium|hard]`  [MANUAL]
- Purpose: [ONE_OR_TWO_SENTENCES]
- Rationale: [WHY_THIS_QUEST_WHY_THIS_ORDER]
- Depends on: [q00N, ... | none]
- Victory conditions:
  - [ ] [VICTORY_CONDITION_VERBATIM_FROM_QUEST_FILE]
- File: `quest-001-[NAME].md`

## Campaign Notes
[RISKS_AND_OPEN_QUESTIONS_CARRIED_INTO_EXECUTION]

### Verified facts
- [FACT_A_QUEST_ASSERTS] — [HOW_IT_WAS_CHECKED: file:line, command + output, or measurement]
- [FACT_THAT_COULD_NOT_BE_CHECKED] — assumed; written as `assumed:` in [QUEST_FILE] step [N]
