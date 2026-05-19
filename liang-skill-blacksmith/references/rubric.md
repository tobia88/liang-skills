# Built-in Rubric and Finding Schema

Reference document for the Liang Skill Blacksmith. Source of truth for every
built-in quality check and the data structure for findings. Downstream quests
(q002, q003, q004) consume this as their foundation.

## Severity Tiers

| Tier | Meaning | Default Action |
|------|---------|---------------|
| `critical` | Structural or consistency defect; must-fix | Always included in the Appraisal |
| `advisory` | Improvement suggestion; not a defect | Included but visually de-emphasized |

When in doubt, assign `advisory`.

## Layer 1: Structural Checks

| ID | Check | Severity | Description | Detection Criteria |
|----|-------|----------|-------------|--------------------|
| L1-01 | Valid YAML frontmatter | critical | Frontmatter must parse as valid YAML with `name` and `description` fields | Parse the YAML block between the opening `---` markers. Fail if: (a) no YAML frontmatter block found, (b) YAML does not parse, (c) `name` field is missing or empty, (d) `description` field is missing or empty. |
| L1-02 | Required sections present | critical | The 8 standard sections expected in every SKILL.md | Scan for H2 headings matching (case-insensitive): Core Contract, Activation, Startup Flow, Boundaries, Failure Modes, Visual Tone, Relationship to Other Skills, Reference Files. Report each missing heading as a separate finding. |
| L1-03 | No orphan sections | advisory | Every H2 heading should map to a recognized section | Collect all H2 headings. Compare against the recognized set: the 8 required sections plus known optional sections (Terminology, Design Principle, Plan YAML Shape, Workflow Detail). Flag any H2 heading not in the recognized set. Suggest marking it as skill-specific or mapping it to a standard section. |
| L1-04 | Consistent heading hierarchy | advisory | No skipped heading levels | Walk the heading tree top-to-bottom. Flag any jump that skips a level (e.g., H2 directly followed by H4 with no intervening H3). Report the specific heading text and levels involved. |

## Layer 2: Language Checks

| ID | Check | Severity | Description | Detection Criteria |
|----|-------|----------|-------------|--------------------|
| L2-01 | Long sentences | advisory | Sentences exceeding 40 words in rule/directive sections | Scope: sections titled Boundaries, Core Contract, Activation, Failure Modes, and any section containing numbered rules or bullet-point directives. Count words per sentence (split on sentence-ending punctuation followed by whitespace). Flag sentences exceeding 40 words. Exclude fenced code blocks and YAML blocks. |
| L2-02 | Passive voice in directives | advisory | Rules and directives should use active imperative voice | Scope: same as L2-01. Flag sentences containing passive constructions: forms of "be" (is, are, was, were, be, been, being) followed by a past participle pattern. Focus on imperative contexts: bullet points starting with articles or passive constructions instead of command verbs. |
| L2-03 | Vague quantifiers | advisory | Imprecise words that weaken directives | Scope: same as L2-01. Flag occurrences of: "various", "some", "etc.", "and so on", "things", "stuff", "many", "several", "a number of", "a lot of". Report the specific word and its surrounding sentence. Exclude quoted examples and fenced code blocks. |
| L2-04 | Duplicate phrasing | advisory | Substantially similar sentences within the same file | Compare every non-trivial sentence (more than 10 words) against all other sentences in the same file. Flag pairs with more than 80% word overlap after normalization (lowercase, stop-words removed). Report both locations. Exclude headings, fenced code blocks, and YAML blocks. |

## Layer 3: Cross-Skill Consistency Checks

These checks require batch mode with 2+ selected SKILL.md files. In single-file
mode, Layer 3 checks are skipped and the run notes that cross-skill checks require
batch mode.

| ID | Check | Severity | Description | Detection Criteria |
|----|-------|----------|-------------|--------------------|
| L3-01 | Terminology drift | critical | Key terms must be consistent across sibling skills | Build a canonical term list from all selected files. For each term appearing in 2+ files, verify consistent spelling and casing. Flag variant forms (e.g., "Quest Contract" vs "Quest Brief", "plan.html" vs "plan file"). Only flag terms with genuinely differing forms, not mere frequency differences. |
| L3-02 | Boundary consistency | critical | Shared boundary declarations must use aligned wording and scope | Identify boundary sections (headings containing "Boundaries", "Hard Stops", "Non-Goals", "Never") across all selected files. For each conceptual boundary appearing in 2+ files, compare wording and scope. Flag mismatches where the same boundary uses different language or coverage. |
| L3-03 | Shared convention adherence | advisory | Common patterns should be consistent across the skill family | Check conventions across all selected files: (a) YAML-in-HTML-comment references, (b) Git/privacy prompt phrasing, (c) open prompt pattern (confirmation before acting), (d) reference file section format. Flag deviations from the majority pattern among selected files. |

## Finding Record Schema

Each finding is a structured record:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `finding_id` | string | yes | Unique within the run: `f` + zero-padded sequence (e.g., `f001`) |
| `check_id` | string | yes | Rubric check that triggered this finding (e.g., `L1-01`) |
| `layer` | integer | yes | Discovery layer: `1`, `2`, or `3` |
| `severity` | string | yes | `"critical"` or `"advisory"` (inherited from the check definition) |
| `file` | string | yes | Absolute path to the SKILL.md file |
| `location` | string | yes | Section heading + approximate line range (e.g., `## Boundaries, lines 45-48`) |
| `description` | string | yes | Human-readable description of the specific finding |
| `evidence` | string | yes | The exact text that triggered the finding (trimmed to relevant excerpt) |
| `before_text` | string | no | Original text span for diff rendering (populated during fix planning phase) |
| `after_text` | string | no | Proposed replacement text (populated during fix planning phase) |
| `cycle_discovered` | integer | yes | Which cycle first discovered this finding (1 through 5) |
| `status` | string | yes | Lifecycle: `"new"` on creation, then `"fixed"` or `"deferred"` |
| `dedup_key` | string | yes | Computed dedup key (see Dedup Logic below) |

### Field Usage Notes

- **Grouping:** Group findings by `file`, then by `layer` for the Appraisal report.
- **Diff rendering:** `before_text` and `after_text` are null during discovery and
  populated during fix planning. The Appraisal report renders these as side-by-side
  or inline diffs.
- **Severity filtering:** The report displays critical findings prominently; advisory
  findings are visually de-emphasized but still shown.

## Dedup Logic

The dedup gate is the mechanical stop condition for the discovery loop.

### Dedup Key Computation

```
dedup_key = hash( check_id + ":" + normalize(file) + ":" + normalize(evidence) )
```

Where:
- `normalize(file)` = lowercase, forward-slash path separators, trim trailing slashes
- `normalize(evidence)` = trim leading/trailing whitespace, collapse internal
  whitespace to single spaces, lowercase
- `hash` = deterministic string hash (SHA-256 truncated to first 16 hex characters)

### Dedup Rules

1. Before recording a finding, compute its `dedup_key`.
2. Look up the key in the accumulated findings set for the current run.
3. If a finding with the same `dedup_key` exists, discard the new finding (duplicate).
4. A finding is "new" only if no prior finding shares its `dedup_key`.
5. At the end of each continuation cycle (cycles 4 and 5), count new findings added
   during that cycle. If zero new findings, terminate the discovery loop.

### Design Rationale

Content-based dedup (using `evidence` text) rather than position-based dedup
(using line numbers) because:
- Line numbers shift as the LLM reads files in different context windows across cycles
- The same finding may appear at slightly different line offsets in different cycles
- `check_id` scopes the comparison to prevent false dedup across unrelated checks
  that happen to flag similar text
