<!--
  saga.md template for liang-quest-saga-planner.
  SKELETON: Replace [BRACKETED_TOKENS] with real values.
  - This is the saga's human dossier: why the split, what each campaign owns.
  - REQUIRED in every saga folder, whatever `planner.html` is set to.
  - NO STATUS ANYWHERE. saga.yaml owns status; the status table is shown in chat,
    and saga.html merges status in at render time.
  - No schemas and no formulas — those stay in inventory.md.
  - Repeat the campaign block for each campaign, in topological order.
-->

# [SAGA_TITLE] — Saga

- Saga: `saga-[YYYY-MM-DD]-[SLUG]`   Short name: [SHORT_NAME]   Skin: [SKIN_SLUG]
- Source prototype: [PROTOTYPE_PATH]

## Why this split
[TWO_TO_FIVE_SENTENCES_ON_THE_SEAMS_CHOSEN]

## Anchors

| id | Label | Decision |
|---|---|---|
| a001 | [ANCHOR_LABEL] | [LOCKED_DECISION] |

## Campaigns

### c01: [CAMPAIGN_TITLE]  `[easy|medium|hard]`
- Purpose: [ONE_SENTENCE_OUTCOME]
- Scope: [ITEM], [ITEM], [ITEM]
- Depends on: [c0N, ... | none]
- Victory conditions:
  - [ ] [CAMPAIGN_VICTORY_CONDITION]
- Non-goals (sibling scopes): c02 owns [X], c03 owns [Y]

## Dependency topology
[TEXT_OR_FENCED_MERMAID_GRAPH_NO_STATUS_COLOURING]

## Risks and open questions
- [RISK_OR_OPEN_QUESTION]
