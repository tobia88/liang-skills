# Family Audit — common rules

Generic rules shared by every liang skill family. Family-specific data (canonical homes,
registry, skeleton, topology, ledger rulings) lives in that family's own core at
`liang-<family>-core/references/family/`. This folder is not a skill: the leading
underscore keeps harnesses from loading it, and nothing in it is read at skill activation.

Consumed by `preflight.py`, the `/goal` command, and judgment children. Together with
each family's `criteria.md` it is the sole source of what gets checked — never invent
checks beyond them.

## Layout

```
_family-audit/
  criteria-common.md   this file — criteria C1–C9 in generic form, edit classes, findings schema
  drift-ledger.md      rulings that span two families
  check-brief.yaml     input envelope for a judgment child (Claude subagent or `pi --print`)
  preflight.py         deterministic audit; reads every liang-*-core/references/family/
liang-<family>-core/references/family/
  criteria.md          the family's data block + family-specific wording of the criteria
  drift-ledger.md      the family's own rulings
  topology.md          (optional) canonical ladder / feed graph
  decisions.md         (optional) log of behavioral changes
.liang/goal/runs/      audit output — gitignored, machine-local
```

Adding a family = adding `references/family/criteria.md` (with a `family:` block) and
`drift-ledger.md` to its core. A check whose data key is absent from the block is skipped
for that family.

## Criteria (generic form)

Each criterion: ID, invariant, check method (`script` = preflight.py, `model` = judgment
child or reviewer), default severity.

- **C1 — Single source of truth** (script + model, critical). Every shared contract has
  exactly one canonical definition in a `*-core` reference. Consumers restate at most
  one summary line, and that line carries a citation to the canonical path. Preflight
  flags candidate duplicates by 8-word shingle similarity across skills; a judgment call
  decides restatement-vs-orchestration per flagged pair. Canonical homes: the family's
  `criteria.md`.
- **C2 — Reference integrity** (script, critical). Every cross-skill citation resolves to
  an existing file. Attributions use section-anchor form — `<file> § <heading>`,
  optionally `per dcNNN` — and the heading exists (a citation may name a heading by its
  leading words, two or more, or a numbered section by its number: `§7c`; a heading written
  in backticks is not machine-checked); line-number attributions are themselves a finding. Ledger
  ids (`dvNNN`) are unique across every ledger, and decision-log ids are unique in their
  log. `dcNNN` numbers are campaign-scoped and are not checked for uniqueness.
- **C3 — Harness neutrality** (script + model, critical). Skills run under both Claude
  Code and pi, with non-Claude models routed via `project.yaml`.
  - No vendor model name in skill prose **or in scripts** (`.js`, `.py`) inside a skill
    dir. Model selection routes only via `project.yaml models.*` with a documented
    fallback chain ending in "harness default". A script never hardcodes a default
    model: an absent model means the call carries none and inherits the harness default.
  - Claude tier aliases may be named in exactly one file per family — the `alias_home`
    its family block declares, under the ledger id in `alias_ledger_id`. The script
    builds that allowance from the block; no other suppression may widen it.
  - Harness words ("Claude-only", "Claude harness") are not model pins.
  - Every delegation point declares both paths: Claude subagent AND pi sub-process
    (`pi --print` / `pi --model`) or an inline fallback. Declared, not proven
    equivalent.
- **C4 — Token budget / progressive disclosure** (script + model, advisory). SKILL.md is
  orchestration-only, soft cap **280 lines**; frontmatter `description` ≤ **120 words**
  (it loads into every session on every harness — say what the skill is and when to
  trigger it, nothing else). No dead weight inside skill dirs: `__pycache__/`, `*.pyc`,
  `*.legacy`, or reference files cited by nothing. A ledger may raise one file's line cap
  (`check: line-budget`); the audit records that skip under the dv id.
- **C5 — Convention conformance** (script + model, critical). Family conventions as the
  family's `criteria.md` lists them. A phrase a convention requires verbatim is declared
  as a `convention_lines` entry — in a family block for that family's files, or in the
  cross-family ledger for every file — and only the phrase itself, never the rest of its
  line, is left out of the C1 shingle check. Headings are left out too. When unsure
  whether a divergence is intentional, emit an `open-question` finding instead of a fix.
- **C6 — Edit classes** (apply-time). See below. Every **behavioral** change is recorded
  as one row in the family's `decisions.md` when the family keeps one.
- **C7 — Family registry** (script, critical). Every skill dir matching the family's
  `members_glob` is named in the family's `registry_file`, and every `project.yaml` key a
  member reads (`models.<key>`, `claude_mode.<key>`) is documented in the family's
  `project_yaml_contract`.
- **C8 — Section skeleton** (script, critical). Every member SKILL.md carries the
  family's `skeleton.required_h2` headings (prefix match, any order, free sections in
  between). Skills listed under `skeleton.exempt` are skipped.
- **C9 — Canonical topology** (script + model, critical). The family's ladder and feed
  graph are defined once, in its `topology_file`. A skill may keep its own
  "Relationship to Other Skills" view, but a ladder statement anywhere else is one
  summary line that cites the topology file.

## Edit classes (C6)

- **mechanical** — meaning-preserving by construction: citation swaps,
  dedup-to-citation, dead-file removal, attribution migration, typo/format fixes.
  Auto-apply in refine mode.
- **structural** — new reference files, content extraction/moves, multi-file lockstep
  edits. One batch approval for the whole changeset; applied all-or-nothing with a
  file-hash staleness gate (hash at preflight time; refuse stale files).
- **behavioral** — changes what a skill does: flow, gates, options, boundaries, schemas.
  Out of scope except under `enhance "<goal>"`, and then only edits serving the named
  goal. Logged in `decisions.md`.

## Aligned — the done bar

A family is **aligned** when preflight reports zero critical findings for it, and every
advisory is either fixed or ruled on in a drift ledger. Criteria that no script can prove
(C3 delegation paths, C5 conventions, C9 wording) are proven by one fresh-context,
read-only reviewer per skill that tries to fail it against these files.

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

`critical` = breaks an invariant now. `advisory` = budget/style. `open-question` = needs
a human ruling. Exit codes (family convention): 0 = clean or advisory-only, 1 = critical
findings, 2 = config error.
