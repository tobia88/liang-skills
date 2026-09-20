# Drift Ledger — quest family

Intentional divergences inside `liang-quest-*`. Anything matching an entry here is
**not** an audit finding; the audit cites the dv ID when skipping. Cross-family rulings
live in `_family-audit/drift-ledger.md`. Only the user rules on entries; the audit may
propose candidates via `open-question` findings. dv012 and dv013 were drafted by Claude and
confirmed by the user on 2026-09-20. dv IDs are unique across all ledgers.

| ID | Scope | Ruling | Review trigger |
|----|-------|--------|----------------|
| dv006 | claude_mode docs | `liang-quest-core/references/project/project-yaml.md` is the one file that may name Claude tier aliases (haiku/sonnet/opus) — in documenting the `claude_mode` mapping, and inside the example model ids of its Full Example block. Every other file cites it. | claude_mode is removed or renamed |
| dv011 | pipeline relationship descriptions | Quest-family skills each state their own view of the planner → executor / batch-sweep graph and shared-contract listings in their Relationship sections; mirrored phrasing is intentional topology documentation. The ladder itself is not covered — it is cited from `topology.md`. | Pipeline topology changes (skill inserted or retired) |
| dv012 | quest convention boilerplate | Boilerplate phrases the family conventions produce, identical wherever they appear — the core-read fail-stop line (C5a), the "User invokes by name" activation lead-in, and the "This skill must never" boundaries lead-in (C8 skeleton) — are not duplication. They are listed under `convention_lines` in `criteria.md`'s family block; the phrase itself, never the rest of its line, is left out of the C1 shingle check in quest files, together with all headings. | A convention line changes wording, or a new mandated line is added |
| dv013 | planner SKILL.md length | `liang-quest-planner/SKILL.md` may run to 310 lines. Moving the quick or headless mode out would put a second hop in front of the saga planner's headless subagents, so the modes stay. Known debt, not yet paid: the "every rendered plan.html must contain" list and the validator check list restate `html-design-contract.md` §7 and §4, and the nine-field Decision Summary shape (copied by the saga planner) has no reference file of its own — extracting those would bring the file near 285 lines. | It passes 310 lines, a mode grows its own sub-flow, or the known debt is paid (then drop this entry) |

## Machine-readable suppressions

Consumed by `_family-audit/preflight.py`. Each rule suppresses matches of `check` in
files matching `file_glob` (paths relative to the liang-skills root, forward slashes).
Pair suppressions follow the `max_shingles` rule described in the cross-family ledger.

```yaml
# dv006 has no entry here: the script builds the alias allowance from the family block's
# alias_home / alias_ledger_id, so the two cannot drift apart.
suppressions:
  - id: dv013
    check: line-budget
    file_glob: "liang-quest-planner/SKILL.md"
    max_lines: 310

pair_suppressions:
  - id: dv011
    check: shingle-duplication
    files: ["liang-quest-batch-sweep/SKILL.md", "liang-quest-executor/SKILL.md"]
    max_shingles: 14
```
