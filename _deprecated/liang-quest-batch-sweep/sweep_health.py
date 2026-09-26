"""
sweep_health.py - what sweep.py uses to watch, diagnose and report a running sweep.

- EventLog: append-only JSONL event stream under .liang/sweep-logs/ that the
  dashboard (sweep-watch.py) and the sweep report read.
- CampaignWatcher: polls one in-flight campaign's manifest and .run/ envelopes,
  emits quest/step events, and detects a stalled dispatch (no file activity, no
  model transcript activity, no build/test process) so sweep.py can kill it.
- diagnose_failure: decides whether a failed campaign is worth one automatic
  re-dispatch, using the shared known-failure playbook in liang-quest-core.
- toast: best-effort Windows desktop notification.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

CORE_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "liang-quest-core" / "scripts"
sys.path.insert(0, str(CORE_SCRIPTS_DIR))
import failure_playbook  # noqa: E402

SWEEP_LOGS_DIR_NAME = ".liang/sweep-logs"
DEFAULT_STALL_SECONDS = 1200.0
DEFAULT_RECOVERY_ATTEMPTS = 1

# A quiet dispatch whose own process tree contains one of these is waiting on
# a build or a test run, not hung. Only descendants of the dispatched child
# count: Rider and the open editor keep dotnet/msbuild alive all night.
BUSY_PROCESS_NAMES = {
    "unrealbuildtool.exe", "ubtshadow.exe", "cl.exe", "link.exe",
    "unrealeditor-cmd.exe", "unrealeditor.exe", "dotnet.exe", "msbuild.exe",
}

# A busy build/test process only buys this many stall windows: a headless
# editor can hang on exit (EOS event loop) and would otherwise hold the sweep
# until the campaign timeout.
BUSY_GRACE_WINDOWS = 3

STEP_TITLE_RE = re.compile(r"^# Step envelope \S+: (.+)$", re.MULTILINE)
OUTPUT_STATUS_RE = re.compile(r"## Output\s*~~~yaml\s*\nstatus:\s*\"?(\w+)", re.MULTILINE)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None


class EventLog:
    """One JSON object per line; readers tolerate a torn final line."""

    def __init__(self, path: Path | None):
        self.path = path
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def for_new_sweep(cls, workspace: Path) -> "EventLog":
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
        return cls(workspace / SWEEP_LOGS_DIR_NAME / f"{stamp}-sweep.events.jsonl")

    def emit(self, kind: str, **fields: Any) -> None:
        if self.path is None:
            return
        record = {"ts": _now_iso(), "kind": kind, **fields}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def read_events(path: Path) -> list[dict[str, Any]]:
    events = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return events
    for line in lines:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def newest_events_file(workspace: Path) -> Path | None:
    files = sorted((workspace / SWEEP_LOGS_DIR_NAME).glob("*.events.jsonl"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def read_step_envelope(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    title = STEP_TITLE_RE.search(text)
    outcome = OUTPUT_STATUS_RE.search(text)
    step_id = path.stem.removeprefix("step-")
    return {
        "step": step_id,
        "title": title.group(1).strip() if title else step_id,
        "outcome": outcome.group(1) if outcome else None,
        "repair": step_id.startswith("fix"),
    }


def claude_transcript_dir(workspace: Path) -> Path:
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(workspace))
    return Path.home() / ".claude" / "projects" / slug


def _process_table() -> list[tuple[int, int, str]]:
    if os.name != "nt":
        return []
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             "Get-CimInstance Win32_Process | ForEach-Object { \"$($_.ProcessId),$($_.ParentProcessId),$($_.Name)\" }"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30, check=False,
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    table = []
    for line in out.splitlines():
        parts = line.strip().split(",", 2)
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            table.append((int(parts[0]), int(parts[1]), parts[2].lower()))
    return table


def busy_descendants(root_pid: int | None) -> set[str]:
    if root_pid is None:
        return set()
    table = _process_table()
    children: dict[int, list[tuple[int, str]]] = {}
    for pid, ppid, name in table:
        children.setdefault(ppid, []).append((pid, name))
    busy, frontier, seen = set(), [root_pid], {root_pid}
    while frontier:
        for pid, name in children.get(frontier.pop(), []):
            if pid in seen:
                continue
            seen.add(pid)
            frontier.append(pid)
            if name in BUSY_PROCESS_NAMES:
                busy.add(name)
    return busy


@dataclass
class CampaignWatcher:
    campaign_id: str
    campaign_dir: Path
    workspace: Path
    events: EventLog
    stall_seconds: float | None
    root_pid: int | None = None
    dispatch_start: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    _quests: dict[str, tuple[Any, Any]] = field(default_factory=dict)
    _steps: dict[Path, tuple[float, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._quests = self._quest_states()
        self._steps = self._step_states()

    def poll(self) -> None:
        self._emit_quest_changes()
        self._emit_step_changes()
        self.last_activity = max(self.last_activity, self._newest_activity())

    def stalled(self) -> bool:
        if not self.stall_seconds:
            return False
        quiet = self.quiet_seconds()
        if quiet < self.stall_seconds:
            return False
        if quiet >= self.stall_seconds * BUSY_GRACE_WINDOWS:
            return True
        return not busy_descendants(self.root_pid)

    def quiet_seconds(self) -> float:
        return time.time() - self.last_activity

    def _quest_states(self) -> dict[str, tuple[Any, Any]]:
        manifest = _load_yaml(self.campaign_dir / "manifest.yaml") or {}
        return {
            q.get("id"): (q.get("status"), q.get("current_cycle"))
            for q in manifest.get("quests") or [] if isinstance(q, dict)
        }

    def _step_states(self) -> dict[Path, tuple[float, Any]]:
        states = {}
        for path in self.campaign_dir.glob(".run/*/step-*.md"):
            try:
                states[path] = (path.stat().st_mtime, read_step_envelope(path)["outcome"])
            except OSError:
                continue
        return states

    def _emit_quest_changes(self) -> None:
        current = self._quest_states()
        for qid, (status, cycle) in current.items():
            old_status, old_cycle = self._quests.get(qid, (None, None))
            if status != old_status:
                self.events.emit(
                    "quest_status", campaign=self.campaign_id, quest=qid,
                    status=status, previous=old_status, **self._completion_details(qid, status),
                )
            elif cycle != old_cycle and status == "in_progress":
                self.events.emit("quest_cycle", campaign=self.campaign_id, quest=qid, cycle=cycle)
        self._quests = current

    def _completion_details(self, qid: str, status: Any) -> dict[str, Any]:
        if status not in ("passed", "failed"):
            return {}
        complete = _load_yaml(self.campaign_dir / ".run" / qid / "complete.yaml") or {}
        details = {
            key: complete[key]
            for key in ("failure_type", "failed_vcs", "vc_repair_rounds", "needs_review", "playbook")
            if complete.get(key)
        }
        return details

    def _emit_step_changes(self) -> None:
        current = self._step_states()
        for path, (mtime, outcome) in current.items():
            previous = self._steps.get(path)
            if previous and previous[1] == outcome:
                continue
            envelope = read_step_envelope(path)
            self.events.emit(
                "repair_round" if envelope["repair"] else "step",
                campaign=self.campaign_id, quest=path.parent.name, **envelope,
            )
        self._steps = current

    def _newest_activity(self) -> float:
        newest = 0.0
        for path in [self.campaign_dir / "manifest.yaml", *self.campaign_dir.glob(".run/**/*")]:
            newest = max(newest, _mtime(path))
        return max(newest, self._newest_transcript_write())

    def _newest_transcript_write(self) -> float:
        """claude -p sessions (and their subagents) stream their transcript to
        disk while working, long before a step envelope is back-filled. Only
        transcripts born after this dispatch count, so an interactive session
        open in the same workspace cannot mask a hung sweep."""
        root = claude_transcript_dir(self.workspace)
        newest = 0.0
        for path in [*root.glob("*.jsonl"), *root.glob("*/subagents/*.jsonl")]:
            try:
                st = path.stat()
            except OSError:
                continue
            if st.st_ctime >= self.dispatch_start - 5:
                newest = max(newest, st.st_mtime)
        return newest


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


@dataclass
class Diagnosis:
    retry: bool
    reason: str
    detail: str = ""
    blocker: bool = False
    playbook_ids: list[str] = field(default_factory=list)


def diagnose_failure(campaign_dir: Path, dispatch_start: float, child_output: str) -> Diagnosis:
    """Decide whether one automatic re-dispatch is worth it. Only infra-shaped
    failures qualify; a real code or plan failure is left for the report,
    because the executor already spent its own retries and repair rounds."""
    manifest = _load_yaml(campaign_dir / "manifest.yaml") or {}
    quests = [q for q in manifest.get("quests") or [] if isinstance(q, dict)]
    interrupted = [q["id"] for q in quests if q.get("status") in ("in_progress", "ready")
                   and (campaign_dir / ".run" / str(q.get("id"))).is_dir()]
    failed = [q["id"] for q in quests if q.get("status") == "failed"]

    logs = [p for qid in failed + interrupted for p in (campaign_dir / ".run" / qid).glob("*.log")
            if _mtime(p) >= dispatch_start - 5]
    log_text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in logs)
    verdict = failure_playbook.classify_text(log_text + "\n" + child_output)
    ids = [m["id"] for m in verdict["matches"] if m["class"] != "ignore"]

    if verdict["verdict"] == "blocker":
        notes = "; ".join(m["note"] for m in verdict["matches"] if m["class"] == "blocker")
        return Diagnosis(False, "blocker", notes, blocker=True, playbook_ids=ids)
    if interrupted and not failed:
        return Diagnosis(True, "interrupted", f"executor stopped mid-quest ({', '.join(interrupted)})", playbook_ids=ids)

    infra_types = failure_playbook.infra_failure_types()
    failure_types = {
        (_load_yaml(campaign_dir / ".run" / qid / "complete.yaml") or {}).get("failure_type") for qid in failed
    }
    if failed and failure_types <= infra_types:
        return Diagnosis(True, "infra", f"failure types {sorted(map(str, failure_types))}", playbook_ids=ids)
    if verdict["verdict"] == "retry":
        notes = "; ".join(m["note"] for m in verdict["matches"] if m["class"] == "retry")
        return Diagnosis(True, "transient", notes, playbook_ids=ids)
    return Diagnosis(False, "code", "failed on its own checks; left for review", playbook_ids=ids)


def toast(title: str, body: str) -> None:
    """Best-effort Windows toast through PowerShell's registered app id. Text is
    passed by environment variable so no quoting can break the script."""
    if os.name != "nt":
        return
    script = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null;"
        "$x = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
        "$t = $x.GetElementsByTagName('text');"
        "$t.Item(0).AppendChild($x.CreateTextNode($env:SWEEP_TOAST_TITLE)) > $null;"
        "$t.Item(1).AppendChild($x.CreateTextNode($env:SWEEP_TOAST_BODY)) > $null;"
        "$app = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe';"
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($app).Show([Windows.UI.Notifications.ToastNotification]::new($x))"
    )
    env = {**os.environ, "SWEEP_TOAST_TITLE": title[:120], "SWEEP_TOAST_BODY": body[:400]}
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass
