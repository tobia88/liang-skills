"""
liang-quest-batch-sweep — sweep.py

Multi-campaign orchestrator script. Discovers all eligible campaigns under
.liang/campaigns/, resolves cross-campaign dependencies via the optional
`campaign_depends_on` manifest field (campaign_id values, per dc001),
toposorts the campaign DAG (rejecting cycles), runs pre-flight validation,
and dispatches one executor invocation per campaign via Pi CLI with
--no-confirm (per q001 of camp-2026-05-24-batch-campaign-sweep).

NAMING: this file is the "sweep script" — the OUTER multi-campaign
orchestrator. It is distinct from the "batch executor script" already
documented inside liang-quest-general-executor under --batch mode, which
orchestrates a SINGLE campaign internally. Per dc006, do not conflate the
two. The sweep script invokes the executor (which may or may not use its
own --batch mode) once per eligible campaign.

State lives on disk in manifest.yaml status fields. The script is
idempotent on relaunch: campaigns with status passed/skipped are skipped;
planned/failed are run. Manifest mutations use write-to-temp-then-rename
(os.replace) for atomicity on Windows NTFS (per dc004).

Exit codes (matching the executor's contract from q001):
  0 — all campaigns passed
  1 — at least one campaign failed
  2 — configuration error (no campaigns eligible, workflow mismatch, etc.)
  3 — unexpected crash

Usage: python sweep.py [--dry-run] [--workspace <path>]
"""

from __future__ import annotations

import argparse
import os
import sys
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml  # pyyaml; see requirements.txt

# Constants
CAMPAIGNS_DIR_NAME = ".liang/campaigns"
PROJECT_YAML_PATH = ".liang/project.yaml"
SWEEP_REPORTS_DIR_NAME = ".liang/sweep-reports"
EXECUTOR_SKILL_NAME = "liang-quest-general-executor"

EXIT_OK = 0
EXIT_QUEST_FAILED = 1
EXIT_CONFIG_ERROR = 2
EXIT_CRASH = 3

RUNNABLE_STATUSES = {"planned", "failed"}
SKIPPABLE_STATUSES = {"passed", "skipped"}
REQUIRED_WORKFLOW = "general"  # per dc005


def discover_campaigns(workspace: Path) -> list[dict[str, Any]]:
    """
    Walk .liang/campaigns/ and load each manifest.yaml. Return a list of
    dicts, each containing the parsed manifest plus a 'campaign_dir' Path
    key for later file operations. Skip directories without a manifest.yaml.
    Skip 'archive/' subdirectory if present.
    """
    campaigns_dir = workspace / CAMPAIGNS_DIR_NAME
    if not campaigns_dir.is_dir():
        return []
    result = []
    for entry in sorted(campaigns_dir.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name == "archive":
            continue
        manifest_path = entry / "manifest.yaml"
        if not manifest_path.is_file():
            continue
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
        if not isinstance(manifest, dict):
            continue
        manifest["campaign_dir"] = entry
        result.append(manifest)
    return result


def toposort_campaigns(campaigns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Order campaigns by their campaign_depends_on graph (Kahn's algorithm).
    Per dc001, campaign_depends_on values are campaign_id strings. Missing
    field or empty list = no cross-campaign deps. Raises ValueError on
    cycle detection. Campaigns whose declared deps don't resolve to known
    campaign_ids are kept (treated as roots) — the cartographer is
    responsible for declaring valid deps; the sweep script tolerates
    missing references rather than blocking the whole sweep.
    """
    by_id: dict[str, dict[str, Any]] = {c["campaign_id"]: c for c in campaigns}
    in_degree: dict[str, int] = {c["campaign_id"]: 0 for c in campaigns}
    dependents: dict[str, list[str]] = {c["campaign_id"]: [] for c in campaigns}

    for c in campaigns:
        cid = c["campaign_id"]
        deps = c.get("campaign_depends_on") or []
        for dep in deps:
            if dep not in by_id:
                # unresolvable dep — log and skip the edge, treat campaign as root
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
      1. workflow field is 'general' (per dc005 — refuse non-general in v1).
      2. quests[] is a non-empty list.
      3. Every quest has a path that resolves to an existing index.html.
      4. Every quest with status 'planned' has a sibling plan.html.
    """
    blocking: list[str] = []
    warnings: list[str] = []

    campaign_dir = campaign["campaign_dir"]
    cid = campaign.get("campaign_id", "<unknown>")

    workflow = campaign.get("workflow")
    if workflow is None:
        blocking.append(f"{cid}: missing workflow stamp; run tactician first")
    elif workflow != REQUIRED_WORKFLOW:
        blocking.append(
            f"{cid}: workflow is '{workflow}', expected '{REQUIRED_WORKFLOW}' (dc005)"
        )

    quests = campaign.get("quests")
    if not isinstance(quests, list) or len(quests) == 0:
        blocking.append(f"{cid}: quests[] is missing or empty")
        return blocking, warnings

    for quest in quests:
        qid = quest.get("id", "<unknown>")
        quest_path = quest.get("path")
        if not quest_path:
            blocking.append(f"{cid}/{qid}: missing path")
            continue
        quest_index = campaign_dir / quest_path
        if not quest_index.is_file():
            blocking.append(f"{cid}/{qid}: quest index.html not found at {quest_index}")
        if quest.get("status") == "planned":
            plan_html = quest_index.parent / "plan.html"
            if not plan_html.is_file():
                blocking.append(f"{cid}/{qid}: status=planned but plan.html missing at {plan_html}")

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


def dispatch_campaign(campaign: dict[str, Any], dry_run: bool = False) -> int:
    """
    Invoke the general executor for one campaign via Pi CLI with
    --no-confirm (per q001 of camp-2026-05-24-batch-campaign-sweep).
    Returns the subprocess exit code:
      0 — all quests passed
      1 — at least one quest failed (planned failure path)
      2 — configuration error
      3 — unexpected crash

    In dry-run mode, prints the command and returns 0 without invoking.

    The exact pi CLI argument layout follows the pattern documented in
    liang-quest-general-executor/SKILL.md (Pi CLI mode child invocation
    style). If pi cannot surface a non-zero exit code natively (per the
    q001 Failure Modes 'Exit code emission failure' entry), this function
    parses the stderr's LAST line for 'EXEC_EXIT_CODE: <n>' as a fallback.
    """
    campaign_dir = campaign["campaign_dir"]
    cid = campaign.get("campaign_id", "<unknown>")

    cmd = [
        "pi",
        "--skill", EXECUTOR_SKILL_NAME,
        "--no-confirm",
        str(campaign_dir),
    ]

    if dry_run:
        print(f"[dry-run] would invoke: {' '.join(cmd)}")
        return EXIT_OK

    print(f"[sweep] dispatching {cid} via {' '.join(cmd)}")
    try:
        completed = subprocess.run(
            cmd,
            cwd=campaign_dir.parent.parent.parent,  # workspace root
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as e:
        print(f"[sweep] pi CLI not found: {e}", file=sys.stderr)
        return EXIT_CRASH
    except Exception as e:
        print(f"[sweep] dispatch failed for {cid}: {e}", file=sys.stderr)
        return EXIT_CRASH

    # surface child stdout/stderr to parent
    if completed.stdout:
        sys.stdout.write(completed.stdout)
    if completed.stderr:
        sys.stderr.write(completed.stderr)

    # honor native exit code first
    exit_code = completed.returncode

    # fallback: parse EXEC_EXIT_CODE: <n> from last stderr line if exit_code is 0
    # but stderr contains a non-zero marker (Pi CLI infra fallback per q001)
    if exit_code == 0 and completed.stderr:
        for line in reversed(completed.stderr.strip().splitlines()):
            line = line.strip()
            if line.startswith("EXEC_EXIT_CODE:"):
                try:
                    exit_code = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
                break

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
        <tr><th>Order</th><th>Campaign ID</th><th>Status</th><th>Run Report</th></tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>

    <p class="footer">Generated by liang-quest-batch-sweep / sweep.py &middot; This is the SWEEP report (multi-campaign). Per-campaign run reports linked above are generated by the executor.</p>
  </main>
</body>
</html>
"""


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
        rows.append(
            f'<tr>'
            f'<td>{r["order"]}</td>'
            f'<td><code>{_html_escape(r["campaign_id"])}</code></td>'
            f'<td><span class="status {r["status"]}">{r["status"]}</span></td>'
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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    workspace: Path = args.workspace.resolve()

    # Workspace pre-flight
    workspace_errors = preflight_workspace(workspace)
    if workspace_errors:
        for e in workspace_errors:
            print(f"[sweep] workspace error: {e}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    # Discover and filter
    all_campaigns = discover_campaigns(workspace)
    if not all_campaigns:
        print(f"[sweep] no campaigns found under {workspace / CAMPAIGNS_DIR_NAME}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    # Toposort (raises ValueError on cycle)
    try:
        ordered = toposort_campaigns(all_campaigns)
    except ValueError as e:
        print(f"[sweep] {e}", file=sys.stderr)
        return EXIT_CONFIG_ERROR

    # Per-campaign pre-flight — collect blocking errors
    blocked_ids: set[str] = set()
    for c in ordered:
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
                "run_report_relpath": None,
            })
            print(f"[sweep] {order_idx}. {cid} — cascade-skipped", file=sys.stderr)
            continue

        # Resume-aware: skip if all quests already terminal
        quest_statuses = [q.get("status") for q in campaign.get("quests", [])]
        if quest_statuses and all(s in SKIPPABLE_STATUSES for s in quest_statuses):
            results.append({
                "campaign_id": cid, "order": order_idx,
                "status": "passed" if all(s == "passed" for s in quest_statuses) else "skipped",
                "run_report_relpath": None,
            })
            print(f"[sweep] {order_idx}. {cid} — already terminal; skipping", file=sys.stderr)
            continue

        # Dispatch
        exit_code = dispatch_campaign(campaign, dry_run=args.dry_run)

        if exit_code == EXIT_OK:
            status = "passed"
        elif exit_code == EXIT_QUEST_FAILED:
            status = "failed"
        elif exit_code == EXIT_CONFIG_ERROR:
            status = "failed"
            print(f"[sweep] {cid} returned EXIT_CONFIG_ERROR — halting sweep", file=sys.stderr)
            results.append({
                "campaign_id": cid, "order": order_idx, "status": "failed",
                "run_report_relpath": None,
            })
            write_sweep_report(workspace, results)
            return EXIT_CONFIG_ERROR
        else:  # EXIT_CRASH or unexpected
            status = "crash"
            print(f"[sweep] {cid} crashed with exit {exit_code} — halting sweep", file=sys.stderr)
            results.append({
                "campaign_id": cid, "order": order_idx, "status": "crash",
                "run_report_relpath": None,
            })
            write_sweep_report(workspace, results)
            return EXIT_CRASH

        # Cascade-skip dependents on failure
        if status == "failed":
            for dep_cid in cascade_skip_dependents(cid, all_campaigns):
                skipped_by_cascade.add(dep_cid)

        # Locate latest executor run report if present
        run_reports = sorted(campaign_dir.glob("run-report-*.html"))
        run_report_relpath = None
        if run_reports:
            latest = run_reports[-1]
            run_report_relpath = str(latest.relative_to(workspace)).replace("\\", "/")

        results.append({
            "campaign_id": cid, "order": order_idx, "status": status,
            "run_report_relpath": run_report_relpath,
        })

    # Write sweep report
    report_path = write_sweep_report(workspace, results)
    print(f"[sweep] sweep report written to {report_path}")

    # Aggregate exit code: 1 if any failed; 0 otherwise
    if any(r["status"] in ("failed", "crash") for r in results):
        return EXIT_QUEST_FAILED
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
