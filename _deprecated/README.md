# Deprecated

Retired skills, kept for history. The Claude Code installers link only top-level
skill directories, so nothing here loads there. pi scans the repo recursively and
still lists them; each description starts with `DEPRECATED` so it won't pick one up.

- `liang-quest-*`, `liang-brainstorm-*` — replaced by `liang-queue-add` / `liang-queue-sweep`.
- `liang-skill-blacksmith`, `liang-replica-forge`, `liang-video-sampler` — retired.
- `goal.md` (was `.claude/commands/goal.md`) and `_family-audit/` — the audit tooling for
  the quest and brainstorm families.

To use one again, link it by hand, e.g.
`ln -s "$PWD/_deprecated/liang-video-sampler" ~/.claude/skills/liang-video-sampler`.
