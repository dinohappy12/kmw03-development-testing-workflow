"""Run a local verification plan once, persist budgets, and stop on repeated failure.
No model calls, dependency installs, network calls, repair loops, or publication here.
"""
import argparse
import hashlib
import json
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
    return {"exit_code": code, "seconds": round(time.monotonic()-start, 3),
            "output": output[-4000:]}

def execute(plan_path, state_path, report_path):
    plan_path = Path(plan_path).resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    root = (plan_path.parent / plan.get("root", ".")).resolve()
    if not root.is_dir():
        raise ValueError("project root does not exist")
    commands = plan.get("commands", [])
    if not commands or len(commands) > 12:
        raise ValueError("use 1..12 narrowly scoped commands")
    ids = [item.get("id") for item in commands]
    if any(not isinstance(x, str) or not x for x in ids) or len(ids) != len(set(ids)):
        raise ValueError("command ids must be unique")
    budget = plan.get("budget", {})
    rounds = min(3, max(1, int(budget.get("max_rounds", 3))))
    max_seconds = min(300, max(1, float(budget.get("total_seconds", 180))))
    fingerprint = hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()
    state_path = Path(state_path)
    state = (json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists()
             else {"rounds": 0, "seconds": 0, "failures": {}, "history": [],
                   "plan_hash": fingerprint})
    if state["plan_hash"] != fingerprint:
        raise ValueError("plan changed: review the budget and use a new explicit run id")
    reason = None
    if state["rounds"] >= rounds:
        reason = "round_budget_exhausted"
    elif state["seconds"] >= max_seconds:
        reason = "time_budget_exhausted"
    elif any(n >= 2 for n in state["failures"].values()):
        reason = "repeated_failure"
    if reason:
        report = {"status": "stopped", "reason": reason, "state": state,
                  "next": "Record the blocker; choose a different method or ask the owner."}
        save(report_path, report)
        return report, 2
    state["rounds"] += 1
    results = []
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for item in commands:
        remaining = max_seconds - state["seconds"]
        if remaining <= 0:
            reason = "time_budget_exhausted"
            break
        argv = item.get("argv")
        if not isinstance(argv, list) or not argv or any(not isinstance(x, str) for x in argv):
            raise ValueError("argv must be a list of strings; shell commands are not accepted")
        if argv[0] == "{python}":
            import sys
            argv = [sys.executable, *argv[1:]]
        result = run_command(argv, root, min(float(item.get("timeout", 30)), remaining), env)
        result["id"] = item["id"]
        results.append(result)
        state["seconds"] += result["seconds"]
        failure_count = state["failures"].get(item["id"], 0)
        state["failures"][item["id"]] = failure_count + 1 if result["exit_code"] else 0
        if result["exit_code"]:
            reason = "command_failed"
            break
    status = "passed" if reason is None and len(results) == len(commands) else "failed"
    if reason == "command_failed" and any(n >= 2 for n in state["failures"].values()):
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
    args = ap.parse_args()
    try:
        report, code = execute(args.plan, args.state, args.report)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        report, code = {"status": "stopped", "reason": str(exc)}, 2
        save(args.report, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code

if __name__ == "__main__":
    raise SystemExit(main())
