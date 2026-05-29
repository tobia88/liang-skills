# Attention Tier Mapping

Source of truth for mapping quest `status` values to attention severity tiers.
The status skill uses these tiers to highlight campaigns needing attention.

## Tier Definitions

| Tier | Severity | Description |
|------|----------|-------------|
| ALERT | Critical | Quests that have failed; require immediate attention |
| ACTIVE | Active | Quests with in-progress work or awaiting pipeline action |
| INFO | Informational | Quests with non-critical advisory states |
| PASSED | Complete | Quests that completed successfully |

## Status-to-Tier Mapping

| Status Value | Tier | Rationale |
|-------------|------|-----------|
| `failed` | ALERT | Execution failed; requires investigation |
| `in_progress` | ACTIVE | Currently being executed |
| `ready` | ACTIVE | Planner-native quest ready to execute (canonical pipeline) |
| `skipped` | INFO | Skipped due to dependency failure |
| `passed` | PASSED | Completed successfully |

## Campaign-Level Tier Derivation

A campaign's attention tier is the highest severity among its quests:

1. If any quest is ALERT, the campaign is ALERT
2. Else if any quest is ACTIVE, the campaign is ACTIVE
3. Else if any quest is INFO, the campaign is INFO
4. Else the campaign is PASSED

## Display Sort Precedence

Campaigns are ordered by tier severity in the dashboard:

1. ALERT campaigns first (most urgent)
2. ACTIVE campaigns
3. INFO campaigns
4. PASSED campaigns (newest-first by `created_at` within this group)

## Unknown Status Values

If a quest has a status value not listed in the mapping:

1. Assign tier: INFO (safe default)
2. Display the raw status value in the quest row
3. Do not fail; unknown statuses are rendered with their literal value
