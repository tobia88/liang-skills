# Built-in Rubric and Finding Schema

Reference document for the Liang Skill Blacksmith. Source of truth for every
built-in quality check and the data structure for findings.

Checks run on one of two engines:

| Engine | Who runs it | Checks |
|--------|-------------|--------|
| `mechanical` | Bundled script `scripts/check_skill.py` — deterministic, never emulated by hand | L1-01, L1-02, L1-03, L1-04, L2-01, L2-03, L2-04 |
| `judgment` | The inspecting agent, reading the file directly | L2-02, L3-01, L3-02, L3-03 |

For mechanical checks, the script is the source of truth for exact detection
mechanics (normalization, alias matching, thresholds). The tables below
describe intent and scope.

## Severity and Fixability

| Tier | Meaning | Default Action |
|------|---------|---------------|
| `critical` | Structural or consistency defect; must-fix | Shown prominently in the report |
| `advisory` | Improvement suggestion; not a defect | Shown but visually de-emphasized |

When in doubt, assign `advisory`.

| Fixable | Meaning |
|---------|---------|
| `yes` | The fix is an edit to existing text; the finding enters fix planning with a before/after diff |
| `no` | A fix would require generating new content (forbidden by the boundaries); the finding is **report-only** and never enters fix planning |

## Layer 1: Structural Checks

| ID | Check | Severity | Fixable | Engine | Intent |
|----|-------|----------|---------|--------|--------|
| L1-01 | Valid YAML frontmatter | critical | yes | mechanical | Frontmatter must parse as YAML with non-empty `name` and `description`. Formatting defects are fixable; if a field's content is genuinely absent, mark the finding `deferred` — inventing content is forbidden. |
| L1-02 | Required sections present | advisory | no | mechanical | The 8 canonical H2 sections expected in workflow-style SKILL.md files: Core Contract, Activation, Startup Flow, Boundaries, Failure Modes, Visual Tone, Relationship to Other Skills, Reference Files. Aliases accepted (e.g. Execution Flow, Error Handling, Reference Index). Hub and tool skills with intentionally different shapes should disable this check via `rubric-override.md`. |
| L1-03 | No orphan sections | advisory | yes | mechanical | Every H2 heading should match a canonical or known-optional section. Fix is limited to renaming the heading to a canonical form; if the section is genuinely skill-specific, mark it `deferred` and suggest an override entry. |
| L1-04 | Consistent heading hierarchy | advisory | yes | mechanical | No skipped heading levels (e.g. H2 followed directly by H4). |

## Layer 2: Language Checks

Scope for L2-01, L2-02, L2-03: directive sections — headings containing
Boundaries, Core Contract, Activation, Failure Modes, Hard Stops, Non-Goals,
or Error Handling. Fenced code, YAML blocks, and table rows are excluded.

| ID | Check | Severity | Fixable | Engine | Intent |
|----|-------|----------|---------|--------|--------|
| L2-01 | Long sentences | advisory | yes | mechanical | Sentences exceeding 40 words in directive sections. |
| L2-02 | Passive voice in directives | advisory | yes | judgment | Rules should use active imperative voice. Flag sentences where a passive construction ("is applied", "should be done") replaces a command verb. Judge in context; do not flag passives inside quoted examples or descriptions of state. |
| L2-03 | Vague quantifiers | advisory | yes | mechanical | Flag: various, some, etc., and so on, things, stuff, many, several, a number of, a lot of. |
| L2-04 | Duplicate phrasing | advisory | yes | mechanical | Sentence pairs (over 10 words) within one file sharing at least 80% of significant words after stopword removal. |

## Layer 3: Cross-Skill Consistency Checks

Layer 3 requires batch mode with 2+ selected files. In single-file mode, skip
Layer 3 and note that cross-skill checks need batch mode. All Layer 3 checks
are judgment checks: run them after Pass A, using the file content already
read.

| ID | Check | Severity | Fixable | Engine | Intent |
|----|-------|----------|---------|--------|--------|
| L3-01 | Terminology drift | critical | yes | judgment | Key terms must be consistent across sibling skills. For each term appearing in 2+ files, verify consistent spelling and casing (e.g. "Quest Contract" vs "Quest Brief"). Flag only genuinely differing forms, not frequency differences. |
| L3-02 | Boundary consistency | critical | yes | judgment | Shared boundary declarations must use aligned wording and scope. Compare boundary sections (Boundaries, Hard Stops, Non-Goals) across files; flag the same conceptual boundary expressed with conflicting language or coverage. |
| L3-03 | Shared convention adherence | advisory | yes | judgment | Family conventions should be consistent: (a) YAML-in-HTML-comment references, (b) confirmation-before-acting prompt pattern, (c) reference file section format. Flag deviations from the majority pattern among the selected files. |

## Finding Record Schema

Each finding is a structured record:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `finding_id` | string | yes | Unique within the run: `f` + zero-padded sequence (e.g. `f001`) |
| `check_id` | string | yes | Rubric check that triggered this finding (e.g. `L1-01`) |
| `layer` | integer | yes | `1`, `2`, or `3` |
| `severity` | string | yes | `"critical"` or `"advisory"`, after any override adjustment |
| `fixable` | boolean | yes | Inherited from the check definition (see Severity and Fixability) |
| `file` | string | yes | Path to the SKILL.md file |
| `location` | string | yes | Section heading + line number (e.g. `## Boundaries, line 47`) |
| `description` | string | yes | Human-readable description of the specific finding |
| `evidence` | string | yes | The exact text that triggered the finding, trimmed to the relevant excerpt |
| `before_text` | string | no | Exact current text span for the fix; must match the file uniquely (populated during fix planning, fixable findings only) |
| `after_text` | string | no | Proposed replacement text (populated during fix planning) |
| `status` | string | yes | `"new"` on creation; then `"fixed"`, `"deferred"` (report-only or declined), or `"stale"` (before_text no longer matched at apply time) |

The mechanical script emits a subset of these fields; the inspecting agent
adds `finding_id` and `status`, and adjusts `severity`/`fixable` per any
override.

**Duplicate rule:** never record two findings with the same `check_id`,
`file`, and `evidence`. Compare the strings directly — no hashing.

**Grouping:** group findings by `file`, then by `layer`, for the report.

## Override File: `rubric-override.md`

A target skill may ship a `rubric-override.md` next to its SKILL.md. The
inspecting agent reads it after running the script and applies it to the
findings; the script itself never reads overrides.

Recognized sections (each optional):

```markdown
# Rubric Override

## Disable
- L1-02
- L1-03

## Severity Overrides
- L2-01: critical

## Additional Checks
| ID | Check | Severity | Fixable | Intent |
|----|-------|----------|---------|--------|
| X-01 | No TODO markers | advisory | yes | Flag TODO/FIXME left in prose. |
```

Rules:

- `Disable` drops every finding from the listed check IDs for that skill.
- `Severity Overrides` reassigns the tier of listed checks for that skill.
- `Additional Checks` are judgment checks run by the inspecting agent. IDs
  must use the `X-` prefix so they never collide with built-in IDs.
- If the file is absent, proceed with the built-in rubric and note the
  absence in the report header.
