# Run Report Schema

Canonical run reports are Markdown files written by `liang-quest-executor`.

## File Location

~~~text
.liang/campaigns/<campaign>/run-report-<iso-8601-timestamp>.md
~~~

## Run Report Front Matter

~~~yaml
---
run_id: "run-<iso-8601-timestamp>"
campaign_id: string
started_at: string
completed_at: string
duration_seconds: integer
quests: []
totals:
  passed: 0
  failed: 0
  skipped: 0
  tier2_failures: 0
  total_tokens: 0        # campaign child-process spend; omit both keys when untracked
  total_cost_usd: 0.0    # sum of harness-priced costs across all child sessions
lessons_count: 0
usage_tracked: boolean   # false in --claude mode or when no session could be harvested
---
~~~

Spend totals cover **child processes only** (execute attempts including retries,
re-plan-children, verify-children). The orchestrator's own session is not included —
the body must label the figure as child-process spend, never as run-total spend.

## Markdown Body

Required sections: `# Run Report`, `## Quest Results`, `## Deferred UAT`, `## Lessons`, `## Spend` when `usage_tracked` is true, and `## Shared Helpers` when applicable.
