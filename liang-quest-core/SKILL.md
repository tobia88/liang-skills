---
name: liang-quest-core
description: Shared reference foundation for the JRPG quest planning family. Contains campaign protocol, manifest schema, plan schemas, status transitions, child process contracts, run report format, and project.yaml contract. The canonical pipeline skills (liang-quest-planner, liang-quest-executor) plus liang-quest-quick and liang-quest-status read from this skill's references/ at activation time. Deprecated cartographer/tactician/executor skills also read from here for in-flight campaigns. This skill has no behavioral logic — it is a pure reference library.
---

# Liang Quest Core

You are the shared reference foundation for the JRPG quest planning family.

This skill contains **no behavioral logic**. It exists solely as a structured library of reference documents consumed by the family skills via reference inclusion.

## What This Skill Provides

| Subdirectory | Contents | Primary Consumers |
|---|---|---|
| `references/campaign/` | Campaign protocol, manifest schema | All family skills (canonical + deprecated chain + quick + status) |
| `references/plan-schema/` | Common plan envelope, TDD cycle schema, general step schema, test approaches | Deprecated tacticians only — canonical pipeline does not use these (planner writes flat quest `.md` files instead) |
| `references/execution/` | Status transitions, child process contracts, run report format | Canonical executor + deprecated executors + quick |
| `references/project/` | `project.yaml` contract | Canonical executor + quick + deprecated chain |

## Schema Version

**Current: schema_version: 4**

The quest planning family uses integer schema versioning. All skills reference the current version from this central declaration.

| Version | Changes |
|---------|---------|
| 1 | Initial schema. `workflow` is Required Core in both manifest and quest contract, assigned by the cartographer. |
| 2 | `workflow` moves from Required Core to Downstream-Stamped on quest entries. Tacticians and quick stamp workflow per quest in the manifest on first contact. Cartographer produces workflow-agnostic quest contracts. v1 campaigns remain valid; pre-existing workflow values are treated as informational. |
| 3 | `workflow` moves from quest-level to campaign-level. Tacticians and quick stamp workflow once at manifest top-level, not per quest. Executors check campaign-level workflow at startup instead of filtering per quest. Per-quest workflow fields in v1/v2 campaigns are ignored. |
| 4 | **Canonical planner-native schema.** `workflow` field removed entirely — the canonical pipeline has a single executor and no workflow discriminator. Quest entries use `file` (path to a flat `quest-NNN-name.md`) instead of `path` (path to a per-quest folder's `index.html`). Quest entries carry `difficulty: easy\|medium\|hard` for downstream model routing. Status vocabulary tightens to `ready / in_progress / passed / failed / skipped` (no `ready_for_planning`/`planned`/`needs_clarification`/`blocked`). v1–v3 campaigns remain valid for in-flight cartographer-format work. |

Skills should check `schema_version` when parsing campaign artifacts and handle v1, v2, v3, and v4 gracefully. Canonical pipeline campaigns (v4) can also be detected structurally: no `workflow` field at any level, quest entries have `file` and `difficulty`, status is `ready`.

The declaration must be prominent and unambiguous — any skill reading quest-core will see the current version immediately after the reference table.

## Family Skills

### Canonical Pipeline (current)

| Skill | Role | Reads From Core |
|---|---|---|
| **liang-quest-core** | Shared references (this skill) | — |
| **liang-quest-planner** | Same-context campaign planner — extracts decisions from in-session conversation, writes `plan.html` + flat `quest-NNN-*.md` files + `manifest.yaml` | `campaign/` (manifest schema, protocol) |
| **liang-quest-executor** | Planner-native executor — spawns child processes per step (Pi CLI / Claude subagents / batch), tiered retry, quest-level VC verification with Tier 1 inline + Tier 2 deferred UAT | `campaign/`, `execution/`, `project/` |

### Live Sibling Pipelines

| Skill | Role | Reads From Core |
|---|---|---|
| **liang-quest-quick** | Single-pass executor for cartographer-format campaigns (per-quest folders with `index.html`). No planning layer, no children, no retries. | `campaign/`, `execution/`, `project/` |
| **liang-quest-status** | Read-only campaign status dashboard. Scans all manifests across all formats (v1–v4) and renders an adaptive markdown view. | `campaign/` (protocol) |

### Deprecated (retained for in-flight campaigns)

| Skill | Role | Status |
|---|---|---|
| **liang-quest-cartographer** | Cartographer-format campaign manifest writer | Deprecated — use `liang-quest-planner` for new work |
| **liang-quest-general-tactician** | Plans general-workflow `plan.html` per quest | Deprecated |
| **liang-quest-tdd-tactician** | Plans TDD-workflow `plan.html` per quest | Deprecated |
| **liang-quest-general-executor** | Executes general-workflow plans with child processes | Deprecated — use `liang-quest-executor` |
| **liang-quest-tdd-executor** | Executes TDD-workflow plans with child processes | Deprecated |

Each deprecated skill carries a DEPRECATED banner pointing to the canonical pair.

## Composition Mechanism

Family skills consume core references via **reference inclusion** — they read the relevant subdirectories at activation time. This is not delegation or embedding; the core's documents become part of the consuming skill's context.

- **Planner** reads `campaign/` (manifest schema, protocol).
- **Executor + quick + deprecated executors** read `campaign/`, `execution/`, `project/`.
- **Status** reads `campaign/` (protocol — for the campaign directory convention).
- **Deprecated tacticians** read `campaign/`, `plan-schema/`.

## Reference Index

### campaign/
- `protocol.md` — Campaign lifecycle, canonical (planner → executor) and deprecated (cartographer → tactician → executor) pipelines, Layered Truth principle.
- `manifest-schema.md` — Canonical (v4) and deprecated (v1–v3) manifest.yaml schemas. Canonical schema is the source of truth for new work.

### plan-schema/
> Used by the deprecated cartographer/tactician chain only. The canonical pipeline does not produce `plan.html` per quest — planner writes flat quest `.md` files instead.

- `common.md` — Shared plan envelope fields, difficulty vocabulary, readiness vocabulary, YAML conventions, schema versioning.
- `tdd-cycles.md` — TDD cycle plan schema (deprecated).
- `general-steps.md` — General step plan schema (deprecated).
- `test-approaches.md` — Test approaches registry schema (deprecated).

### execution/
- `status-transitions.md` — Manifest status vocabulary, allowed transitions (canonical + deprecated), executor-owned fields, tiered retry behavior.
- `child-contracts.md` — Child process I/O contracts. "Planner-Native" sections cover the canonical executor; sections below the deprecation banner cover the deprecated TDD/general executors.
- `run-report.md` — Run report schema and visual conventions shared by the canonical executor, the deprecated executors, and quick.

### project/
- `project-yaml.md` — `.liang/project.yaml` schema, first-run interview contract, executor extensions.

## Boundaries

- This skill never plans, executes, or produces artifacts.
- This skill never modifies campaign files, manifests, or project config.
- This skill is never invoked directly by the user — it is consumed silently by other skills.
- All behavioral logic belongs in the family skills, not here.

## YAML Conventions (Global)

All YAML across the family follows these rules:

- `snake_case` keys
- lowercase, ASCII only
- Formal names in schema keys (no JRPG metaphors — those stay in HTML views)
- ISO 8601 for all dates and timestamps
- VCS-neutral language in plan content (checkpoint, not commit/push/branch)
