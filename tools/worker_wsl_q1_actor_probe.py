#!/usr/bin/env python3
"""Run inside the Q1 namespace as UID 65534; no provider call is made."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ACTOR = Path(os.environ["CLAUDE_PROJECT_DIR"])
BASE = Path("/var/lib/orchestrator-worker-n4")
NODE = "/opt/orchestrator-worker-runtime/bin/node"
GRAFT = "/opt/orchestrator-worker-runtime/lib/node_modules/@nanonets/graft/dist/cli.js"


def denied(path: Path, *, write: bool = False) -> bool:
    try:
        if write:
            with path.open("ab") as stream:
                stream.write(b"Q1_FORBIDDEN\n")
        else:
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
        value = json.loads(line)
        if value.get("id") == ident:
            if "error" in value:
                raise RuntimeError(f"Graft rejected {method}")
            return value.get("result", {})


def graft_scope() -> dict[str, bool]:
    built = subprocess.run([NODE, GRAFT, "build", str(ACTOR)], capture_output=True,
                           text=True, timeout=120)
    if built.returncode:
        raise RuntimeError("actor Graft build failed: " + built.stderr[-300:])
    process = subprocess.Popen([NODE, GRAFT, "mcp", str(ACTOR)], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               text=True, bufsize=1)
    try:
        rpc(process, 1, "initialize", {"protocolVersion": "2025-06-18",
            "capabilities": {}, "clientInfo": {"name": "q1-actor-probe", "version": "1"}})
        assert process.stdin
        process.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
        process.stdin.flush()
        tools = rpc(process, 2, "tools/list", {})
        names = {item["name"] for item in tools.get("tools", [])}
        visible = rpc(process, 3, "tools/call", {"name": "graft_find_all",
            "arguments": {"pattern": "Q1_ACTOR_VISIBLE_", "fixed": True}})
        hidden = rpc(process, 4, "tools/call", {"name": "graft_find_all",
            "arguments": {"pattern": "N4_EVALUATOR_SECRET_", "fixed": True}})
        escaped = rpc(process, 5, "tools/call", {"name": "graft_file_api",
            "arguments": {"file": "../../evaluator/oracle.py"}})
        return {
            "graft_six_tools": {"graft_check_freshness", "graft_repo_map",
                                "graft_find_code", "graft_file_api",
                                "graft_trace_calls", "graft_find_all"} <= names,
            "graft_sees_both_modules": all(name in json.dumps(visible)
                                           for name in ("main.py", "helper.py")),
            "graft_evaluator_absent": "oracle.py" not in json.dumps(hidden),
            "graft_parent_escape_rejected": escaped.get("isError") is True,
        }
    finally:
        process.terminate()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()


def main() -> int:
    sibling = sys.argv[1]
    link = ACTOR / ".scratch" / "oracle-link"
    link.symlink_to(BASE / "evaluator" / "oracle.py")
    checks = {
        "actor_uid": os.getuid() == 65534,
        "editable_main": not denied(ACTOR / "src/main.py", write=True),
        "editable_helper": not denied(ACTOR / "src/helper.py", write=True),
        "protected_issue": denied(ACTOR / "ISSUE.md", write=True),
        "protected_acceptance": denied(ACTOR / "acceptance.json", write=True),
        "protected_public_check": denied(ACTOR / "tests/public_check.py", write=True),
        "new_root_file_denied": denied(ACTOR / "new.py", write=True),
        "new_nested_file_denied": denied(ACTOR / "src/new.py", write=True),
        "evaluator_direct_denied": denied(BASE / "evaluator" / "oracle.py"),
        "evaluator_symlink_denied": denied(link),
        "sibling_actor_denied": denied(BASE / "actors" / sibling / "src/main.py"),
        "windows_mount_hidden": denied(Path("/mnt/c/Users/Bob")),
        "wsl_login_hidden": denied(Path("/home/wsl/.claude/.credentials.json")),
        "sanitised_env": "ANTHROPIC_API_KEY" not in os.environ
                         and "WSL_INTEROP" not in os.environ
                         and "CLAUDE_CONFIG_DIR" not in os.environ,
    }
    checks.update(graft_scope())
    print(json.dumps({"checks": checks, "result": "PASS" if all(checks.values()) else "FAIL"},
                     sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"result": "ERROR", "error": str(exc)[:300]}))
        raise SystemExit(1)
