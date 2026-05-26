# VCS Artifact Policy

Shared VCS artifact handling for all liang-brainstorm-* skills.

## Default Stance

Reports are private working notes by default. Before applying VCS rules,
read the centralized artifact policy.

## Policy Lookup

Read `vcs_artifacts.planning` from `.liang/project.yaml`:

| Policy | Action |
|---|---|
| `"ignore"` | Apply VCS ignore rules to `.liang/brainstorm-reports/` silently. Do not prompt. |
| `"commit"` | Leave reports trackable. Do not apply ignore rules. |
| `"ask"` | Present the privacy prompt below and let the user choose. |

## Fallback Behavior

If `.liang/project.yaml` exists but `vcs_artifacts` is absent, treat as
`"ask"`. After the user answers, write their choice to `project.yaml`
under `vcs_artifacts.planning` so subsequent runs are silent.

If `project.yaml` does not exist, use `"ask"` behavior without writing.

## Ask Prompt Template

When the policy resolves to `"ask"` (explicitly or via fallback), present
this prompt:

```text
Private Notes Warning

This Strategy Report may include private reasoning, rejected paths, and
rough planning notes.

How should I handle VCS rules for planning artifacts?

A. Apply ignore rules to .liang/brainstorm-reports/ (keep out of version control).
B. Leave reports trackable (I may want to commit/share them).
C. Decide later; write the report without changing VCS rules.
```

## Rule

Do not silently modify Git ignore rules.

Source: extracted from liang-brainstorm-relentless/SKILL.md VCS Artifact
Policy section (lines 433-461) per dc001.
