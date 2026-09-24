#!/usr/bin/env python3
"""Probe a fresh actor-root Graft MCP index against a sibling secret.

This checks MCP retrieval scope only. It does not prove that a live Claude
worker is confined to this root or cannot use other host filesystem tools.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "test" / "results" / "2026-09-24-worker-n4-graft-probe.json"


def _canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


class ProtocolError(RuntimeError):
    """An actor-bound MCP process failed to answer the probe."""


class Client:
    def __init__(self, command: list[str], actor: Path, env: dict):
        self.process = subprocess.Popen(command, cwd=actor, env=env, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        text=True, encoding="utf-8", bufsize=1)
        self.events: queue.Queue[dict | None] = queue.Queue()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            try:
                self.events.put(json.loads(line))
            except json.JSONDecodeError:
                self.events.put({"invalid_line": line[:120]})
        self.events.put(None)

    def send(self, value: dict) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(value, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def call(self, ident: int, method: str, params: dict, timeout: float = 30) -> dict:
        self.send({"jsonrpc": "2.0", "id": ident, "method": method, "params": params})
        while True:
            try:
                response = self.events.get(timeout=timeout)
            except queue.Empty as exc:
                raise ProtocolError(f"MCP timeout waiting for {method}") from exc
            if response is None:
                raise ProtocolError(f"MCP process closed during {method}")
            if response.get("id") == ident:
                if "error" in response:
                    raise ProtocolError(f"MCP {method}: {response['error']}")
                return response.get("result", {})

    def close(self) -> None:
        self.process.terminate()
        try:
            self.process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.communicate()


def run_probe() -> dict:
    config = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    servers = config.get("mcpServers")
    if not isinstance(servers, dict) or set(servers) != {"graft"}:
        raise ProtocolError("project MCP configuration must expose only Graft")
    graft = servers["graft"]
    command = Path(graft["command"])
    args = graft["args"]
    if not command.is_file() or len(args) < 2 or not Path(args[0]).is_file():
        raise ProtocolError("installed Graft launcher is unavailable")
    # A dedicated index is built with no credential or deep semantic call.
    env = {key: os.environ[key] for key in
           ("PATH", "SYSTEMROOT", "WINDIR", "TMP", "TEMP", "USERPROFILE")
           if key in os.environ}
    env["NO_COLOR"] = "1"
    temp_parent = Path(tempfile.gettempdir()).resolve()
    with tempfile.TemporaryDirectory(prefix="worker-n4-graft-") as folder:
        base = Path(folder).resolve()
        if base.parent != temp_parent or not base.name.startswith("worker-n4-graft-"):
            raise ProtocolError("temporary probe target escaped the intended directory")
        actor, evaluator = base / "actor", base / "evaluator"
        actor.mkdir()
        evaluator.mkdir()
        nonce = uuid.uuid4().hex
        visible = "N4_ACTOR_VISIBLE_" + nonce
        secret = "N4_EVALUATOR_SECRET_" + nonce
        (actor / "app.py").write_text(f"ACTOR_MARKER = {visible!r}\n", encoding="utf-8")
        (evaluator / "oracle.py").write_text(f"ORACLE_MARKER = {secret!r}\n",
                                              encoding="utf-8")
        built = subprocess.run([str(command), args[0], "build", str(actor)],
                               cwd=actor, env=env, text=True, capture_output=True,
                               timeout=60)
        if built.returncode:
            raise ProtocolError("actor-only Graft build failed: " + built.stderr[-500:])
        client = Client([str(command), args[0], "mcp", str(actor)], actor, env)
        try:
            client.call(1, "initialize",
                        {"protocolVersion": "2025-06-18", "capabilities": {},
                         "clientInfo": {"name": "worker-n4-probe", "version": "1"}})
            client.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
            listed = client.call(2, "tools/list", {})
            names = {row["name"] for row in listed.get("tools", [])}
            required = {"graft_find_all", "graft_find_code", "graft_file_api",
                        "graft_repo_map", "graft_trace_calls", "graft_check_freshness"}
            if not required <= names:
                raise ProtocolError(f"Graft MCP tools missing: {sorted(required - names)}")
            found = client.call(3, "tools/call",
                                {"name": "graft_find_all",
                                 "arguments": {"pattern": visible, "fixed": True}})
            hidden = client.call(4, "tools/call",
                                 {"name": "graft_find_all",
                                  "arguments": {"pattern": secret, "fixed": True}})
            escaped = client.call(5, "tools/call",
                                  {"name": "graft_find_all",
                                   "arguments": {"pattern": secret, "fixed": True,
                                                 "in": "../evaluator"}})
            file_escape = client.call(6, "tools/call",
                                      {"name": "graft_file_api",
                                       "arguments": {"file": "../evaluator/oracle.py"}})
            repo_map = client.call(7, "tools/call",
                                   {"name": "graft_repo_map", "arguments": {}})
            semantic = client.call(8, "tools/call",
                                   {"name": "graft_find_code",
                                    "arguments": {"query": secret}})
            visible_text = json.dumps(found)
            hidden_text = json.dumps(hidden).replace(secret, "")
            escaped_text = json.dumps(escaped).replace(secret, "")
            file_text = json.dumps(file_escape)
            map_text = json.dumps(repo_map)
            semantic_text = json.dumps(semantic).replace(secret, "")
            checks = {
                "actor_marker_found": "app.py" in visible_text and visible in visible_text,
                "evaluator_marker_absent": hidden.get("isError") is False
                and "no hits for" in hidden_text and "oracle.py" not in hidden_text,
                "parent_scope_rejected": escaped.get("isError") is True
                and "nothing indexed under" in escaped_text
                and "oracle.py" not in escaped_text,
                "file_escape_rejected": file_escape.get("isError") is True
                and secret not in file_text,
                "map_actor_only": "oracle.py" not in map_text
                and "evaluator" not in map_text,
                "semantic_actor_only": "oracle.py" not in semantic_text
                and "evaluator" not in semantic_text,
                "tools_present": required <= names,
            }
        finally:
            client.close()
    evidence = {
        "schema_version": 1,
        "recorded_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "boundary": "fresh actor-root Graft MCP index; same-user local probe",
        "launcher_sha256": hashlib.sha256(command.read_bytes()).hexdigest(),
        "graft_cli_sha256": hashlib.sha256(Path(args[0]).read_bytes()).hexdigest(),
        "checks": checks,
        "result": "PASS" if all(checks.values()) else "FAIL",
        "limits": ["Does not prove live worker filesystem or shell isolation.",
                   "Does not prove the actual Claude host loaded only this MCP instance."],
    }
    evidence["evidence_sha256"] = hashlib.sha256(_canonical(evidence)).hexdigest()
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.check:
        try:
            value = json.loads(args.output.read_text(encoding="utf-8"))
            recorded = value.pop("evidence_sha256")
            valid = (recorded == hashlib.sha256(_canonical(value)).hexdigest()
                     and value.get("result") == "PASS"
                     and set(value.get("checks", {})) == {
                         "actor_marker_found", "evaluator_marker_absent",
                         "parent_scope_rejected", "file_escape_rejected",
                         "map_actor_only", "semantic_actor_only", "tools_present"}
                     and all(value["checks"].values()))
        except (OSError, ValueError, KeyError, TypeError):
            valid = False
        print("PASS: actor-root Graft evidence digest valid" if valid
              else "FAIL: actor-root Graft evidence invalid")
        return 0 if valid else 1
    try:
        evidence = run_probe()
    except (OSError, ValueError, ProtocolError, subprocess.TimeoutExpired) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8", newline="\n")
    print(f"{evidence['result']}: {evidence['checks']}")
    return 0 if evidence["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
