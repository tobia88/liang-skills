---
name: liang-quest-core
description: Shared reference foundation for the JRPG quest planning family. Contains campaign protocol, manifest schema, plan schemas (TDD cycles + general steps), status transitions, child process contracts, run report format, and project.yaml contract. All four workflow-specific skills (TDD tactician, TDD executor, general tactician, general executor) read from this skill's references/ at activation time. This skill has no behavioral logic — it is a pure reference library.
---

# Liang Quest Core

You are the shared reference foundation for the JRPG quest planning family.

This skill contains **no behavioral logic**. It exists solely as a structured library of reference documents consumed by the four workflow-specific skills via reference inclusion.

## What This Skill Provides

| Subdirectory | Contents | Consumers |
|---|---|---|
| `references/campaign/` | Campaign protocol, manifest schema | All four workflow skills + Campaign Cartographer |
| `references/plan-schema/` | Common plan envelope, TDD cycle schema, general step schema | Both tacticians |
| `references/execution/` | Status transitions, child process contracts, run report format | Both executors |
| `references/project/` | `project.yaml` contract | All four workflow skills |

## Schema Version

**Current: schema_version: 3**

The quest planning family uses integer schema versioning. All skills reference the current version from this central declaration.

| Version | Changes |
|---------|---------|
| 1 | Initial schema. workflow is Required Core in both manifest and quest contract, assigned by the cartographer. |
| 2 | workflow moves from Required Core to Downstream-Stamped on quest entries. Tacticians and quick stamp workflow per quest in the manifest on first contact. Cartographer produces workflow-agnostic quest contracts. v1 campaigns remain valid; pre-existing workflow values are treated as informational. |
| 3 | workflow moves from quest-level to campaign-level. Tacticians and quick stamp workflow once at manifest top-level, not per quest. Executors check campaign-level workflow at startup instead of filtering per quest. Per-quest workflow fields in v1/v2 campaigns are ignored. |

Skills should check schema_version when parsing campaign artifacts and handle v1, v2, and v3 gracefully.

The declaration must be prominent and unambiguous -- any skill reading quest-core will see the current version immediately after the reference table.

## Five-Skill Family

| Skill | Role | Reads From Core |
|---|---|---|
| **liang-quest-core** | Shared references (this skill) | — |
| **liang-quest-tdd-tactician** | TDD planning: cycles, 9-item checklist spine | `campaign/`, `plan-schema/` |
| **liang-quest-general-tactician** | General planning: ordered steps, pre/postconditions, two-tier verification | `campaign/`, `plan-schema/` |
| **liang-quest-tdd-executor** | TDD execution: cycle processing, test_command verification | `campaign/`, `execution/` |
| **liang-quest-general-executor** | General execution: step processing, two-tier verification, lesson extraction | `campaign/`, `execution/` |

## Composition Mechanism

Workflow-specific skills consume core references via **reference inclusion** — they read the relevant subdirectories at activation time. This is not delegation or embedding; the core's documents become part of the consuming skill's context.

Each workflow skill reads only the subdirectories it needs:
- **Tacticians** read `campaign/` + `plan-schema/`
- **Executors** read `campaign/` + `execution/`
- **All skills** read `project/` for the project.yaml contract

## Reference Index

### campaign/
- `protocol.md` — Campaign lifecycle, quest flow, routing, and the Layered Truth principle.
- `manifest-schema.md` — Canonical manifest.yaml schema (Required Core + Optional Extensions).

### plan-schema/
- `common.md` — Shared plan envelope fields, difficulty vocabulary, readiness vocabulary, YAML conventions, schema versioning.
- `tdd-cycles.md` — TDD cycle plan schema: cycles[], 9-item and 5-item checklist spines, enriched fields.
- `general-steps.md` — General step plan schema: steps[], flat schema, pre/postconditions, two-tier verification marking.
- `test-approaches.md` — Test approaches registry schema: entry shapes, rules, validation for .liang/test-approaches.yaml.

### execution/
- `status-transitions.md` — Manifest status vocabulary, allowed transitions, executor-owned fields.
- `child-contracts.md` — Child process I/O contracts for all child types (execute, verify, re-plan) across both workflows.
- `run-report.md` — Run report schema and visual conventions shared by both executors.

### project/
- `project-yaml.md` — `.liang/project.yaml` schema, first-run interview contract, executor extensions.

## Boundaries

- This skill never plans, executes, or produces artifacts.
- This skill never modifies campaign files, manifests, or project config.
- This skill is never invoked directly by the user — it is consumed silently by other skills.
- All behavioral logic belongs in the workflow-specific skills, not here.

## YAML Conventions (Global)

All YAML across the family follows these rules:

- `snake_case` keys
- lowercase, ASCII only
- Formal names in schema keys (no JRPG metaphors — those stay in HTML views)
- ISO 8601 for all dates and timestamps
- VCS-neutral language in plan content (checkpoint, not commit/push/branch)
