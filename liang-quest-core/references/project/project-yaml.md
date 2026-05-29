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
  planning: string           # model ID for planning (planner)
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
  max_step_retries: integer      # default: 3; max retry attempts per step. Read by liang-quest-executor.
  child_timeout_seconds: integer # default: 300; max time per child invocation
```

If the `executor` block is absent, use defaults silently.

### VCS Artifact Policy (optional)

```yaml
vcs_artifacts:
  planning: string           # "ignore" | "commit" | "ask" — policy for planning artifacts (.liang/brainstorm-reports/, .liang/campaigns/)
  execution: string          # "ignore" | "commit" | "ask" — policy for execution artifacts (.run/, lessons.yaml)
```

If the `vcs_artifacts` block is absent, all skills treat both categories as `"ask"` (preserving current per-skill prompt behavior). Once a user answers the prompt, the skill writes the answer back to `project.yaml`, making the config self-healing.

| Value | Behavior |
|---|---|
| `"ignore"` | Apply VCS ignore rules silently; suppress commit suggestions for this category |
| `"commit"` | Leave artifacts trackable; suggest commit command at campaign completion |
| `"ask"` | Preserve current per-skill prompt behavior (ask each time) |

#### Full Example

```yaml
schema_version: 1
vcs: "git"
models:
  planning: "claude-opus-4-6"
  verify: "claude-haiku-4-5-20251001"
  execution_by_difficulty:
    easy: "claude-haiku-4-5-20251001"
    medium: "claude-sonnet-4-6"
    hard: "claude-opus-4-6"
vcs_artifacts:
  planning: "ignore"
  execution: "ignore"
created_at: "2026-05-19T22:31:00+08:00"
```

## First-Run Interview

The canonical `liang-quest-executor` bootstraps `project.yaml` via an interactive interview when the file is missing.

Questions are asked one at a time, in order:

1. **VCS** — "Which version control system does this project use?" Offer: `git`, `perforce`, `none`.

   If vcs is not none, ask:
2. **Planning artifacts policy** — "How should planning artifacts (brainstorm reports, campaigns) be handled by VCS?" Offer: `ignore`, `commit`, `ask`. Recommend: `ignore`.
3. **Execution artifacts policy** — "How should execution artifacts (.run/ data, lessons) be handled by VCS?" Offer: `ignore`, `commit`, `ask`. Recommend: `ignore`.

   When vcs is 'none', omit the vcs_artifacts block from the written project.yaml.

4. **Planning model** — Present available models, then ask for a model ID (free-text).
5. **Easy execution model** — Ask for easy-difficulty model ID.
6. **Medium execution model** — Ask for medium-difficulty model ID.
7. **Hard execution model** — Ask for hard-difficulty model ID.

Each question is independent — no "same as previous" shortcuts. The user may type any model ID.

## Verify Model Configuration

The `models.verify` field is required by both executors. If absent when an executor runs:

1. Explain that a verify model is needed.
2. Present an interactive model selection prompt.
3. Write the chosen model to `project.yaml` under `models.verify`.
4. Do not silently default to any model.

## Schema Versioning

- Current version: `schema_version: 1`
- **Additive-optional** fields (new keys with a safe default when absent) do not require a `schema_version` bump. Example: `vcs_artifacts` defaults to `"ask"` when absent, preserving existing behavior.
- **Breaking changes** (removed fields, changed semantics, new required fields without safe defaults) require a `schema_version` bump.
- Never retroactively edit existing configs for schema changes
- Skills must check `schema_version` before parsing

## Rules

- The canonical `liang-quest-executor` creates `project.yaml` when absent and reads it on every run.
- The executor may add the `executor` block if absent (extension, not core change).
- The executor may add `models.verify` via interactive prompt if absent.
- No skill may extend the schema beyond defined fields without a version bump.
- VCS-specific behavior (checkpoint actions) is driven by the `vcs` field but never appears in plan content.
