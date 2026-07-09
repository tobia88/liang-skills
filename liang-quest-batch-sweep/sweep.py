"""
liang-quest-batch-sweep — sweep.py

Multi-campaign orchestrator script. Discovers all eligible campaigns under
.liang/campaigns/, resolves cross-campaign dependencies via the optional
`campaign_depends_on` manifest field, toposorts the campaign DAG (rejecting
cycles), runs pre-flight validation, and dispatches one executor invocation
per campaign via Pi CLI with --no-confirm.

Scoping: `--saga <id|path>` restricts the sweep to the campaigns listed in one
saga's saga.yaml (produced by liang-quest-saga-planner); `--only <id,id,...>`
restricts to an explicit campaign_id list. Without a scope flag the sweep is
workspace-global — on a workspace with historical campaigns that will re-run
every non-passed quest ever left behind, so scoped invocation is the norm.
A scoped campaign may depend on a campaign outside the scope only if that
campaign is already fully passed on disk.

Manual quests: a quest with `manual: true` in the manifest is human-in-editor
work that must never be dispatched to a headless child. Before dispatch, the
sweep holds such quests (and, transitively, their un-passed in-campaign
dependents) at status "skipped" with skip_reason "manual_deferred" /
"manual_dependency". The executor builds its queue solely from status: ready,
so held quests are invisible to it. A campaign whose remaining quests are all
manual holds counts as PASSED with a manual backlog (surfaced in the sweep
report); cross-campaign dependents still run. Complete the manual work, set
those quests to "passed", and re-sweep — stale holds are released
automatically.

NAMING: this file is the "sweep script" — the OUTER multi-campaign
orchestrator. It invokes liang-quest-executor (which may use its own --batch
mode internally) once per eligible campaign.

State lives on disk in manifest.yaml status fields. The script is
idempotent on relaunch: fully-passed campaigns are skipped; any campaign with
non-passed quests has them reset to "ready" and is re-dispatched, so the
executor (which only queues status: ready) actually re-runs them. Pass/fail is
read back from the post-run manifest gated by fresh execution evidence — NOT
from the child process exit code, which `pi --print` always returns as 0.
Manifest mutations use write-to-temp-then-rename (os.replace) for atomicity on
Windows NTFS (per dc004).

Exit codes (matching the executor's contract from q001):
  0 — all campaigns passed
  1 — at least one campaign failed
  2 — configuration error (no campaigns eligible, etc.)
  3 — unexpected crash

Usage: python sweep.py [--dry-run] [--workspace <path>]
                       [--saga <id|path>] [--only <campaign_id,...>]
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import sys
import subprocess
import tempfile
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml  # pyyaml; see requirements.txt

# Constants
CAMPAIGNS_DIR_NAME = ".liang/campaigns"
SAGAS_DIR_NAME = ".liang/sagas"
PROJECT_YAML_PATH = ".liang/project.yaml"
SWEEP_REPORTS_DIR_NAME = ".liang/sweep-reports"
EXECUTOR_SKILL_NAME = "liang-quest-executor"

# skip_reason values the sweep itself writes to hold manual quests out of the
# dispatch queue. Holds are released and recomputed on every sweep.
MANUAL_SKIP_REASONS = ("manual_deferred", "manual_dependency")

EXIT_OK = 0
EXIT_QUEST_FAILED = 1
EXIT_CONFIG_ERROR = 2
EXIT_CRASH = 3
EXIT_TIMEOUT = 124  # internal sentinel: a dispatch exceeded its wall-clock budget

# Per-campaign wall-clock budget for a single executor dispatch. Overridable via
# project.yaml -> executor.campaign_timeout_seconds; set 0 to disable. Guards
# AFK runs against a hung pi process stalling the whole sweep indefinitely.
DEFAULT_CAMPAIGN_TIMEOUT = 3600.0

# Filesystem mtime granularity can be coarse; allow a small slack so artifacts
# written in the same second as dispatch start still count as "this run's".
EVIDENCE_SLACK_SECONDS = 2.0

RUNNABLE_STATUSES = {"planned", "failed", "ready", "in_progress"}  # "ready" is the v4/canonical planner status
SKIPPABLE_STATUSES = {"passed", "skipped"}

def discover_campaigns(workspace: Path) -> tuple[list[dict[str, Any]], list[tuple[str, str]]]:
    """
    Walk .liang/campaigns/ and load each manifest.yaml. Return
    (campaigns, errors) where campaigns is a list of dicts, each containing
    the parsed manifest plus a 'campaign_dir' Path key for later file
    operations, and errors is a list of (dir_name, message) for manifests
    that failed to read/parse. The caller decides which errors are fatal —
    a scoped sweep tolerates broken manifests outside its scope. Skips
    directories without a manifest.yaml and the 'archive/' subdirectory.
    """
    campaigns_dir = workspace / CAMPAIGNS_DIR_NAME
    if not campaigns_dir.is_dir():
        return [], []
    result: list[dict[str, Any]] = []
    errors: list[tuple[str, str]] = []
    for entry in sorted(campaigns_dir.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name == "archive":
            continue
        manifest_path = entry / "manifest.yaml"
        if not manifest_path.is_file():
            continue
        try:
            with manifest_path.open("r", encoding="utf-8") as f:
                manifest = yaml.safe_load(f)
        except (OSError, yaml.YAMLError) as e:
            errors.append((entry.name, f"{manifest_path}: manifest read/parse error: {e}"))
            continue
        if not isinstance(manifest, dict):
            errors.append((entry.name, f"{manifest_path}: manifest must be a YAML mapping"))
            continue
        manifest["campaign_dir"] = entry
        result.append(manifest)
    return result, errors


def toposort_campaigns(campaigns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Order campaigns by their campaign_depends_on graph (Kahn's algorithm).
    Per dc001, campaign_depends_on values are campaign_id strings. Missing
    field or empty list = no cross-campaign deps. Raises ValueError on
    cycle detection. Unresolved deps are validated by validate_campaign_deps
    before this function is called; the guard below is defensive only.
    """
    by_id: dict[str, dict[str, Any]] = {c["campaign_id"]: c for c in campaigns}
    in_degree: dict[str, int] = {c["campaign_id"]: 0 for c in campaigns}
    dependents: dict[str, list[str]] = {c["campaign_id"]: [] for c in campaigns}

    for c in campaigns:
        cid = c["campaign_id"]
        deps = c.get("campaign_depends_on") or []
        for dep in deps:
            if dep not in by_id:
                # Defensive: validate_campaign_deps catches this before toposort.
                continue
            in_degree[cid] += 1
            dependents[dep].append(cid)

    queue = [cid for cid, deg in in_degree.items() if deg == 0]
    ordered: list[dict[str, Any]] = []
    while queue:
        cid = queue.pop(0)
        ordered.append(by_id[cid])
        for dependent in dependents[cid]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(ordered) != len(campaigns):
        # cycle detected — collect campaigns with nonzero in_degree
        cyclic = [cid for cid, deg in in_degree.items() if deg > 0]
        raise ValueError(
            f"campaign_depends_on cycle detected involving: {sorted(cyclic)}"
        )
    return ordered


def preflight_workspace(workspace: Path) -> list[str]:
    """
    Validate workspace-level prerequisites. Returns a list of error strings
    (empty list = pass). Does not raise — caller decides whether to halt.
    """
    errors: list[str] = []
    project_yaml = workspace / PROJECT_YAML_PATH
    if not project_yaml.is_file():
        errors.append(f"missing required file: {project_yaml}")
        return errors
    try:
        with project_yaml.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        if not isinstance(cfg, dict):
            errors.append(f"{project_yaml}: top-level must be a mapping")
    except yaml.YAMLError as e:
        errors.append(f"{project_yaml}: yaml parse error: {e}")
    return errors


def preflight_campaign(campaign: dict[str, Any]) -> tuple[list[str], list[str]]:
    """
    Validate a single campaign. Returns (blocking_errors, warnings).
    Blocking errors prevent the campaign from being dispatched.

    Checks performed:
      1. quests[] is a non-empty list.
      2. Campaign has a campaign-level plan.html.
      3. Every quest has a file field that resolves to an existing .md file.
    """
    blocking: list[str] = []
    warnings: list[str] = []

    campaign_dir = campaign["campaign_dir"]
    cid = campaign.get("campaign_id", "<unknown>")

    quests = campaign.get("quests")
    if not isinstance(quests, list) or len(quests) == 0:
        blocking.append(f"{cid}: quests[] is missing or empty")
        return blocking, warnings

    plan_html = campaign_dir / "plan.html"
    if not plan_html.is_file():
        blocking.append(f"{cid}: campaign plan.html missing at {plan_html}")

    for quest in quests:
        qid = quest.get("id", "<unknown>")
        quest_file = quest.get("file")
        if not quest_file:
            blocking.append(f"{cid}/{qid}: missing file")
            continue
        quest_md = campaign_dir / quest_file
        if not quest_md.is_file():
            blocking.append(f"{cid}/{qid}: quest markdown not found at {quest_md}")

    return blocking, warnings


def write_manifest_atomic(manifest_path: Path, manifest: dict[str, Any]) -> None:
    """
    Atomically write a manifest dict to manifest_path. Strategy per dc004:
      1. Serialize to YAML in memory.
      2. Write to a temp file in the same directory as manifest_path.
      3. os.replace(temp, manifest_path) — atomic on Windows NTFS for
         same-volume renames.
      4. On exception, delete the temp file and re-raise so the original
         manifest is preserved.

    Strips the 'campaign_dir' Path key before writing (added by
    discover_campaigns; not part of the on-disk schema).
    """
    serializable = {k: v for k, v in manifest.items() if k != "campaign_dir"}

    fd, tmp_path_str = tempfile.mkstemp(
        prefix=".manifest.", suffix=".yaml.tmp", dir=str(manifest_path.parent)
    )
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            yaml.safe_dump(
                serializable,
                f,
                sort_keys=False,
                allow_unicode=True,
                default_flow_style=False,
            )
        os.replace(tmp_path, manifest_path)
    except Exception:
        try:
            tmp_path.unlink()
        except FileNotFoundError:
            pass
        raise


def set_quest_status(
    manifest: dict[str, Any], quest_id: str, new_status: str, **extra_fields: Any
) -> bool:
    """
    Mutate the in-memory manifest dict: find quest by id, set status, merge
    any extra_fields. Returns True if the quest was found and mutated,
    False otherwise. Does NOT write to disk — caller invokes
    write_manifest_atomic separately.
    """
    for quest in manifest.get("quests", []):
        if quest.get("id") == quest_id:
            quest["status"] = new_status
            for k, v in extra_fields.items():
                quest[k] = v
            return True
    return False


def reset_for_retry(campaign: dict[str, Any]) -> int:
    """Reset non-passed quests to "ready" so the executor re-queues them on the
    next dispatch, clearing executor-owned bookkeeping fields. Returns the count
    of quests reset. `passed` quests are left untouched (their dependents stay
    satisfied). In-memory only — the caller persists via write_manifest_atomic.

    Why this is load-bearing: liang-quest-executor builds its run queue solely
    from status: ready (SKILL.md §5.2). Without this reset, re-dispatching a
    previously-failed campaign would run zero quests yet still write a fresh run
    report — which the outcome assessment would otherwise read as a pass.
    """
    reset = 0
    for quest in campaign.get("quests", []):
        if _is_manual_hold(quest):
            # Sweep-owned hold: awaiting a human, never re-queued headlessly.
            continue
        if quest.get("status") in ("failed", "skipped", "in_progress"):
            quest["status"] = "ready"
            for field in (
                "skip_reason", "started_at", "completed_at",
                "current_cycle", "total_cycles",
            ):
                quest.pop(field, None)
            reset += 1
    return reset


def validate_campaign_ids(campaigns: list[dict[str, Any]]) -> list[str]:
    """Return error strings for manifests with a missing or duplicate
    campaign_id. Empty list = all good. Runs before toposort, which subscripts
    campaign_id directly and would otherwise KeyError on a malformed manifest."""
    errors: list[str] = []
    seen: dict[str, Any] = {}
    for c in campaigns:
        cid = c.get("campaign_id")
        cdir = c.get("campaign_dir")
        if not isinstance(cid, str) or not cid.strip():
            errors.append(f"{cdir}: manifest missing required 'campaign_id'")
            continue
        if cid in seen:
            errors.append(f"duplicate campaign_id '{cid}' in {cdir} and {seen[cid]}")
        else:
            seen[cid] = cdir
    return errors


def validate_campaign_deps(campaigns: list[dict[str, Any]]) -> list[str]:
    """Return error strings for campaign_depends_on values that reference
    unknown campaign_ids. Empty list = all good. Call before toposort so
    unresolved deps are configuration errors, not silently treated as roots."""
    errors: list[str] = []
    by_id: set[str] = {c["campaign_id"] for c in campaigns
                        if isinstance(c.get("campaign_id"), str)}
    for c in campaigns:
        cid = c.get("campaign_id", "<unknown>")
        for dep in c.get("campaign_depends_on") or []:
            if dep not in by_id:
                errors.append(
                    f"{cid}: campaign_depends_on references unknown campaign_id '{dep}'"
                )
    return errors


def _is_manual_hold(quest: dict[str, Any]) -> bool:
    """True if the quest is currently held out of dispatch for manual reasons."""
    return (
        quest.get("status") == "skipped"
        and quest.get("skip_reason") in MANUAL_SKIP_REASONS
    )


def _quest_done(quest: dict[str, Any]) -> bool:
    """True if the quest needs no further dispatch this sweep: passed, or held
    as manual work awaiting a human (which never resolves headlessly)."""
    return quest.get("status") == "passed" or _is_manual_hold(quest)


def resolve_saga_selection(
    workspace: Path, token: str
) -> tuple[str, list[str], list[str]]:
    """
    Resolve a --saga token to (saga_title, campaign_ids, warnings).

    Token forms accepted, in order:
      1. A path (absolute or workspace-relative) to a saga.yaml file.
      2. A path to a saga directory containing saga.yaml.
      3. A directory name under .liang/sagas/ (exact).
      4. A unique substring of a directory name under .liang/sagas/.

    Campaign entries without a campaign_id (not yet planned) are excluded
    with a warning. Raises ValueError on no match, ambiguous match, or a
    saga.yaml with no planned campaigns.
    """
    saga_yaml: Path | None = None
    cand = Path(token) if Path(token).is_absolute() else workspace / token
    if cand.is_file():
        saga_yaml = cand
    elif cand.is_dir() and (cand / "saga.yaml").is_file():
        saga_yaml = cand / "saga.yaml"
    else:
        sagas_root = workspace / SAGAS_DIR_NAME
        exact = sagas_root / token / "saga.yaml"
        if exact.is_file():
            saga_yaml = exact
        elif sagas_root.is_dir():
            hits = [
                d for d in sorted(sagas_root.iterdir())
                if d.is_dir() and token in d.name and (d / "saga.yaml").is_file()
            ]
            if len(hits) == 1:
                saga_yaml = hits[0] / "saga.yaml"
            elif len(hits) > 1:
                names = ", ".join(d.name for d in hits)
                raise ValueError(f"--saga '{token}' is ambiguous; matches: {names}")
    if saga_yaml is None:
        raise ValueError(
            f"--saga '{token}': no saga.yaml found (tried it as a path, as "
            f"{SAGAS_DIR_NAME}/{token}/, and as a directory-name substring)"
        )

    data = _safe_load_yaml(saga_yaml)
    if not isinstance(data, dict):
        raise ValueError(f"{saga_yaml}: unreadable or not a YAML mapping")
    title = str(data.get("title") or saga_yaml.parent.name)

    ids: list[str] = []
    warnings: list[str] = []
    for entry in data.get("campaigns") or []:
        if not isinstance(entry, dict):
            continue
        cid = entry.get("campaign_id")
        if isinstance(cid, str) and cid.strip():
            ids.append(cid.strip())
        else:
            label = entry.get("id") or entry.get("title") or "<unknown>"
            warnings.append(
                f"saga entry '{label}' has no campaign_id (not planned yet) — excluded from scope"
            )
    if not ids:
        raise ValueError(f"{saga_yaml}: no campaign entries carry a campaign_id")
    return title, ids, warnings


def validate_scoped_deps(
    selected: list[dict[str, Any]], all_campaigns: list[dict[str, Any]]
) -> list[str]:
    """
    Scoped-sweep replacement for validate_campaign_deps. A campaign_depends_on
    target inside the scope is handled by the toposort as usual. A target
    OUTSIDE the scope is satisfied only if that campaign exists on disk with
    every quest done (passed, or a manual hold awaiting a human) — otherwise
    it is a configuration error: widen the scope or run the dependency first.
    """
    errors: list[str] = []
    selected_ids = {c["campaign_id"] for c in selected}
    by_id = {c.get("campaign_id"): c for c in all_campaigns}
    for c in selected:
        cid = c["campaign_id"]
        for dep in c.get("campaign_depends_on") or []:
            if dep in selected_ids:
                continue
            dep_campaign = by_id.get(dep)
            if dep_campaign is None:
                errors.append(
                    f"{cid}: campaign_depends_on references '{dep}', which is not on disk"
                )
                continue
            quests = dep_campaign.get("quests") or []
            if not quests or not all(_quest_done(q) for q in quests):
                errors.append(
                    f"{cid}: depends on '{dep}', which is outside the sweep scope and "
                    f"not fully passed — include it in the scope or run it first"
                )
    return errors


def apply_manual_holds(campaign: dict[str, Any]) -> tuple[int, bool]:
    """
    Hold `manual: true` quests — and, transitively, their un-passed in-campaign
    dependents — out of the dispatch queue by marking them skipped with a
    manual skip_reason. The executor builds its queue solely from status:
    ready, so a held quest is never handed to a headless child (which could
    not do human-in-editor work and would fail the campaign, cascade-skipping
    every dependent).

    Stale holds are released first and recomputed from scratch, so a manual
    quest the user has since completed (status: passed) frees its dependents
    on the next sweep. Dependents are held rather than run because their
    ordering after the manual quest is usually load-bearing (e.g. "delete the
    legacy widgets" ordered after "manually assemble the replacements").

    Returns (held_count, changed). In-memory only — the caller persists via
    write_manifest_atomic.
    """
    quests = campaign.get("quests") or []
    changed = False

    for q in quests:
        if _is_manual_hold(q):
            q["status"] = "ready"
            q.pop("skip_reason", None)
            changed = True

    held: set[str] = set()
    for q in quests:
        if q.get("manual") and q.get("status") != "passed":
            q["status"] = "skipped"
            q["skip_reason"] = "manual_deferred"
            held.add(q.get("id"))
            changed = True

    grew = True
    while grew:
        grew = False
        for q in quests:
            if q.get("id") in held or q.get("status") == "passed":
                continue
            if any(dep in held for dep in q.get("depends_on") or []):
                q["status"] = "skipped"
                q["skip_reason"] = "manual_dependency"
                held.add(q.get("id"))
                changed = True
                grew = True
    return len(held), changed


def _safe_load_yaml(path: Path) -> Any:
    """Parse a YAML file, returning None on any read/parse failure."""
    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except (OSError, yaml.YAMLError):
        return None


def _any_mtime_at_least(paths: Any, cutoff: float) -> bool:
    """True if any path's mtime is >= cutoff."""
    for p in paths:
        try:
            if p.stat().st_mtime >= cutoff:
                return True
        except OSError:
            continue
    return False


def assess_campaign_outcome(
    campaign_dir: Path, workspace: Path, dispatch_start: float, exit_code: int
) -> tuple[str, str | None]:
    """Decide a dispatched campaign's outcome from on-disk truth rather than the
    child's process exit code (`pi --print` returns 0 regardless of quest
    results). Returns (status, run_report_relpath) where status is one of
    "passed" | "failed" | "config_error" | "crash".

    Precedence:
      1. An explicit halt signal in the child exit code (native, or surfaced via
         the EXEC_EXIT_CODE output marker): 2 -> config_error, 3 -> crash.
      2. The re-read manifest the executor mutated during the run: any quest
         failed, or any still ready/in_progress (queue unfinished) -> failed.
      3. False-green guard: a clean manifest with NO execution evidence (run
         report or step envelope) written during THIS dispatch -> failed.
    """
    if exit_code == EXIT_CONFIG_ERROR:
        return "config_error", None
    if exit_code == EXIT_CRASH:
        return "crash", None

    # The executor's run report is Markdown (SKILL.md §8: run-report-*.md);
    # older runs wrote .html. Accept both — globbing only .html made every
    # clean dispatch look evidence-free and thus "failed".
    run_reports = sorted(
        [*campaign_dir.glob("run-report-*.md"), *campaign_dir.glob("run-report-*.html")]
    )
    run_report_relpath: str | None = None
    if run_reports:
        run_report_relpath = (
            str(run_reports[-1].relative_to(workspace)).replace("\\", "/")
        )

    cutoff = dispatch_start - EVIDENCE_SLACK_SECONDS
    has_fresh_evidence = (
        _any_mtime_at_least(run_reports, cutoff)
        # Step envelopes are Markdown per the executor contract; keep the old
        # .html pattern for backward compatibility.
        or _any_mtime_at_least(campaign_dir.glob(".run/*/step-*.md"), cutoff)
        or _any_mtime_at_least(campaign_dir.glob(".run/*/step-*.html"), cutoff)
    )

    manifest = _safe_load_yaml(campaign_dir / "manifest.yaml")
    statuses: list[Any] = []
    if isinstance(manifest, dict):
        statuses = [q.get("status") for q in (manifest.get("quests") or [])]

    if not statuses:
        # Manifest unreadable post-run — fall back to evidence alone.
        return ("passed" if has_fresh_evidence else "failed"), run_report_relpath

    if any(s == "failed" for s in statuses):
        return "failed", run_report_relpath
    if any(s in ("ready", "in_progress") for s in statuses):
        # Executor did not run the queue to completion.
        return "failed", run_report_relpath
    if not has_fresh_evidence:
        # All quests claim passed/skipped but nothing was written this run.
        return "failed", run_report_relpath
    return "passed", run_report_relpath


def _extract_exec_exit_code(output: str) -> int | None:
    """Return the most recent EXEC_EXIT_CODE marker found from the bottom of the output."""
    for line in reversed(output.splitlines()):
        line = line.strip()
        if line.startswith("EXEC_EXIT_CODE:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None


def _stream_combined_output(pipe: Any, sink: Any, collected: list[str]) -> None:
    """Copy a child pipe to a parent stream while retaining text for parsing."""
    try:
        for line in iter(pipe.readline, ""):
            collected.append(line)
            # The live echo must never kill this thread: an encode error on a
            # cp1252 sink would close the pipe (finally below) and break the
            # child's stdout mid-run. Collection above is what feeds the
            # EXEC_EXIT_CODE parsing; the echo is best-effort.
            try:
                sink.write(line)
                sink.flush()
            except (UnicodeEncodeError, OSError, ValueError):
                pass
    finally:
        try:
            pipe.close()
        except OSError:
            pass


def _kill_process_tree(process: subprocess.Popen[Any]) -> None:
    """Best-effort kill of a timed-out child process tree."""
    if process.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            process.kill()
        return

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except Exception:
        process.kill()
        return

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except Exception:
            process.kill()


def dispatch_campaign(
    campaign: dict[str, Any], workspace: Path, timeout: float | None, dry_run: bool = False
) -> int:
    """
    Invoke the general executor for one campaign via Pi CLI in non-interactive
    mode (`--print`), delivering the no-confirm intent as message text (NOT as
    an argv flag — pi has no `--no-confirm` flag and rejects it).
    Returns the subprocess exit code:
      0 — all quests passed
      1 — at least one quest failed (planned failure path)
      2 — configuration error
      3 — unexpected crash

    In dry-run mode, prints the command and returns 0 without invoking.

    The exact pi CLI argument layout follows the pattern documented in
    liang-quest-executor/SKILL.md (Pi CLI mode child invocation
    style). If pi cannot surface a non-zero exit code natively (per the
    q001 Failure Modes 'Exit code emission failure' entry), this function
    parses the combined child output's LAST non-empty line for
    'EXEC_EXIT_CODE: <n>' as a fallback.
    """
    campaign_dir = campaign["campaign_dir"]
    cid = campaign.get("campaign_id", "<unknown>")

    # Resolve the pi launcher to its full path. On Windows the npm shim is
    # `pi.cmd`, and subprocess (shell=False) uses CreateProcess, which does NOT
    # apply PATHEXT — so bare "pi" raises FileNotFoundError. shutil.which honors
    # PATHEXT and is a no-op (returns the resolved path) on POSIX.
    pi_exe = shutil.which("pi") or "pi"

    # `--no-confirm` is NOT a pi CLI flag. pi rejects unknown options
    # ("Unknown option: --no-confirm") — it is only a *convention the executor
    # skill reads from its prompt*; no pi extension registers it. So the
    # no-confirm intent is delivered as MESSAGE TEXT (the positional below),
    # never as argv. `--print` is mandatory: without it pi launches an
    # interactive TUI and hangs on a TTY-less stdin. `--exclude-tools
    # ask_question` is a headless safety net so a stray prompt can't block.
    # Validated live 2026-05-29 (canary: all 4 quests passed, exit 0); the old
    # `[..., "--no-confirm", dir]` form hung/failed every dispatch.
    # MUST be a single line: pi resolves to the npm `pi.CMD` batch shim on
    # Windows, and cmd.exe terminates the command at a newline — everything
    # after the first `\n` in an argv element is silently dropped (verified
    # live 2026-07-09: the child received only the first line, ran the
    # interactive flow, and dead-ended on the §1/§5 confirm prompt).
    no_confirm_msg = (
        f"Execute the planner campaign at this directory: {campaign_dir} -- "
        "Run in NON-INTERACTIVE --no-confirm mode exactly as the skill "
        "documents: skip the Step 1 intent confirmation, default Step 4 "
        "crash-recovery to Resume, skip the Step 5 confirm-once gate, skip the "
        "Step 8a UAT prompt (leave all Tier-2 victory conditions as "
        "tier_2_deferred), preserve all files in Step 9, treat Step 10 "
        "vcs_artifacts as ignore, and skip the Step 11 commit suggestion. "
        "Process the entire quest queue in dependency order to completion, then "
        "write the Markdown run report. Do not ask any questions; proceed with the "
        "documented defaults. As the VERY LAST line of your output, print "
        "exactly 'EXEC_EXIT_CODE: <n>' on its own line, where <n> is 0 "
        "if every quest passed, 1 if any quest failed, 2 on a configuration "
        "error, or 3 on an unexpected crash."
    )
    # Batch-shim newline guard (see comment above) — collapse any whitespace
    # run to a single space so an edit to the prose can never reintroduce one.
    no_confirm_msg = " ".join(no_confirm_msg.split())
    cmd = [
        pi_exe,
        "--print",                          # non-interactive: process and exit
        "--skill", EXECUTOR_SKILL_NAME,
        "--exclude-tools", "ask_question",  # never block on an interactive prompt
        no_confirm_msg,                     # no-confirm intent + campaign dir as the message
    ]
    cmd_display = (
        f"{pi_exe} --print --skill {EXECUTOR_SKILL_NAME} "
        f"--exclude-tools ask_question <no-confirm msg for {cid}>"
    )

    if dry_run:
        print(f"[sweep] would RUN: {cmd_display}")
        return EXIT_OK

    print(f"[sweep] dispatching {cid} via {cmd_display}")
    output_chunks: list[str] = []
    process: subprocess.Popen[Any] | None = None
    reader: threading.Thread | None = None
    try:
        popen_kwargs: dict[str, Any] = {}
        if os.name != "nt":
            popen_kwargs["start_new_session"] = True
        process = subprocess.Popen(
            cmd,
            cwd=workspace,
            stdin=subprocess.DEVNULL,  # pi blocks on an inherited open stdin without this
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            # pi emits UTF-8; without an explicit encoding, text mode decodes
            # with the locale codec (cp1252 on Windows), and undefined bytes
            # like 0x9d kill the reader thread mid-run.
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            **popen_kwargs,
        )
        if process.stdout is None:
            raise RuntimeError("failed to capture child output")
        reader = threading.Thread(
            target=_stream_combined_output,
            args=(process.stdout, sys.stdout, output_chunks),
            daemon=True,
        )
        reader.start()
        # pi (node) can finish its agent loop yet never exit: observed
        # 2026-07-09 on c01 of the battle-simulator saga — the child printed
        # its final EXEC_EXIT_CODE line at 01:30, then the process sat idle
        # until the 3600s campaign timeout killed it at 01:59 and the sweep
        # read a fully-passed campaign as failed (cascade-skipping 6
        # dependents). So: poll in short slices; once the completion marker
        # appears in the collected output, give the process a short grace to
        # exit on its own, then reap the hung tree and trust the marker.
        deadline = None if timeout is None else time.monotonic() + timeout
        marker_grace_deadline: float | None = None
        while True:
            try:
                exit_code = process.wait(timeout=15)
                break
            except subprocess.TimeoutExpired:
                now = time.monotonic()
                if (
                    marker_grace_deadline is None
                    and _extract_exec_exit_code("".join(output_chunks)) is not None
                ):
                    marker_grace_deadline = now + 60
                if marker_grace_deadline is not None and now >= marker_grace_deadline:
                    print(
                        f"[sweep] {cid} printed EXEC_EXIT_CODE but the pi process "
                        f"did not exit — reaping the hung process tree and "
                        f"continuing with the marker code",
                        file=sys.stderr,
                    )
                    _kill_process_tree(process)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    exit_code = 0  # kill code is meaningless; marker wins below
                    break
                if deadline is not None and now >= deadline:
                    raise
        reader.join(timeout=5)
    except subprocess.TimeoutExpired:
        if process is not None:
            _kill_process_tree(process)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        if reader is not None:
            reader.join(timeout=5)
        timeout_label = f"{timeout:.0f}s" if timeout is not None else "unbounded"
        print(f"[sweep] {cid} dispatch timed out after {timeout_label}", file=sys.stderr)
        return EXIT_TIMEOUT
    except FileNotFoundError as e:
        print(f"[sweep] pi CLI not found: {e}", file=sys.stderr)
        return EXIT_CRASH
    except Exception as e:
        if process is not None and process.poll() is None:
            _kill_process_tree(process)
        print(f"[sweep] dispatch failed for {cid}: {e}", file=sys.stderr)
        return EXIT_CRASH

    # Honor native exit code first. If Pi returns 0 (normal for pi --print even
    # when skill logic failed), fall back to EXEC_EXIT_CODE on the final line of
    # combined stdout/stderr.
    marker_code = _extract_exec_exit_code("".join(output_chunks))
    if exit_code == 0 and marker_code is not None:
        exit_code = marker_code

    return exit_code


def cascade_skip_dependents(
    failed_campaign_id: str, all_campaigns: list[dict[str, Any]]
) -> list[str]:
    """
    For a failed campaign, find all transitive dependent campaigns and
    return their campaign_ids. Per dc001, campaign_depends_on uses
    campaign_id values. Used by the main loop to mark dependent campaigns
    skipped before the loop reaches them.
    """
    dependents_of: dict[str, list[str]] = {c["campaign_id"]: [] for c in all_campaigns}
    for c in all_campaigns:
        for dep in c.get("campaign_depends_on") or []:
            if dep in dependents_of:
                dependents_of[dep].append(c["campaign_id"])

    # BFS from failed_campaign_id
    result: list[str] = []
    visited: set[str] = set()
    queue = [failed_campaign_id]
    while queue:
        current = queue.pop(0)
        for dep in dependents_of.get(current, []):
            if dep not in visited:
                visited.add(dep)
                result.append(dep)
                queue.append(dep)
    return result


SWEEP_REPORT_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Sweep Report &mdash; {timestamp}</title>
  <style>
    :root {{ --bg:#f6f1e8; --paper:#fffaf0; --ink:#252338; --muted:#6f6984;
      --line:rgba(45,40,70,0.14); --deep:#17182e; --deep-2:#232245;
      --gold:#d6a84f; --ok:#3f8f6b; --danger:#b85757; --warn:#b8872c; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--ink);
      font:16px/1.65 ui-sans-serif, system-ui, "Segoe UI", sans-serif; }}
    .page {{ width:min(1080px, calc(100% - 32px)); margin:0 auto; padding:32px 0 48px; }}
    .hero {{ border-radius:24px; padding:30px;
      background:linear-gradient(145deg, var(--deep), var(--deep-2));
      color:#fff8e8; box-shadow:0 12px 36px rgba(31,27,49,0.18); }}
    .eyebrow {{ color:#f3d58b; font-size:0.75rem; font-weight:800;
      letter-spacing:0.14em; text-transform:uppercase; margin:0 0 8px; }}
    h1 {{ margin:0; font-size:clamp(1.6rem,3vw,2.5rem); letter-spacing:-0.03em; }}
    .meta-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr));
      gap:10px; margin-top:18px; }}
    .meta-card {{ padding:12px 14px; border:1px solid rgba(255,255,255,0.14);
      border-radius:12px; background:rgba(255,255,255,0.07); }}
    .meta-label {{ display:block; color:rgba(255,248,232,0.62);
      font-size:0.7rem; font-weight:800; letter-spacing:0.08em;
      text-transform:uppercase; }}
    .meta-value {{ display:block; margin-top:4px; font-weight:800; }}
    table {{ width:100%; margin-top:22px; border-collapse:collapse;
      background:var(--paper); border-radius:14px; overflow:hidden;
      box-shadow:0 8px 22px rgba(31,27,49,0.07); }}
    th, td {{ padding:12px 14px; border-bottom:1px solid var(--line); text-align:left; }}
    th {{ background:rgba(23,24,46,0.94); color:#fff8e8; font-size:0.75rem;
      text-transform:uppercase; letter-spacing:0.08em; }}
    tr:last-child td {{ border-bottom:0; }}
    .status {{ display:inline-block; padding:3px 10px; border-radius:999px;
      font-size:0.75rem; font-weight:800; text-transform:uppercase; letter-spacing:0.05em; }}
    .status.passed {{ background:rgba(63,143,107,0.14); color:#2d6d52; }}
    .status.failed {{ background:rgba(184,87,87,0.14); color:#8d3f3f; }}
    .status.skipped {{ background:rgba(184,135,44,0.16); color:#805d1d; }}
    .status.crash {{ background:rgba(123,92,200,0.14); color:#5d45a0; }}
    .uat-badge {{ display:inline-block; padding:2px 8px; border-radius:999px;
      font-size:0.7rem; font-weight:800; text-transform:uppercase;
      letter-spacing:0.05em;
      background:rgba(184,135,44,0.20); color:#805d1d; }}
    .uat-none {{ color:var(--muted); font-size:0.8rem; }}
    .footer {{ margin-top:28px; padding-top:18px; color:var(--muted);
      font-size:0.85rem; text-align:center; }}
  </style>
</head>
<body>
  <main class="page">
    <header class="hero">
      <p class="eyebrow">Sweep Report</p>
      <h1>Batch Campaign Sweep &mdash; {timestamp}</h1>
      <section class="meta-grid">
        <div class="meta-card"><span class="meta-label">Total</span><span class="meta-value">{total}</span></div>
        <div class="meta-card"><span class="meta-label">Passed</span><span class="meta-value">{passed}</span></div>
        <div class="meta-card"><span class="meta-label">Failed</span><span class="meta-value">{failed}</span></div>
        <div class="meta-card"><span class="meta-label">Skipped</span><span class="meta-value">{skipped}</span></div>
      </section>
    </header>

    <table>
      <thead>
        <tr><th>Order</th><th>Campaign ID</th><th>Status</th><th>UAT</th><th>Manual</th><th>Run Report</th></tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>

    <p class="footer">Generated by liang-quest-batch-sweep / sweep.py &middot; This is the SWEEP report (multi-campaign). Per-campaign run reports linked above are generated by the executor. "Pending" in the UAT column means the campaign passed mechanically but has deferred Tier-2 victory conditions awaiting human review. A count in the Manual column means that many quests are human-in-editor work the sweep held out of the queue (skip_reason manual_deferred / manual_dependency) &mdash; do them, mark them passed, and re-sweep.</p>
  </main>
</body>
</html>
"""


def _check_uat_pending(run_report_relpath: str | None, workspace: Path) -> bool:
    """Scan the per-campaign run report for deferred Tier-2 UAT indicators.
    Returns True if the report contains 'tier_2_deferred' or 'Pending UAT'."""
    if not run_report_relpath:
        return False
    report_path = workspace / run_report_relpath
    try:
        text = report_path.read_text(encoding="utf-8")
        return "tier_2_deferred" in text or "Pending UAT" in text
    except OSError:
        return False


def _html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_sweep_report(
    workspace: Path, results: list[dict[str, Any]]
) -> Path:
    """
    Write the multi-campaign sweep report. Per dc006, the report's footer
    and title use 'sweep report' / 'sweep' wording — distinct from any
    per-campaign run report or batch-executor-script artifact.

    results is a list of dicts each containing:
      - campaign_id: str
      - order: int (1-based index in dispatch order)
      - status: 'passed' | 'failed' | 'skipped' | 'crash'
      - run_report_relpath: str | None (path to executor's run report, if any)
      - has_uat_pending: bool
      - manual_pending: int (quests held as manual work awaiting a human)
    """
    reports_dir = workspace / SWEEP_REPORTS_DIR_NAME
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    report_path = reports_dir / f"{timestamp}.html"

    counts = {"passed": 0, "failed": 0, "skipped": 0, "crash": 0}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    rows: list[str] = []
    for r in results:
        link = ""
        if r.get("run_report_relpath"):
            link = (
                f'<a href="{_html_escape(r["run_report_relpath"])}">view</a>'
            )
        else:
            link = "&mdash;"
        uat_cell = ""
        if r.get("has_uat_pending"):
            uat_cell = '<span class="uat-badge">Pending</span>'
        else:
            uat_cell = '<span class="uat-none">&mdash;</span>'
        manual_n = r.get("manual_pending") or 0
        if manual_n:
            manual_cell = f'<span class="uat-badge">{manual_n} deferred</span>'
        else:
            manual_cell = '<span class="uat-none">&mdash;</span>'
        rows.append(
            f'<tr>'
            f'<td>{r["order"]}</td>'
            f'<td><code>{_html_escape(r["campaign_id"])}</code></td>'
            f'<td><span class="status {r["status"]}">{r["status"]}</span></td>'
            f'<td>{uat_cell}</td>'
            f'<td>{manual_cell}</td>'
            f'<td>{link}</td>'
            f'</tr>'
        )

    html = SWEEP_REPORT_TEMPLATE.format(
        timestamp=timestamp,
        total=len(results),
        passed=counts["passed"],
        failed=counts["failed"],
        skipped=counts["skipped"],
        rows="\n".join(rows),
    )
    report_path.write_text(html, encoding="utf-8")
    return report_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="sweep",
        description="liang-quest-batch-sweep — multi-campaign orchestrator (sweep script).",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Workspace root (default: current directory)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be dispatched without invoking the executor",
    )
    parser.add_argument(
        "--saga",
        type=str,
        default=None,
        help=(
            "Scope the sweep to one saga's campaigns: a saga id / directory "
            f"name (substring ok) under {SAGAS_DIR_NAME}/, or a path to a "
            "saga directory or saga.yaml"
        ),
    )
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help="Scope the sweep to a comma-separated list of campaign_ids (unioned with --saga)",
    )
    return parser.parse_args(argv)


def _force_utf8_stdio() -> None:
    """Windows consoles/pipes default to cp1252, which cannot encode glyphs
    the child output and reports contain — that raises UnicodeEncodeError and
    crashes the harness. Force UTF-8 so output never dies on encoding."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main(argv: list[str] | None = None) -> int:
    _force_utf8_stdio()
    args = parse_args(argv)
    workspace: Path = args.workspace.resolve()

    # Workspace pre-flight
    workspace_errors = preflight_workspace(workspace)
    if workspace_errors:
        for e in workspace_errors:
            print(f"[sweep] workspace error: {e}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    # Resolve the sweep scope (if any) before discovery error handling — a
    # scoped sweep tolerates broken manifests outside its scope.
    scope_ids: set[str] | None = None
    scope_label: str | None = None
    if args.saga or args.only:
        scope_ids = set()
        if args.saga:
            try:
                saga_title, saga_ids, saga_warnings = resolve_saga_selection(
                    workspace, args.saga
                )
            except ValueError as e:
                print(f"[sweep] scope error: {e}", file=sys.stderr)
                return EXIT_CONFIG_ERROR
            for w in saga_warnings:
                print(f"[sweep] warning: {w}", file=sys.stderr)
            scope_ids |= set(saga_ids)
            scope_label = f"saga '{saga_title}'"
        if args.only:
            only_ids = {t.strip() for t in args.only.split(",") if t.strip()}
            if not only_ids:
                print("[sweep] scope error: --only given but no campaign_ids parsed", file=sys.stderr)
                return EXIT_CONFIG_ERROR
            scope_ids |= only_ids
            scope_label = f"{scope_label} + --only" if scope_label else "--only list"

    # Discover
    all_campaigns, discover_errors = discover_campaigns(workspace)
    if discover_errors:
        # Unscoped: every broken manifest is fatal (historical behavior).
        # Scoped: fatal only if the broken folder is (by the dir==campaign_id
        # naming convention) inside the scope; others downgrade to warnings.
        fatal = [
            msg for dir_name, msg in discover_errors
            if scope_ids is None or dir_name in scope_ids
        ]
        for dir_name, msg in discover_errors:
            level = "manifest error" if (scope_ids is None or dir_name in scope_ids) else "warning (out of scope)"
            print(f"[sweep] {level}: {msg}", file=sys.stderr)
        if fatal:
            return EXIT_CONFIG_ERROR
    if not all_campaigns:
        print(f"[sweep] no campaigns found under {workspace / CAMPAIGNS_DIR_NAME}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    # Validate campaign identity before building the dependency graph — a missing
    # or duplicate campaign_id would otherwise KeyError mid-toposort. In scoped
    # mode, identity problems on out-of-scope campaigns are warnings only.
    id_errors = validate_campaign_ids(all_campaigns)
    if id_errors:
        if scope_ids is not None:
            fatal_ids = [e for e in id_errors if any(cid in e for cid in scope_ids)]
        else:
            fatal_ids = id_errors
        for e in id_errors:
            level = "manifest error" if e in fatal_ids else "warning (out of scope)"
            print(f"[sweep] {level}: {e}", file=sys.stderr)
        if fatal_ids:
            return EXIT_CONFIG_ERROR

    # Apply the scope filter and validate dependencies.
    if scope_ids is not None:
        by_id = {c.get("campaign_id"): c for c in all_campaigns}
        missing = sorted(cid for cid in scope_ids if cid not in by_id)
        if missing:
            for cid in missing:
                print(
                    f"[sweep] scope error: campaign '{cid}' not found under "
                    f"{CAMPAIGNS_DIR_NAME}",
                    file=sys.stderr,
                )
            return EXIT_CONFIG_ERROR
        campaigns = [c for c in all_campaigns if c.get("campaign_id") in scope_ids]
        dep_errors = validate_scoped_deps(campaigns, all_campaigns)
        if dep_errors:
            for e in dep_errors:
                print(f"[sweep] scope error: {e}", file=sys.stderr)
            return EXIT_CONFIG_ERROR
        print(
            f"[sweep] scope: {scope_label} — {len(campaigns)} of "
            f"{len(all_campaigns)} campaign(s) in scope; "
            f"{len(all_campaigns) - len(campaigns)} excluded",
            file=sys.stderr,
        )
    else:
        campaigns = all_campaigns
        # Unresolved campaign_depends_on is a configuration error, not a silent root.
        dep_errors = validate_campaign_deps(campaigns)
        if dep_errors:
            for e in dep_errors:
                print(f"[sweep] manifest error: {e}", file=sys.stderr)
            return EXIT_CONFIG_ERROR

    # Per-campaign wall-clock budget for a single executor dispatch.
    proj_cfg = _safe_load_yaml(workspace / PROJECT_YAML_PATH) or {}
    executor_cfg = proj_cfg.get("executor") or {}
    if not isinstance(executor_cfg, dict):
        executor_cfg = {}
    campaign_timeout_raw = executor_cfg.get(
        "campaign_timeout_seconds", DEFAULT_CAMPAIGN_TIMEOUT
    )
    if campaign_timeout_raw is None:
        campaign_timeout_raw = DEFAULT_CAMPAIGN_TIMEOUT
    try:
        campaign_timeout = float(campaign_timeout_raw)
    except (TypeError, ValueError):
        print(
            "[sweep] project config error: executor.campaign_timeout_seconds must be numeric",
            file=sys.stderr,
        )
        return EXIT_CONFIG_ERROR
    if campaign_timeout < 0:
        print(
            "[sweep] project config error: executor.campaign_timeout_seconds cannot be negative",
            file=sys.stderr,
        )
        return EXIT_CONFIG_ERROR
    if campaign_timeout == 0:
        campaign_timeout = None

    # Toposort (raises ValueError on cycle). In scoped mode, deps outside the
    # scope were validated as fully-done above and are ignored by the sort.
    try:
        ordered = toposort_campaigns(campaigns)
    except ValueError as e:
        print(f"[sweep] {e}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    # Per-campaign pre-flight — collect blocking errors.
    # Skip campaigns where all quests are already terminal (passed/skipped/failed)
    # — they don't need structural validation.
    blocked_ids: set[str] = set()
    for c in ordered:
        quests = c.get("quests", [])
        # Only a fully-done campaign (passed, or held manual work) is exempt from
        # structural validation. Anything else is a dispatch candidate — its
        # non-passed quests get reset to ready below — so it must be well-formed.
        if quests and all(_quest_done(q) for q in quests):
            continue
        blocking, warnings = preflight_campaign(c)
        for w in warnings:
            print(f"[sweep] warning: {w}", file=sys.stderr)
        if blocking:
            for b in blocking:
                print(f"[sweep] blocking: {b}", file=sys.stderr)
            blocked_ids.add(c["campaign_id"])

    if blocked_ids:
        print(
            f"[sweep] {len(blocked_ids)} campaign(s) failed pre-flight; halting sweep",
            file=sys.stderr,
        )
        return EXIT_CONFIG_ERROR

    # Dispatch loop
    results: list[dict[str, Any]] = []
    skipped_by_cascade: set[str] = set()

    for order_idx, campaign in enumerate(ordered, start=1):
        cid = campaign["campaign_id"]
        campaign_dir = campaign["campaign_dir"]
        manifest_path = campaign_dir / "manifest.yaml"

        if cid in skipped_by_cascade:
            # mark every quest as skipped if not already terminal
            for q in campaign.get("quests", []):
                if q.get("status") in RUNNABLE_STATUSES:
                    set_quest_status(
                        campaign, q["id"], "skipped",
                        skip_reason="cascade-skip from failed cross-campaign dependency",
                    )
            if not args.dry_run:
                write_manifest_atomic(manifest_path, campaign)
            results.append({
                "campaign_id": cid, "order": order_idx, "status": "skipped",
                "run_report_relpath": None, "has_uat_pending": False,
                "manual_pending": 0,
            })
            action = "CASCADE-SKIP"
            print(f"[sweep] {order_idx}. {cid} — {action} (depends on failed campaign)", file=sys.stderr)
            continue

        # Hold manual quests (and their un-passed dependents) out of the
        # dispatch queue before anything else looks at statuses.
        manual_pending, holds_changed = apply_manual_holds(campaign)

        # Resume-aware: a fully-done campaign (passed everywhere, modulo manual
        # holds awaiting a human) is done; nothing to dispatch.
        quests = campaign.get("quests", [])
        if quests and all(_quest_done(q) for q in quests):
            if holds_changed and not args.dry_run:
                write_manifest_atomic(manifest_path, campaign)
            results.append({
                "campaign_id": cid, "order": order_idx,
                "status": "passed", "run_report_relpath": None,
                "has_uat_pending": False, "manual_pending": manual_pending,
            })
            suffix = (
                f"all quests passed" if manual_pending == 0
                else f"all automated quests passed; {manual_pending} manual quest(s) still deferred"
            )
            print(f"[sweep] {order_idx}. {cid} — SKIP ({suffix})", file=sys.stderr)
            continue

        # Retry-aware: reset non-passed quests to ready so the executor (which
        # only queues status: ready) actually re-runs them on this dispatch.
        # Manual holds are excluded from the reset.
        reset_n = reset_for_retry(campaign)
        if (reset_n or holds_changed) and not args.dry_run:
            write_manifest_atomic(manifest_path, campaign)
        if reset_n:
            print(f"[sweep] {order_idx}. {cid} — reset {reset_n} non-passed quest(s) "
                  f"to ready for retry", file=sys.stderr)
        if manual_pending:
            print(f"[sweep] {order_idx}. {cid} — holding {manual_pending} manual "
                  f"quest(s) out of the queue (manual_deferred/manual_dependency)",
                  file=sys.stderr)

        # Dispatch
        dispatch_start = time.time()
        exit_code = dispatch_campaign(
            campaign, workspace=workspace, timeout=campaign_timeout, dry_run=args.dry_run
        )

        if args.dry_run:
            results.append({
                "campaign_id": cid, "order": order_idx, "status": "passed",
                "run_report_relpath": None, "has_uat_pending": False,
                "manual_pending": manual_pending,
            })
            continue

        # Timeout is a soft failure: mark failed, cascade, and keep going so one
        # hung campaign doesn't abort the whole sweep.
        if exit_code == EXIT_TIMEOUT:
            timeout_label = (
                f"{campaign_timeout:.0f}s" if campaign_timeout is not None else "configured"
            )
            print(f"[sweep] {cid} exceeded the {timeout_label} campaign "
                  f"timeout — marking FAILED and continuing.", file=sys.stderr)
            for dep_cid in cascade_skip_dependents(cid, campaigns):
                skipped_by_cascade.add(dep_cid)
            results.append({
                "campaign_id": cid, "order": order_idx, "status": "failed",
                "run_report_relpath": None, "has_uat_pending": False,
                "manual_pending": manual_pending,
            })
            continue

        # Pass/fail is read from the post-run manifest gated by fresh execution
        # evidence — NOT from the child exit code (`pi --print` returns 0 whatever
        # the quests did). Exit 2/3 (native or via EXEC_EXIT_CODE) is honored only
        # as an explicit halt signal.
        status, run_report_relpath = assess_campaign_outcome(
            campaign_dir, workspace, dispatch_start, exit_code
        )

        uat_pending = _check_uat_pending(run_report_relpath, workspace)

        if status == "config_error":
            print(f"[sweep] {cid} reported a configuration error — halting sweep", file=sys.stderr)
            results.append({
                "campaign_id": cid, "order": order_idx, "status": "failed",
                "run_report_relpath": run_report_relpath,
                "has_uat_pending": False, "manual_pending": manual_pending,
            })
            write_sweep_report(workspace, results)
            return EXIT_CONFIG_ERROR

        if status == "crash":
            print(f"[sweep] {cid} crashed (exit {exit_code}) — halting sweep", file=sys.stderr)
            results.append({
                "campaign_id": cid, "order": order_idx, "status": "crash",
                "run_report_relpath": run_report_relpath,
                "has_uat_pending": False, "manual_pending": manual_pending,
            })
            write_sweep_report(workspace, results)
            return EXIT_CRASH

        # Cascade-skip dependents on failure
        if status == "failed":
            for dep_cid in cascade_skip_dependents(cid, campaigns):
                skipped_by_cascade.add(dep_cid)

        results.append({
            "campaign_id": cid, "order": order_idx, "status": status,
            "run_report_relpath": run_report_relpath,
            "has_uat_pending": uat_pending, "manual_pending": manual_pending,
        })

    # Write sweep report (live mode only; dry-run writes nothing)
    if not args.dry_run:
        report_path = write_sweep_report(workspace, results)
        print(f"[sweep] sweep report written to {report_path}")
    else:
        print(f"[sweep] dry-run complete — no reports written, no manifests mutated")

    # Aggregate exit code: 1 if any failed; 0 otherwise
    if any(r["status"] in ("failed", "crash") for r in results):
        return EXIT_QUEST_FAILED
    return EXIT_OK


if __name__ == "__main__":
    # Honor the documented "exit 3 on unexpected crash" contract: any uncaught
    # exception becomes a clean EXIT_CRASH with a traceback on stderr, rather
    # than a bare Python traceback + exit 1.
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException:  # noqa: BLE001 — last-resort crash boundary
        print("[sweep] unexpected crash:", file=sys.stderr)
        traceback.print_exc()
        sys.exit(EXIT_CRASH)
