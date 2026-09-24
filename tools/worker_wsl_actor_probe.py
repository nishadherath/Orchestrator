#!/usr/bin/env python3
"""Unprivileged N4 probe, executed inside the same namespace as a worker.

No protected content or secret marker is passed to this process. Results are
individual booleans; the root-owned host driver decides whether to attest it.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ACTOR = Path(os.environ["CLAUDE_PROJECT_DIR"])
HIDDEN = Path("/var/lib/orchestrator-worker-n4/evaluator/oracle.py")
GRAFT = Path("/opt/orchestrator-worker-runtime/lib/node_modules/@nanonets/graft/dist/cli.js")
NODE = Path("/opt/orchestrator-worker-runtime/bin/node")


def denied(path: Path) -> bool:
    try:
        path.read_bytes()
    except (FileNotFoundError, PermissionError, NotADirectoryError):
        return True
    return False


def rpc(process: subprocess.Popen, ident: int, method: str, params: dict) -> dict:
    assert process.stdin and process.stdout
    process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": ident,
                                    "method": method, "params": params}) + "\n")
    process.stdin.flush()
    while True:
        line = process.stdout.readline()
        if not line:
            raise RuntimeError(f"Graft closed during {method}")
        response = json.loads(line)
        if response.get("id") == ident:
            if "error" in response:
                raise RuntimeError(f"Graft returned an error for {method}")
            return response.get("result", {})


def graft_checks() -> dict[str, bool]:
    built = subprocess.run([str(NODE), str(GRAFT), "build", str(ACTOR)],
                           capture_output=True, text=True, timeout=90)
    if built.returncode:
        raise RuntimeError("actor Graft build failed: " + built.stderr[-300:])
    process = subprocess.Popen([str(NODE), str(GRAFT), "mcp", str(ACTOR)],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True, bufsize=1)
    try:
        rpc(process, 1, "initialize", {"protocolVersion": "2025-06-18",
                 "capabilities": {}, "clientInfo": {"name": "wsl-actor-probe", "version": "1"}})
        assert process.stdin
        process.stdin.write(json.dumps({"jsonrpc": "2.0",
                                        "method": "notifications/initialized"}) + "\n")
        process.stdin.flush()
        listed = rpc(process, 2, "tools/list", {})
        names = {item["name"] for item in listed.get("tools", [])}
        required = {"graft_check_freshness", "graft_repo_map", "graft_find_code",
                    "graft_file_api", "graft_trace_calls", "graft_find_all"}
        visible = rpc(process, 3, "tools/call", {"name": "graft_find_all",
                          "arguments": {"pattern": "N4_ACTOR_VISIBLE_", "fixed": True}})
        hidden = rpc(process, 4, "tools/call", {"name": "graft_find_all",
                         "arguments": {"pattern": "N4_EVALUATOR_SECRET_", "fixed": True}})
        escaped = rpc(process, 5, "tools/call", {"name": "graft_file_api",
                          "arguments": {"file": "../../evaluator/oracle.py"}})
        return {
            "graft_six_tools": required <= names,
            "graft_actor_visible": "app.py" in json.dumps(visible),
            "graft_evaluator_absent": "oracle.py" not in json.dumps(hidden),
            "graft_parent_rejected": escaped.get("isError") is True,
        }
    finally:
        process.terminate()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()


def main() -> int:
    target = ACTOR / "escape-link"
    target.symlink_to(HIDDEN)
    search = subprocess.run(["find", "/var/lib/orchestrator-worker-n4", "-name",
                             "oracle.py", "-print"], capture_output=True, text=True,
                            timeout=10)
    version = subprocess.run(["/opt/orchestrator-worker-runtime/bin/claude", "--version"],
                             capture_output=True, text=True, timeout=20)
    checks = {
        "actor_uid": os.getuid() == 65534,
        "actor_read_write": (ACTOR / "probe-output.txt").write_text("actor-output\n") > 0,
        "evaluator_direct_denied": denied(HIDDEN),
        "evaluator_symlink_denied": denied(target),
        "recursive_search_denied": "oracle.py" not in search.stdout,
        "windows_c_unmounted": denied(Path("/mnt/c/Users/Bob")),
        "windows_d_unmounted": " /mnt/d " not in
        Path("/proc/self/mountinfo").read_text(),
        "interop_socket_hidden": not Path("/run/WSL").exists(),
        "proc_root_no_escape": denied(Path("/proc/1/root") / HIDDEN.relative_to("/")),
        "claude_native_runs": version.returncode == 0 and "2.1.273" in version.stdout,
        "sanitized_environment": "WSL_INTEROP" not in os.environ
                                 and "ANTHROPIC_API_KEY" not in os.environ,
    }
    checks.update(graft_checks())
    print(json.dumps({"checks": checks, "result": "PASS" if all(checks.values()) else "FAIL"},
                     sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"result": "ERROR", "error": str(exc)[:300]}))
        raise SystemExit(1)
