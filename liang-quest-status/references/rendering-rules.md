# Adaptive Rendering Rules

Source of truth for how the status skill adapts its display format based on
campaign state. The skill produces adaptive-density output: compact for
fully-passed campaigns, expanded for campaigns needing attention.

## Display Modes

### Compact Mode (Single-Line)

**Trigger:** All quests in the campaign have `status: passed`.

**Format:** One line per campaign in the prescribed table format showing:
campaign title, quest count, completion percentage, and elapsed time (if available).

### Expanded Mode (Full Detail)

**Trigger:** Any quest in the campaign has a non-`passed` status.

**Format:** Campaign header line followed by per-quest detail rows showing:
quest title, status, attention tier, and progress information
(`current_cycle`/`total_cycles` if available).

## Prescribed Table Format

The dashboard uses a fixed markdown table with these columns:

### Campaign Summary Table

| Column | Content | Notes |
|--------|---------|-------|
| Campaign | Title | Campaign title from manifest |
| Quests | N total | Total quest count |
| Done | N% | Completion percentage |
| Tier | ALERT/ACTIVE/INFO/PASSED | Highest severity tier |
| Elapsed | Duration or `-` | Total elapsed time if available |

### Quest Detail Rows (Expanded Mode Only)

Indented below the campaign row for non-passed campaigns:

| Column | Content | Notes |
|--------|---------|-------|
| Quest | Title | Quest title from manifest |
| Status | Status value | Raw status string |
| Progress | N/M or `-` | current_cycle/total_cycles if available |

## Derived Statistics

### Completion Percentage

```
completion_pct = count(quests where status == "passed") / count(all quests) * 100
```

Displayed per campaign. Round to nearest integer. Show as `N%`.

**Empty quest lists:** When a manifest has zero quests (`count(all quests) == 0`), display `0%` with a `[WARN] empty` indicator. Never divide by zero — guard the computation before computing the percentage.

### Total Elapsed Time

When timing data is available on quests:

```
elapsed = max(completed_at across all quests) - min(started_at across all quests)
```

Display as human-readable duration (e.g., `12m`, `1h 23m`).
When timing data is absent, display `-`.

## Output Ordering

### Campaign Order

1. Attention campaigns first, ordered by tier severity: ALERT > ACTIVE > INFO
2. Passed campaigns after, ordered newest-first by `created_at`

### Quest Order Within Campaign

Quests are displayed in topological dependency order:

1. Sort by `depends_on` graph: quests with no dependencies first
2. Dependent quests follow their prerequisites
3. Within the same dependency level, maintain manifest order

**Dependency cycles:** If the `depends_on` graph contains a cycle (e.g., A depends on B, B depends on A), the topological sort is impossible. In this case, emit a `[WARN] cycle` indicator and fall back to manifest order for all quests in that campaign. Do not crash, infinite-loop, or skip the campaign.

## Self-Compression

The dashboard adapts total output length based on campaign count:

- **Few campaigns (1-5):** Show expanded detail for all non-passed campaigns
- **Many campaigns (6+):** Show expanded detail only for ALERT and ACTIVE
  campaigns; INFO campaigns use compact mode; PASSED campaigns always use
  compact mode

## Error Rendering

### Missing/Malformed Manifests

When a `manifest.yaml` cannot be parsed (invalid YAML, missing file):

- Display an inline ERROR row with the campaign directory name
- Include the error type (parse error, missing file)
- Continue processing remaining campaigns

### Unknown Schema Version WARN

When `schema_version` is present but unrecognized:

- Display a WARN indicator next to the campaign title
- Parse with best-effort (see field-registry.md Version-Aware Parsing)
- Do not fail or skip the campaign
