#!/usr/bin/env python3
"""Run inside one unprivileged X3 actor to test oracle and Graft isolation."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "/opt/orchestrator-worker-runtime")
from worker_wsl_q1_actor_probe import ACTOR, GRAFT, NODE, rpc  # noqa: E402


def denied(path: Path) -> bool:
    try:
        path.read_bytes()
    except (FileNotFoundError, PermissionError, NotADirectoryError):
        return True
    return False


def write_denied(path: Path) -> bool:
    try:
        with path.open("ab") as stream:
            stream.write(b"X3_PROTECTED_EDIT\n")
    except (FileNotFoundError, PermissionError, NotADirectoryError):
        return True
    return False


def probe(oracle_path: Path, protected_phrase: str,
          visible_phrase: str) -> dict:
    shell_search = subprocess.run(["/usr/bin/find", str(oracle_path.parent),
                                   "-type", "f"], capture_output=True,
                                  text=True, timeout=10)
    home = Path(os.environ["HOME"])
    build = subprocess.run([NODE, GRAFT, "build", str(ACTOR)],
                           capture_output=True, text=True, timeout=120)
    if build.returncode:
        raise RuntimeError("actor-scoped Graft build failed")
    process = subprocess.Popen([NODE, GRAFT, "mcp", str(ACTOR)],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True, bufsize=1)
    try:
        rpc(process, 1, "initialize", {"protocolVersion": "2025-06-18",
            "capabilities": {}, "clientInfo": {"name": "x3-isolation", "version": "1"}})
        assert process.stdin
        process.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
        process.stdin.flush()
        names = {row["name"] for row in rpc(process, 2, "tools/list", {}).get("tools", [])}
        visible = rpc(process, 3, "tools/call", {"name": "graft_find_all",
            "arguments": {"pattern": visible_phrase, "fixed": True}})
        hidden = rpc(process, 4, "tools/call", {"name": "graft_find_all",
            "arguments": {"pattern": protected_phrase, "fixed": True}})
        escaped = rpc(process, 5, "tools/call", {"name": "graft_file_api",
            "arguments": {"file": f"../../../../test/oracles/controller_x3/{oracle_path.name}"}})
        mapping = rpc(process, 6, "tools/call", {"name": "graft_repo_map",
            "arguments": {"max_dirs": 16}})
        visible_text = json.dumps(visible)
        hidden_text = json.dumps(hidden)
        map_text = json.dumps(mapping)
        checks = {
            "actor_uid": os.getuid() == 65534,
            "oracle_direct_read_denied": denied(oracle_path),
            "windows_mount_hidden": denied(oracle_path.parent.parent.parent),
            "shell_search_oracle_denied": shell_search.returncode != 0
                                           and not shell_search.stdout.strip(),
            "public_check_write_denied": write_denied(ACTOR / "public_check.py"),
            "acceptance_write_denied": write_denied(ACTOR / "acceptance.json"),
            "entrypoint_write_denied": write_denied(ACTOR / "app.py"),
            "no_inherited_instruction_file": not any(
                (base / name).exists() for base in (ACTOR, home)
                for name in ("AGENTS.md", "CLAUDE.md")),
            "provider_secrets_absent": not any(
                key in os.environ for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY",
                                       "CLAUDE_CONFIG_DIR", "CODEX_HOME")),
            "graft_six_tools": {"graft_check_freshness", "graft_repo_map",
                                 "graft_find_code", "graft_file_api",
                                 "graft_trace_calls", "graft_find_all"} <= names,
            "graft_public_actor_visible": visible_phrase in visible_text,
            "graft_oracle_phrase_absent": "no hits for" in hidden_text
                                          and hidden.get("isError") is False
                                          and "test/oracles" not in hidden_text,
            "graft_parent_escape_rejected": escaped.get("isError") is True,
            "graft_map_actor_only": "controller_x3" not in map_text
                                    and "oracles" not in map_text,
        }
        return {"checks": checks,
                "diagnostic": {"hidden_is_error": hidden.get("isError"),
                               "hidden_response_tail": hidden_text[-600:]}
                if not all(checks.values()) else None,
                "result": "PASS" if all(checks.values()) else "FAIL",
                "provider_calls": 0}
    finally:
        process.terminate()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(2)
    print(json.dumps(probe(Path(sys.argv[1]), sys.argv[2], sys.argv[3]),
                     sort_keys=True))
