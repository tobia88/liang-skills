# Brainstorm Family Criteria

The brainstorm family's own data for the family audit. Generic wording of the criteria,
the edit classes, the done bar, and the findings schema live in
`_family-audit/criteria-common.md` at the liang-skills root; this file only says what
they mean **for `liang-brainstorm-*`**.

**Maintainers and the audit only.** No brainstorm variant reads `references/family/` at
activation.

## Family block

Read by `_family-audit/preflight.py`. Paths are relative to the liang-skills root. Keys
this family does not declare (registry, skeleton, topology, decisions) switch the
matching checks off for it.

```yaml
family:
  name: brainstorm
  core: liang-brainstorm-core
  members_glob: "liang-brainstorm-*"
```

## C1 — canonical homes

| Contract | Canonical home |
|---|---|
| Question cadence | `liang-brainstorm-core/references/question-cadence.md` |
| Shared terminology | `liang-brainstorm-core/references/terminology.md` |
| Scout rules | `liang-brainstorm-core/references/scout-rules.md` |
| VCS artifact policy | `liang-brainstorm-core/references/vcs-policy.md` |
| Alignment-first protocol | `liang-brainstorm-core/references/alignment-protocol.md` |

## C5 — brainstorm conventions

- (a) **Activation checklist** with fail-stop wherever a variant consumes core references.
- (b) **JRPG flavor in HTML views only** — formal neutral terms in YAML, schema keys,
  and finding records.
- (c) **File-write segregation** as each skill documents it (core: never; quick: never;
  relentless: finalization only).
- (d) **Invocation-only discovery** — no routers, no startup detection, no
  cross-references added to adjacent skills.
- (e) **Anti-centralization** — variant-specific terms and behaviors stay inline in
  their variant. Never merge into core anything the drift ledger marks variant-local.
