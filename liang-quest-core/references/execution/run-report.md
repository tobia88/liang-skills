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
lessons_count: 0
---
~~~

## Markdown Body

Required sections: `# Run Report`, `## Quest Results`, `## Deferred UAT`, `## Lessons`, and `## Shared Helpers` when applicable.
