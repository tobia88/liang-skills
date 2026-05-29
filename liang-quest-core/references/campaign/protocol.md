# Campaign Protocol

Shared protocol for how campaigns operate across the JRPG quest planning family.

## Pipelines

### Canonical: Planner → Executor

Input layout (produced by `liang-quest-planner`):

```
.liang/campaigns/campaign-<YYYY-MM-DD>-<HHMM>-<slug>/
  plan.html                       # campaign-level editorial dossier
  quest-001-<name>.md             # executable "do" doc (steps + code blocks)
  quest-002-<name>.md
  manifest.yaml
```

Status path: `ready` → `in_progress` → `passed` | `failed` | `skipped`
Downstream executor: `liang-quest-executor`

No workflow stamp. The planner-native pipeline has a single executor — there is no workflow discriminator.

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
.liang/campaigns/
  campaign-<yyyy-mm-dd>-<slug>/
    plan.html                  # campaign-level editorial dossier
    manifest.yaml              # machine-readable quest index
    quest-001-<name>.md        # executable "do" doc
    quest-002-<name>.md
    ...
    .run/                      # executor working directory (per-quest subdirs)
    lessons.yaml               # failure lessons (append-only)
    run-report-<timestamp>.html  # run results
```

## Quest Dependency Order

Quests declare dependencies via `depends_on: [quest-id, ...]`. The dependency graph must be acyclic. The canonical executor executes quests whose dependencies are all `passed` or have no dependencies. Failed quests cascade-skip all transitive dependents.

## Quest ID and Slug Conventions

- Quest IDs: `q001`, `q002`, ... (stable within a campaign)
- File prefixes: `quest-001-`, `quest-002-`, ... (communicate order in filesystem)
- Slugs: lowercase, hyphen-separated, ASCII, no spaces
- Step IDs: `s01`, `s02`, ...

## Visual Tone

All HTML artifacts in the family share:

- Dark hero/header, light readable cards
- Subtle gold/blue/violet accents
- Green for passed, red for failed, amber for skipped/warning
- Native HTML/CSS only; no JavaScript; no external dependencies
- HTML-escape all source-derived content
- JRPG labels (Quest Board, Boss Board, Fog of War) in HTML views only — never in YAML keys
