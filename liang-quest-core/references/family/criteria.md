# Quest Family Criteria

The quest family's own data for the family audit. Generic wording of criteria C1–C9, the
edit classes, the done bar, and the findings schema live in
`_family-audit/criteria-common.md` at the liang-skills root; this file only says what
they mean **for `liang-quest-*`**.

**Maintainers and the audit only.** No family skill reads `references/family/` at
activation — it costs a running skill nothing.

## Family block

Read by `_family-audit/preflight.py`. Paths are relative to the liang-skills root.

```yaml
family:
  name: quest
  core: liang-quest-core
  members_glob: "liang-quest-*"
  registry_file: liang-quest-core/SKILL.md
  project_yaml_contract: liang-quest-core/references/project/project-yaml.md
  alias_home: liang-quest-core/references/project/project-yaml.md
  alias_ledger_id: dv006
  topology_file: liang-quest-core/references/family/topology.md
  decisions_file: liang-quest-core/references/family/decisions.md
  ladder_rungs: [saga, campaign, quest]
  skeleton:
    required_h2:
      - Core Contract
      - Activation
      - Boundaries
      - Relationship to Other Skills
      - Reference Files
    exempt: [liang-quest-core]
  core_read_checklist:
    section: Reference Files
    fail_stop_phrase: "stop and report"
  # Phrases a quest convention REQUIRES verbatim (ledger dv012). Only the phrase — never
  # the rest of its line — is left out of the C1 shingle check, and only in quest files.
  # The two cross-family clauses (dv009, dv010) are declared in _family-audit/drift-ledger.md.
  convention_lines:
    - "If a listed core file is missing, stop and report it."
    - "User invokes by name"
    - "This skill must never"
```

## C1 — canonical homes

| Contract | Canonical home |
|---|---|
| Status vocabulary & transitions | `liang-quest-core/references/execution/status-transitions.md` |
| Difficulty criteria | `liang-quest-core/references/campaign/difficulty-guide.md` |
| Manifest schema | `liang-quest-core/references/campaign/manifest-schema.md` |
| Campaign protocol / layout | `liang-quest-core/references/campaign/protocol.md` |
| Child process I/O | `liang-quest-core/references/execution/child-contracts.md` |
| project.yaml contract, model-resolution chains, Claude tier-alias defaults | `liang-quest-core/references/project/project-yaml.md` |
| Ladder and feed graph | `liang-quest-core/references/family/topology.md` |
| Recon artifact contract | `liang-quest-recon/references/artifacts.md` |
| Plan/saga HTML class contract | `liang-quest-planner/references/templates/class-contract.md` |

## C3 — harness neutrality, quest specifics

- **Alias home.** Claude tier aliases are named only in `project-yaml.md` § Model Routing
  Extensions. Everywhere else a default is written as "default per
  `liang-quest-core/references/project/project-yaml.md`" — never the alias itself.
- **Scripts.** Recon's Workflow scripts and the sweep/archive scripts carry no model
  default. Workflow scripts are Claude-only by nature, and that is fine — the skill that
  ships one must also declare the pi path for the same stage.
- **Delegation points** today: planner body-drafter, executor children (execute / verify
  / re-plan), saga-planner batch planners / alignment verifiers / rollup workers / saga body-drafter, recon
  stage workers, batch-sweep dispatch. Each names its Claude path and its pi path or
  inline fallback.

## C5 — quest conventions

- (a) **Reference Files is the core-read checklist.** Quest skills have no separate
  activation checklist: the `## Reference Files` section lists every
  `liang-quest-core/...` file the skill cites anywhere in its SKILL.md (cites of
  `references/family/` excepted — nothing reads those at run time), says when each is
  read (upfront or at the phase that needs it), and carries one fail-stop line: if a
  listed core file is missing, stop and report it. Core reliance is always written as a
  full path, never as "per core protocol".
- (b) **JRPG flavor in HTML views only** — formal neutral terms in YAML, schema keys, and
  finding records.
- (c) **File-write segregation** as each skill documents it (core: never; status: never;
  planner: its campaign folder; saga planner: its saga folder plus the one manifest
  patch; recon: its breakdown folder; executor: executor-owned manifest fields and run
  artifacts; batch-sweep: sweep reports, lock and logs, plus the retry-reset of quest
  statuses; archiver: moves under `archive/` and `.run/` ledger deletion). The planner,
  saga planner and executor may also bootstrap `project.yaml` through the first-run
  interview and write back the keys `project-yaml.md` names.
- (d) **Invocation-only discovery** — no routers, no startup detection. (The brainstorm
  family's "no cross-references to adjacent skills" clause does not apply here: quest
  skills name each other in their Relationship sections by design — ledger dv011.)
- (e) **Anti-centralization** — behavior specific to one skill stays in that skill;
  never merge into core anything a ledger marks skill-local.
- (f) **Files are the API between skills.** A downstream skill reads what an upstream
  skill wrote to disk, never its in-band return. Recon folders and finalized campaigns
  are frozen for their consumers.

## C7 — registry

`liang-quest-core/SKILL.md` § Family Skills names every `liang-quest-*` skill, and
§ Composition Mechanism says which core subfolders each one reads. `project-yaml.md`
documents every `models.*` / `claude_mode.*` key any member resolves.

## C8 — skeleton

The five required sections are the bookends of every quest SKILL.md except core (pure
library). Phase, stage, mode, and flag sections sit freely between them. Headings match
by prefix, so "Boundaries — Hard Stops" satisfies "Boundaries".

## C9 — topology

`topology.md` is the only place the ladder and the feed graph are defined. A skill keeps
its own "Relationship to Other Skills" section (its local view — ledger dv011), but a
ladder sentence in any other file is one line and cites `topology.md`.
