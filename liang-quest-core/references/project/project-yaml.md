# Project Config — `.liang/project.yaml`

Workspace-wide shared configuration for the JRPG quest planning family.

## Location

```
<workspace-root>/.liang/project.yaml
```

## Schema (v1)

### Required Core

```yaml
schema_version: 1            # integer; bump when schema changes
vcs: string                  # "git" | "perforce" | "none"
models:
  planning: string           # model ID for planning (tacticians, re-plan children)
  verify: string             # model ID for verification (verify children)
  execution_by_difficulty:
    easy: string             # model ID for easy-difficulty execution
    medium: string           # model ID for medium-difficulty execution
    hard: string             # model ID for hard-difficulty execution
created_at: string           # ISO 8601
```

### Executor Extensions (optional)

```yaml
executor:
  max_cycle_retries: integer     # default: 3; max retry attempts per cycle/step
  child_timeout_seconds: integer # default: 300; max time per child invocation
  max_step_retries: integer      # default: 3; alias for general executor (same as max_cycle_retries)
```

If the `executor` block is absent, use defaults silently.

## First-Run Interview

The tactician (whichever runs first) bootstraps `project.yaml` via an interactive interview. Questions are asked one at a time, in order:

1. **VCS** — "Which version control system does this project use?" Offer: `git`, `perforce`, `none`.
2. **Planning model** — Present available models, then ask for a model ID (free-text).
3. **Easy execution model** — Ask for easy-difficulty model ID.
4. **Medium execution model** — Ask for medium-difficulty model ID.
5. **Hard execution model** — Ask for hard-difficulty model ID.

Each question is independent — no "same as previous" shortcuts. The user may type any model ID.

## Verify Model Configuration

The `models.verify` field is required by both executors. If absent when an executor runs:

1. Explain that a verify model is needed.
2. Present an interactive model selection prompt.
3. Write the chosen model to `project.yaml` under `models.verify`.
4. Do not silently default to any model.

## Schema Versioning

- Current version: `schema_version: 1`
- New fields require a `schema_version` bump
- Never retroactively edit existing configs for schema changes
- Skills must check `schema_version` before parsing

## Rules

- The tactician creates `project.yaml`; the executor reads it.
- The executor may add the `executor` block if absent (extension, not core change).
- The executor may add `models.verify` via interactive prompt if absent.
- No skill may extend the schema beyond defined fields without a version bump.
- VCS-specific behavior (checkpoint actions) is driven by the `vcs` field but never appears in plan content.
