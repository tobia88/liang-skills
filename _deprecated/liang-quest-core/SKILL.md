---
name: liang-quest-core
description: DEPRECATED, use liang-queue-add / liang-queue-sweep instead. Shared reference foundation for the JRPG quest planning family. Contains campaign protocol, manifest schema, status transitions, child process contracts, run report format, the project.yaml contract, and the family's own rules (registry, topology, audit criteria, decision log). Every liang-quest-* skill reads the references it needs from here. This skill has no behavioral logic — it is a pure reference library.
---

# Liang Quest Core

You are the shared reference foundation for the JRPG quest planning family.

This skill contains **no behavioral logic**. It exists solely as a structured library of reference documents consumed by the family skills via reference inclusion.

## What This Skill Provides

| Subdirectory | Contents | Primary Consumers |
|---|---|---|
| `references/campaign/`  | Campaign protocol, manifest schema, difficulty guide | planner, executor, batch-sweep, status, saga planner, archiver |
| `references/execution/` | Status transitions, child process contracts, run report format | executor, batch-sweep, status |
| `references/project/`   | `project.yaml` contract | planner, executor, batch-sweep, saga planner, recon, archiver |
| `references/code-style/` | UE C++ code-block style contract | planner, executor |
| `references/family/` | Family rules: audit criteria, canonical topology, decision log, drift ledger | maintainers and the family audit only — **never read at activation** |

## Schema Version

**Current campaign manifest schema: schema_version: 4**

This is the canonical `manifest.yaml` schema version for quest campaigns. It is distinct from `.liang/project.yaml`'s `schema_version: 1` — the two files use independent, non-overlapping version namespaces. When a skill reads "schema_version", the context (campaign manifest vs project.yaml) determines which version line applies.

The quest planning family uses integer schema versioning for campaign manifests. All skills reference the current version from this central declaration.

| Version | Changes |
|---------|---------|
| 4 | **Canonical planner-native schema.** `workflow` field removed entirely — the canonical pipeline has a single executor and no workflow discriminator. Quest entries use `file` (path to a flat `quest-NNN-name.md`) instead of `path` (path to a per-quest folder's `index.html`). Quest entries carry `difficulty: easy\|medium\|hard` for downstream model routing. Status vocabulary tightens to `ready / in_progress / passed / failed / skipped` (no `ready_for_planning`/`planned`/`needs_clarification`/`blocked`). |

Skills should check `schema_version` when parsing campaign artifacts and handle v1, v2, v3, and v4 gracefully. Parsers must tolerate the field as either integer (e.g. `4`) or string (e.g. `"4"`) for backward compatibility. Canonical pipeline campaigns (v4) can also be detected structurally: no `workflow` field at any level, quest entries have `file` and `difficulty`, status is `ready`. Skills that only support the canonical schema (e.g. the executor) satisfy this by refusing non-v4 input cleanly with a clear error, rather than attempting best-effort parsing of older versions.

The declaration must be prominent and unambiguous — any skill reading quest-core will see the current version immediately after the reference table.

## Family Skills

| Skill | Role | Reads From Core |
|---|---|---|
| **liang-quest-core** | Shared references (this skill) | — |
| **liang-quest-planner** | Same-context campaign planner — extracts decisions from in-session conversation, writes `plan.md` (+ optional `plan.html`) + flat `quest-NNN-*.md` files + `manifest.yaml` | `campaign/` (protocol, manifest schema, difficulty guide), `project/`, `code-style/` (UE C++ code blocks) |
| **liang-quest-executor** | Planner-native executor — spawns child processes per step (Pi CLI / Claude subagents / batch), tiered retry, quest-level VC verification with Tier 1 inline + Tier 2 deferred UAT | `campaign/`, `execution/`, `project/`, `code-style/` |
| **liang-quest-batch-sweep** | Multi-campaign sweep launcher/orchestrator — wraps `sweep.py`, dispatches executor per eligible campaign, writes sweep reports | `campaign/`, `execution/` (manual holds, retry-reset), `project/` |
| **liang-quest-status** | Read-only campaign status dashboard. Scans all manifests across all formats and renders an adaptive markdown view. | `campaign/` (protocol, manifest schema), `execution/` (status vocabulary) |
| **liang-quest-saga-planner** | Upper orchestrator — turns a discussion's decisions (plus optional recon folders) into 2–8 related campaigns via repeated planner handoffs; resumable state in `.liang/sagas/`; post-execution UAT / tour / handover rollups | `campaign/` (manifest schema — `campaign_depends_on`), `project/` |
| **liang-quest-recon** | Side scout — the only skill that reads a raw prototype; writes a line-referenced breakdown folder (lite profile) plus verified gap analysis against the codebase (full profile) | `project/` (model routing keys) |
| **liang-quest-archiver** | Moves finished campaigns under `.liang/campaigns/archive/`, out of every other skill's discovery glob | `campaign/` (protocol — § Archived Campaigns), `project/` (model keys) |

How these fit together — the ladder and the feed graph — is defined once, in `references/family/topology.md`.

## Composition Mechanism

Family skills consume core references via **reference inclusion** — each reads the core files its own `## Reference Files` section lists, upfront or at the phase that needs them, as that section says. This is not delegation or embedding; the core's documents become part of the consuming skill's context.

- **Planner** reads `campaign/` (protocol, manifest schema, difficulty guide) and `project/`, plus `code-style/` when planned code blocks are UE C++.
- **Executor** reads `campaign/`, `execution/`, `project/`, plus `code-style/` for UE C++ child briefs.
- **Batch sweep** reads `campaign/`, `execution/` (manual holds, sweep retry-reset), and `project/`.
- **Status** reads `campaign/` (directory convention, manifest schema) and `execution/` (status vocabulary).
- **Saga planner** reads `campaign/` (manifest schema, for the `campaign_depends_on` patch) and `project/` (first-run interview, model routing).
- **Recon** reads `project/` (model routing keys); its own artifact contract lives in its own `references/`.
- **Archiver** reads `campaign/` (protocol — the archive directory convention) and `project/` (model keys).

## Reference Index

### campaign/
- `protocol.md` — Campaign lifecycle for the canonical planner → executor pipeline. Layered Truth principle.
- `manifest-schema.md` — Canonical (v4) manifest.yaml schema. Source of truth.
- `difficulty-guide.md` — Canonical easy/medium/hard difficulty criteria and tie-break rule.

### execution/
- `status-transitions.md` — Manifest status vocabulary, allowed transitions, executor-owned fields, tiered retry behavior.
- `child-contracts.md` — Child process I/O contracts for the canonical executor.
- `run-report.md` — Run report schema and visual conventions for the canonical executor.

### project/
- `project-yaml.md` — `project.yaml` contract.

### code-style/
- `ue-cpp.md` — UE C++ code-block style contract (Allman braces and related rules), distilled from `liang-ue-cpp-style`.

### family/ (maintainers and audit only)
- `criteria.md` — what the family audit criteria mean for `liang-quest-*`; canonical homes, skeleton, registry rules. Generic rules and the audit script live in `_family-audit/` at the liang-skills root.
- `topology.md` — the canonical ladder and feed graph.
- `decisions.md` — log of behavioral changes to the family (`qdNNN`).
- `drift-ledger.md` — intentional divergences inside the family (`dvNNN`).

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
