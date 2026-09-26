# Drift Ledger — cross-family rulings

Intentional divergences that involve **two** families. Single-family rulings live in that
family's `liang-<family>-core/references/family/drift-ledger.md`. Anything matching an
entry in any ledger is not a finding; the audit cites the dv ID when skipping. Only the
user rules on entries; the audit may propose candidates via `open-question` findings.
dv IDs are unique across all ledgers.

| ID | Scope | Ruling | Review trigger |
|----|-------|--------|----------------|
| dv007 | core-skill boundary boilerplate | Both `liang-*-core` SKILL.md files share the "shared reference foundation / no behavioral logic / never invoked directly / pure reference library" preamble and boundary prose verbatim — parallel family convention for pure-reference cores. | A third *-core skill is added |
| dv009 | invocation-only activation clause | The "Activate only when: 1. The user explicitly invokes this skill by name" clause is shared family-wide — convention boilerplate, no canonical home warranted for a one-sentence clause. | The invocation-only discovery model changes |
| dv010 | secrets/build-outputs hard-stop | The "secrets, `.env`, `.env.*`, `.git/`, credentials, tokens, dependency folders, build outputs, or large binaries" hard-stop clause is carried identically by skills in both families — shared security boundary; extracting it would create a cross-family dependency the invocation-only convention prohibits. | A family-wide security-policy reference is introduced in a shared core |

## Machine-readable suppressions

Consumed by `preflight.py`.

`convention_lines` — phrases both families carry verbatim under dv009 / dv010. The phrase
itself (never the rest of its line) is left out of the C1 shingle check in every scanned
file, which is what rules these two clauses; they need no per-pair entries.

`pair_suppressions` — for the C1 shingle-duplication check: a finding whose file pair
matches (order-insensitive) AND whose shared-shingle count is <= `max_shingles` is
suppressed with the dv id. A count ABOVE `max_shingles` fires the finding anyway — growth
beyond current level + headroom means new duplication, not known boilerplate.

```yaml
convention_lines:
  - id: dv009
    phrase: "explicitly invokes this skill by name"
  - id: dv010
    phrase: "dependency folders, build outputs, or large binaries"

pair_suppressions:
  - id: dv007
    check: shingle-duplication
    files: ["liang-brainstorm-core/SKILL.md", "liang-quest-core/SKILL.md"]
    max_shingles: 45
```
