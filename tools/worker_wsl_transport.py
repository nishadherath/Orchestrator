#!/usr/bin/env python3
"""Windows-to-WSL transport for one admitted N4-style Claude worker call.

This module stages the public package, launches the root-owned namespace
wrapper, and collects app.py only after a terminal Claude event. It does not
own admission, retries, billing or authentication. An ambiguous stop leaves
the staged actor untouched for manual reconciliation.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import threading
from pathlib import Path

from worker_adapter import CapabilityError, WorkerAdapter, WorkerRequest, digest

RUNTIME = "/opt/orchestrator-worker-runtime"
LAUNCHER = f"{RUNTIME}/bin/worker-wsl-namespace"
CLAUDE = f"{RUNTIME}/bin/claude"
NODE = f"{RUNTIME}/bin/node"
GRAFT = f"{RUNTIME}/lib/node_modules/@nanonets/graft/dist/cli.js"
MATERIALIZE = f"{RUNTIME}/worker_wsl_materialize.py"
COLLECT = f"{RUNTIME}/worker_wsl_collect.py"
MCP = f"{RUNTIME}/actor-mcp.json"
PUBLIC = ("app.py", "public_check.py", "ISSUE.md", "acceptance.json")
GRAFT_TOOLS = {"mcp__graft__" + name for name in (
    "graft_check_freshness", "graft_repo_map", "graft_find_code",
    "graft_file_api", "graft_trace_calls", "graft_find_all")}


class TransportError(RuntimeError):
    """The WSL host could not prove a safe launch or collection step."""


def _environment() -> dict[str, str]:
    # No project/provider credentials are inherited by the WSL root launcher.
    return {name: os.environ[name] for name in
            ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "USERPROFILE")
            if name in os.environ}


def _wsl_argv(*linux_args: str) -> list[str]:
    return ["wsl.exe", "-u", "root", "--", "bash", "-lc", shlex.join(linux_args)]


def _checked(*linux_args: str, timeout: float = 30) -> str:
    try:
        process = subprocess.run(_wsl_argv(*linux_args), capture_output=True,
                                 text=True, encoding="utf-8", errors="replace",
                                 env=_environment(), timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise TransportError("WSL host command unavailable or timed out") from exc
    if process.returncode:
        raise TransportError("WSL host step failed: " + process.stderr[-250:])
    return process.stdout.strip()


def _source_files(root: Path) -> None:
    if root.is_symlink() or not root.is_dir():
        raise TransportError("actor source must be a real directory")
    for name in PUBLIC:
        path = root / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 1_000_000:
            raise TransportError(f"public actor file is missing or unsafe: {name}")


def _linux_command(command: list[str]) -> list[str]:
    if not command or command[0] != "claude":
        raise TransportError("worker command must be produced by WorkerAdapter")
    if "--restricted" not in command or "--strict-mcp-config" not in command:
        raise TransportError("restricted strict MCP launch is required")
    if sum(value.startswith("--mcp-config=") for value in command) != 1:
        raise TransportError("one explicit Graft MCP configuration is required")
    if [value for value in command if value.startswith("--tools=")] != [
            "--tools=Read,Edit,Write,Glob,Grep"]:
        raise TransportError("unexpected built-in tool contract")
    allowlists = [value.removeprefix("--allowedTools=") for value in command
                  if value.startswith("--allowedTools=")]
    if len(allowlists) != 1 or set(allowlists[0].split(",")) != GRAFT_TOOLS:
        raise TransportError("exactly six Graft retrieval tools are required")
    if any(value.startswith(("--add-dir", "--settings", "--plugin-dir",
                             "--dangerously-skip-permissions")) for value in command):
        raise TransportError("worker command broadens host access")
    return [CLAUDE, *(f"--mcp-config={MCP}" if value.startswith("--mcp-config=")
                      else value for value in command[1:])]


def _has_terminal_event(stdout: str) -> bool:
    for line in stdout.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("type") == "result":
            return True
    return False


class WslTransport:
    """One-shot transport; cancellation is conservative and never replays."""

    def __init__(self):
        self._active: dict[str, subprocess.Popen] = {}
        self._cancelled: set[str] = set()
        self._lock = threading.Lock()

    def cancel(self, invocation_id: str) -> bool:
        with self._lock:
            self._cancelled.add(invocation_id)
            process = self._active.get(invocation_id)
        if process is None or process.poll() is not None:
            return False
        process.terminate()
        return True

    def invoke(self, *, invocation_id: str, command: list[str], source: Path,
               timeout: float) -> subprocess.CompletedProcess:
        if not re.fullmatch(r"[0-9a-f]{32}", invocation_id):
            raise TransportError("invocation identity must be 32 lowercase hex characters")
        linux_command = _linux_command(command)
        if source.is_symlink():
            raise TransportError("actor source cannot be a symlink")
        root = source.resolve()
        _source_files(root)
        linux_source = _checked("wslpath", "-a", root.as_posix())
        name = "inv-" + invocation_id
        staged = _checked("python3", MATERIALIZE, "--source", linux_source,
                          "--name", name)
        try:
            actor = json.loads(staged)["actor_root"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise TransportError("materializer returned no actor identity") from exc
        if actor != f"/var/lib/orchestrator-worker-n4/actors/{name}":
            raise TransportError("materializer returned an unexpected actor root")
        # Claude may report the MCP server connected without registering its
        # retrieval tools when this fresh actor has no graph yet.
        _checked(LAUNCHER, actor, "--", NODE, GRAFT, "build", actor, timeout=90)
        argv = _wsl_argv(LAUNCHER, actor, "--", *linux_command)
        with self._lock:
            if invocation_id in self._cancelled:
                raise TransportError("invocation cancelled before WSL launch")
            process = subprocess.Popen(argv, cwd=root, env=_environment(),
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       text=True, encoding="utf-8", errors="replace")
            self._active[invocation_id] = process
        try:
            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                process.kill()
                stdout, stderr = process.communicate()
                raise subprocess.TimeoutExpired(argv, timeout, stdout, stderr) from exc
            with self._lock:
                cancelled = invocation_id in self._cancelled
            if cancelled:
                raise subprocess.TimeoutExpired(argv, timeout, stdout, stderr)
            if _has_terminal_event(stdout):
                _checked("python3", COLLECT, "--name", name,
                         "--source", linux_source)
            return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)
        finally:
            with self._lock:
                self._active.pop(invocation_id, None)
                self._cancelled.discard(invocation_id)


class WslWorkerAdapter(WorkerAdapter):
    """TaskExecutor adapter gated by the current manifest-bound WSL evidence."""

    def __init__(self, attestation_path: Path | None = None):
        import worker_wsl_attestation as host_attestation

        super().__init__(mcp_config=host_attestation.ROOT / ".mcp.json")
        self.attestation_path = attestation_path or host_attestation.OUTPUT
        self.host = WslTransport()

    def capability(self, actor_root: Path) -> dict:
        import worker_wsl_attestation as host_attestation

        if actor_root.is_symlink():
            raise CapabilityError("actor root cannot be a symlink")
        root = actor_root.resolve()
        try:
            _source_files(root)
            evidence = json.loads(self.attestation_path.read_text(encoding="utf-8"))
            if not host_attestation.validate(evidence, check_host=True):
                raise CapabilityError("WSL attestation is stale or invalid")
            if evidence["checks"].get("windows_transport_path") is not True:
                raise CapabilityError("Windows-to-WSL transport path has not been attested")
        except (OSError, ValueError, TransportError, KeyError) as exc:
            raise CapabilityError(f"WSL worker capability unavailable: {exc}") from exc
        return {"configured": True, "graft_only": True, "actor_root": str(root),
                "config_digest": evidence["runtime_hashes"]["actor-mcp.json"],
                "host_attestation_sha256": evidence["evidence_sha256"],
                "enforcement_proven": True, "managed_delegation_enforced": True,
                "cancellation_supported": True, "max_child_depth": 0,
                "max_child_concurrency": 0}

    def _run_process(self, request: WorkerRequest, cmd: list[str], root: Path,
                     env: dict) -> subprocess.CompletedProcess:
        return self.host.invoke(invocation_id=request.invocation_id, command=cmd,
                                source=root, timeout=request.timeout_s)

    def cancel(self, invocation_id: str) -> bool:
        return self.host.cancel(invocation_id)

    def run(self, request: WorkerRequest) -> dict:
        capability = self.capability(request.actor_root)
        requested_command = self.command(request)
        receipt = super().run(request)
        receipt["command_contract"]["requested_argv_sha256"] = digest(requested_command)
        receipt["command_contract"]["argv_sha256"] = digest(
            _linux_command(requested_command))
        receipt["command_contract"]["transport"] = "wsl-private-mount-pid-uid65534"
        receipt["command_contract"]["filesystem_enforcement_proven"] = True
        receipt["command_contract"]["host_attestation_sha256"] = (
            capability["host_attestation_sha256"])
        return receipt
