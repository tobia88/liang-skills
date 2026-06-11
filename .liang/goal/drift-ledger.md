# Drift Ledger — intentional divergences

Anything matching an entry here is **not** a `/goal` finding. `/goal` cites the dv ID
when skipping. Only the user adds or removes entries; `/goal` may propose candidates
via `open-question` findings.

| ID | Scope | Ruling | Review trigger |
|----|-------|--------|----------------|
| dv001 | terminology | Variant-specific terms (quick: Pushback Budget, Scope-Creep Banner, Execution Brief; relentless: Planning Lenses, Save Points) stay inline in their variant, never centralized. Source: brainstorm-core `terminology.md` note. | A third brainstorm variant is created |
| dv002 | dialogue-hub | relentless does NOT read `dialogue-hub.md` yet — "may adopt" is recorded intent, not drift. | relentless adopts dialogue-hub; then update its Activation Checklist AND dialogue-hub.md's consumer note together |
| dv003 | vague/risky/contradiction handling | relentless keeps long-form examples; quick keeps one-line condensations. Same concept, intentionally different depth. Do not extract to core until a third consumer exists. | A third skill needs the conversion pattern |
| dv004 | vcs-policy | quick intentionally skips `vcs-policy.md` (zero file writes). Its absence from quick's Activation Checklist is correct. | quick ever gains file output |
| dv005 | scope-creep detection | quick-only heuristic; relentless uses lens selection instead. One-way escalation (quick → relentless) is by design. | — |
| dv006 | claude_mode docs | Files documenting the `claude_mode` mapping may name Claude tier aliases (haiku/sonnet/opus) in that context only. | claude_mode is removed or renamed |
| dv007 | core-skill boundary boilerplate | Both `liang-*-core` SKILL.md files share the "shared reference foundation / no behavioral logic / never invoked directly / pure reference library" preamble and boundary prose verbatim — parallel family convention for pure-reference cores. | A third *-core skill is added |
| dv008 | brainstorm activation checklist | quick and relentless carry an identical Activation Checklist preamble and core-reference file list with fail-stop — mandated by C5(a); identical wording is the invariant, not drift. | A variant reads a different core-reference set, or a fifth core reference is added |
| dv009 | invocation-only activation clause | The "Activate only when: 1. The user explicitly invokes this skill by name" clause is shared family-wide — C5(d) convention boilerplate, no canonical home warranted for a one-sentence clause. | The invocation-only discovery model changes |
| dv010 | secrets/build-outputs hard-stop | The "secrets, `.env`, `.env.*`, `.git/`, credentials, tokens, dependency folders, build outputs, or large binaries" hard-stop clause is carried identically by skills in both families — shared security boundary; extracting it would create a cross-family dependency C5(d) prohibits. | A family-wide security-policy reference is introduced in a shared core |
| dv011 | pipeline relationship descriptions | Quest-family skills each state their own view of the planner → executor / batch-sweep graph and shared-contract listings in their Relationship sections; mirrored phrasing is intentional topology documentation. | Pipeline topology changes (skill inserted or retired) |

## Machine-readable suppressions

Consumed by `preflight.py`. Each rule suppresses matches of `check` in files matching
`file_glob` (paths relative to the liang-skills root, forward slashes).

```yaml
suppressions:
  - id: dv006
    check: vendor-model-grep
    file_glob: "liang-quest-core/references/project/project-yaml.md"
    pattern: "haiku|sonnet|opus"
  - id: dv006
    check: vendor-model-grep
    file_glob: "liang-quest-core/references/execution/child-contracts.md"
    pattern: "haiku|sonnet|opus"
  - id: dv006
    check: vendor-model-grep
    file_glob: "liang-quest-executor/SKILL.md"
    pattern: "haiku|sonnet|opus"

# Pair suppressions for the C1 shingle-duplication check. A finding whose file
# pair matches (order-insensitive) AND whose shared-shingle count is <= max_shingles
# is suppressed with the dv id. A count ABOVE max_shingles fires the finding anyway —
# growth beyond current level + headroom means new duplication, not known boilerplate.
pair_suppressions:
  - id: dv007
    check: shingle-duplication
    files: ["liang-brainstorm-core/SKILL.md", "liang-quest-core/SKILL.md"]
    max_shingles: 45
  - id: dv008
    check: shingle-duplication
    files: ["liang-brainstorm-quick/SKILL.md", "liang-brainstorm-relentless/SKILL.md"]
    max_shingles: 50
  - id: dv009
    check: shingle-duplication
    files: ["liang-brainstorm-quick/SKILL.md", "liang-quest-batch-sweep/SKILL.md"]
    max_shingles: 12
  - id: dv010
    check: shingle-duplication
    files: ["liang-brainstorm-quick/SKILL.md", "liang-quest-executor/SKILL.md"]
    max_shingles: 20
  - id: dv011
    check: shingle-duplication
    files: ["liang-quest-batch-sweep/SKILL.md", "liang-quest-executor/SKILL.md"]
    max_shingles: 32
```
