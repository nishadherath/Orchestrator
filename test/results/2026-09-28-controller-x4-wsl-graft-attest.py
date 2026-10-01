#!/usr/bin/env python3
"""Provider-free Claude Code init probe for the X4 Controller role host.

Use an empty credential directory so this process cannot issue a model call.
Inspect the exact default role factory's MCP and tool flags at CLI init, not
just the project configuration file or a role's self-report.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path("/mnt/c/Users/Bob/Desktop/Code/Claude/Orchestrator")
sys.path.insert(0, str(ROOT / "tools"))

import controller_dispatch  # noqa: E402

PROJECT = Path("/var/lib/orchestrator-worker-n4/seed/controller-x4-t6wli9y1")
CLAUDE = "/opt/orchestrator-worker-runtime/bin/claude"
OUT = ROOT / "test/results/2026-09-28-controller-x4-wsl-graft-attest.json"


def main() -> int:
    if os.geteuid() != 0 or not (PROJECT / "graft").is_dir() or OUT.exists():
        raise RuntimeError("fresh root, graph and result path are required")
    adapter = controller_dispatch.ControllerRuntimeAdapter()
    adapter.capability(PROJECT)
    role = adapter._factory(PROJECT, "standard")(lambda: 4.0)
    with tempfile.TemporaryDirectory(prefix="controller-graft-no-auth-") as raw:
        private = Path(raw)
        private.chmod(0o700)
        env = {key: value for key, value in os.environ.items()
               if key not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
                              "CLAUDE_CODE_OAUTH_TOKEN")}
        env["CLAUDE_CONFIG_DIR"] = str(private)
        cmd = [CLAUDE, "-p", "probe", "--output-format=stream-json", "--verbose",
               "--model", "sonnet", "--effort", "low", "--max-budget-usd", "0.01",
               *role.extra_args]
        process = subprocess.run(cmd, cwd=PROJECT, env=env, capture_output=True,
                                 text=True, timeout=45)
    events = [json.loads(line) for line in process.stdout.splitlines()
              if line.strip()]
    init = next((row for row in events if row.get("type") == "system"
                 and row.get("subtype") == "init"), None)
    if init is None:
        raise RuntimeError("unauthenticated CLI produced no init event: "
                           + process.stderr[-250:])
    names = set(init.get("tools", []))
    connected = init.get("mcp_servers") == [{"name": "graft", "status": "connected"}]
    expected = set(controller_dispatch.GRAFT_READ_TOOLS)
    allowed = expected | {"Read", "Glob", "Grep"}
    assistant_events = sum(row.get("type") == "assistant" for row in events)
    final = next((row for row in reversed(events) if row.get("type") == "result"), {})
    charged = final.get("total_cost_usd")
    checks = {
        "graft_connected": connected,
        "six_graft_tools_visible": expected <= names,
        "no_extra_tools": names <= allowed,
        "no_execution_tools": not names.intersection(
            {"Bash", "PowerShell", "Task", "WebFetch", "WebSearch"}),
        "no_provider_call": assistant_events == 0 and charged in (None, 0, 0.0),
        "safe_mode_absent": "--safe-mode" not in role.extra_args,
    }
    receipt = {"schema_version": 1, "status": "PASS" if all(checks.values()) else "FAIL",
               "checks": checks, "mcp_servers": init.get("mcp_servers"),
               "tool_names": sorted(names), "provider_calls": 0 if checks["no_provider_call"] else None,
               "cli_returncode": process.returncode}
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "checks": checks,
                      "provider_calls": receipt["provider_calls"]}, sort_keys=True))
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
