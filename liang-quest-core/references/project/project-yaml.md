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
  body_drafter: string       # model ID for the planner's body-drafting subagent (planner 2c and Phase 3 re-renders)
  apply_brief: string        # model ID for liang-brainstorm-quick's Option A (apply-immediately) delegation
  saga_intake: string        # model ID for liang-quest-saga-planner's Phase 1 intake subagent
  saga_planner: string       # model ID for the saga planner's batch-mode per-campaign planner subagent
  saga_align: string         # model ID for the saga planner's Phase 4.5 alignment-verify subagent
  saga_uat: string           # model ID for the saga planner's Phase 5/6 executor-artifact workers (§8b UAT backfill, §8c walkthrough)
  claude_mode:               # Claude-harness tier overrides — Claude tier aliases ONLY
    easy: string             # "haiku" | "sonnet" | "opus"
    medium: string
    hard: string
    verify: string            # tier alias for Tier-1 verify-children in --claude mode (default: haiku)
    planning: string          # tier alias for re-plan-children in --claude mode (default: sonnet)
    body_drafter: string     # tier alias for the planner's body-drafter when running under Claude Code
    saga_intake: string      # tier alias for the saga planner's intake subagent (default: medium)
    saga_planner: string     # tier alias for the saga planner's batch campaign-planner subagent (default: hard)
    saga_align: string       # tier alias for the saga planner's alignment verifier (default: medium)
    saga_uat: string         # tier alias for the saga planner's Phase 5/6 executor-artifact workers (default: medium)
```

Both keys are additive-optional: safe defaults when absent, no `schema_version` bump.

**`models.body_drafter`** — consumed read-only by `liang-quest-planner` for the body-drafting subagent. Resolution chain:

1. `models.body_drafter`
2. `models.execution_by_difficulty.medium` — body drafting is contract-following transcription of structured output, a medium-difficulty profile
3. Harness default (no model override — the subagent inherits whatever the harness assigns, typically the session model)
4. No subagent support at all → the planner drafts the body inline

A step that resolves to a model the current harness cannot spawn is treated as **unresolved** — continue down the chain. Harnesses that spawn subagents by tier alias rather than raw model ID (Claude Code can only spawn Claude tiers) resolve through the `claude_mode` namespace instead: `models.claude_mode.body_drafter` → `models.claude_mode.medium` → `sonnet` (the namespace's medium default). This keeps a mixed-vendor `execution_by_difficulty` block (e.g. pi model IDs) from silently routing the drafter to the session model under Claude Code. The planner announces the resolved drafter model — and any step skipped as unspawnable — in one line before spawning.

`project.yaml` is required at planning time, so this chain always resolves against a real file: when the file is missing, the planner runs the shared first-run interview (see § First-Run Interview) before drafting. The harness-default step covers a missing `models.body_drafter` **key**, not a missing file. The first-run interview does not ask for this key.

**`models.apply_brief`** — Model used by liang-brainstorm-quick's Option A (apply-immediately) delegation. Resolution chain: `models.apply_brief` → `models.execution_by_difficulty.medium` → harness default. Additive optional key; absence does not bump schema_version.

**`models.saga_intake` / `models.saga_planner` / `models.saga_align` / `models.saga_uat`** — consumed read-only by `liang-quest-saga-planner`. Resolution chains: `saga_intake` → `models.planning` → harness default; `saga_planner` → `models.planning` → harness default; `saga_align` → `models.verify` → harness default; `saga_uat` → `models.verify` → harness default (backfill is extraction/formatting against a fixed §8b contract — a medium-grade profile, same character as verify work). The same unresolved-step rule applies as for `body_drafter` (a model the harness cannot spawn continues the chain), and tier-alias harnesses (or an explicit `--claude` invocation) resolve through `claude_mode.saga_intake` (default `medium` tier), `claude_mode.saga_planner` (default `hard`), `claude_mode.saga_align` (default `medium`), and `claude_mode.saga_uat` (default `medium`) instead. All additive-optional; no schema_version bump.

**`models.claude_mode`** — the Claude-harness tier namespace. Consumed by `liang-quest-executor` in `--claude` mode (`easy` / `medium` / `hard` for execute-children, `verify` for Tier-1 verify-children, `planning` for re-plan-children), by `liang-quest-planner` for the body-drafter when running under Claude Code (`body_drafter`, falling back to `medium`), and by `liang-quest-saga-planner` for its intake / batch campaign-planner / alignment-verify / UAT-backfill subagents (`saga_intake` / `saga_planner` / `saga_align` / `saga_uat`, defaults `medium` / `hard` / `medium` / `medium`). Values are **Claude Code subagent tier aliases** (`haiku` / `sonnet` / `opus`), not pi model IDs — Claude Code cannot spawn non-Claude children, which is why this is a separate namespace from `execution_by_difficulty`. When the block (or any key in it) is absent, the defaults apply: easy → `haiku`, medium → `sonnet`, hard → `opus`, verify → `haiku`, planning → `sonnet`; `body_drafter` defaults to the `medium` tier.

### Planner Extensions (optional)

```yaml
planner:
  visual: string             # "auto" | "always" | "never" — plan-visual policy for liang-quest-planner (default: "auto")
  html: boolean              # true | false — REQUIRED, no default; plan/saga render surface
```

`planner.visual` is additive-optional: when the block or key is absent, `auto` applies. `planner.html` has **no default** — an absent key is asked once and written back (below). Neither key bumps `schema_version`.

**`planner.visual`** — consumed read-only by `liang-quest-planner` in Phase 2a (semantics in the planner's `references/html-design-contract.md` §10). `auto` lets the skip-biased classifier decide per campaign (UI wireframe / flow-state diagram / sequence timeline / none); `always` forces a visual on every plan (the planner still picks the type); `never` suppresses visuals entirely. Per-run invocation flags `--visual` / `--no-visual` override this key. The first-run interview does not ask for it; add it manually when explicit control is wanted.

**`planner.html`** — the render surface for `liang-quest-planner` and `liang-quest-saga-planner`. A **required boolean with no default**:

- `true` — the planner renders `plan.html` and opens it, and discussion happens on the page; the saga planner renders `saga.html` and `handover.html`.
- `false` — **trust mode**: no HTML, no discussion phase. The markdown dossiers (`plan.md`, `saga.md`) are the only human-readable output.

Per-run invocation flags `--html` / `--no-html` override the key for one invocation. There is no `auto` value.

When the key is absent, the next planner or saga-planner run asks interview question 8 once and writes the answer back to `project.yaml` — the same self-healing pattern as `vcs_artifacts` and `models.verify`. In headless mode (no user to answer) a missing key is a hard stop with a clear message, exactly like a missing file.

### Executor Extensions (optional)

```yaml
executor:
  max_step_retries: integer          # default: 3; max retry attempts per step. Read by liang-quest-executor.
  child_timeout_seconds: integer     # default: 300; max time per child invocation
  campaign_timeout_seconds: number   # default: 3600; max time per campaign dispatch in liang-quest-batch-sweep; 0 disables
  unattended: boolean                # default: false; true makes every liang-quest-executor run behave as --no-confirm
```

If the `executor` block is absent, use defaults silently.

**`executor.unattended`** — when `true`, `liang-quest-executor` treats every invocation as `--no-confirm`: no intent confirm, no intake confirm, crash recovery resumes, UAT stays deferred to `uat-checklist.md`, cleanup preserves, VCS policy `ask` reads as `ignore`. A `--confirm` flag on one invocation restores the interactive gates for that run only. The setting does not change what the executor may ask mid-run — that is never anything, in any mode — it only removes the start and end gates. Additive-optional; no `schema_version` bump.

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

## First-Run Interview (shared: executor, planner, saga planner)

`project.yaml` is required by `liang-quest-executor`, `liang-quest-planner`, and `liang-quest-saga-planner`. Whichever of the three runs first against a workspace that has no `project.yaml` bootstraps it via this interactive interview — the definition lives here so all three ask the same questions in the same order.

In headless mode (a fresh-context subagent or any invocation with no user present) a missing `project.yaml` — or a present file missing the `planner.html` key — is a **hard stop**: report which file or key is missing and exit without planning. Never guess a value.

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
8. **Plan render surface** — "Will you read plan pages in a browser for this project? (yes = render plan.html and discuss on it; no = trust mode, markdown only)". Write the answer to `planner.html` as `true` or `false`.

Each question is independent — no "same as previous" shortcuts. The user may type any model ID.

The interview does not ask for the optional routing keys (`models.body_drafter`, `models.claude_mode`) or `planner.visual` — their fallback chains and defaults make them optional in practice; add them to `project.yaml` manually when explicit control is wanted. `planner.html` **is** asked, because it has no default.

## Verify Model Configuration

The `models.verify` field is required by both executors. If absent when an executor runs:

1. Explain that a verify model is needed.
2. Present an interactive model selection prompt.
3. Write the chosen model to `project.yaml` under `models.verify`.
4. Do not silently default to any model.

## Schema Versioning

- Current version: `schema_version: 1`
- **Additive-optional** fields (new keys with a safe default when absent) do not require a `schema_version` bump. Examples: `vcs_artifacts` defaults to `"ask"` when absent; `models.body_drafter` and `models.claude_mode` fall back to their documented resolution chains; `planner.visual` defaults to `"auto"`. `planner.html` has no default, but its absence triggers a one-time prompt and write-back rather than a parse failure — the same additive-optional shape as `vcs_artifacts`.
- **Breaking changes** (removed fields, changed semantics, new required fields without safe defaults) require a `schema_version` bump.
- Never retroactively edit existing configs for schema changes
- Skills must check `schema_version` before parsing

## Rules

- The canonical `liang-quest-executor` creates `project.yaml` when absent and reads it on every run.
- `liang-quest-planner` and `liang-quest-saga-planner` require `project.yaml` and read it on every run (`models.body_drafter`, `planner.visual`, `planner.html`, and the saga `models.saga_*` chains). Both may bootstrap the file via the shared first-run interview when it is missing, and both may write back `planner.html` after asking question 8. They write no other key.
- The executor may add the `executor` block if absent (extension, not core change).
- The executor may add `models.verify` via interactive prompt if absent.
- No skill may extend the schema beyond defined fields without a version bump.
- VCS-specific behavior (checkpoint actions) is driven by the `vcs` field but never appears in plan content.
