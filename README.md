# liang-skills

Personal skill library for the [pi](https://github.com/badlogic/pi-mono) agent harness.
Each skill is one directory with a `SKILL.md` (contract) plus optional `references/`
and scripts. Skills are written harness-agnostic, so the same directories also load
in Claude Code via links (see [Install](#install)).

## Skills

### Queue family — park agreed work, run it unattended

| Skill | What it does |
| --- | --- |
| `liang-queue-add` | Captures agreed work as `.liang/queue/YYYYMMDD_NN_TaskName/task.md` (goal, the user's decisions, done-when, boundaries — no step plan) and saves its assets. Owns the task format. |
| `liang-queue-sweep` | Runs `ready` tasks in order while the user is away: pre-flight, one fresh child session per task, logged judgement calls, saved evidence, run summary and push. `--check` and `--status` modes. |

### Standalone tools

| Skill | What it does |
| --- | --- |
| `liang-code-cleanup` | Behavior-preserving readability pass (renames, dead code, why-comments) with recon and a no-logic-change attestation. |
| `liang-game-prototyper` | Small playable HTML game prototypes in `.liang/prototypes/`, reusing a shared asset pool. |
| `liang-ue-cpp-style` | UE5.5+ C++ coding conventions reference. |

### Deprecated

Retired skills live in [`_deprecated/`](_deprecated/): the quest and brainstorm
families (replaced by the queue family), `liang-skill-blacksmith`,
`liang-replica-forge`, `liang-video-sampler`, plus the `/goal` family-audit command
and `_family-audit/`. The Claude Code installers only link top-level skill directories, so none of
these load there; pi scans recursively and still sees them, tagged `DEPRECATED`. See [`_deprecated/README.md`](_deprecated/README.md).

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

### Updating

`git pull`, then re-run the installer if skills were added or removed.

## Conventions

- **Slim skills.** `SKILL.md` states the contract only (triggers, inputs/outputs,
  control flow). Templates, schemas, and edge-case rules live
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
