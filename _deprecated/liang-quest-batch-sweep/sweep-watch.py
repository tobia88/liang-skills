#!/usr/bin/env python3
"""
sweep-watch.py — live browser dashboard for a running batch sweep.

Serves a self-refreshing page on localhost that reads the campaign
manifests, each quest's .run/ step envelopes, the sweep lock, the newest afk
log and the sweep's event stream. Read-only: it never writes to the workspace.

    python sweep-watch.py --workspace F:\\Unreal\\p4_super_GameDev \\
        --saga saga-2026-09-24-route-map-slice-parity [--port 8799]

Without --saga it shows every campaign that still has unfinished quests.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sweep import _pid_is_alive, resolve_saga_selection  # noqa: E402
from sweep_health import newest_events_file, read_events, read_step_envelope  # noqa: E402

CAMPAIGNS_DIR = Path(".liang") / "campaigns"
VERIFICATION_RE = re.compile(r"## Verification\s*~~~yaml\s*\n(.*?)\n~~~", re.DOTALL)
TIMELINE_LENGTH = 60

# UE's own HTTP listeners probe 8765 during headless test runs.
DEFAULT_PORT = 8799


def load_yaml(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}


def sweep_state(ws: Path) -> dict:
    lock = load_yaml(ws / ".liang" / "sweep.lock")
    pid = lock.get("pid")
    logs = sorted((ws / ".liang" / "sweep-logs").glob("*-afk.log"), key=lambda p: p.stat().st_mtime)
    tail: list[str] = []
    if logs:
        lines = logs[-1].read_text(encoding="utf-8", errors="replace").splitlines()
        tail = [line for line in lines if line.strip()][-12:]
    return {
        "pid": pid,
        "alive": isinstance(pid, int) and _pid_is_alive(pid),
        "started": lock.get("started"),
        "log": str(logs[-1]) if logs else None,
        "log_tail": tail,
    }


def step_files(run_dir: Path) -> list[Path]:
    return sorted(run_dir.glob("step-*.md"), key=lambda p: p.stat().st_mtime)


def latest_step(steps: list[Path]) -> dict | None:
    if not steps:
        return None
    envelope = read_step_envelope(steps[-1])
    envelope["count"] = sum(1 for s in steps if not s.stem.startswith("step-fix"))
    return envelope


def failed_vc_evidence(steps: list[Path]) -> list[dict]:
    """The newest envelope carrying a Verification block holds the last verdict."""
    for path in reversed(steps):
        match = VERIFICATION_RE.search(path.read_text(encoding="utf-8", errors="replace"))
        if not match:
            continue
        try:
            results = (yaml.safe_load(match.group(1)) or {}).get("vc_results") or []
        except yaml.YAMLError:
            return []
        return [
            {"vc": r.get("vc"), "evidence": str(r.get("evidence", ""))}
            for r in results if isinstance(r, dict) and r.get("pass") is False
        ]
    return []


def quest_view(campaign_dir: Path, quest: dict) -> dict:
    run_dir = campaign_dir / ".run" / str(quest.get("id", ""))
    complete = load_yaml(run_dir / "complete.yaml")
    retries = complete.get("retries") or {}
    steps = step_files(run_dir)
    return {
        "id": quest.get("id"),
        "title": quest.get("title"),
        "status": quest.get("status"),
        "manual": bool(quest.get("manual")),
        "difficulty": quest.get("difficulty"),
        "cycle": quest.get("current_cycle"),
        "cycles": quest.get("total_cycles"),
        "started": quest.get("started_at"),
        "completed": quest.get("completed_at"),
        "step": latest_step(steps),
        "repair_rounds": sum(1 for s in steps if s.stem.startswith("step-fix")),
        "retries": sum(v for v in retries.values() if isinstance(v, int)),
        "drift": complete.get("plan_drift") or [],
        "failure_type": complete.get("failure_type"),
        "failed_vcs": complete.get("failed_vcs") or [],
        "evidence": failed_vc_evidence(steps) if quest.get("status") == "failed" else [],
        "needs_review": complete.get("needs_review") or [],
        "playbook": complete.get("playbook") or [],
        "skip_reason": quest.get("skip_reason"),
    }


def campaign_view(campaign_dir: Path) -> dict:
    manifest = load_yaml(campaign_dir / "manifest.yaml")
    return {
        "id": campaign_dir.name,
        "title": manifest.get("title", campaign_dir.name),
        "quests": [quest_view(campaign_dir, q) for q in manifest.get("quests") or []],
    }


def is_unfinished(campaign: dict) -> bool:
    return any(q["status"] not in ("passed", "skipped") for q in campaign["quests"])


def timeline(ws: Path) -> dict:
    path = newest_events_file(ws)
    if path is None:
        return {"events": [], "file": None}
    return {"events": read_events(path)[-TIMELINE_LENGTH:], "file": str(path)}


def snapshot(ws: Path, campaign_ids: list[str] | None, title: str) -> dict:
    root = ws / CAMPAIGNS_DIR
    if campaign_ids is None:
        campaigns = [campaign_view(d) for d in sorted(root.iterdir()) if (d / "manifest.yaml").is_file()]
        campaigns = [c for c in campaigns if is_unfinished(c)]
    else:
        campaigns = [campaign_view(root / cid) for cid in campaign_ids if (root / cid).is_dir()]
    return {
        "title": title,
        "now": datetime.now(timezone.utc).isoformat(),
        "sweep": sweep_state(ws),
        "campaigns": campaigns,
        "timeline": timeline(ws),
    }


def make_handler(ws: Path, campaign_ids: list[str] | None, title: str):
    page = (Path(__file__).resolve().parent / "sweep-watch.html").read_bytes()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path.startswith("/data"):
                body = json.dumps(snapshot(ws, campaign_ids, title), default=str).encode("utf-8")
                self.reply(body, "application/json")
            elif self.path in ("/", "/index.html"):
                self.reply(page, "text/html; charset=utf-8")
            else:
                self.send_error(404)

        def reply(self, body: bytes, content_type: str):
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--saga")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    ws = Path(args.workspace).resolve()
    campaign_ids = None
    title = "Unfinished campaigns"
    if args.saga:
        title, campaign_ids, _ = resolve_saga_selection(ws, args.saga)

    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(ws, campaign_ids, title))
    print(f"[watch] http://127.0.0.1:{args.port}/  ({title}) — Ctrl+C to stop", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
