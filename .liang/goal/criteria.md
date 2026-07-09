# /goal Criteria — liang skill family invariants

Consumed by the `/goal` command, `preflight.py`, and judgment children. This file is
the sole source of what `/goal` checks. Never invent checks beyond it.

Each criterion: ID, invariant, check method (`script` = preflight.py, `model` =
judgment child), default severity.

## C1 — Single source of truth (script + model, critical)

Every shared contract has exactly one canonical definition in a `*-core` reference.
Consumers may restate at most one summary line, and that line must carry a citation
to the canonical path.

Preflight flags candidate duplicates via shingle similarity (8-word shingles across
all family `SKILL.md` and `references/*.md` files); a judgment child decides
restatement-vs-orchestration for each flagged pair. Known canonical homes:

| Contract | Canonical home |
|---|---|
| Status vocabulary & transitions | `liang-quest-core/references/execution/status-transitions.md` |
| Difficulty criteria | `liang-quest-core/references/campaign/difficulty-guide.md` |
| Manifest schema | `liang-quest-core/references/campaign/manifest-schema.md` |
| Campaign protocol / layout | `liang-quest-core/references/campaign/protocol.md` |
| Child process I/O | `liang-quest-core/references/execution/child-contracts.md` |
| project.yaml contract | `liang-quest-core/references/project/project-yaml.md` |
| Question cadence | `liang-brainstorm-core/references/question-cadence.md` |
| Shared terminology | `liang-brainstorm-core/references/terminology.md` |
| Scout rules | `liang-brainstorm-core/references/scout-rules.md` |
| VCS artifact policy | `liang-brainstorm-core/references/vcs-policy.md` |
| Alignment-first protocol | `liang-brainstorm-core/references/alignment-protocol.md` |

## C2 — Reference integrity (script, critical)

- Every cross-skill citation resolves to an existing file.
- Source attributions use the section-anchor form — `<file> § <heading> per dcNNN` —
  and the cited heading exists in the cited file. Line-number attributions
  (`lines N-M`) are themselves a finding: migrate to anchor form (mechanical).
- dc/dv decision numbers are unique family-wide.

## C3 — Harness neutrality (script + model, critical)

These skills run under both Claude Code and pi, with non-Claude models routed via
`project.yaml`. Therefore:

- No vendor model name (`sonnet|opus|haiku|claude-*|deepseek-*|gpt-*|gemini-*`) in
  skill prose. Model selection routes only via `project.yaml models.*` with a
  documented fallback chain ending in "harness default" (pattern: planner
  body-drafter; resolution chains, never single pins).
- Every delegation point declares both paths: Claude subagent AND pi sub-process
  (`pi --print`/`pi --model`) or an inline fallback.
- Exception: documentation of the `claude_mode` mapping itself may name Claude tier
  aliases — scoped by ledger entry dv006, not by judgment.

## C4 — Token budget / progressive disclosure (script + model, advisory)

- SKILL.md is orchestration-only; contracts live in `references/`. Soft cap **280
  lines** per SKILL.md — exceeding produces an advisory finding proposing extractions.
- Frontmatter `description` ≤ 120 words.
- No dead weight inside skill dirs: `__pycache__/`, `*.pyc`, `*.legacy`, or files in
  `references/` cited by nothing (mechanical removal findings).

## C5 — Convention conformance (model, critical)

Family conventions to enforce:

- (a) **Activation checklist** with fail-stop wherever a skill consumes core references.
- (b) **JRPG flavor in HTML views only** — formal neutral terms in YAML, schema keys,
  and finding records.
- (c) **File-write segregation** as each skill documents it (core: never; quick:
  never; relentless: finalization only; etc.).
- (d) **Invocation-only discovery** — no routers, no startup detection, no
  cross-references added to adjacent skills.
- (e) **Anti-centralization** — variant-specific terms and behaviors stay inline in
  their variant. Never merge into core anything the drift ledger marks variant-local.

When unsure whether a divergence is intentional, emit an `open-question` finding
instead of a fix — open questions are candidates for new ledger entries, decided by
the user, never by `/goal`.

## C6 — Edit classes (apply-time enforcement)

- **mechanical** — meaning-preserving by construction: citation swaps,
  dedup-to-citation, dead-file removal, attribution migration, typo/format fixes.
  Auto-apply in refine mode.
- **structural** — new reference files, content extraction/moves, multi-file
  lockstep edits. One batch approval for the whole changeset; applied all-or-nothing
  with a file-hash staleness gate (hash at preflight time; refuse stale files).
- **behavioral** — changes what a skill does: flow, gates, options, boundaries,
  schemas. Out of scope except under `enhance "<goal>"`, and then only edits serving
  the named goal.

## Findings schema

Shared by preflight.py, judgment children, and the run report (`findings.yaml`):

```yaml
findings:
  - id: f-c2-001            # f-<criterion>-<seq>
    criterion: C2
    severity: critical      # critical | advisory | open-question
    class: mechanical       # mechanical | structural | behavioral | judgment-needed
    file: "liang-brainstorm-core/references/question-cadence.md"
    location: "line 3"      # heading or line
    summary: "line-number attribution; migrate to section-anchor form"
    excerpt: |
      ...
    proposed_fix:           # null until planned
      before: "..."
      after: "..."
suppressed:                 # findings matched by drift-ledger suppressions
  - id: f-c3-004
    ledger: dv006
stats: {files_scanned: 0, critical: 0, advisory: 0, judgment_needed: 0}
```

## Severity → report mapping

`critical` = breaks an invariant now. `advisory` = budget/style. `open-question` =
needs a human ruling. Exit codes (family convention): 0 = clean or advisory-only,
1 = critical findings, 2 = config error.
