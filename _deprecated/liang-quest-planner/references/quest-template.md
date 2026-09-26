<!--
  Quest Markdown template for liang-quest-planner.
  SKELETON: Replace [BRACKETED_TOKENS] with real values.
  - Repeat Step blocks for each step in the quest.
  - Code blocks are optional per step (include per code block heuristics).
  - Code blocks must have a file path comment on the first line.
  - Lean executable contract only: Purpose, Steps/code blocks, Dependencies, Victory Conditions.
  - No tutorial prose, rationale, or "why" explanations.
  - Every count, path, pattern, or measured value in a step was checked against the
    workspace (plan.md "Verified facts"); one that could not be checked is written
    as "assumed: <fact>" so the execute-child verifies it before building on it.
  - Victory conditions use checkbox format, not narrative.
  - This is the "do" doc; plan.md is the "why" doc.
-->

# Quest [NNN]: [QUEST_TITLE]

## Purpose
[ONE_SENTENCE_PURPOSE]

## Steps

### Step 1: [STEP_TITLE]
[STEP_DESCRIPTION]

```[LANGUAGE]
// file: [FILE_PATH]
[CODE_CONTENT]
```

### Step 2: [STEP_TITLE]
[STEP_DESCRIPTION]

## Dependencies
- [q00N, ... | none]

## Victory Conditions
- [ ] [VICTORY_CONDITION_1]
- [ ] [VICTORY_CONDITION_2]
