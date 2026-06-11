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

- **Plan HTML** (`plan.html`) is a planner-authored human dossier. The executor ignores it.
- **Quest Markdown** (`quest-NNN-*.md`) carries the executable contract: steps, code blocks, dependencies, and victory conditions.
- **Step envelopes** (`.run/<quest-id>/step-<sid>.md`) are executor-generated Markdown transport/ledger artifacts.
- **Run Report Markdown** (`run-report-<timestamp>.md`) carries the full run result.

Never duplicate full contracts into the manifest. Never split campaign metadata into quest files. Each artifact carries exactly one layer of truth.

## Legacy HTML Comment Convention (tolerated)

Legacy `.html` step envelopes and run reports carry metadata in an opening HTML comment. This convention predates the Markdown ledger convention.

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

The HTML body is the human-readable view (JRPG dashboard style). The YAML comment is the machine-readable contract. New executor runs produce Markdown artifacts instead.

## Markdown Ledger Convention

Executor-generated Markdown artifacts carry structured data in predictable places:

- Run reports use YAML front matter.
- Step envelopes use fenced YAML blocks under stable headings: `Input`, `Output`, `Re-plan`, and `Verification`.

Legacy `.html` step envelopes and run reports may exist in old campaign folders. New executor runs write Markdown artifacts.

### Step Envelope Fenced YAML

Step envelopes (`step-<sid>.md`) use Markdown fenced YAML sections. Each fenced section (`## Input`, `## Output`, `## Re-plan`, `## Verification`) carries one part of the child contract:

```markdown
## Input
~~~yaml
child_type: "execute"
quest_id: "q001"
step_id: "s01"
~~~

## Output
~~~yaml
status: "success"
files_changed: []
implementation_summary: ""
~~~
```

The Markdown body between fenced sections is the human-readable transport/ledger view. The fenced YAML blocks are the machine-readable contract. For `plan.html`, the quest Markdown remains the executable contract.

## Campaign Folder Structure

```
.liang/campaigns/
  campaign-<yyyy-mm-dd>-<HHMM>-<slug>/
    plan.html                    # planner-authored human dossier (ignored by executor)
    manifest.yaml                # machine-readable quest index
    quest-001-<name>.md          # executable "do" doc
    quest-002-<name>.md
    ...
    .run/                        # executor run ledger
      q001/
        step-s01.md              # step envelope (Markdown fenced YAML)
        step-s02.md
        ...
        complete.yaml            # quest-completion marker
      q002/
        step-s01.md
        ...
    lessons.yaml                 # failure lessons (append-only)
    run-report-<timestamp>.md    # run results (Markdown with YAML front matter)
```

Key points:
- `plan.html` remains the planner-authored human dossier; the executor never reads it.
- Quest step envelopes live under `.run/<quest-id>/step-<sid>.md`.
- Run reports are Markdown files with YAML front matter: `run-report-<timestamp>.md`.
- The `.run/` directory is executor-owned metadata; no campaign semantics depend on it for correctness.

## Shared Helper Ownership

Reusable executor helpers are owned by the quest skill/core layer, not by campaign `.run/` directories. Use `liang-quest-executor` for executor-only helpers and `liang-quest-core` for helpers shared across quest-family skills. A campaign may record helper metadata or a deliberate reproducibility snapshot in `.run/`, but the canonical implementation should not be regenerated per campaign.

Before adding shared helper code, decide the concrete owner path, reference-vs-snapshot policy, whether `plan.html` remains a human-only dossier (the executor never reads it), and whether run-report generation is executor-local or core-shared.

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
