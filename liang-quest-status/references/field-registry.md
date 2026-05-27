# Manifest Field Registry

Source of truth for manifest.yaml fields consumed by the liang-quest-status skill.
Documents the field union across schema versions v1, v2, and v3.

## Campaign-Level Fields

### Required by Status Skill

| Field | Type | v1 | v2 | v3 | Purpose |
|-------|------|:--:|:--:|:--:|---------|
| `campaign_id` | string | Y | Y | Y | Campaign identifier |
| `title` | string | Y | Y | Y | Campaign display name |
| `created_at` | string (ISO 8601) | Y | Y | Y | Sort order and elapsed time base |
| `schema_version` | string | opt | Y | Y | Determines parsing behavior; absent implies v1 |

### Optional / Enrichment

| Field | Type | v1 | v2 | v3 | Purpose |
|-------|------|:--:|:--:|:--:|---------|
| `slug` | string | Y | Y | Y | Filesystem identifier |
| `source_report` | string | Y | Y | Y | Reference only |
| `lens` | string | Y | Y | Y | Planning lens; enrichment in expanded view |
| `summary` | string | Y | Y | Y | Campaign description; enrichment |
| `workflow` | string | N | N | Y | Campaign-level workflow stamp (v3 only) |
| `notes` | string | opt | opt | opt | Free-form notes |
| `tags` | [string] | opt | opt | opt | Tags |
| `generated_by` | string | opt | opt | opt | Generator identity |

## Quest-Level Fields

### Required by Status Skill

| Field | Type | v1 | v2 | v3 | Purpose |
|-------|------|:--:|:--:|:--:|---------|
| `id` | string | Y | Y | Y | Quest identifier |
| `title` | string | Y | Y | Y | Quest display name |
| `status` | string | Y | Y | Y | Drives attention tier assignment |
| `depends_on` | [string] | Y | Y | Y | Topological sort for display order |

### Optional / Enrichment

Cross-version notes: `v4` is the planner-native (canonical) schema produced by `liang-quest-planner` (no workflow field, uses `file` instead of `path`, status is `ready`). `v1`–`v3` belong to the deprecated cartographer/tactician chain.

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

## Status Vocabulary

Complete set of quest status values across the pipeline. The canonical pipeline (`liang-quest-planner` → `liang-quest-executor`) uses the compact set `ready / in_progress / passed / failed / skipped`. The deprecated cartographer/tactician chain adds `ready_for_planning`, `needs_clarification`, `blocked`, `planned`.

| Status | Source Skill | Meaning |
|--------|-------------|---------|
| `ready` | Planner (canonical) | Quest is planned and ready to execute |
| `in_progress` | Executor | Currently being executed |
| `passed` | Executor | Completed successfully |
| `failed` | Executor | Execution failed |
| `skipped` | Executor | Cascade-skipped due to dependency failure |
| `ready_for_planning` | Cartographer (deprecated) | Quest contract complete, awaiting tactician |
| `needs_clarification` | Cartographer (deprecated) | Quest contract has gaps |
| `blocked` | Cartographer (deprecated) | External dependency prevents progress |
| `planned` | Tactician (deprecated) | Plan written, awaiting executor |

## Version-Aware Parsing

### Known Versions

| Version | Detection | Behavior |
|---------|-----------|----------|
| v1 | `schema_version` absent or `"1"` | Deprecated cartographer chain. Per-quest `workflow` field may be present. `generated_by` may use legacy name `"liang-brainstorm-campaign-cartographer"`. |
| v2 | `schema_version: "2"` | Deprecated cartographer chain. Per-quest `workflow` field. `current_step_started_at` may appear on quest entries. |
| v3 | `schema_version: "3"` | Deprecated cartographer chain. Campaign-level `workflow` field. Per-quest `workflow` fields are ignored if present. |
| v4 | `schema_version: "4"` OR canonical-format detection (no `workflow` field, quest uses `file` not `path`, quest `difficulty` present) | Canonical planner-native schema. No workflow field. Quests use `file` (not `path`) and have `difficulty`. Status vocabulary uses `ready` (not `ready_for_planning`/`planned`). |

### Unknown Versions

When `schema_version` is present but not recognized:

1. Parse with best-effort: read all known fields, ignore unknown fields.
2. Display a WARN indicator on the campaign row.
3. Do not fail or skip the campaign.

### Absent `schema_version`

Treat as v1. No warning.
