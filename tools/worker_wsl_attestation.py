#!/usr/bin/env python3
"""Attest the disposable N4 WSL actor boundary without a paid worker call.

The probe launches the *actual* native Claude CLI far enough to inspect its
MCP/tool initialization. Its empty actor home has no credentials; a zero-token
authentication failure is expected. N5 must perform a fresh attestation and
still needs a separately authorised live campaign runner.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path, PurePosixPath

from worker_evaluation import ROOT, freeze

CORPUS = ROOT / "test" / "fixtures" / "worker_n4"
OUTPUT = ROOT / "test" / "results" / "2026-09-24-worker-n4-wsl-host.json"
RUNTIME = PurePosixPath("/opt/orchestrator-worker-runtime")
ACTOR_BASE = "/var/lib/orchestrator-worker-n4/actors/"
RUNTIME_FILES = (
    "bin/node", "bin/claude", "bin/worker-wsl-namespace", "actor-probe.py",
    "actor-mcp.json", "lib/node_modules/@nanonets/graft/dist/cli.js",
)
SOURCE_FILES = (
    "tools/setup_worker_wsl.sh", "tools/worker_wsl_stage.sh",
    "tools/worker_wsl_namespace.sh", "tools/worker_wsl_actor_probe.py",
    "tools/worker_wsl_attestation.py",
)
GRAFT_TOOLS = {"mcp__graft__" + name for name in (
    "graft_check_freshness", "graft_repo_map", "graft_find_code",
    "graft_file_api", "graft_trace_calls", "graft_find_all")}


class AttestationError(RuntimeError):
    """A host fact is unavailable or violates the worker isolation contract."""


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wsl(*args: str, timeout: int = 120) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["wsl.exe", "-u", "root", "--", "bash", "-lc",
                               shlex.join(args)],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AttestationError("WSL command unavailable or timed out") from exc


def checked(*args: str, timeout: int = 120) -> str:
    result = wsl(*args, timeout=timeout)
    if result.returncode:
        raise AttestationError("WSL check failed: " + result.stderr[-300:])
    return result.stdout.strip()


def runtime_hashes() -> dict[str, str]:
    paths = [str(RUNTIME / name) for name in RUNTIME_FILES]
    lines = checked("sha256sum", *paths).splitlines()
    if len(lines) != len(paths):
        raise AttestationError("incomplete runtime fingerprint")
    values = {}
    for name, line, path in zip(RUNTIME_FILES, lines, paths):
        fields = line.split(maxsplit=1)
        if len(fields) != 2 or fields[1].lstrip("*") != path:
            raise AttestationError("runtime fingerprint path mismatch")
        values[name] = fields[0]
    # Graft loads native parser modules from transitive dependencies; hashing
    # only its entry point would miss an altered .node binary.
    tree = r'''
import hashlib, os, pathlib, sys
root = pathlib.Path(sys.argv[1])
digest = hashlib.sha256()
for directory, directories, files in os.walk(root, followlinks=False):
    directories.sort()
    for name in sorted(directories + files):
        path = pathlib.Path(directory) / name
        relative = path.relative_to(root).as_posix().encode()
        digest.update(len(relative).to_bytes(4, "big") + relative)
        if path.is_symlink():
            data = os.readlink(path).encode()
        elif path.is_file():
            data = hashlib.sha256(path.read_bytes()).digest()
        else:
            data = b"directory"
        digest.update(len(data).to_bytes(8, "big") + data)
print(digest.hexdigest())
'''
    values["graft_package_tree"] = checked("python3", "-c", tree,
        str(RUNTIME / "lib/node_modules/@nanonets/graft"))
    return values


def validate(value: dict, *, check_host: bool) -> bool:
    if not isinstance(value, dict):
        return False
    digest = value.get("evidence_sha256")
    body = {k: v for k, v in value.items() if k != "evidence_sha256"}
    if digest != hashlib.sha256(canonical(body)).hexdigest():
        return False
    if value.get("schema_version") != 1 or value.get("result") != "PASS":
        return False
    if value.get("manifest_sha256") != freeze(CORPUS)["manifest_sha256"]:
        return False
    checks = value.get("checks")
    if not isinstance(checks, dict) or not checks or not all(v is True for v in checks.values()):
        return False
    if value.get("source_hashes") != {name: sha(ROOT / name) for name in SOURCE_FILES}:
        return False
    if check_host and value.get("runtime_hashes") != runtime_hashes():
        return False
    return True


def run() -> dict:
    manifest = freeze(CORPUS)
    source_hashes = {name: sha(ROOT / name) for name in SOURCE_FILES}
    stage = checked("wslpath", "-a", (ROOT / "tools" / "worker_wsl_stage.sh")
                    .as_posix())
    actor = checked("bash", stage).splitlines()[-1]
    if not actor.startswith(ACTOR_BASE) or not actor[len(ACTOR_BASE):].startswith("probe-"):
        raise AttestationError("stage returned an invalid actor root")

    launcher = str(RUNTIME / "bin" / "worker-wsl-namespace")
    probe = wsl(launcher, actor, "--", "/usr/bin/python3",
                str(RUNTIME / "actor-probe.py"), timeout=150)
    try:
        report = json.loads(probe.stdout.strip())
    except json.JSONDecodeError as exc:
        raise AttestationError("actor probe returned no JSON: " + probe.stderr[-300:]) from exc
    if probe.returncode or report.get("result") != "PASS":
        raise AttestationError("actor boundary probe failed: " + json.dumps(report)[:400])

    # Use the same non-greedy option syntax as WorkerAdapter.command(). The
    # unauthenticated actor can initialize tools but cannot make a paid call.
    claude_args = [str(RUNTIME / "bin" / "claude"), "-p", "probe",
                   "--output-format=stream-json", "--verbose", "--model", "sonnet",
                   "--effort", "low", "--max-budget-usd", "0.01", "--restricted",
                   "--strict-mcp-config",
                   f"--mcp-config={RUNTIME / 'actor-mcp.json'}",
                   "--no-session-persistence", "--permission-mode=acceptEdits",
                   "--permission-prompts=none", "--tools=Read,Edit,Write,Glob,Grep",
                   "--allowedTools=" + ",".join(sorted(GRAFT_TOOLS))]
    started = wsl(launcher, actor, "--", *claude_args, timeout=45)
    try:
        events = [json.loads(line) for line in started.stdout.splitlines() if line.strip()]
        init = next(row for row in events if row.get("type") == "system"
                    and row.get("subtype") == "init")
        result = next(row for row in reversed(events) if row.get("type") == "result")
    except (ValueError, StopIteration) as exc:
        raise AttestationError("Claude did not produce an init and terminal event") from exc
    names = set(init.get("tools", []))
    mcp = init.get("mcp_servers")
    cli_checks = {
        "claude_actor_cwd": init.get("cwd") == actor,
        "claude_graft_connected": mcp == [{"name": "graft", "status": "connected"}],
        "claude_graft_six_tools": GRAFT_TOOLS <= names,
        "claude_no_execution_tools": not names.intersection({"Bash", "PowerShell", "Task",
                                                         "WebFetch", "WebSearch"}),
        "claude_only_expected_tools": names <= GRAFT_TOOLS | {"Read", "Edit", "Write",
                                                             "Glob", "Grep"},
        "claude_no_inherited_plugins": init.get("plugins") == [],
        "claude_no_credentials": init.get("apiKeySource") == "none",
        "claude_no_paid_call": (started.returncode != 0
                               and result.get("total_cost_usd") == 0
                               and result.get("usage", {}).get("input_tokens") == 0
                               and result.get("usage", {}).get("output_tokens") == 0),
    }
    checks = {**report["checks"], **cli_checks}
    evidence = {
        "schema_version": 1,
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "manifest_sha256": manifest["manifest_sha256"],
        "actor_root": actor,
        "boundary": "WSL private mount+PID namespaces, uid 65534, Linux ext4 actor/evaluator",
        "runtime_hashes": runtime_hashes(),
        "source_hashes": source_hashes,
        "checks": checks,
        "result": "PASS" if all(checks.values()) else "FAIL",
        "limits": ["No authenticated provider request or paid worker edit occurred.",
                   "N5 requires a fresh attestation, credential configuration and live runner."],
    }
    evidence["evidence_sha256"] = hashlib.sha256(canonical(evidence)).hexdigest()
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    try:
        if args.check:
            valid = validate(json.loads(args.output.read_text(encoding="utf-8")),
                             check_host=True)
            print("PASS: WSL host attestation current" if valid else
                  "FAIL: WSL host attestation stale or invalid")
            return 0 if valid else 1
        evidence = run()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8", newline="\n")
        print(f"{evidence['result']}: {len(evidence['checks'])} WSL host checks; "
              f"manifest {evidence['manifest_sha256'][:12]}")
        return 0 if evidence["result"] == "PASS" else 1
    except (OSError, ValueError, KeyError, AttestationError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
