---
name: liang-quest-core
description: Shared reference foundation for the JRPG quest planning family. Contains campaign protocol, manifest schema, plan schemas, status transitions, child process contracts, run report format, and project.yaml contract. The canonical pipeline skills (liang-quest-planner, liang-quest-executor) plus liang-quest-status read from this skill's references/ at activation time. This skill has no behavioral logic — it is a pure reference library.
---

# Liang Quest Core

You are the shared reference foundation for the JRPG quest planning family.

This skill contains **no behavioral logic**. It exists solely as a structured library of reference documents consumed by the family skills via reference inclusion.

## What This Skill Provides

| Subdirectory | Contents | Primary Consumers |
|---|---|---|
| `references/campaign/`  | Campaign protocol, manifest schema | planner, executor, status |
| `references/execution/` | Status transitions, child process contracts, run report format | executor |
| `references/project/`   | `project.yaml` contract | executor |

## Schema Version

**Current: schema_version: 4**

The quest planning family uses integer schema versioning. All skills reference the current version from this central declaration.

| Version | Changes |
|---------|---------|
| 4 | **Canonical planner-native schema.** `workflow` field removed entirely — the canonical pipeline has a single executor and no workflow discriminator. Quest entries use `file` (path to a flat `quest-NNN-name.md`) instead of `path` (path to a per-quest folder's `index.html`). Quest entries carry `difficulty: easy\|medium\|hard` for downstream model routing. Status vocabulary tightens to `ready / in_progress / passed / failed / skipped` (no `ready_for_planning`/`planned`/`needs_clarification`/`blocked`). |

Skills should check `schema_version` when parsing campaign artifacts and handle v1, v2, v3, and v4 gracefully. Canonical pipeline campaigns (v4) can also be detected structurally: no `workflow` field at any level, quest entries have `file` and `difficulty`, status is `ready`.

The declaration must be prominent and unambiguous — any skill reading quest-core will see the current version immediately after the reference table.

## Family Skills

| Skill | Role | Reads From Core |
|---|---|---|
| **liang-quest-core** | Shared references (this skill) | — |
| **liang-quest-planner** | Same-context campaign planner — extracts decisions from in-session conversation, writes `plan.html` + flat `quest-NNN-*.md` files + `manifest.yaml` | `campaign/` (manifest schema, protocol) |
| **liang-quest-executor** | Planner-native executor — spawns child processes per step (Pi CLI / Claude subagents / batch), tiered retry, quest-level VC verification with Tier 1 inline + Tier 2 deferred UAT | `campaign/`, `execution/`, `project/` |
| **liang-quest-status** | Read-only campaign status dashboard. Scans all manifests across all formats and renders an adaptive markdown view. | `campaign/` (protocol) |

## Composition Mechanism

Family skills consume core references via **reference inclusion** — they read the relevant subdirectories at activation time. This is not delegation or embedding; the core's documents become part of the consuming skill's context.

- **Planner** reads `campaign/` (manifest schema, protocol).
- **Executor** reads `campaign/`, `execution/`, `project/`.
- **Status** reads `campaign/` (protocol — for the campaign directory convention).

## Reference Index

### campaign/
- `protocol.md` — Campaign lifecycle for the canonical planner → executor pipeline. Layered Truth principle.
- `manifest-schema.md` — Canonical (v4) manifest.yaml schema. Source of truth.

### execution/
- `status-transitions.md` — Manifest status vocabulary, allowed transitions, executor-owned fields, tiered retry behavior.
- `child-contracts.md` — Child process I/O contracts for the canonical executor.
- `run-report.md` — Run report schema and visual conventions for the canonical executor.

### project/
- `project-yaml.md` — `project.yaml` contract.

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
