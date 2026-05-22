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

| Field | Type | v1 | v2 | v3 | Purpose |
|-------|------|:--:|:--:|:--:|---------|
| `priority` | string | Y | Y | Y | Display enrichment in expanded view |
| `path` | string | Y | Y | Y | Quest file path |
| `readiness` | string | Y | Y | Y | Planning readiness |
| `workflow` | string | opt | opt | N | Per-quest workflow (v1/v2 only); ignored in v3 |
| `current_cycle` | integer | opt | opt | opt | Progress: current step/cycle index |
| `total_cycles` | integer | opt | opt | opt | Progress: total step/cycle count |
| `started_at` | string (ISO 8601) | opt | opt | opt | Elapsed time computation |
| `completed_at` | string (ISO 8601) | opt | opt | opt | Elapsed time computation |
| `current_step_started_at` | string (ISO 8601) | N | opt | opt | Progress polling timestamp |
| `skip_reason` | string | N | N | def | Reason for skipped quests |

## Status Vocabulary

Complete set of quest status values across the pipeline:

| Status | Source Skill | Meaning |
|--------|-------------|---------|
| `ready_for_planning` | Cartographer | Quest contract complete, awaiting tactician |
| `needs_clarification` | Cartographer | Quest contract has gaps |
| `blocked` | Cartographer | External dependency prevents progress |
| `planned` | Tactician | Plan written, awaiting executor |
| `in_progress` | Executor | Currently being executed |
| `passed` | Executor | Completed successfully |
| `failed` | Executor | Execution failed |
| `skipped` | Executor | Cascade-skipped due to dependency failure |

## Version-Aware Parsing

### Known Versions

| Version | Detection | Behavior |
|---------|-----------|----------|
| v1 | `schema_version` absent or `"1"` | Per-quest `workflow` field may be present. `generated_by` may use legacy name `"liang-brainstorm-campaign-cartographer"`. |
| v2 | `schema_version: "2"` | Per-quest `workflow` field. `current_step_started_at` may appear on quest entries. |
| v3 | `schema_version: "3"` | Campaign-level `workflow` field. Per-quest `workflow` fields are ignored if present. |

### Unknown Versions

When `schema_version` is present but not recognized:

1. Parse with best-effort: read all known fields, ignore unknown fields.
2. Display a WARN indicator on the campaign row.
3. Do not fail or skip the campaign.

### Absent `schema_version`

Treat as v1. No warning.
