"""
sweep-preflight.py — deep preflight for liang-quest-batch-sweep.

Shipped inside the liang-quest-batch-sweep skill so every project shares it.
sweep.py --dry-run only validates *structure* (files present, no dependency
cycles). It never contacts a model, so it cannot catch the config/environment
errors that make liang-quest-executor exit-2 mid-sweep. This script mirrors the
executor's hard-block gates (SKILL.md §2/§3) PLUS the pi runtime environment,
and — only when asked with --probe — fires a single cheap pi call to confirm
the configured model key actually round-trips before you commit a full sweep.

Read-only by default. Touches no manifest, plan, or source file. With --probe
it makes exactly one trivial model call.

Exit codes:
  0  all hard checks passed (WARNs may remain — read them)
  2  at least one hard check FAILED — do not launch the sweep until fixed

Usage:
  python sweep-preflight.py --workspace <project-root> [--probe]
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

# ---- result accumulation -------------------------------------------------

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"
_results: list[tuple[str, str, str]] = []  # (level, check, detail)


def record(level: str, check: str, detail: str = "") -> None:
    _results.append((level, check, detail))


# ---- pi config discovery -------------------------------------------------

def pi_agent_dir() -> Path:
    # Honor PI_AGENT_DIR if set, else default to ~/.pi/agent
    env = os.environ.get("PI_AGENT_DIR")
    if env:
        return Path(env)
    return Path.home() / ".pi" / "agent"


def load_json(path: Path) -> dict[str, Any]:
    import json
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def locally_defined_models(model_json: dict[str, Any]) -> set[str]:
    """Model ids that have a concrete provider block in model.json."""
    ids: set[str] = set()
    for prov in (model_json.get("providers") or {}).values():
        for m in prov.get("models") or []:
            if isinstance(m, dict) and m.get("id"):
                ids.add(m["id"])
    return ids


def defined_providers(model_json: dict[str, Any]) -> set[str]:
    return set((model_json.get("providers") or {}).keys())


def enabled_model_map(settings: dict[str, Any]) -> dict[str, str]:
    """Map bare model id -> provider, parsed from settings.enabledModels
    entries of the form 'provider/model'."""
    out: dict[str, str] = {}
    for entry in settings.get("enabledModels") or []:
        if "/" in entry:
            prov, mid = entry.split("/", 1)
            out[mid] = prov
    return out


# ---- checks --------------------------------------------------------------

LEGAL_STATUSES = {"ready", "passed", "failed", "skipped", "in_progress"}
TERMINAL = {"passed", "skipped", "failed"}


def check_project_yaml(ws: Path) -> dict[str, Any]:
    py = ws / ".liang" / "project.yaml"
    if not py.is_file():
        record(FAIL, "project.yaml exists", str(py))
        return {}
    try:
        cfg = yaml.safe_load(py.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        record(FAIL, "project.yaml parses", str(e))
        return {}
    record(PASS, "project.yaml exists & parses")

    models = cfg.get("models") or {}
    # executor §2 hard block
    if models.get("verify"):
        record(PASS, "models.verify set (executor §2)", models["verify"])
    else:
        record(FAIL, "models.verify set (executor §2)",
               "executor hard-blocks with exit 2 when absent")
    ebd = models.get("execution_by_difficulty") or {}
    for tier in ("easy", "medium", "hard"):
        if ebd.get(tier):
            record(PASS, f"execution_by_difficulty.{tier} set", ebd[tier])
        else:
            record(FAIL, f"execution_by_difficulty.{tier} set", "required by executor")
    if not models.get("planning"):
        record(WARN, "models.planning set",
               "re-plan-child (retry 2+) has no planning model")
    return cfg


def check_models_resolvable(cfg: dict[str, Any], agent_dir: Path) -> None:
    model_json = load_json(agent_dir / "model.json")
    settings = load_json(agent_dir / "settings.json")
    if not model_json and not settings:
        record(WARN, "pi config found",
               f"no model.json/settings.json under {agent_dir} — skipping model resolvability")
        return

    local = locally_defined_models(model_json)
    providers = defined_providers(model_json)
    enabled = enabled_model_map(settings)

    models = cfg.get("models") or {}
    refs: list[tuple[str, str]] = []  # (role, model id)
    if models.get("planning"):
        refs.append(("planning", models["planning"]))
    if models.get("verify"):
        refs.append(("verify", models["verify"]))
    for tier, mid in (models.get("execution_by_difficulty") or {}).items():
        refs.append((f"exec/{tier}", mid))

    for role, mid in refs:
        if mid in local:
            record(PASS, f"model resolvable [{role}]", mid)
        elif mid in enabled:
            prov = enabled[mid]
            if prov in providers:
                record(PASS, f"model resolvable [{role}]", f"{mid} (provider {prov})")
            else:
                record(WARN, f"model resolvable [{role}]",
                       f"{mid}: enabled as '{prov}/{mid}' but no '{prov}' provider block "
                       f"in model.json — relies on a built-in/default provider; verify pi can resolve it")
        else:
            record(FAIL, f"model resolvable [{role}]",
                   f"{mid}: not in model.json and not in settings.enabledModels")


def check_api_key(cfg: dict[str, Any], agent_dir: Path) -> None:
    # Each provider's apiKey may reference an env var ($NAME); confirm it's set.
    model_json = load_json(agent_dir / "model.json")
    needs: set[str] = set()
    for prov in (model_json.get("providers") or {}).values():
        key = prov.get("apiKey", "")
        if isinstance(key, str) and key.startswith("$"):
            needs.add(key[1:])
    auth_present = (agent_dir / "auth.json").is_file()
    for var in sorted(needs):
        if os.environ.get(var):
            record(PASS, f"env {var} set")
        elif auth_present:
            record(WARN, f"env {var} set",
                   f"not in environment; pi may source it from {agent_dir / 'auth.json'} — confirm")
        else:
            record(FAIL, f"env {var} set", "no env var and no auth.json — children cannot authenticate")


def resolve_pi() -> str | None:
    """Full path to the pi launcher, honoring PATHEXT (pi.cmd on Windows)."""
    return shutil.which("pi")


def check_pi_spawnable() -> None:
    """sweep.py spawns pi via subprocess(shell=False). On Windows that path
    needs the resolved pi.cmd — bare 'pi' raises FileNotFoundError. Catch it
    here (cheap, no API call) so a live sweep never crashes on dispatch."""
    p = resolve_pi()
    if p:
        record(PASS, "pi executable spawnable", p)
    else:
        record(FAIL, "pi executable spawnable",
               "shutil.which('pi') is None — subprocess cannot launch the executor")


def check_governance_context(ws: Path) -> None:
    """The execute-children inherit project governance only via pi's
    CLAUDE.md/AGENTS.md discovery. Confirm a context file is present and that
    an AGENTS.md doesn't silently shadow a CLAUDE.md in the same ancestor."""
    has_claude = (ws / "CLAUDE.md").is_file()
    has_agents = (ws / "AGENTS.md").is_file() or (ws / "AGENTS.MD").is_file()
    if has_claude or has_agents:
        record(PASS, "governance context at root",
               str(ws / ("AGENTS.md" if has_agents else "CLAUDE.md")))
    else:
        record(WARN, "governance context at root",
               "no CLAUDE.md/AGENTS.md — children run with no project governance context")
    # AGENTS.md anywhere from root down to .liang/campaigns shadows CLAUDE.md
    if has_claude:
        for d in (ws, ws / ".liang", ws / ".liang" / "campaigns"):
            for name in ("AGENTS.md", "AGENTS.MD"):
                if (d / name).is_file():
                    record(WARN, "no AGENTS.md shadowing CLAUDE.md",
                           f"{d / name} is loaded *instead of* CLAUDE.md in {d}")


def check_campaigns(ws: Path) -> None:
    camp_root = ws / ".liang" / "campaigns"
    if not camp_root.is_dir():
        record(FAIL, "campaigns dir exists", str(camp_root))
        return
    runnable = 0
    for entry in sorted(camp_root.iterdir()):
        if not entry.is_dir() or entry.name == "archive":
            continue
        man = entry / "manifest.yaml"
        if not man.is_file():
            continue
        try:
            m = yaml.safe_load(man.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            record(FAIL, f"manifest parses [{entry.name}]", str(e))
            continue
        quests = m.get("quests") or []
        statuses = [q.get("status") for q in quests]
        if statuses and all(s in {"passed", "skipped"} for s in statuses):
            continue  # terminal — sweep will skip; no need to validate
        runnable += 1
        cid = m.get("campaign_id", entry.name)
        # plan.html (sweep.py + executor expectation)
        if not (entry / "plan.html").is_file():
            record(FAIL, f"plan.html present [{cid}]", "sweep.py preflight blocks")
        # per-quest gates (executor §3)
        for q in quests:
            qid = q.get("id", "?")
            f = q.get("file") or q.get("path")
            if not f:
                record(FAIL, f"quest file set [{cid}/{qid}]", "no file/path field")
            elif not (entry / f).is_file():
                record(FAIL, f"quest file resolves [{cid}/{qid}]", str(entry / f))
            st = q.get("status")
            if st not in LEGAL_STATUSES:
                record(FAIL, f"quest status legal [{cid}/{qid}]", f"illegal: {st!r}")
            if not q.get("difficulty"):
                record(FAIL, f"quest difficulty set [{cid}/{qid}]",
                       "executor §3 hard-block")
        record(PASS, f"campaign well-formed [{cid}]", f"{len(quests)} quests, status ready")
    if runnable == 0:
        record(WARN, "runnable campaigns", "nothing for the sweep to do (all terminal)")
    else:
        record(PASS, "runnable campaigns", f"{runnable} would dispatch")


def probe_pi(cfg: dict[str, Any]) -> None:
    """Single cheap live call to confirm the cheapest exec model round-trips."""
    ebd = (cfg.get("models") or {}).get("execution_by_difficulty") or {}
    model = ebd.get("easy") or ebd.get("medium") or (cfg.get("models") or {}).get("verify")
    if not model:
        record(WARN, "pi live probe", "no model to probe")
        return
    pi_exe = resolve_pi()
    if not pi_exe:
        record(FAIL, "pi live probe", "shutil.which('pi') is None — cannot locate launcher")
        return
    cmd = [pi_exe, "--model", model, "-p", "Reply with exactly: OK"]
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
    except FileNotFoundError:
        record(FAIL, "pi live probe", f"could not spawn {pi_exe}")
        return
    except subprocess.TimeoutExpired:
        record(FAIL, "pi live probe", f"{model} timed out (120s)")
        return
    blob = (cp.stdout or "") + (cp.stderr or "")
    if cp.returncode == 0 and "OK" in blob.upper():
        record(PASS, "pi live probe", f"{model} responded")
    else:
        record(FAIL, "pi live probe",
               f"{model} exit {cp.returncode}; tail: {blob.strip()[-200:]!r}")


# ---- main ----------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Deep preflight for liang-quest-batch-sweep.")
    ap.add_argument("--workspace", type=Path, default=Path.cwd())
    ap.add_argument("--probe", action="store_true",
                    help="make one live pi call to confirm the model key works")
    args = ap.parse_args(argv)
    ws = args.workspace.resolve()
    agent_dir = pi_agent_dir()

    cfg = check_project_yaml(ws)
    if cfg:
        check_models_resolvable(cfg, agent_dir)
        check_api_key(cfg, agent_dir)
    check_pi_spawnable()
    check_governance_context(ws)
    check_campaigns(ws)
    if args.probe and cfg:
        probe_pi(cfg)

    # ---- report ----
    icon = {PASS: "[ OK ]", WARN: "[WARN]", FAIL: "[FAIL]"}
    print(f"\nSweep preflight — workspace {ws}\n" + "-" * 64)
    for level, check, detail in _results:
        line = f"{icon[level]} {check}"
        if detail:
            line += f"  — {detail}"
        print(line)
    n_fail = sum(1 for r in _results if r[0] == FAIL)
    n_warn = sum(1 for r in _results if r[0] == WARN)
    print("-" * 64)
    print(f"{n_fail} FAIL, {n_warn} WARN, {sum(1 for r in _results if r[0]==PASS)} PASS")
    if n_fail:
        print("\nDO NOT launch the sweep — fix the FAILs above first.")
        return 2
    print("\nHard checks clear. Review WARNs before launching.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
