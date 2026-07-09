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

### Model Routing Extensions (optional)

```yaml
models:
  body_drafter: string       # model ID for the planner's body-drafting subagent (Phase 2c / Phase 3 full regens)
  apply_brief: string        # model ID for liang-brainstorm-quick's Option A (apply-immediately) delegation
  claude_mode:               # Claude-harness tier overrides — Claude tier aliases ONLY
    easy: string             # "haiku" | "sonnet" | "opus"
    medium: string
    hard: string
    body_drafter: string     # tier alias for the planner's body-drafter when running under Claude Code
```

Both keys are additive-optional: safe defaults when absent, no `schema_version` bump.

**`models.body_drafter`** — consumed read-only by `liang-quest-planner` for the body-drafting subagent. Resolution chain:

1. `models.body_drafter`
2. `models.execution_by_difficulty.medium` — body drafting is contract-following transcription of structured output, a medium-difficulty profile
3. Harness default (no model override — the subagent inherits whatever the harness assigns, typically the session model)
4. No subagent support at all → the planner drafts the body inline

A step that resolves to a model the current harness cannot spawn is treated as **unresolved** — continue down the chain. Harnesses that spawn subagents by tier alias rather than raw model ID (Claude Code can only spawn Claude tiers) resolve through the `claude_mode` namespace instead: `models.claude_mode.body_drafter` → `models.claude_mode.medium` → `sonnet` (the namespace's medium default). This keeps a mixed-vendor `execution_by_difficulty` block (e.g. pi model IDs) from silently routing the drafter to the session model under Claude Code. The planner announces the resolved drafter model — and any step skipped as unspawnable — in one line before spawning.

If `project.yaml` itself is missing at planning time, the planner skips to step 3 silently — planning may legitimately run in a fresh workspace before the executor's first-run interview has ever run. The planner never writes `project.yaml`, and the first-run interview does not ask for this key.

**`models.apply_brief`** — Model used by liang-brainstorm-quick's Option A (apply-immediately) delegation. Resolution chain: `models.apply_brief` → `models.execution_by_difficulty.medium` → harness default. Additive optional key; absence does not bump schema_version.

**`models.claude_mode`** — the Claude-harness tier namespace. Consumed by `liang-quest-executor` in `--claude` mode (`easy` / `medium` / `hard`) and by `liang-quest-planner` for the body-drafter when running under Claude Code (`body_drafter`, falling back to `medium`). Values are **Claude Code subagent tier aliases** (`haiku` / `sonnet` / `opus`), not pi model IDs — Claude Code cannot spawn non-Claude children, which is why this is a separate namespace from `execution_by_difficulty`. When the block (or any key in it) is absent, the defaults apply: easy → `haiku`, medium → `sonnet`, hard → `opus`; `body_drafter` defaults to the `medium` tier.

### Planner Extensions (optional)

```yaml
planner:
  visual: string             # "auto" | "always" | "never" — plan-visual policy for liang-quest-planner (default: "auto")
```

Additive-optional: when the block or key is absent, `auto` applies; no `schema_version` bump.

**`planner.visual`** — consumed read-only by `liang-quest-planner` in Phase 2a (semantics in the planner's `references/html-design-contract.md` §10). `auto` lets the skip-biased classifier decide per campaign (UI wireframe / flow-state diagram / sequence timeline / none); `always` forces a visual on every plan (the planner still picks the type); `never` suppresses visuals entirely. Per-run invocation flags `--visual` / `--no-visual` override this key. The first-run interview does not ask for it; add it manually when explicit control is wanted.

### Executor Extensions (optional)

```yaml
executor:
  max_step_retries: integer          # default: 3; max retry attempts per step. Read by liang-quest-executor.
  child_timeout_seconds: integer     # default: 300; max time per child invocation
  campaign_timeout_seconds: number   # default: 3600; max time per campaign dispatch in liang-quest-batch-sweep; 0 disables
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

The interview does not ask for the optional routing keys (`models.body_drafter`, `models.claude_mode`) or `planner.visual` — their fallback chains and defaults make them optional in practice; add them to `project.yaml` manually when explicit control is wanted.

## Verify Model Configuration

The `models.verify` field is required by both executors. If absent when an executor runs:

1. Explain that a verify model is needed.
2. Present an interactive model selection prompt.
3. Write the chosen model to `project.yaml` under `models.verify`.
4. Do not silently default to any model.

## Schema Versioning

- Current version: `schema_version: 1`
- **Additive-optional** fields (new keys with a safe default when absent) do not require a `schema_version` bump. Examples: `vcs_artifacts` defaults to `"ask"` when absent; `models.body_drafter` and `models.claude_mode` fall back to their documented resolution chains; `planner.visual` defaults to `"auto"`.
- **Breaking changes** (removed fields, changed semantics, new required fields without safe defaults) require a `schema_version` bump.
- Never retroactively edit existing configs for schema changes
- Skills must check `schema_version` before parsing

## Rules

- The canonical `liang-quest-executor` creates `project.yaml` when absent and reads it on every run.
- `liang-quest-planner` reads `project.yaml` (for `models.body_drafter` and `planner.visual` resolution) but never creates or writes it.
- The executor may add the `executor` block if absent (extension, not core change).
- The executor may add `models.verify` via interactive prompt if absent.
- No skill may extend the schema beyond defined fields without a version bump.
- VCS-specific behavior (checkpoint actions) is driven by the `vcs` field but never appears in plan content.
