# Manifest Field Registry

Source of truth for manifest.yaml fields consumed by the liang-quest-status skill.
Documents the field union across schema versions v1, v2, v3, and canonical planner-native v4.

## Campaign-Level Fields

### Required by Status Skill

| Field | Type | v1 | v2 | v3 | v4 | Purpose |
|-------|------|:--:|:--:|:--:|:--:|---------|
| `campaign_id` | string | Y | Y | Y | Y | Campaign identifier |
| `title` | string | Y | Y | Y | Y | Campaign display name |
| `created_at` | string (ISO 8601) | Y | Y | Y | Y | Sort order and elapsed time base |
| `schema_version` | string | opt | Y | Y | opt | Determines parsing behavior; absent implies v1 unless canonical-format detection matches v4 |

### Optional / Enrichment

| Field | Type | v1 | v2 | v3 | v4 | Purpose |
|-------|------|:--:|:--:|:--:|:--:|---------|
| `slug` | string | Y | Y | Y | opt | Filesystem identifier |
| `source_report` | string | Y | Y | Y | opt | Reference only |
| `source` | string | N | N | N | opt | Canonical planner source, e.g. brainstorm or in-session conversation |
| `quest_count` | integer | N | N | N | Y | Number of quest entries in canonical manifests |
| `lens` | string | Y | Y | Y | opt | Planning lens; enrichment in expanded view |
| `summary` | string | Y | Y | Y | opt | Campaign description; enrichment |
| `workflow` | string | N | N | Y | N | Campaign-level workflow stamp (v3 only); absent in v4 |
| `notes` | string | opt | opt | opt | opt | Free-form notes |
| `tags` | [string] | opt | opt | opt | opt | Tags |
| `generated_by` | string | opt | opt | opt | opt | Generator identity |

## Quest-Level Fields

### Required by Status Skill

| Field | Type | v1 | v2 | v3 | v4 | Purpose |
|-------|------|:--:|:--:|:--:|:--:|---------|
| `id` | string | Y | Y | Y | Y | Quest identifier |
| `title` | string | Y | Y | Y | Y | Quest display name |
| `status` | string | Y | Y | Y | Y | Drives attention tier assignment |
| `depends_on` | [string] | Y | Y | Y | Y | Topological sort for display order |

### Optional / Enrichment

Cross-version notes: `v4` is the planner-native (canonical) schema produced by `liang-quest-planner`.

| Field | Type | v1 | v2 | v3 | v4 | Purpose |
|-------|------|:--:|:--:|:--:|:--:|---------|
| `priority` | string | Y | Y | Y | N | Display enrichment (deprecated chain only) |
| `path` | string | Y | Y | Y | N | Quest file path (deprecated chain: `quest-NNN-slug/index.html`) |
| `file` | string | N | N | N | Y | Quest file path (canonical: `quest-NNN-name.md`) |
| `difficulty` | string | N | N | N | Y | `easy` / `medium` / `hard` (canonical only) |
| `readiness` | string | Y | Y | Y | N | Planning readiness (deprecated chain only) |
| `workflow` | string | opt | opt | N | N | Per-quest workflow (v1/v2 only); ignored in v3; absent in v4 |
| `current_cycle` | integer | opt | opt | opt | opt | Progress: current step/cycle index |
| `total_cycles` | integer | opt | opt | opt | opt | Progress: total step/cycle count |
| `started_at` | string (ISO 8601) | opt | opt | opt | opt | Elapsed time computation |
| `completed_at` | string (ISO 8601) | opt | opt | opt | opt | Elapsed time computation |
| `current_step_started_at` | string (ISO 8601) | N | opt | opt | N | Progress polling timestamp (deprecated chain only) |
| `skip_reason` | string | N | N | def | def | Reason for skipped quests |
| `usage` | map | N | N | N | opt | Child-process spend rollup written by the executor: `total_tokens` (integer), `cost_usd` (float). Absent when untracked. Display enrichment only — never affects attention tiers. |

## Status Vocabulary

Complete set of quest status values for the canonical pipeline (`liang-quest-planner` → `liang-quest-executor`): `ready / in_progress / passed / failed / skipped`.

| Status | Source Skill | Meaning |
|--------|-------------|---------|
| `ready` | Planner (canonical) | Quest is ready to execute |
| `in_progress` | Executor | Currently being executed |
| `passed` | Executor | Completed successfully |
| `failed` | Executor | Execution failed |
| `skipped` | Executor | Cascade-skipped due to dependency failure |


## Version-Aware Parsing

### Known Versions

| Version | Detection | Behavior |
|---------|-----------|----------|
| v1 | absent `schema_version` without canonical-format markers | Deprecated chain schema; best-effort parse legacy `path`/`priority` fields. |
| v2 | `schema_version: "2"` or `schema_version: 2` | Deprecated chain schema; best-effort parse legacy fields. |
| v3 | `schema_version: "3"` or `schema_version: 3` | Deprecated chain schema with campaign-level `workflow`. |
| v4 | `schema_version: "4"` or `schema_version: 4` OR canonical-format detection (no `workflow` field, quest uses `file` not `path`, quest `difficulty` present) | Canonical planner-native schema. No workflow field. Quests use `file` (not `path`) and have `difficulty`. |

### Integer vs String Tolerance

Parsers must tolerate `schema_version` as either an integer (e.g. `4`) or a string (e.g. `"4"`). Normalize by coercing to a string before comparing to known version keys. YAML parsers may produce `int` when the value is unquoted.

### Unknown Versions

When `schema_version` is present but not recognized:

1. Parse with best-effort: read all known fields, ignore unknown fields.
2. Display a WARN indicator on the campaign row.
3. Do not fail or skip the campaign.

### Absent `schema_version`

First run canonical-format detection (`file` + `difficulty`, no `workflow`). If it matches, parse as v4; otherwise parse as v1 without warning.
