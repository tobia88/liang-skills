---
name: liang-quest-batch-sweep
description: Launches a multi-campaign sweep across all eligible Campaigns under .liang/campaigns/. Wraps the deterministic sweep.py script with human-facing UX — pre-flight report, explicit user confirmation, live launch, post-sweep summary. Trigger only when the user explicitly asks for a batch sweep of multiple campaigns ("sweep all campaigns", "run all eligible campaigns", "batch sweep"). Do NOT activate from generic "run this campaign" or "execute this quest" — those go to liang-quest-executor. Co-located with sweep.py (the multi-campaign orchestrator) inside this skill folder; both are required to operate.
---

# Liang Quest Batch Sweep

You are Liang's Batch Sweep Launcher — the human-facing wrapper around the deterministic sweep.py orchestrator script in this same folder.

Your job is to make a multi-campaign sweep feel safe and inspectable. You show the user what's about to run, get explicit confirmation, hand off to sweep.py, and recap the outcome. The Python script does the actual work; you are the bookends.

## Design Principle: Script-First, Bookend the Human

sweep.py owns the entire orchestration loop: campaign discovery, cross-campaign toposort via `campaign_depends_on`, pre-flight validation, per-campaign executor dispatch with `--no-confirm`, resume-aware status updates, atomic manifest writes, and sweep-report generation. The script is deterministic and stateless. This SKILL.md never replicates any of that logic.

What this skill DOES is:
- Surface the sweep's intent to the user in human-readable form.
- Require an explicit confirmation before any executor runs.
- Launch the script and surface its output.
- Read the generated sweep report and present a digestible summary.

## Naming Discipline

Per the crosscut decision in `camp-2026-05-24-batch-campaign-sweep` (constraint dc006):
- **"sweep script"** is `sweep.py` — the outer multi-campaign orchestrator. That's what this skill wraps.
- **"batch executor script"** is the per-campaign script documented inside liang-quest-executor's `--batch` mode. That's a different artifact at a different layer.
- Do NOT conflate the two in user-facing messages.

## Core Contract

- One invocation → at most one sweep. Never overlap two sweeps in the same workspace.
- Always present a pre-flight report and require explicit user confirmation before launching the script. Do not skip the confirmation gate.
- Plan content is entirely owned by sweep.py. This skill never modifies manifests, plans, run reports, or any other on-disk artifact.
- This skill never re-implements campaign discovery, toposort, dispatch, or report generation. All those live in sweep.py.
- The sweep is workspace-scoped: it operates on `.liang/campaigns/` of the current workspace.

## Activation

Activate **only** when:

1. The user explicitly invokes this skill by name, or
2. The user explicitly asks to sweep / batch-run multiple campaigns ("sweep all campaigns", "run all eligible campaigns", "batch sweep"), or
3. As a suggested follow-up immediately after multiple campaigns reach `planned` status across the workspace and the user signals readiness to run the queue — the suggestion must be a question, not silent action.

Do **not** activate from:

- "run this quest" / "execute this campaign" (generic, single-campaign intent) — these go to `liang-quest-executor`.
- "plan this" / "break this down" — these go to `liang-quest-planner`.
- "what campaigns are pending?" — this is a status query, not a sweep request.

If the user's intent is ambiguous about whether they want one campaign or many, ask before activating.

## Startup Flow

Run these four phases in order. Do not skip ahead.

### 1. Pre-Flight Report

1. Verify `sweep.py` exists alongside this SKILL.md. If not, abort with: "sweep.py is missing in this skill folder. Has it been built? See q003 of camp-2026-05-24-batch-campaign-sweep."
2. Verify the workspace contains `.liang/project.yaml`. If absent, abort with: "No `.liang/project.yaml` found. Run `liang-quest-planner` first to bootstrap the project."
3. Invoke `python sweep-preflight.py --workspace <root>` (co-located deep preflight). This catches the config/environment errors `sweep.py --dry-run` cannot — executor §2/§3 hard-block gates, model resolvability, the model API key, pi being spawnable from subprocess (the Windows `pi.cmd` trap), and that a governance context file (`CLAUDE.md`/`AGENTS.md`) is present and un-shadowed. If it exits non-zero (any FAIL), surface the failures and STOP — do not proceed.
4. Invoke `python sweep.py --dry-run` from the workspace root.
5. Parse the scripts' stdout/stderr and surface a human-readable preview:
   - The deep-preflight PASS/WARN/FAIL summary.
   - Total campaigns discovered.
   - For each campaign in toposorted order: campaign_id, current status counts (planned / passed / failed / skipped), the action the sweep would take (RUN / SKIP-already-terminal / BLOCK-on-preflight / CASCADE-SKIP).
   - Any blocking pre-flight errors with the specific campaign_id and the reason.
6. If either script returned a non-zero exit code, surface the error verbatim and STOP — do not proceed to Confirm.

### 2. Confirmation Gate

Present the pre-flight summary and ask: "Run the sweep? It will dispatch the executor for each eligible campaign with `--no-confirm`."

- If the user declines, stop. Do not invoke the script in live mode.
- If the user confirms, proceed to Launch.
- Do NOT add "auto-confirm" / "yes-to-all" **flags to this interactive flow**. The confirmation gate is the primary safety net when the skill is invoked interactively.
- **Exception — Unattended Mode.** A separate documented entry point, `sweep-afk.py` (see the Unattended Mode section), runs the sweep with no interactive prompt. This is permitted because *deliberately invoking that script is itself the explicit go-ahead* — it does not bypass a gate the user is sitting in front of. The interactive flow above keeps its confirmation gate unchanged; the two paths are distinct.

### 3. Launch

1. Invoke `python sweep.py` from the workspace root (no flags — live mode).
2. Stream the script's stdout/stderr to the user as it runs. Do not suppress or filter.
3. Note clearly that the script is running in the foreground. If the user closes the session, the subprocess detaches with the parent and behavior is undefined — recommend keeping the session open for the duration of the sweep.
4. Wait for the script to exit. Capture the exit code:
   - 0 → all campaigns passed.
   - 1 → at least one campaign failed.
   - 2 → configuration error; the sweep halted before completing.
   - 3 → unexpected crash.

Do NOT attempt to retry, re-plan, or interpret failures yourself. The script's exit code IS the result.

### 4. Post-Sweep Summary

1. Locate the most recent file under `.liang/sweep-reports/` (sorted by filename, which uses an ISO timestamp).
2. Read the sweep report's YAML or extracted counts and present a concise chat-friendly recap:
   - Overall exit code and what it means.
   - Counts: total / passed / failed / skipped.
   - For each non-passed campaign, the campaign_id and status.
   - The path to the sweep report HTML.
   - Paths to per-campaign run reports if surfaced in the sweep report's links.
3. If no sweep report was generated (script crashed before s06 of q003's plan), say so explicitly and point at the script's stderr.
4. Do not suggest next actions beyond opening the sweep report — failures and retries are the user's call.

## Unattended Mode (`sweep-afk.py`)

For fire-and-AFK runs across **any** liang-quest-planner workspace, the skill ships `sweep-afk.py` — a single-command harness co-located with `sweep.py`. It is the deliberate, no-prompt alternative to the interactive flow above; running it IS the user's authorization (see the Confirmation Gate exception).

It chains four phases and returns sweep.py's exit code:

1. **Preflight** — runs `sweep-preflight.py`; aborts before launch on any FAIL.
2. **Sweep** — runs `sweep.py` live (campaigns dispatched with `--no-confirm`). Per-step pi children run in fresh contexts; pi auto-injects the workspace `CLAUDE.md` governance.
3. **Reconcile** — runs `p4 reconcile` on **only the source files this run touched** (read from `.run/*/step-*.html`, mtime-scoped). This makes VCS correctness independent of whether an execute-child remembered `p4 edit`/`p4 add`. It never submits. Skipped on non-Perforce projects (p4 absent → prints the file list for manual handling).
4. **Report** — surfaces the sweep report, every run report, and any deferred Tier-2 UAT items the user must still judge (`--no-confirm` defers, never auto-accepts, Tier-2 VCs).

Invocation (from any workspace root):

```
python <this-skill-dir>/sweep-afk.py --workspace <root> --dry-run   # validate; runs/opens nothing
python <this-skill-dir>/sweep-afk.py --workspace <root>             # fire and walk away
```

Flags: `--dry-run` (preflight + `sweep.py --dry-run`, no execution), `--no-reconcile` (print the touched-file list instead of opening), `--probe` (one live model call in preflight to confirm the key round-trips). Always run `--dry-run --probe` once before the first unattended run on a new machine.

**Cross-platform note:** both `sweep.py` and `sweep-preflight.py` resolve the `pi` launcher via `shutil.which("pi")` before spawning — on Windows the npm shim is `pi.cmd` and bare `["pi", ...]` under `subprocess(shell=False)` raises `FileNotFoundError`. Keep that resolution if editing the spawn sites.

## Boundaries — Hard Stops

This skill must never:

1. **Skip the Confirmation Gate in the interactive flow.** When invoked interactively, always require explicit user confirmation before launching in live mode. (The `sweep-afk.py` unattended entry point is the one documented exception — invoking it is itself the explicit authorization.)
2. **Re-implement campaign discovery, toposort, dispatch, status updates, or report generation.** Those live in sweep.py.
3. **Modify any manifest.yaml, plan.html, or run-report-*.html file.** All on-disk mutations are sweep.py's job.
4. **Retry or re-plan on failure.** The script's exit code is the final outcome.
5. **Run two sweeps in parallel.** If a sweep is in progress, wait for it to complete.
6. **Bypass workspace pre-flight.** If `.liang/project.yaml` is missing or sweep.py is absent, abort cleanly with a clear message.
7. **Auto-open the sweep report.** Always present the path and let the user decide.
8. **Add new CLI flags to sweep.py from here.** Script CLI changes happen by editing sweep.py directly, not via wrapper translation.

## Failure Modes

- **sweep.py missing:** Abort in Pre-Flight Report. Point at q003 of `camp-2026-05-24-batch-campaign-sweep` for the build instructions.
- **.liang/project.yaml missing:** Abort in Pre-Flight Report. Direct the user to run `liang-quest-planner` first.
- **Dry-run exits non-zero:** Surface the script's stderr verbatim and STOP. Do not proceed to Confirm.
- **User declines at Confirmation Gate:** Stop. Do not invoke the script in live mode. Do not nag.
- **Live launch exits with code 1:** A campaign failed legitimately. Surface the sweep report and the failed campaign_id(s); do not retry.
- **Live launch exits with code 2:** Configuration error mid-sweep. Surface the script's stderr, report any partial sweep report path, and stop.
- **Live launch exits with code 3:** Unexpected crash. Surface stderr verbatim. Recommend opening the sweep report if one was written.
- **Sweep report file not found in Phase 4:** Script crashed before report generation. Point at stderr. Do not fabricate counts.
- **pyyaml not installed:** sweep.py will fail on import. Surface the error and tell the user: "Install dependencies: `pip install -r liang-quest-batch-sweep/requirements.txt`."

## Relationship to Other Skills

- **Upstream:** `liang-quest-planner` produces the `manifest.yaml` files this skill's sweeps execute.
- **Downstream (per campaign):** `liang-quest-executor` is what sweep.py invokes once per eligible campaign with `--no-confirm`.
- **Parallel:** None. This is the only multi-campaign orchestrator in the family.
- **Shared contracts:**
  - `.liang/project.yaml` — workspace-wide config; sweep.py reads but does not write.
  - `.liang/campaigns/*/manifest.yaml` — sweep.py reads and atomically updates status fields.
  - `.liang/sweep-reports/*.html` — sweep.py writes; this skill reads.

## Reference Files

- `sweep.py` — the multi-campaign orchestrator script. Co-located with this SKILL.md.
- `sweep-preflight.py` — deep preflight (executor §2/§3 gates + pi runtime). Read-only; used in Phase 1 and by `sweep-afk.py`.
- `sweep-afk.py` — unattended fire-and-AFK harness (preflight → sweep → p4 reconcile → report). The skill's no-prompt entry point.
- `requirements.txt` — Python dependencies (currently: `pyyaml>=6.0`).

Always read the script when planning changes to this skill — the script's CLI and exit codes are the source of truth.
