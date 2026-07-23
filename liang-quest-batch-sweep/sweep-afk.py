"""
sweep-afk.py — fire-and-AFK harness for liang-quest-batch-sweep.

Shipped inside the skill so it's shared across every project. One command, any
workspace, no plan edits. Chains the four things you'd otherwise do by hand
around a batch sweep:

  1. PREFLIGHT  — run sweep-preflight.py; abort on any FAIL before launching.
  2. SWEEP      — run the batch-sweep orchestrator (sweep.py) in live mode.
                  Each quest's steps execute in fresh per-step pi child
                  contexts; governance (CLAUDE.md) is auto-injected by pi.
  3. RECONCILE  — reads `.liang/project.yaml` `vcs` field. When
                  `vcs: perforce`, runs `p4 reconcile` on ONLY the source
                  files this sweep touched (read from .run/*/step-*.md,
                  legacy .html fallback, mtime-scoped). For `git`, `none`,
                  or missing VCS, prints
                  the touched-file list for manual handling. Never submits.
  4. REPORT     — surface every run report + sweep report, and list any
                  deferred Tier-2 UAT items that need your eyes.

This is the skill's documented UNATTENDED entry point. Invoking it is itself
the explicit go-ahead — it deliberately runs sweep.py with --no-confirm, in
place of the skill's interactive confirmation gate. For an attended run with a
confirmation prompt, use the skill's interactive flow (see SKILL.md) instead.

General: discovers campaigns + the sweep script dynamically, so it works for
any campaign produced by liang-quest-planner, not one specific case.

Safe to dry-run: `--dry-run` does preflight + `sweep.py --dry-run` and PRINTS
what it would reconcile, executing no quests and opening no files.

AFK hardening: `--detach` re-launches this script as a detached background
process (survives the caller's shell/session ending) and returns almost
instantly with the child's PID and log path. The detached child (internal
`--detached-child` flag) runs a supervisor loop around sweep.py that
auto-resumes on infra-level death (orphaned process, broken pipe, unexpected
crash) but never retries a legitimate campaign failure or a config error.
`--status` is a read-only, always-succeeds query of lock/log/report/campaign
state — safe to run at any time, including while a sweep is in progress.

Exit codes:
  0  sweep completed, all campaigns passed
  1  sweep ran but a campaign failed (see reports)
  2  preflight failed / config error — nothing was launched
  3  harness could not locate sweep.py or the preflight script

Usage:
  python sweep-afk.py --workspace <project-root> [--dry-run]
                      [--no-reconcile] [--probe]
                      [--saga <id|path>] [--only <campaign_id,...>]
  python sweep-afk.py --workspace <project-root> --detach [...same scope flags]
  python sweep-afk.py --workspace <project-root> --status

--saga / --only are forwarded verbatim to sweep.py to scope the sweep (e.g. to
one saga's campaigns instead of every campaign in the workspace). See
sweep.py's docstring for resolution rules and manual-quest hold semantics.
"""

from __future__ import annotations

import argparse
import ctypes
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent


# ---- locating the moving parts (general, not hard-coded) -----------------

def find_preflight() -> Path | None:
    cand = HERE / "sweep-preflight.py"
    return cand if cand.is_file() else None


def find_sweep_script() -> Path | None:
    """sweep.py is co-located with this harness inside the skill folder."""
    cand = HERE / "sweep.py"
    if cand.is_file():
        return cand
    # Fallback: search the pi agent skills tree.
    env = os.environ.get("PI_AGENT_DIR")
    root = Path(env) if env else Path.home() / ".pi" / "agent"
    skills = root / "skills"
    if skills.is_dir():
        for hit in skills.glob("**/liang-quest-batch-sweep/sweep.py"):
            return hit
    return None


# ---- step-file parsing (source of truth for touched files / UAT) ---------

_FENCED_YAML_RE = re.compile(r"^(~~~|```)yaml\s*\n(.*?)\n\1\s*$", re.DOTALL | re.MULTILINE)


def _md_output_yaml(md_path: Path) -> dict[str, Any]:
    """step-<sid>.md stores each contract section as a fenced YAML block
    under a '## <Section>' heading (executor references/step-envelope.md).
    Pull the fenced YAML under '## Output' and parse it."""
    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    m = re.search(r"^## Output\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL | re.MULTILINE)
    if not m:
        return {}
    m2 = _FENCED_YAML_RE.search(m.group(1))
    if not m2:
        return {}
    try:
        data = yaml.safe_load(m2.group(2))
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def _embedded_yaml(html_path: Path) -> dict[str, Any]:
    """Legacy step-<sid>.html format: unsupported since the executor moved
    to Markdown step envelopes. Kept only so pre-existing .html envelopes
    from older runs still contribute to reconcile/UAT discovery."""
    try:
        text = html_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    m = re.search(r"<!--\s*\n(.*?)\n-->", text, re.DOTALL)
    block = m.group(1) if m else text
    m2 = re.search(r"^---\s*\n(.*?)\n---\s*$", block, re.DOTALL | re.MULTILINE)
    payload = m2.group(1) if m2 else block
    try:
        data = yaml.safe_load(payload)
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


def collect_touched_files(ws: Path, since: float = 0.0) -> list[Path]:
    """Union of output.files_changed across step files written at/after
    `since` (epoch seconds). Scoping by mtime keeps reconcile to THIS run's
    writes instead of re-opening files from older, already-submitted
    campaigns. `since=0` includes all step files (illustrative)."""
    out: set[Path] = set()
    camp_root = ws / ".liang" / "campaigns"
    steps = [
        *camp_root.glob("*/.run/*/step-*.md"),
        *camp_root.glob("*/.run/*/step-*.html"),
    ]
    for step in steps:
        try:
            if step.stat().st_mtime < since:
                continue
        except OSError:
            continue
        if step.suffix == ".md":
            changed = _md_output_yaml(step).get("files_changed") or []
        else:
            data = _embedded_yaml(step)
            changed = (data.get("output") or {}).get("files_changed") or []
        for f in changed:
            if not isinstance(f, str) or not f.strip():
                continue
            p = Path(f)
            p = p if p.is_absolute() else (ws / f)
            # never reconcile the sweep's own bookkeeping
            if ".liang" in p.parts:
                continue
            # compile-step children have been observed dumping the build log's
            # rebuilt-file list into files_changed — drop build/derived output
            if _BUILD_OUTPUT_SEGMENTS & set(p.parts):
                continue
            out.add(p)
    return sorted(out)


# UE build/derived-data trees: their presence in files_changed means a child
# recorded compiler output, not an edit list.
_BUILD_OUTPUT_SEGMENTS = {"Intermediate", "Binaries", "Saved", "DerivedDataCache"}


def collect_deferred_uat(ws: Path) -> list[tuple[str, str]]:
    """Return (campaign_dir_name, run_report_path) for reports that carry
    deferred Tier-2 UAT items the user still needs to judge."""
    hits: list[tuple[str, str]] = []
    camp_root = ws / ".liang" / "campaigns"
    reports = [
        *camp_root.glob("*/run-report-*.md"),
        *camp_root.glob("*/run-report-*.html"),
    ]
    for report in reports:
        try:
            txt = report.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            continue
        if "tier_2_deferred" in txt or "pending uat" in txt:
            hits.append((report.parent.name, str(report.relative_to(ws))))
    return hits


# ---- phases --------------------------------------------------------------

def run_preflight(preflight: Path, ws: Path, probe: bool) -> int:
    print("\n=== [1/4] PREFLIGHT " + "=" * 44)
    cmd = [sys.executable, str(preflight), "--workspace", str(ws)]
    if probe:
        cmd.append("--probe")
    return subprocess.run(cmd, check=False).returncode


def run_sweep(
    sweep: Path, ws: Path, dry_run: bool,
    saga: str | None = None, only: str | None = None,
) -> int:
    label = "DRY-RUN" if dry_run else "LIVE"
    print(f"\n=== [2/4] SWEEP ({label}) " + "=" * (40 - len(label)))
    cmd = [sys.executable, str(sweep), "--workspace", str(ws)]
    if dry_run:
        cmd.append("--dry-run")
    if saga:
        cmd.extend(["--saga", saga])
    if only:
        cmd.extend(["--only", only])
    return subprocess.run(cmd, cwd=str(ws), check=False).returncode


def _read_project_vcs(ws: Path) -> str | None:
    """Read .liang/project.yaml vcs field. Returns None if missing/unreadable."""
    proj_yaml = ws / ".liang" / "project.yaml"
    try:
        cfg = yaml.safe_load(proj_yaml.read_text(encoding="utf-8")) or {}
        return cfg.get("vcs")
    except (OSError, yaml.YAMLError):
        return None


def run_reconcile(ws: Path, dry_run: bool, enabled: bool, since: float) -> None:
    print("\n=== [3/4] RECONCILE " + "=" * 44)
    collected = collect_touched_files(ws, since=since)
    if not collected:
        where = "during this run" if since else "in .run/*/step-*.md"
        print(f"  no touched source files recorded {where} (nothing to reconcile).")
        return
    # A recorded path that is absent on disk is suspect (build-log noise or a
    # wrong path); reconciling it would open the depot file FOR DELETE. Only a
    # human confirming a deliberate deletion should do that.
    files = [f for f in collected if f.exists()]
    missing = [f for f in collected if not f.exists()]
    if missing:
        print(f"  {len(missing)} recorded path(s) absent on disk — EXCLUDED from reconcile")
        print("  (verify manually: deliberate deletion vs envelope noise):")
        for f in missing:
            print(f"    {f}")
    if not files:
        print("  no surviving files to reconcile.")
        return
    print(f"  {len(files)} source file(s) touched by the sweep:")
    for f in files:
        print(f"    {f}")
    if not enabled:
        print("  --no-reconcile set; skipping.")
        return

    vcs = _read_project_vcs(ws)
    if vcs != "perforce":
        label = vcs or "unspecified"
        print(f"  VCS is '{label}', not Perforce — no automatic reconcile. Review and")
        print(f"  stage/commit the files above manually.")
        return

    if dry_run:
        print("  [dry-run] would run: p4 reconcile <the files above>  (open for add/edit/delete; never submits)")
        return
    cmd = ["p4", "reconcile", *[str(f) for f in files]]
    try:
        cp = subprocess.run(cmd, cwd=str(ws), capture_output=True, text=True, check=False)
    except FileNotFoundError:
        print("  p4 CLI not found on PATH. Reconcile these manually:")
        for f in files:
            print(f"    p4 reconcile {f}")
        return
    if cp.stdout:
        print(cp.stdout.rstrip())
    if cp.returncode != 0:
        print(f"  [warn] p4 reconcile exit {cp.returncode}: {cp.stderr.strip()[-300:]}")
    else:
        print("  reconcile complete — files opened in your default changelist. "
              "Review + submit manually.")


def report(ws: Path) -> None:
    print("\n=== [4/4] REPORT " + "=" * 47)
    camp_root = ws / ".liang" / "campaigns"
    runs = sorted([
        *camp_root.glob("*/run-report-*.md"),
        *camp_root.glob("*/run-report-*.html"),
    ])
    sweeps = sorted((ws / ".liang" / "sweep-reports").glob("*.html"))
    if sweeps:
        print(f"  sweep report : {sweeps[-1].relative_to(ws)}")
    if runs:
        print("  run reports  :")
        for r in runs:
            print(f"    {r.relative_to(ws)}")
    uat = collect_deferred_uat(ws)
    if uat:
        print(f"\n  ⚠ {len(uat)} run report(s) carry deferred Tier-2 UAT items you must judge:")
        for name, path in uat:
            print(f"    [{name}]  {path}")
    else:
        print("  no deferred Tier-2 UAT items detected.")


# ---- AFK hardening: lock probe, keep-awake, supervisor, detach, status ---

def _pid_is_alive(pid: int) -> bool:
    """Cross-platform, non-lethal PID liveness probe. Duplicated from
    sweep.py (small enough not to warrant importing that script as a module)
    — keep the two in sync if this logic ever changes.

    POSIX: signal 0 via os.kill delivers nothing — it only checks
    existence/permission — so probing with it is safe.

    Windows: os.kill's "signal" argument is not a real signal. For any value
    other than CTRL_C_EVENT/CTRL_BREAK_EVENT, CPython's os.kill() on Windows
    calls TerminateProcess(), which would KILL the process being probed.
    Never use it here. Instead go straight to the Win32 API: open a
    query-only handle and read the exit code — STILL_ACTIVE (259) means the
    process has not exited yet.
    """
    if os.name == "nt":
        process_query_limited_information = 0x1000
        still_active = 259
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(process_query_limited_information, False, pid)
        if not handle:
            return False
        try:
            exit_code = ctypes.c_ulong(0)
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return False
            return exit_code.value == still_active
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, just owned by someone else
    return True


def _safe_load_yaml(path: Path) -> Any:
    """Parse a YAML file, returning None on any read/parse failure."""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None


def _log(msg: str) -> None:
    """Timestamped progress line. Whatever stdout is bound to (a real
    terminal for foreground/plain runs, an append-mode log file for the
    detached child) gets the same format either way."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {msg}", flush=True)


def _keep_awake_enable() -> None:
    """Prevent Windows from sleeping mid-sweep (a multi-hour unattended run
    dying because the machine suspended is exactly the kind of infra death
    this hardening pass exists to avoid). ES_CONTINUOUS keeps the state
    latched until explicitly reset; ES_SYSTEM_REQUIRED forces the system
    (not just the display) to stay awake. No-op on non-Windows."""
    if os.name != "nt":
        return
    es_continuous = 0x80000000
    es_system_required = 0x00000001
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(es_continuous | es_system_required)
    except (AttributeError, OSError):
        pass


def _keep_awake_disable() -> None:
    """Reset the execution-state latch set by _keep_awake_enable. No-op on
    non-Windows."""
    if os.name != "nt":
        return
    es_continuous = 0x80000000
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(es_continuous)
    except (AttributeError, OSError):
        pass


def run_supervised(
    sweep: Path, ws: Path, dry_run: bool,
    saga: str | None, only: str | None,
) -> tuple[int, int]:
    """
    Run sweep.py under a bounded-retry supervisor.

    Terminal exit codes — 0 (all passed), 1 (a campaign legitimately
    failed), 2 (config error) — are returned as-is on whichever attempt
    produces them and are NEVER retried; that ban is contractual (a real
    failure needs a human, not a relaunch).

    Any other exit code (3, negative, or anything outside {0,1,2,3}) is
    treated as an infra-level death — the launching shell got killed, the
    process was orphaned and died on pipe backpressure, etc. sweep.py is
    resume-aware (idempotent on manifest state), so relaunching it is safe.
    At most 2 retries (3 attempts total).

    Returns (final_returncode, attempts_made).
    """
    terminal = {0, 1, 2}
    max_attempts = 3
    rc = 3
    attempt = 0
    for attempt in range(1, max_attempts + 1):
        rc = run_sweep(sweep, ws, dry_run, saga=saga, only=only)
        if rc in terminal:
            _log(f"attempt {attempt} exited rc={rc} (terminal)")
            break
        if attempt == max_attempts:
            _log(f"attempt {attempt} exited rc={rc} (abnormal) — retry budget "
                 f"exhausted, giving up")
            break
        _log(f"attempt {attempt} exited rc={rc} (abnormal) — resuming")
    return rc, attempt


def cmd_detach(raw_args: list[str], ws: Path) -> int:
    """
    Re-launch this script as a detached background process and return
    almost instantly. The child gets every original arg except --detach,
    plus the hidden --detached-child flag that puts it on the supervisor
    path. Total runtime of THIS function must stay near-instant — it does
    no preflight, no sweep, no reconcile; it only spawns and reports.
    """
    forwarded = [a for a in raw_args if a != "--detach"]
    child_argv = [
        sys.executable, "-u", str(Path(__file__).resolve()),
        *forwarded, "--detached-child",
    ]

    log_dir = ws / ".liang" / "sweep-logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%MZ")
    log_path = log_dir / f"{ts}-afk.log"

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    popen_kwargs: dict[str, Any] = {
        "cwd": str(ws),
        "stdin": subprocess.DEVNULL,
        "stdout": open(log_path, "ab"),
        "stderr": subprocess.STDOUT,
        "env": env,
    }
    if os.name == "nt":
        detached_process = 0x00000008
        create_new_process_group = 0x00000200
        popen_kwargs["creationflags"] = detached_process | create_new_process_group
    else:
        popen_kwargs["start_new_session"] = True

    proc = subprocess.Popen(child_argv, **popen_kwargs)

    print(f"[afk] detached — pid {proc.pid}")
    print(f"[afk] log: {log_path}")
    print(f"[afk] check on it with: python {Path(__file__).name} "
          f"--workspace {ws} --status")
    return 0


def cmd_status(ws: Path) -> int:
    """
    Read-only status query: lock, newest log tail, newest sweep report,
    per-campaign quest-status counts. Must work while a sweep is running and
    must never fail loudly on partial/missing state — always returns 0.
    """
    try:
        print(f"=== AFK STATUS — {ws} " + "=" * max(4, 40 - len(str(ws))))

        lock_path = ws / ".liang" / "sweep.lock"
        if not lock_path.is_file():
            print("  lock    : absent — no sweep is holding the lock")
        else:
            lock = _safe_load_yaml(lock_path)
            if not isinstance(lock, dict) or not isinstance(lock.get("pid"), int):
                print(f"  lock    : present but unparsable at {lock_path}")
            else:
                pid = lock["pid"]
                started = lock.get("started", "unknown")
                state = "alive" if _pid_is_alive(pid) else "dead"
                print(f"  lock    : pid {pid} started {started} — {state}")

        log_dir = ws / ".liang" / "sweep-logs"
        logs = sorted(log_dir.glob("*.log")) if log_dir.is_dir() else []
        if logs:
            newest_log = logs[-1]
            print(f"\n  log     : {newest_log}")
            try:
                lines = newest_log.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                lines = []
            print(f"  last {min(20, len(lines))} line(s):")
            for line in lines[-20:]:
                print(f"    {line}")
        else:
            print("\n  log     : none found under .liang/sweep-logs/")

        reports_dir = ws / ".liang" / "sweep-reports"
        reports = [p for p in reports_dir.glob("*") if p.is_file()] if reports_dir.is_dir() else []
        if reports:
            newest_report = max(reports, key=lambda p: p.stat().st_mtime)
            mtime = datetime.fromtimestamp(
                newest_report.stat().st_mtime, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            print(f"\n  report  : {newest_report}  (mtime {mtime})")
        else:
            print("\n  report  : none found under .liang/sweep-reports/")

        camp_root = ws / ".liang" / "campaigns"
        print("\n  campaigns:")
        entries = sorted(camp_root.iterdir()) if camp_root.is_dir() else []
        any_campaign = False
        for entry in entries:
            if not entry.is_dir() or entry.name == "archive":
                continue
            manifest_path = entry / "manifest.yaml"
            if not manifest_path.is_file():
                continue
            any_campaign = True
            manifest = _safe_load_yaml(manifest_path)
            if not isinstance(manifest, dict):
                print(f"    {entry.name}: <unreadable manifest>")
                continue
            quests = manifest.get("quests") or []
            counts: dict[str, int] = {}
            for q in quests:
                status = q.get("status", "unknown") if isinstance(q, dict) else "unknown"
                counts[status] = counts.get(status, 0) + 1
            summary = " / ".join(f"{n} {status}" for status, n in sorted(counts.items()))
            print(f"    {entry.name}: {summary or 'no quests'}")
        if not any_campaign:
            print("    none found under .liang/campaigns/")

        return 0
    except Exception as e:  # noqa: BLE001 — status must never fail loudly
        print(f"[afk] status query hit an unexpected error: {e}", file=sys.stderr)
        return 0


# ---- main ----------------------------------------------------------------

def _force_utf8_stdio() -> None:
    """Windows consoles default to cp1252, which cannot encode glyphs the
    report prints (e.g. the ⚠ marker) — that raises UnicodeEncodeError and
    crashes the harness. Force UTF-8 so output never dies on encoding."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main(argv: list[str] | None = None) -> int:
    _force_utf8_stdio()
    ap = argparse.ArgumentParser(description="Fire-and-AFK harness for liang-quest-batch-sweep.")
    ap.add_argument("--workspace", type=Path, default=Path.cwd())
    ap.add_argument("--dry-run", action="store_true",
                    help="preflight + sweep --dry-run; execute nothing, open nothing")
    ap.add_argument("--no-reconcile", action="store_true",
                    help="skip p4 reconcile; just print the touched-file list")
    ap.add_argument("--probe", action="store_true",
                    help="have the preflight make one live pi model call")
    ap.add_argument("--saga", type=str, default=None,
                    help="scope the sweep to one saga's campaigns (forwarded to sweep.py)")
    ap.add_argument("--only", type=str, default=None,
                    help="scope the sweep to a comma-separated campaign_id list (forwarded to sweep.py)")
    ap.add_argument("--detach", action="store_true",
                    help="launch this harness as a detached background process and return "
                         "immediately (the sweep survives the caller's session ending)")
    ap.add_argument("--status", action="store_true",
                    help="read-only: report lock / log / report / campaign status and exit "
                         "(never fails, safe to run while a sweep is in progress)")
    ap.add_argument("--detached-child", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    ws = args.workspace.resolve()

    if args.status:
        return cmd_status(ws)

    if args.detach:
        raw_args = list(argv) if argv is not None else list(sys.argv[1:])
        return cmd_detach(raw_args, ws)

    preflight = find_preflight()
    sweep = find_sweep_script()
    if not preflight:
        print(f"[afk] sweep-preflight.py not found next to {Path(__file__).name}", file=sys.stderr)
        return 3
    if not sweep:
        print("[afk] could not locate liang-quest-batch-sweep/sweep.py.", file=sys.stderr)
        return 3

    # Keep-awake only matters for the detached supervisor — a plain foreground
    # invocation has a human at the terminal who owns their own machine's
    # sleep settings. Wrapped in try/finally so a mid-run crash never leaves
    # the execution-state latch stuck.
    keep_awake = args.detached_child
    if keep_awake:
        _keep_awake_enable()
    try:
        # Preflight always re-runs here even though the caller (this same
        # script's --dry-run pass, or the skill's interactive Phase 1) may
        # have already run it — cheap re-validation beats trusting stale
        # state across a process boundary, especially for a detached child
        # that could start minutes after it was queued.
        if run_preflight(preflight, ws, args.probe) != 0:
            print("\n[afk] preflight FAILED — aborting before launch. Fix the FAILs and re-run.",
                  file=sys.stderr)
            return 2

        # Scope reconcile to step files written from now on (this run's writes).
        # In dry-run nothing is written, so include all (illustrative) with since=0.
        sweep_start = 0.0 if args.dry_run else time.time()
        sweep_rc, attempts = run_supervised(
            sweep, ws, args.dry_run, saga=args.saga, only=args.only
        )
        run_reconcile(ws, args.dry_run, enabled=not args.no_reconcile, since=sweep_start)
        report(ws)

        print("\n" + "=" * 64)
        if args.dry_run:
            print("[afk] DRY-RUN complete. Re-run without --dry-run to execute for real.")
            final_rc = 0
        elif sweep_rc == 0:
            print("[afk] sweep complete — all campaigns passed. Review reports, then p4 submit.")
            final_rc = 0
        else:
            print(f"[afk] sweep finished with exit {sweep_rc} — at least one campaign failed. "
                  f"See run reports; re-run to resume failed campaigns.")
            final_rc = sweep_rc

        _log(f"AFK COMPLETE exit={final_rc} attempts={attempts}")
        return final_rc
    finally:
        if keep_awake:
            _keep_awake_disable()


if __name__ == "__main__":
    sys.exit(main())
