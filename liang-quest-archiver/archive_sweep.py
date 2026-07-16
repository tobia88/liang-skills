#!/usr/bin/env python3
"""archive_sweep.py — deterministic campaign archiver for the liang-quest family.

Scans .liang/campaigns/*/manifest.yaml, classifies each campaign, and (in
--execute mode) moves fully-terminal campaigns to .liang/campaigns/archive/,
deleting their .run/ ledgers. Dry-run is the default; the invoking model is
expected to run dry-run first, present the plan, then re-run with --execute.

Classification rules (holds are release-able only via --force / --trust-skips):
  ARCHIVE            every quest status == "passed" (and no other hold applies)
  OPEN               any quest is ready / in_progress / planned /
                     ready_for_planning / unknown  -> never archived, even forced
                     (exception: --force may move a campaign with ready quests,
                     but never one with in_progress quests)
  HOLD open-saga     campaign is listed (campaign_id) in a saga whose
                     saga.yaml status is not "complete"
  HOLD skips         terminal but contains "skipped" quests (possible infra
                     false negatives; verify, then --trust-skips or --force)
  HOLD failed        terminal but contains "failed" quests (archiving would
                     hide a problem; --force after triage)
  HOLD no-manifest   directory has no manifest.yaml (--force after eyeballing)

Exit codes: 0 = ok (dry-run or all moves succeeded), 1 = a move failed.
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

TERMINAL = {"passed", "skipped", "failed"}
IN_PROGRESS = {"in_progress"}
QUEST_STATUS_RE = re.compile(r'^\s+status:\s*"?([a-z_]+)"?', re.MULTILINE)
CAMPAIGN_ID_RE = re.compile(r'^campaign_id:\s*"?([^"\s]+)"?', re.MULTILINE)
SAGA_STATUS_RE = re.compile(r'^status:\s*"?([a-z_]+)"?', re.MULTILINE)
SAGA_CAMPAIGN_ID_RE = re.compile(r'^\s+campaign_id:\s*"?([^"\s]+)"?', re.MULTILINE)


def read_text(path):
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as err:
        print(f"WARN cannot read {path}: {err}")
        return ""


def open_saga_campaign_ids(workspace):
    """Return the set of campaign_ids referenced by sagas not marked complete."""
    held = set()
    sagas_root = workspace / ".liang" / "sagas"
    if not sagas_root.is_dir():
        return held
    for saga_yaml in sorted(sagas_root.glob("*/saga.yaml")):
        text = read_text(saga_yaml)
        status_match = SAGA_STATUS_RE.search(text)
        status = status_match.group(1) if status_match else "unknown"
        if status != "complete":
            ids = set(SAGA_CAMPAIGN_ID_RE.findall(text))
            if ids:
                print(f"NOTE saga {saga_yaml.parent.name} status={status}: "
                      f"holding {len(ids)} campaign(s)")
            held |= ids
    return held


def classify(campaign_dir, saga_held, trust_skips):
    """Return (verdict, detail) for one campaign directory."""
    manifest = campaign_dir / "manifest.yaml"
    if not manifest.is_file():
        return "HOLD", "no-manifest"
    text = read_text(manifest)
    statuses = QUEST_STATUS_RE.findall(text)
    if not statuses:
        return "HOLD", "no quest statuses parsed"

    tally = {}
    for status in statuses:
        tally[status] = tally.get(status, 0) + 1
    detail = " ".join(f"{count}x{status}" for status, count in sorted(tally.items()))

    non_terminal = [s for s in statuses if s not in TERMINAL]
    if non_terminal:
        return "OPEN", detail

    id_match = CAMPAIGN_ID_RE.search(text)
    campaign_id = id_match.group(1) if id_match else campaign_dir.name
    if campaign_id in saga_held or campaign_dir.name in saga_held:
        return "HOLD", f"open-saga ({detail})"
    if "failed" in tally:
        return "HOLD", f"failed quests ({detail})"
    if "skipped" in tally and not trust_skips:
        return "HOLD", f"unverified skips ({detail})"
    return "ARCHIVE", detail


def has_in_progress(campaign_dir):
    manifest = campaign_dir / "manifest.yaml"
    if not manifest.is_file():
        return False
    statuses = QUEST_STATUS_RE.findall(read_text(manifest))
    return any(s in IN_PROGRESS for s in statuses)


def archive_one(campaign_dir, archive_root, keep_run):
    """Move one campaign into archive/ and delete its .run ledgers."""
    target = archive_root / campaign_dir.name
    if target.exists():
        print(f"ERROR target already exists, skipping move: {target}")
        return False
    shutil.move(str(campaign_dir), str(target))
    if not keep_run:
        for run_dir in sorted(target.rglob(".run")):
            if run_dir.is_dir():
                shutil.rmtree(run_dir, ignore_errors=True)
    return True


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Archive fully-terminal quest campaigns.")
    parser.add_argument("--workspace", default=".", help="workspace root (contains .liang/)")
    parser.add_argument("--execute", action="store_true",
                        help="perform moves (default is dry-run report only)")
    parser.add_argument("--trust-skips", action="store_true",
                        help="treat skipped quests as verified-complete")
    parser.add_argument("--force", default="",
                        help="comma-separated campaign dir names to archive despite holds")
    parser.add_argument("--keep-run", action="store_true",
                        help="do not delete .run/ ledgers inside archived campaigns")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    campaigns_root = workspace / ".liang" / "campaigns"
    if not campaigns_root.is_dir():
        print(f"ERROR no campaign root at {campaigns_root}")
        return 1
    archive_root = campaigns_root / "archive"
    forced = {name.strip() for name in args.force.split(",") if name.strip()}

    saga_held = open_saga_campaign_ids(workspace)

    to_move = []
    rows = []
    for campaign_dir in sorted(campaigns_root.iterdir()):
        if not campaign_dir.is_dir() or campaign_dir.name == "archive":
            continue
        verdict, detail = classify(campaign_dir, saga_held, args.trust_skips)
        if campaign_dir.name in forced and verdict != "ARCHIVE":
            if has_in_progress(campaign_dir):
                rows.append(("REFUSED", "forced but has in_progress quests", campaign_dir.name))
                continue
            verdict, detail = "ARCHIVE", f"forced ({detail})"
        if verdict == "ARCHIVE":
            to_move.append(campaign_dir)
        rows.append((verdict, detail, campaign_dir.name))

    width = max((len(v) for v, _, _ in rows), default=7)
    for verdict, detail, name in rows:
        print(f"{verdict:<{width}}  {name}  [{detail}]")

    counts = {}
    for verdict, _, _ in rows:
        counts[verdict] = counts.get(verdict, 0) + 1
    summary = ", ".join(f"{verdict}={count}" for verdict, count in sorted(counts.items()))
    print(f"\nSUMMARY {summary} (total={len(rows)})")

    if not args.execute:
        print("DRY-RUN no files were moved. Re-run with --execute to archive "
              f"{len(to_move)} campaign(s).")
        return 0

    archive_root.mkdir(exist_ok=True)
    moved = 0
    failed = 0
    for campaign_dir in to_move:
        if archive_one(campaign_dir, archive_root, args.keep_run):
            moved += 1
        else:
            failed += 1
    print(f"EXECUTED moved={moved} failed={failed} archive_root={archive_root}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
