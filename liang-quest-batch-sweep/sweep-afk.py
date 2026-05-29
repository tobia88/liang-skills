"""
sweep-afk.py — fire-and-AFK harness for liang-quest-batch-sweep.

Shipped inside the skill so it's shared across every project. One command, any
workspace, no plan edits. Chains the four things you'd otherwise do by hand
around a batch sweep:

  1. PREFLIGHT  — run sweep-preflight.py; abort on any FAIL before launching.
  2. SWEEP      — run the batch-sweep orchestrator (sweep.py) in live mode.
                  Each quest's steps execute in fresh per-step pi child
                  contexts; governance (CLAUDE.md) is auto-injected by pi.
  3. RECONCILE  — `p4 reconcile` ONLY the source files the sweep actually
                  touched (read from .run/*/step-*.html output sections).
                  Makes Perforce correctness independent of whether a child
                  remembered `p4 edit`/`p4 add`. Never submits.
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

Exit codes:
  0  sweep completed, all campaigns passed
  1  sweep ran but a campaign failed (see reports)
  2  preflight failed / config error — nothing was launched
  3  harness could not locate sweep.py or the preflight script

Usage:
  python sweep-afk.py --workspace <project-root> [--dry-run]
                      [--no-reconcile] [--probe]
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
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

def _embedded_yaml(html_path: Path) -> dict[str, Any]:
    """step-<sid>.html stores its contract as YAML inside the opening
    HTML comment. Pull it out and parse it."""
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
    for step in camp_root.glob("*/.run/*/step-*.html"):
        try:
            if step.stat().st_mtime < since:
                continue
        except OSError:
            continue
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
            out.add(p)
    return sorted(out)


def collect_deferred_uat(ws: Path) -> list[tuple[str, str]]:
    """Return (campaign_dir_name, run_report_path) for reports that carry
    deferred Tier-2 UAT items the user still needs to judge."""
    hits: list[tuple[str, str]] = []
    camp_root = ws / ".liang" / "campaigns"
    for report in camp_root.glob("*/run-report-*.html"):
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


def run_sweep(sweep: Path, ws: Path, dry_run: bool) -> int:
    label = "DRY-RUN" if dry_run else "LIVE"
    print(f"\n=== [2/4] SWEEP ({label}) " + "=" * (40 - len(label)))
    cmd = [sys.executable, str(sweep), "--workspace", str(ws)]
    if dry_run:
        cmd.append("--dry-run")
    return subprocess.run(cmd, cwd=str(ws), check=False).returncode


def run_reconcile(ws: Path, dry_run: bool, enabled: bool, since: float) -> None:
    print("\n=== [3/4] RECONCILE " + "=" * 44)
    files = collect_touched_files(ws, since=since)
    if not files:
        where = "during this run" if since else "in .run/*/step-*.html"
        print(f"  no touched source files recorded {where} (nothing to reconcile).")
        return
    print(f"  {len(files)} source file(s) touched by the sweep:")
    for f in files:
        print(f"    {f}")
    if not enabled:
        print("  --no-reconcile set; skipping. Run `p4 reconcile` on the above yourself.")
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
    runs = sorted(camp_root.glob("*/run-report-*.html"))
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


# ---- main ----------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fire-and-AFK harness for liang-quest-batch-sweep.")
    ap.add_argument("--workspace", type=Path, default=Path.cwd())
    ap.add_argument("--dry-run", action="store_true",
                    help="preflight + sweep --dry-run; execute nothing, open nothing")
    ap.add_argument("--no-reconcile", action="store_true",
                    help="skip p4 reconcile; just print the touched-file list")
    ap.add_argument("--probe", action="store_true",
                    help="have the preflight make one live pi model call")
    args = ap.parse_args(argv)
    ws = args.workspace.resolve()

    preflight = find_preflight()
    sweep = find_sweep_script()
    if not preflight:
        print(f"[afk] sweep-preflight.py not found next to {Path(__file__).name}", file=sys.stderr)
        return 3
    if not sweep:
        print("[afk] could not locate liang-quest-batch-sweep/sweep.py.", file=sys.stderr)
        return 3

    if run_preflight(preflight, ws, args.probe) != 0:
        print("\n[afk] preflight FAILED — aborting before launch. Fix the FAILs and re-run.",
              file=sys.stderr)
        return 2

    # Scope reconcile to step files written from now on (this run's writes).
    # In dry-run nothing is written, so include all (illustrative) with since=0.
    sweep_start = 0.0 if args.dry_run else time.time()
    sweep_rc = run_sweep(sweep, ws, args.dry_run)
    run_reconcile(ws, args.dry_run, enabled=not args.no_reconcile, since=sweep_start)
    report(ws)

    print("\n" + "=" * 64)
    if args.dry_run:
        print("[afk] DRY-RUN complete. Re-run without --dry-run to execute for real.")
        return 0
    if sweep_rc == 0:
        print("[afk] sweep complete — all campaigns passed. Review reports, then p4 submit.")
    else:
        print(f"[afk] sweep finished with exit {sweep_rc} — at least one campaign failed. "
              f"See run reports; re-run to resume failed campaigns.")
    return sweep_rc


if __name__ == "__main__":
    sys.exit(main())
