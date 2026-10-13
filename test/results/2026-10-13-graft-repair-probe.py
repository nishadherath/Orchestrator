"""Provider-free evidence for the project-local Graft retrieval repair."""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import time
import tomllib
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from worker_graft_probe import Client

OUTPUT = ROOT / "test/results/2026-10-13-graft-mcp-verification.json"
evidence = {"recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "provider_calls": 0, "checks": []}
ident = 0


def request(client, label, method, params, expected):
    global ident
    ident += 1
    start = time.monotonic()
    result = client.call(ident, method, params, timeout=150)
    text = "\n".join(c.get("text", "") for c in result.get("content", []))
    ok = not result.get("isError") and expected(result, text)
    evidence["checks"].append({"id": label, "pass": bool(ok),
        "elapsed_seconds": round(time.monotonic() - start, 3),
        "text": text, "server": result.get("serverInfo")})
    OUTPUT.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(label, "PASS" if ok else "FAIL", evidence["checks"][-1]["elapsed_seconds"], flush=True)
    assert ok, label
    return result


def tool(client, label, name, args, expected):
    return request(client, label, "tools/call", {"name": name, "arguments": args}, expected)


config = tomllib.loads((ROOT / ".codex/config.toml").read_text(encoding="utf-8"))["mcp_servers"]["graft"]
command = [config["command"], *config["args"]]
client = Client(command, ROOT, dict(os.environ))
probe = ROOT / "src" / ("graft_repair_probe_" + uuid.uuid4().hex + ".py")
marker = "graft_repair_marker_" + uuid.uuid4().hex
try:
    request(client, "codex_initialize", "initialize", {
        "protocolVersion": "2024-11-05", "capabilities": {},
        "clientInfo": {"name": "graft-project-repair", "version": "1"}},
        lambda r, t: r.get("serverInfo", {}).get("name") == "graft")
    client.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    names = {"graft_check_freshness", "graft_find_code", "graft_find_all",
             "graft_file_api", "graft_trace_calls", "graft_repo_map"}
    request(client, "six_tools", "tools/list", {},
            lambda r, t: {v["name"] for v in r.get("tools", [])} == names)
    tool(client, "initial_freshness", "graft_check_freshness", {},
         lambda r, t: "graph check: OK" in t and "STALE" not in t)
    tool(client, "source_query", "graft_find_code", {
        "query": "run_probe", "in": "tools/worker_graft_probe.py", "limit": 1},
        lambda r, t: "tools/worker_graft_probe.py:L80-L179" in t)
    tool(client, "file_api", "graft_file_api", {"file": "tools/worker_graft_probe.py"},
         lambda r, t: "def run_probe()" in t)
    tool(client, "literal_search", "graft_find_all", {
        "pattern": "class ProtocolError", "fixed": True, "in": "tools/worker_graft_probe.py"},
        lambda r, t: "L30:" in t and "ProtocolError" in t)
    tool(client, "callers", "graft_trace_calls", {
        "symbol": "run_probe", "in": "tools/worker_graft_probe.py"},
        lambda r, t: "main" in t and "worker_graft_probe.py" in t)
    tool(client, "repo_map", "graft_repo_map", {"max_dirs": 8},
         lambda r, t: "tools" in t and "test/fixtures" not in t and "test/results" not in t)

    probe.write_text(f"def {marker}():\n    return 'fresh source'\n", encoding="utf-8")
    tool(client, "detect_new_source", "graft_check_freshness", {},
         lambda r, t: "graph check: STALE" in t and probe.name in t)
    tool(client, "automatic_refresh", "graft_find_code", {
        "query": marker, "in": probe.relative_to(ROOT).as_posix(), "limit": 1},
        lambda r, t: "return 'fresh source'" in t and marker in t)
finally:
    probe.unlink(missing_ok=True)
    try:
        tool(client, "automatic_removal", "graft_find_code", {
            "query": marker, "in": "src", "limit": 1},
            lambda r, t: marker not in t.split("\n\n1.")[-1] if "\n\n1." in t else "no hits" in t)
        tool(client, "final_freshness", "graft_check_freshness", {},
             lambda r, t: "graph check: OK" in t and "STALE" not in t)
    finally:
        client.close()

graph = json.loads((ROOT / "graft/.graph/wiring.json").read_text(encoding="utf-8"))
files = {n["path"] for n in graph["nodes"] if n["kind"] == "file"}
assert all(p.startswith(("src/", "tools/", "test/harness/")) for p in files)
assert not any(probe.name in p for p in files)
evidence["graph"] = {"files": len(files), "nodes": len(graph["nodes"]),
                     "edges": len(graph["edges"]), "languages": graph["meta"]["languages"],
                     "only_dirs": ["src", "tools", "test/harness"]}

claude = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]["graft"]
args = [v.replace("${CLAUDE_PROJECT_DIR:-.}", str(ROOT)) for v in claude["args"]]
client = Client([claude["command"], *args], ROOT, dict(os.environ))
try:
    request(client, "claude_initialize", "initialize", {
        "protocolVersion": "2024-11-05", "capabilities": {},
        "clientInfo": {"name": "graft-project-repair", "version": "1"}},
        lambda r, t: r.get("serverInfo", {}).get("name") == "graft")
    client.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    tool(client, "claude_source_query", "graft_file_api", {"file": "tools/worker_graft_probe.py"},
         lambda r, t: "def run_probe()" in t)
finally:
    client.close()

evidence["pass"] = all(c["pass"] for c in evidence["checks"])
OUTPUT.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
