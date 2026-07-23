# liang-skills

Personal skill library for the [pi](https://github.com/badlogic/pi-mono) agent harness.
Each skill is one directory with a `SKILL.md` (contract) plus optional `references/`
and scripts. Skills are written harness-agnostic, so the same directories also load
in Claude Code via links (see [Install](#install)).

## Skills

### Quest family — JRPG-style campaign planning & execution

| Skill | What it does |
| --- | --- |
| `liang-quest-core` | Shared protocol library: campaign protocol, manifest/plan schemas, status transitions, child-process contracts, run-report format. Not invocable. |
| `liang-quest-planner` | Turns brainstorm output and/or conversation into a campaign: locked decisions → HTML plan → quest markdown files. |
| `liang-quest-saga-planner` | Decomposes a large prototype into multiple related campaigns with cross-campaign dependencies; resumable state in `.liang/sagas/`. |
| `liang-quest-executor` | Runs planner campaigns quest-by-quest via child processes; models routed from `project.yaml` `execution_by_difficulty`. |
| `liang-quest-batch-sweep` | Multi-campaign sweep (`sweep.py`): pre-flight report, confirmation gate, live launch, post-sweep summary. |
| `liang-quest-status` | Read-only campaign dashboard scanned from `manifest.yaml` files, with tiered attention highlighting. |
| `liang-quest-archiver` | Moves fully-terminal campaigns into `.liang/campaigns/archive/` via `archive_sweep.py` (dry-run by default). |

### Brainstorm family — structured planning dialogue

| Skill | What it does |
| --- | --- |
| `liang-brainstorm-core` | Shared behavioral contracts: question cadence, terminology, VCS policy, scout rules. Not invocable. |
| `liang-brainstorm-quick` | Lite brainstorm: 5 base questions + up to 2 pushbacks, in-chat Strategy Report only, zero files. |
| `liang-brainstorm-relentless` | One-question-at-a-time deep brainstorm with pushback on vague answers; ends in a Markdown Strategy Report. |

### Standalone tools

| Skill | What it does |
| --- | --- |
| `liang-code-cleanup` | Behavior-preserving readability pass (renames, dead code, why-comments) with recon and a no-logic-change attestation. |
| `liang-game-prototyper` | Small playable HTML game prototypes in `.liang/prototypes/`, reusing a shared asset pool. |
| `liang-skill-blacksmith` | Rubric-driven quality refinement for SKILL.md files: mechanical checker script + judged fixes, inspect/verify modes. |
| `liang-video-sampler` | Timestamped screenshots from local videos/GIFs so the agent can visually analyze clips. |
| `liang-ue-cpp-style` | UE5.5+ C++ coding conventions reference. |

## Install

### pi

Clone into the pi skills root — pi discovers every `SKILL.md` directory beneath it:

```sh
# Git Bash / macOS / Linux
git clone https://github.com/tobia88/liang-skills.git ~/.pi/agent/skills/liang-skills

# PowerShell — no tilde: PS passes it to git unexpanded, creating a literal "~" folder
git clone https://github.com/tobia88/liang-skills.git "$HOME\.pi\agent\skills\liang-skills"
```

(HTTPS works on any machine; use `git@github.com:tobia88/liang-skills.git` instead
if the machine has an SSH key registered with GitHub.)

### Claude Code

Claude Code only loads `~/.claude/skills/<name>/SKILL.md` one level deep, so the repo
can't be cloned there directly. Instead run the installer, which links every skill
directory into `~/.claude/skills/` (junctions on Windows — no admin needed):

```sh
# Windows
powershell -File install.ps1

# macOS / Linux
./install.sh
```

Both are re-runnable: they link new skills, skip existing entries, and prune links
that point into this repo but whose source skill was deleted.

The repo also ships a Claude Code `/goal` command (`.claude/commands/goal.md`),
picked up automatically when a Claude Code session runs inside this repo.

### Updating

`git pull`, then re-run the installer if skills were added or removed.

## Conventions

- **Slim skills.** `SKILL.md` states the contract only (triggers, inputs/outputs,
  control flow; soft cap ~200 lines). Templates, schemas, and edge-case rules live
  in `references/`, loaded on demand. Protocol shared by sibling skills belongs in
  a `*-core` skill, never duplicated.
- **Cross-harness prose.** pi runs these with varying models — skill text never
  hardcodes vendor model names or harness-specific tooling. Model selection routes
  through the active workspace's `.liang/project.yaml` under `models.*`.
- **Artifacts stay out of the repo.** Everything a skill generates at runtime goes
  to the active workspace's `.liang/<category>/` (campaigns, reviews, reports).
  `.liang/` is machine-local runtime state and is gitignored.
- **Machine-local files** (not in git): `Agent.md` (agent preferences, e.g.
  English-only output), `.liang/`, `.pi/`, `.claude/settings.local.json`.
