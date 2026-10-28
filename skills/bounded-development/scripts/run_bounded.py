"""Execute one bounded local verification round; preserve evidence across revisions.
No model calls, dependency installation, automatic repairs or publication.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def positive_seconds(value, name):
    number = float(value)
    if isinstance(value, bool) or not math.isfinite(number) or number <= 0:
        raise ValueError(name + " must be a finite positive number")
    return number


def run_command(argv, cwd, timeout, env):
    start = time.monotonic()
    kwargs = {"cwd": str(cwd), "env": env, "stdout": subprocess.PIPE,
              "stderr": subprocess.STDOUT, "text": True, "encoding": "utf-8",
              "errors": "replace"}
    if os.name != "nt":
        kwargs["start_new_session"] = True
    else:
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    proc = subprocess.Popen(argv, **kwargs)
    try:
        output, _ = proc.communicate(timeout=timeout)
        code = proc.returncode
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=5, check=False)
        else:
            os.killpg(proc.pid, signal.SIGKILL)
        proc.kill()
        output, _ = proc.communicate(timeout=5)
        code = 124
    result = {"exit_code": code, "seconds": round(time.monotonic()-start, 3),
              "output": output[-4000:]}
    if code == 124:
        result["error_type"] = "command_timeout"
    return result


def execute(plan_path, state_path, report_path, revision_reason=None):
    plan_path = Path(plan_path).resolve()
    state_path, report_path = Path(state_path), Path(report_path)
    if state_path.resolve() == report_path.resolve() or plan_path in (
            state_path.resolve(), report_path.resolve()):
        raise ValueError("plan, state and report must use different paths")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    root = (plan_path.parent / plan.get("root", ".")).resolve()
    if not root.is_dir():
        raise ValueError("project root does not exist")
    commands = plan.get("commands", [])
    if not isinstance(commands, list) or not 1 <= len(commands) <= 12:
        raise ValueError("use 1..12 narrowly scoped commands")
    if any(not isinstance(item, dict) for item in commands):
        raise ValueError("each command must be an object")
    ids = [item.get("id") for item in commands]
    if any(not isinstance(x, str) or not x.strip() for x in ids) or len(ids) != len(set(ids)):
        raise ValueError("command ids must be unique nonblank strings")
    for item in commands:
        argv = item.get("argv")
        if not isinstance(argv, list) or not argv or any(not isinstance(x, str) for x in argv):
            raise ValueError("argv must be a list of strings; shell commands are not accepted")
        positive_seconds(item.get("timeout", 30), "timeout")
        if not isinstance(item.get("timeout_reason", ""), str):
            raise ValueError("timeout_reason must be a string")
    budget = plan.get("budget", {})
    limits = {"max_rounds": min(3, max(1, int(budget.get("max_rounds", 3)))),
              "total_seconds": min(300, positive_seconds(budget.get("total_seconds", 180), "total_seconds"))}
    fingerprint = hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()
    state = (json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists()
             else {"rounds": 0, "seconds": 0, "failures": {}, "history": [],
                   "plan_hash": fingerprint, "original_budget": limits,
                   "command_ids": ids, "plan_revisions": [], "in_progress": None})
    if state["plan_hash"] != fingerprint:
        if not isinstance(revision_reason, str) or not revision_reason.strip():
            raise ValueError("plan changed: keep the same state and supply --revision-reason; do not reset the budget")
        if "original_budget" not in state or "command_ids" not in state:
            raise ValueError("legacy state: first run the original plan to preserve its budget before revising")
        if limits != state["original_budget"] or set(ids) != set(state["command_ids"]):
            raise ValueError("revision must preserve original budget and case ids; record a separately authorized scope for new work")
        state.setdefault("plan_revisions", []).append({"from_hash": state["plan_hash"],
            "to_hash": fingerprint, "reason": revision_reason.strip(),
            "after_round": state["rounds"], "seconds_used": state["seconds"]})
        state["plan_hash"] = fingerprint
        save(state_path, state)
    # Migrate an unchanged older plan without discarding any prior consumption.
    state.setdefault("original_budget", limits)
    state.setdefault("command_ids", ids)
    state.setdefault("plan_revisions", [])
    state.setdefault("in_progress", None)
    limits = state["original_budget"]
    reason = None
    if state["in_progress"]:
        reason = "interrupted_run"
    elif state["rounds"] >= limits["max_rounds"]:
        reason = "round_budget_exhausted"
    elif state["seconds"] >= limits["total_seconds"]:
        reason = "time_budget_exhausted"
    elif any(n >= 2 for n in state["failures"].values()):
        reason = "repeated_failure"
    if reason:
        save(state_path, state)
        report = {"status": "stopped", "reason": reason, "state": state,
                  "release": "human_review_required",
                  "next": "Record the blocker and retained budget. An interrupted command requires review before further execution."}
        save(report_path, report)
        return report, 2
    state["rounds"] += 1
    results = []
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for item in commands:
        remaining = limits["total_seconds"] - state["seconds"]
        if remaining <= 0:
            reason = "time_budget_exhausted"
            break
        argv = item["argv"]
        if argv[0] == "{python}":
            import sys
            argv = [sys.executable, *argv[1:]]
        requested = positive_seconds(item.get("timeout", 30), "timeout")
        timeout_reason = item.get("timeout_reason", "").strip()
        timeout = min(requested, remaining, requested if timeout_reason else 30)
        state["in_progress"] = {"command_id": item["id"], "round": state["rounds"],
                                "started_unix": time.time(), "timeout_seconds": timeout}
        save(state_path, state)
        save(report_path, {"status": "running", "round": state["rounds"],
                          "command_id": item["id"], "seconds_total": state["seconds"],
                          "results": results, "release": "human_review_required"})
        start = time.monotonic()
        try:
            result = run_command(argv, root, timeout, env)
        except OSError as exc:
            result = {"exit_code": 127, "seconds": round(time.monotonic()-start, 3),
                      "output": str(exc)[-4000:], "error_type": "launch_error"}
        result.update({"id": item["id"], "requested_timeout": requested,
                       "effective_timeout": timeout, "timeout_reason": timeout_reason})
        results.append(result)
        state["seconds"] += result["seconds"]
        state["failures"][item["id"]] = (state["failures"].get(item["id"], 0) + 1
                                        if result["exit_code"] else 0)
        state["in_progress"] = None
        save(state_path, state)
        if result["exit_code"]:
            reason = result.get("error_type", "command_failed")
            break
    status = "passed" if reason is None and len(results) == len(commands) else "failed"
    if any(n >= 2 for n in state["failures"].values()):
        status, reason = "stopped", "repeated_failure"
    state["history"].append({"round": state["rounds"], "status": status,
                             "reason": reason, "results": results})
    save(state_path, state)
    report = {"status": status, "reason": reason, "round": state["rounds"],
              "seconds_total": round(state["seconds"], 3), "results": results,
              "release": "human_review_required"}
    save(report_path, report)
    return report, 0 if status == "passed" else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--state", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--revision-reason", help="Record why the plan changed; retain the same state and budget")
    args = ap.parse_args()
    try:
        report, code = execute(args.plan, args.state, args.report, args.revision_reason)
    except (ValueError, OSError, TypeError) as exc:
        report, code = {"status": "stopped", "reason": str(exc),
                        "release": "human_review_required"}, 2
        if Path(args.report).resolve() not in (Path(args.state).resolve(), Path(args.plan).resolve()):
            save(args.report, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
