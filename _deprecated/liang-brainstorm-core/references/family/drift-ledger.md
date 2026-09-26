# Drift Ledger — brainstorm family

Intentional divergences inside `liang-brainstorm-*`. Anything matching an entry here is
**not** an audit finding; the audit cites the dv ID when skipping. Cross-family rulings
live in `_family-audit/drift-ledger.md`. Only the user rules on entries; the audit may
propose candidates via `open-question` findings. dv IDs are unique across all ledgers.

| ID | Scope | Ruling | Review trigger |
|----|-------|--------|----------------|
| dv001 | terminology | Variant-specific terms (quick: Pushback Budget, Scope-Creep Banner, Execution Brief; relentless: Planning Lenses, Save Points) stay inline in their variant, never centralized. Source: brainstorm-core `terminology.md` note. | A third brainstorm variant is created |
| dv002 | dialogue-hub | relentless does NOT read `dialogue-hub.md` yet — "may adopt" is recorded intent, not drift. | relentless adopts dialogue-hub; then update its Activation Checklist AND dialogue-hub.md's consumer note together |
| dv003 | vague/risky/contradiction handling | relentless keeps long-form examples; quick keeps one-line condensations. Same concept, intentionally different depth. Do not extract to core until a third consumer exists. | A third skill needs the conversion pattern |
| dv004 | vcs-policy | quick intentionally skips `vcs-policy.md` (zero file writes). Its absence from quick's Activation Checklist is correct. | quick ever gains file output |
| dv005 | scope-creep detection | quick-only heuristic; relentless uses lens selection instead. One-way escalation (quick → relentless) is by design. | — |
| dv008 | brainstorm activation checklist | quick and relentless carry an identical Activation Checklist preamble and core-reference file list with fail-stop — mandated by C5(a); identical wording is the invariant, not drift. | A variant reads a different core-reference set, or a fifth core reference is added |

## Machine-readable suppressions

Consumed by `_family-audit/preflight.py`. Pair suppressions follow the `max_shingles`
rule described in the cross-family ledger.

```yaml
pair_suppressions:
  - id: dv008
    check: shingle-duplication
    files: ["liang-brainstorm-quick/SKILL.md", "liang-brainstorm-relentless/SKILL.md"]
    max_shingles: 50
```
