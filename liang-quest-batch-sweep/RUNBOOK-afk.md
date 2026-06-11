# Fire-and-AFK Batch Sweep — Runbook

General procedure for executing **all** eligible `liang-quest-planner` campaigns
unattended, with no edits to any quest plan. Shipped inside the
`liang-quest-batch-sweep` skill, so it applies to every project — current and
future — that has a `.liang/campaigns/` directory.

`<SKILL>` below = this skill's directory
(`~/.pi/agent/skills/liang-skills/liang-quest-batch-sweep/`).

## TL;DR

```bash
# from the project/workspace root (the dir containing .liang/ and CLAUDE.md)
python <SKILL>/sweep-afk.py --workspace . --dry-run --probe   # validate + live key check
python <SKILL>/sweep-afk.py --workspace .                     # fire, then walk away
```

`--workspace .` works because the scripts default `--workspace` to cwd; pass an
absolute path to run against another project from anywhere.

## What runs, and why it's safe to leave

The harness chains four phases (`sweep-afk.py`):

1. **Preflight** (`sweep-preflight.py`) — mirrors the executor's hard-block
   gates + the pi runtime (models resolvable, model API key set, `pi`
   spawnable, governance context present and un-shadowed, every quest
   well-formed). **Aborts before launch on any FAIL.**
2. **Sweep** (`sweep.py`, live) — dispatches `pi --print --skill
   liang-quest-executor` once per eligible campaign, in dependency order,
   with non-interactive intent delivered as prompt text (no `--no-confirm`
   flag — pi has none). Already-passed campaigns are skipped; `failed` ones
   are re-run on a later invocation.
3. **Reconcile** — reads `.liang/project.yaml` `vcs` field. When
   `vcs: perforce`, runs `p4 reconcile` on **only** the source files this run
   actually wrote (read from `.run/*/step-*.html`, mtime-scoped). Makes
   Perforce correctness independent of whether a child remembered
   `p4 edit`/`p4 add`. Never submits. For `git`, `none`, or missing VCS,
   prints the touched-file list for manual handling.
4. **Report** — lists the sweep report, every run report, and any deferred
   Tier-2 UAT items awaiting your judgment.

### The two design facts that make this work without touching plans

- **Clean context per quest is automatic.** In Pi CLI mode the executor spawns a
  *fresh* `pi` child per step. Each loads the project context file from scratch,
  does one step, and exits — no cross-quest context bleed, for any campaign.
- **Governance is injected generally, not per-plan.** pi's resource loader walks
  ancestor dirs and auto-loads `CLAUDE.md`/`AGENTS.md` into every child of every
  campaign. Project rules (e.g. Perforce, build policy, style) reach the workers
  with zero plan edits. Preflight verifies the context file is present and not
  shadowed.

### Why Perforce correctness doesn't depend on the model

If execution runs on a cheaper/non-Claude model, a child may not faithfully run
`p4 edit`/`p4 add` even though it sees the context file. That's fine:
**`p4 reconcile` in phase 3 diffs the workspace against the depot and opens
whatever actually changed** — so VCS state is correct regardless. Unchanged
files are depot-identical and reconcile skips them. You verify and submit
manually. The only dimension still leaning on the model is *code style*, caught
at compile/review.

## Flags

| Flag | Effect |
|------|--------|
| `--dry-run` | Preflight + `sweep.py --dry-run`; executes nothing, opens nothing. Run this first. |
| `--probe` | Preflight makes one live pi call to confirm the model key round-trips. Run once per machine. |
| `--no-reconcile` | Skip `p4 reconcile`; just print the touched-file list. |
| `--workspace <path>` | Target a project root (default: cwd). |

## Attended alternative

For an interactive run with a confirmation prompt before launch, invoke the
**skill** itself (`/liang-pi skill:liang-quest-batch-sweep` or `pi --skill
liang-quest-batch-sweep`) and follow its Startup Flow. `sweep-afk.py` is the
deliberate unattended counterpart — running it is the explicit go-ahead.

## After it finishes

1. Open the **run reports** (paths printed in phase 4) — check quest pass/fail.
2. Drain any **deferred Tier-2 UAT** items the report flags. In non-interactive
   mode these pass *provisionally* and are never auto-judged — they're yours to
   confirm.
3. **Perforce projects:** files are open in your default changelist (phase 3). Compile, review, then `p4 submit`.
   **Non-Perforce projects:** the touched-file list was printed in phase 3; handle changes manually (e.g. `git add`, manual review).

## Re-running / resume

Re-invoke any time. The sweep is idempotent: `passed`/`skipped` campaigns are
left alone, `failed` ones re-dispatch and the executor resumes from the last
good step. Per-step retries (lesson → re-plan, cap 3) happen automatically.

## Files (all co-located in `<SKILL>/`)

- `sweep-afk.py` — the AFK harness (entry point).
- `sweep-preflight.py` — standalone deep preflight (phase 1).
- `sweep.py` — the orchestrator the harness wraps.
- `SKILL.md` — interactive flow + Unattended Mode contract.
