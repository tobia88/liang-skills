---
name: liang-quest-batch-sweep
description: Launches a multi-campaign sweep across eligible Campaigns under .liang/campaigns/ — workspace-wide, or scoped to one saga's campaigns via sweep.py --saga (or an explicit --only campaign_id list). Wraps the deterministic sweep.py script with human-facing UX — pre-flight report, explicit user confirmation, live launch, post-sweep summary. Trigger only when the user explicitly asks for a batch sweep of multiple campaigns ("sweep all campaigns", "run all eligible campaigns", "batch sweep", "sweep the saga", "sweep saga <name>"). Do NOT activate from generic "run this campaign" or "execute this quest" — those go to liang-quest-executor. Co-located with sweep.py (the multi-campaign orchestrator) inside this skill folder; both are required to operate.
---

# Liang Quest Batch Sweep

You are Liang's Batch Sweep Launcher — the human-facing wrapper around the deterministic sweep.py orchestrator script in this same folder.

Your job is to make a multi-campaign sweep feel safe and inspectable. You show the user what's about to run, get explicit confirmation, hand off to sweep.py, and recap the outcome. The Python script does the actual work; you are the bookends.

## Design Principle: Script-First, Bookend the Human

sweep.py owns the entire orchestration loop: campaign discovery, cross-campaign toposort via `campaign_depends_on`, pre-flight validation, per-campaign executor dispatch in non-interactive mode (no-confirm intent delivered as prompt text, not an argv flag), resume-aware status updates, atomic manifest writes, and sweep-report generation. The script is deterministic and stateless. This SKILL.md never replicates any of that logic.

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
- Sweep orchestration is entirely owned by `sweep.py`. This skill never modifies manifests, planner artifacts, run reports, or any other on-disk artifact; planner-authored `plan.html` and `quest-NNN-*.md` files remain read-only.
- This skill never re-implements campaign discovery, toposort, dispatch, or report generation. All those live in sweep.py.
- Campaigns archived by `liang-quest-archiver` (`.liang/campaigns/archive/<name>/`) are out of sweep scope by construction — sweep.py's one-level discovery glob never sees them (liang-quest-core protocol § Archived Campaigns). Archiving completed campaigns is the standing mitigation for the historical-campaign hazard below.
- The sweep operates on `.liang/campaigns/` of the current workspace — either workspace-wide, or scoped via `--saga` / `--only` (see Scoped Sweeps). On a workspace with historical campaigns, **default to a scoped sweep**: an unscoped sweep re-dispatches every non-passed quest ever left behind (sweep.py resets `failed`/`skipped` quests to `ready` before dispatch). If the user asks for an unscoped sweep on a workspace where the pre-flight shows more campaigns than they plausibly intend, say so before the Confirmation Gate.

## Harness Support

- This skill is pi-only: `sweep.py` dispatches campaigns as pi CLI children and `sweep-preflight.py` hard-fails when pi is not spawnable. There is no `--claude` sweep mode.
- On a Claude-only environment, the equivalent is running campaigns individually: `liang-quest-executor <campaign-path> --claude`, in `campaign_depends_on` topological order. The executor holds `manual: true` quests at intake; the sweep-only features you lose are cross-campaign toposort, retry-reset, and sweep reports.

## Scoped Sweeps (`--saga` / `--only`)

`sweep.py --saga <token>` restricts the sweep to the campaigns listed in one saga's `saga.yaml` (produced by `liang-quest-saga-planner`). The token may be the saga's directory name under `.liang/sagas/` (a unique substring works, e.g. `battle-simulator-port`), or a path to the saga directory or its saga.yaml. `--only <campaign_id,...>` restricts to an explicit list; both flags union.

Resolution and validation live in sweep.py, not here:

- Saga entries without a `campaign_id` (not yet planned) are excluded with a warning.
- Every scoped campaign_id must exist on disk with a parseable manifest — otherwise config error.
- A `campaign_depends_on` target **outside** the scope is satisfied only if that campaign is already fully done on disk; otherwise config error ("include it in the scope or run it first").
- Broken manifests **outside** the scope are downgraded to warnings, so historical clutter cannot block a scoped sweep.

### Manual quests (`manual: true`)

A quest flagged `manual: true` in the manifest is human-in-editor work that can never run headlessly. Before dispatching a campaign, sweep.py **holds** such quests — and, transitively, their un-passed in-campaign dependents — at `status: skipped` with `skip_reason: manual_deferred` / `manual_dependency`. The executor queues only `status: ready`, so held quests are invisible to it, and the retry-reset never releases a hold.

Consequences you must surface to the user:

- A campaign whose only remaining quests are manual holds counts as **passed with a manual backlog** (shown in the sweep report's Manual column); its cross-campaign dependents still run. Automated quests in later campaigns are expected to verify independently (e.g. compile gates) — a dependent that genuinely needed the manual output will fail its own verification, not silently succeed.
- After the sweep, the user completes the manual quests in the editor, sets them to `passed` in the manifest, and re-sweeps; stale holds (and their held dependents) are released automatically on the next run.
- In the post-sweep summary, always list the deferred manual quests per campaign as the user's to-do list.

## Activation

Activate **only** when:

1. The user explicitly invokes this skill by name, or
2. The user explicitly asks to sweep / batch-run multiple campaigns ("sweep all campaigns", "run all eligible campaigns", "batch sweep", "sweep the saga", "sweep saga <name>" — the saga forms map to `--saga`), or
3. As a suggested follow-up immediately after multiple campaigns reach `ready` status across the workspace and the user signals readiness to run the queue — the suggestion must be a question, not silent action.

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
4. Invoke `python sweep.py --dry-run` from the workspace root, carrying the user's scope: append `--saga <token>` / `--only <ids>` when they asked for a saga or a subset. Reuse the exact same scope flags in the live Launch later.
5. Parse the scripts' stdout/stderr and surface a human-readable preview:
   - The deep-preflight PASS/WARN/FAIL summary.
   - Total campaigns discovered, and — if scoped — the scope line (`N of M campaign(s) in scope`).
   - For each campaign in toposorted order: campaign_id, current status counts (ready / in_progress / passed / failed / skipped), the action the sweep would take (RUN / SKIP-already-terminal / BLOCK-on-preflight / CASCADE-SKIP), and any manual-hold counts (`holding N manual quest(s)`).
   - Any blocking pre-flight errors with the specific campaign_id and the reason.
6. If either script returned a non-zero exit code, surface the error verbatim and STOP — do not proceed to Confirm.

### 2. Confirmation Gate

Present the pre-flight summary and ask: "Run the sweep? It will dispatch the executor for each eligible campaign in non-interactive mode (no-confirm intent delivered to the executor as prompt text)."

- If the user declines, stop. Do not invoke the script in live mode.
- If the user confirms, proceed to Launch.
- Do NOT add "auto-confirm" / "yes-to-all" **flags to this interactive flow**. The confirmation gate is the primary safety net when the skill is invoked interactively.
- **Exception — Unattended Mode.** A separate documented entry point, `sweep-afk.py` (see the Unattended Mode section), runs the sweep with no interactive prompt. This is permitted because *deliberately invoking that script is itself the explicit go-ahead* — it does not bypass a gate the user is sitting in front of. The interactive flow above keeps its confirmation gate unchanged; the two paths are distinct.

### 3. Launch

1. **Never launch sweep.py (or sweep-afk.py without `--detach`) as a foreground exec/bash tool call.** A sweep runs for hours; agent-harness exec tools enforce timeouts (pi's bash tool killed a live sweep's shell at 30 minutes on 2026-07-17). Worse, on Windows the timeout kills only the wrapper shell: sweep.py survives orphaned, its stdout pipe loses its reader, and it later wedges or crashes on a broken pipe mid-campaign — the harness reports a dead sweep from a stale buffered view while the real process grinds on unattended.
2. After the Confirmation Gate, run exactly one fast call:
   `python <skill-dir>/sweep-afk.py --workspace <root> --detach` plus the same `--saga` / `--only` scope flags the dry-run used.
   This one call is all you need — it does no preflight, no sweep, no reconcile itself. It spawns a detached child (internally re-invoking itself with a hidden `--detached-child` flag), writes that child's stdout/stderr to a fresh file under `.liang/sweep-logs/`, and returns almost instantly with the child's PID and the log path.
3. Verify the launch succeeded: confirm the printed PID is alive and the log file exists and is growing. Report the PID and log path to the user, and state plainly that the sweep now survives the session ending — closing this chat/session does not stop it.
4. Monitor with short, timeout-safe checks — `sweep-afk.py --workspace <root> --status` (read-only, always exits 0, safe to call anytime a sweep might be running) or tailing the log file — never by holding a long-running tool call open.
5. Completion is signaled by the log's final `AFK COMPLETE exit=<n> attempts=<n>` line and a new file in `.liang/sweep-reports/`. Interpret the exit code:
   - 0 → all campaigns passed.
   - 1 → at least one campaign failed.
   - 2 → configuration error; the sweep halted before completing.
   - 3 → unexpected crash.

   Codes 0/1/2 are what sweep.py itself reports and are never retried. A bare 3 (or any other unexpected code) is first treated as an infra-level death by the built-in supervisor, which auto-resumes sweep.py up to twice before giving up and surfacing it as final — see Unattended Mode below.

Do NOT attempt to retry, re-plan, or interpret failures yourself. The script's exit code IS the result.

### 4. Post-Sweep Summary

1. Locate the most recent file under `.liang/sweep-reports/` (sorted by filename, which uses an ISO timestamp).
2. Read the sweep report's YAML or extracted counts and present a concise chat-friendly recap:
   - Overall exit code and what it means.
   - Counts: total / passed / failed / skipped.
   - For each non-passed campaign, the campaign_id and status.
   - The deferred manual backlog: every quest held as `manual_deferred` / `manual_dependency`, grouped by campaign — this is the user's in-editor to-do list, followed by "mark them passed and re-sweep".
   - The path to the sweep report HTML.
   - Paths to per-campaign run reports if surfaced in the sweep report's links.
3. If no sweep report was generated (script crashed before s06 of q003's plan), say so explicitly and point at the script's stderr.
4. Do not suggest next actions beyond opening the sweep report — failures and retries are the user's call.

## Unattended Mode (`sweep-afk.py`)

For fire-and-AFK runs across **any** liang-quest-planner workspace, the skill ships `sweep-afk.py` — a single-command harness co-located with `sweep.py`. It is the deliberate, no-prompt alternative to the interactive flow above; running it IS the user's authorization (see the Confirmation Gate exception).

It chains four phases and returns sweep.py's exit code:

1. **Preflight** — runs `sweep-preflight.py`; aborts before launch on any FAIL.
2. **Sweep** — runs `sweep.py` live (campaigns dispatched in non-interactive mode; no-confirm intent is delivered as prompt text, not an argv flag). Per-step pi children run in fresh contexts; pi auto-injects the workspace `CLAUDE.md` governance.
3. **Reconcile** — runs `p4 reconcile` on **only the source files this run touched** (read from `.run/*/step-*.md`, mtime-scoped). This makes VCS correctness independent of whether an execute-child remembered `p4 edit`/`p4 add`. It never submits. Skipped on non-Perforce projects (p4 absent → prints the file list for manual handling).
4. **Report** — surfaces the sweep report, every run report, and any deferred Tier-2 UAT items the user must still judge (non-interactive mode defers, never auto-accepts, Tier-2 VCs).

Invocation (from any workspace root):

```
python <this-skill-dir>/sweep-afk.py --workspace <root> --dry-run   # validate; runs/opens nothing
python <this-skill-dir>/sweep-afk.py --workspace <root>             # fire and walk away (foreground)
python <this-skill-dir>/sweep-afk.py --workspace <root> --detach    # fire, detach, return instantly
python <this-skill-dir>/sweep-afk.py --workspace <root> --saga <id> # scoped: one saga only
python <this-skill-dir>/sweep-afk.py --workspace <root> --status    # read-only progress check
```

Flags: `--dry-run` (preflight + `sweep.py --dry-run`, no execution), `--no-reconcile` (print the touched-file list instead of opening), `--probe` (one live model call in preflight to confirm the key round-trips), `--saga` / `--only` (forwarded verbatim to sweep.py — see Scoped Sweeps), `--detach` (below), `--status` (below). Always run `--dry-run --probe` once before the first unattended run on a new machine. On a workspace with historical campaigns, prefer the scoped form for AFK runs.

**`--detach`** re-launches `sweep-afk.py` itself as a detached background process and returns almost immediately with a PID and a log path — this is the flag an agent harness must use (see Launch step 2); it is also convenient from a real terminal when you don't want to hold the shell open. The detached child runs with a hidden `--detached-child` flag that puts it on the supervisor path described below; its combined stdout/stderr goes to a new file under `.liang/sweep-logs/` (named like `2026-07-17T0330Z-afk.log`), unbuffered so `tail -f` shows live progress.

**Supervisor / auto-resume.** Every invocation of `sweep-afk.py` — detached or foreground — runs sweep.py under a small supervisor loop instead of a single call. sweep.py's own terminal exit codes (0 = all passed, 1 = a campaign legitimately failed, 2 = config error) are returned as-is and **never** retried — that ban is contractual, matching hard stop 4 below. Any other exit code (3, negative, or anything unexpected) is treated as an infra-level death — the process got orphaned, its stdout pipe broke mid-campaign, the machine's exec-tool timeout killed only the wrapper shell — and the supervisor relaunches sweep.py (which is resume-aware) up to twice, for three attempts total, logging each transition. The final line of every run is `AFK COMPLETE exit=<n> attempts=<n>`.

**Keep-awake.** The detached child also holds the Windows machine awake for the duration of the run (`SetThreadExecutionState`, reset when the run ends) so a multi-hour AFK sweep doesn't die because the machine went to sleep. No-op on non-Windows.

**Single-instance lockfile.** Before sweep.py dispatches anything in live mode, it takes `.liang/sweep.lock` (pid + start time). A second live sweep started in the same workspace while that lock's pid is still alive exits immediately with configuration-error (2) instead of racing the first sweep's manifest writes. A lock left behind by a pid that is no longer alive (stale — e.g. the machine was rebooted) is detected and silently replaced. `--dry-run` never touches the lock. Note: sweeps started before this hardening pass hold no lock file, so the guard only protects runs launched with the upgraded script.

**`--status`** is a read-only query — safe to run at any time, including while a sweep is in progress, and it always exits 0. It reports: whether `.liang/sweep.lock` is held and by a pid that's alive or dead; the newest log under `.liang/sweep-logs/` with its last ~20 lines; the newest file under `.liang/sweep-reports/` with its modification time; and a one-line quest-status summary per campaign read straight from each `manifest.yaml` (e.g. `5 passed / 1 ready / 1 skipped`). Use it instead of holding a long-running tool call open to watch a sweep.

`sweep-afk.py` is designed to be run from a **real terminal** the user owns. If it is ever launched from inside an agent instead, the same rule as Launch step 1 applies: use `--detach`, never a foreground tool call subject to a harness timeout.

**Cross-platform note:** both `sweep.py` and `sweep-preflight.py` resolve the `pi` launcher via `shutil.which("pi")` before spawning — on Windows the npm shim is `pi.cmd` and bare `["pi", ...]` under `subprocess(shell=False)` raises `FileNotFoundError`. Keep that resolution if editing the spawn sites.

## Boundaries — Hard Stops

This skill must never:

1. **Skip the Confirmation Gate in the interactive flow.** When invoked interactively, always require explicit user confirmation before launching in live mode. (The `sweep-afk.py` unattended entry point is the one documented exception — invoking it is itself the explicit authorization.)
2. **Re-implement campaign discovery, toposort, dispatch, status updates, or report generation.** Those live in sweep.py.
3. **Modify any `plan.html`, `quest-NNN-*.md`, or `run-report-*.md` file.** Planner artifacts and generated reports are read-only to this wrapper. Manifest/status mutations and sweep-report generation are `sweep.py`'s job.
4. **Retry or re-plan on failure.** The script's exit code is the final outcome.
5. **Run two sweeps in parallel.** If a sweep is in progress, wait for it to complete.
6. **Bypass workspace pre-flight.** If `.liang/project.yaml` is missing or sweep.py is absent, abort cleanly with a clear message.
7. **Auto-open the sweep report.** Always present the path and let the user decide.
8. **Add new CLI flags to sweep.py from here.** Script CLI changes happen by editing sweep.py directly, not via wrapper translation.

## Failure Modes

- **sweep.py missing:** Abort in Pre-Flight Report. Point at q003 of `camp-2026-05-24-batch-campaign-sweep` for the build instructions.
- **.liang/project.yaml missing:** Abort in Pre-Flight Report. Direct the user to run `liang-quest-planner` first.
- **Dry-run exits non-zero:** Surface the script's stderr verbatim and STOP. Do not proceed to Confirm.
- **Malformed campaign manifest:** sweep.py treats unreadable, unparsable, or non-mapping `manifest.yaml` files as configuration errors (exit 2) and halts the sweep; fix the manifest or move the campaign to `archive/` before retrying.
- **User declines at Confirmation Gate:** Stop. Do not invoke the script in live mode. Do not nag.
- **Live launch exits with code 1:** A campaign failed legitimately. Surface the sweep report and the failed campaign_id(s); do not retry.
- **Live launch exits with code 2:** Configuration error mid-sweep. Surface the script's stderr, report any partial sweep report path, and stop.
- **Live launch exits with code 3:** Unexpected crash. Surface stderr verbatim. Recommend opening the sweep report if one was written.
- **Sweep report file not found in Phase 4:** Script crashed before report generation. Point at stderr. Do not fabricate counts.
- **pyyaml not installed:** sweep.py will fail on import. Surface the error and tell the user: "Install dependencies: `pip install -r liang-quest-batch-sweep/requirements.txt`."
- **A previous foreground launch "timed out":** the sweep is probably NOT dead — the harness killed only the wrapper shell. Before relaunching, check for a live `python … sweep.py` process (`Get-CimInstance Win32_Process | ? { $_.CommandLine -match 'sweep\.py' }`) and compare campaign-manifest / `.run/` artifact mtimes against the harness's report; the report may be a stale buffered view. Never start a second sweep while one is alive (hard stop 5). If a live orphan is found, either let it finish (monitor manifests) or kill its whole tree before relaunching detached. For runs launched with the lockfile-hardened `sweep.py`, this scenario is now largely self-defending: a second live sweep in the same workspace exits 2 immediately instead of racing the first (see next entry), and `sweep-afk.py`'s own supervisor auto-resumes an orphaned/crashed sweep.py without any manual relaunch. This manual-check procedure still matters for sweeps started before the upgrade, or for a wrapper shell around sweep.py that isn't sweep-afk.py.
- **Second sweep exits 2 immediately:** a sweep is already running in this workspace — `.liang/sweep.lock` is held by a live pid. Do not retry or force it. Run `sweep-afk.py --workspace <root> --status` to see who holds it, how long it's been running, and the live campaign/quest counts; wait for it to finish (or investigate why you thought it wasn't running).

## Relationship to Other Skills

- **Upstream:** `liang-quest-planner` produces the `manifest.yaml` files this skill's sweeps execute.
- **Downstream (per campaign):** `liang-quest-executor` is what sweep.py invokes once per eligible campaign in non-interactive mode (no-confirm intent delivered as prompt text, not an argv flag).
- **Parallel:** None. This is the only multi-campaign orchestrator in the family.
- **Shared contracts:**
  - `.liang/project.yaml` — workspace-wide config; sweep.py reads but does not write.
  - `.liang/campaigns/*/manifest.yaml` — sweep.py reads and atomically updates status fields.
  - `.liang/sweep-reports/*.html` — sweep.py writes; this skill reads.
  - `.liang/sweep.lock` — sweep.py writes (live mode only) before dispatching, removes on exit; single-instance guard. See Unattended Mode.
  - `.liang/sweep-logs/*.log` — sweep-afk.py writes when launched with `--detach`; this skill (and `--status`) reads.

## Reference Files

- `sweep.py` — the multi-campaign orchestrator script. Co-located with this SKILL.md.
- `sweep-preflight.py` — deep preflight (executor §2/§3 gates + pi runtime). Read-only; used in Phase 1 and by `sweep-afk.py`.
- `sweep-afk.py` — unattended fire-and-AFK harness (preflight → sweep → p4 reconcile → report), with `--detach` (spawn detached + return), `--status` (read-only progress query), and a built-in supervisor that auto-resumes sweep.py on infra-level death. The skill's no-prompt entry point.
- `requirements.txt` — Python dependencies (currently: `pyyaml>=6.0`).

Always read the script when planning changes to this skill — the script's CLI and exit codes are the source of truth.
