# Campaign Protocol

Shared protocol for how campaigns operate across the JRPG quest planning family.

## Campaign Lifecycle

```
Brainstorm Report
    ↓
Campaign Cartographer → Campaign (manifest + quest contracts)
    ↓
Tactician (TDD or General) → plan.html per quest
    ↓
Executor (TDD or General) → run report
```

## Layered Truth

- **Manifest** is for orientation: campaign metadata + quest summary index.
- **Quest HTML** carries the full contract: everything a planner needs.
- **Plan HTML** carries the full plan: everything an executor needs.
- **Run Report HTML** carries the full run result.

Never duplicate full contracts into the manifest. Never split campaign metadata into quest files. Each artifact carries exactly one layer of truth.

## YAML-in-HTML-Comment Convention

All structured data lives inside the opening HTML comment of its HTML file:

```html
<!--
---
key: value
---
-->
<!doctype html>
<html>
  ...
</html>
```

The HTML body is the human-readable view (JRPG dashboard style). The YAML comment is the machine-readable contract.

## Campaign Folder Structure

```
campaigns/
  campaign-<yyyy-mm-dd>-<slug>/
    manifest.html              # human-readable quest board
    manifest.yaml              # machine-readable quest index
    quest-001-<slug>/
      index.html               # quest contract (YAML in comment)
      plan.html                # plan (YAML in comment) — written by tactician
    quest-002-<slug>/
      index.html
      plan.html
    ...
    .run/                      # executor working directory (per-quest subdirs)
    lessons.yaml               # failure lessons (append-only)
    run-report-<timestamp>.html  # run results
```

## Quest Dependency Order

Quests declare dependencies via `depends_on: [quest-id, ...]`. The dependency graph must be acyclic. Skills process quests in dependency order:

- Tacticians plan quests whose dependencies are all `planned` or have no dependencies.
- Executors execute quests whose dependencies are all `passed` or have no dependencies.
- Failed quests cascade-skip all transitive dependents.

## Quest ID and Slug Conventions

- Quest IDs: `q001`, `q002`, ... (stable within a campaign)
- Folder prefixes: `quest-001-`, `quest-002-`, ... (communicate order in filesystem)
- Slugs: lowercase, hyphen-separated, ASCII, no spaces
- Plan IDs: `p001`, `p002`, ...
- Cycle IDs (TDD): `c01`, `c02`, ...
- Step IDs (General): `s01`, `s02`, ...

## Visual Tone

All HTML artifacts in the family share:

- Dark hero/header, light readable cards
- Subtle gold/blue/violet accents
- Green for passed, red for failed, amber for skipped/warning
- Native HTML/CSS only; no JavaScript; no external dependencies
- HTML-escape all source-derived content
- JRPG labels (Quest Board, Boss Board, Fog of War) in HTML views only — never in YAML keys
