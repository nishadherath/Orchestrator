#!/usr/bin/env python3
"""One bounded Claude worker call, independent of evaluation fixtures.

The executor owns admission, retry, accounting and acceptance. This module
only validates a scoped host capability, launches once and reports what the
stream actually proves. A requested effort is not a measured served effort.
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import json
import math
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable

import model_registry


class CapabilityError(RuntimeError):
    """A managed worker cannot be launched with the available host controls."""


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


@dataclasses.dataclass(frozen=True)
class WorkerRequest:
    actor_root: Path
    issue: str
    allowed_edits: tuple[str, ...]
    requested_cell: str
    allowance_usd: float
    policy: str
    timeout_s: float = 900.0
    admission_token: str = ""
    invocation_id: str = ""
    revision_id: str = ""
    decision_digest: str = ""
    intent_digest: str = ""


def parse_stream(stdout: str) -> dict:
    roots: set[str] = set()
    children: set[str] = set()
    billed: set[str] = set()
    final: dict = {}
    invalid = 0
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            invalid += 1
            continue
        if not isinstance(event, dict):
            invalid += 1
            continue
        if event.get("type") == "assistant" and isinstance(event.get("message"), dict):
            model = event["message"].get("model")
            if isinstance(model, str) and model:
                (children if event.get("parent_tool_use_id") else roots).add(model)
        if event.get("type") == "result":
            final = event
    usage = final.get("modelUsage", final.get("model_usage"))
    if isinstance(usage, dict):
        billed.update(usage)
    return {"root_models": sorted(roots), "child_models": sorted(children),
            "billed_models": sorted(billed), "final": final,
            "invalid_line_count": invalid}


def _valid_relative(root: Path, value: str) -> bool:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        return False
    resolved = (root / value).resolve()
    return resolved != root and resolved.is_relative_to(root)


class WorkerAdapter:
    """Production single-call adapter; fake transport is injectable for tests.

    `mcp_config` must be an explicit JSON file exposing *only* Graft and a
    launcher rooted to this actor. A fake transport tests the command/receipt,
    not the host's actual filesystem or MCP enforcement.
    """

    def __init__(self, mcp_config: Path | None = None,
                 transport: Callable | None = None):
        self.mcp_config = mcp_config
        self.transport = transport
        self._active: dict[str, subprocess.Popen] = {}
        self._cancelled: set[str] = set()
        self._active_lock = threading.Lock()

    @staticmethod
    def _transport(cmd: list[str], root: Path, env: dict, timeout: float):
        return subprocess.run(cmd, cwd=root, env=env, capture_output=True,
                              text=True, encoding="utf-8", timeout=timeout)

    def _run_process(self, request: WorkerRequest, cmd: list[str], root: Path,
                     env: dict) -> subprocess.CompletedProcess:
        with self._active_lock:
            if request.invocation_id in self._cancelled:
                raise CapabilityError("invocation was cancelled before subprocess launch")
            proc = subprocess.Popen(cmd, cwd=root, env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True, encoding="utf-8")
            self._active[request.invocation_id] = proc
        try:
            try:
                stdout, stderr = proc.communicate(timeout=request.timeout_s)
            except subprocess.TimeoutExpired as exc:
                proc.kill()
                stdout, stderr = proc.communicate()
                raise subprocess.TimeoutExpired(cmd, request.timeout_s, stdout, stderr) from exc
            return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)
        finally:
            with self._active_lock:
                self._active.pop(request.invocation_id, None)
                self._cancelled.discard(request.invocation_id)

    def cancel(self, invocation_id: str) -> bool:
        """Signal an active local writer; termination/cost still need a receipt."""
        with self._active_lock:
            self._cancelled.add(invocation_id)
            proc = self._active.get(invocation_id)
        if proc is None or proc.poll() is not None:
            return False
        proc.terminate()
        return True

    def capability(self, actor_root: Path) -> dict:
        root = actor_root.resolve()
        if not root.is_dir():
            raise CapabilityError(f"actor root is not a directory: {root}")
        if self.mcp_config is None or not self.mcp_config.is_file():
            raise CapabilityError("explicit actor-scoped Graft MCP config is required")
        try:
            config = json.loads(self.mcp_config.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CapabilityError(f"unreadable Graft MCP config: {exc}") from exc
        servers = config.get("mcpServers") if isinstance(config, dict) else None
        if not isinstance(servers, dict) or set(servers) != {"graft"}:
            raise CapabilityError("MCP config must expose only the graft server")
        graft = servers["graft"]
        if not isinstance(graft, dict) or not isinstance(graft.get("command"), str):
            raise CapabilityError("Graft MCP launcher is missing")
        launcher = graft["command"]
        if (not (Path(launcher).is_file() if Path(launcher).is_absolute() else shutil.which(launcher))):
            raise CapabilityError("Graft MCP launcher is unavailable on this host")
        arguments = graft.get("args")
        if not isinstance(arguments, list) or not all(isinstance(x, str) for x in arguments):
            raise CapabilityError("Graft MCP arguments are invalid")
        # The launcher must use the current actor as its index root. A static
        # checkout path is unsafe for isolated evaluation actors.
        if not any("${CLAUDE_PROJECT_DIR" in item for item in arguments):
            raise CapabilityError("Graft MCP root must bind to CLAUDE_PROJECT_DIR")
        if not any("graft" in item.lower() for item in [launcher, *arguments]):
            raise CapabilityError("MCP launcher does not identify a Graft implementation")
        for item in arguments:
            if Path(item).is_absolute() and not Path(item).exists():
                raise CapabilityError(f"Graft MCP argument path is unavailable: {item}")
        return {"configured": True, "graft_only": True, "actor_root": str(root),
                "config_digest": digest(config), "enforcement_proven": False,
                "managed_delegation_enforced": False, "cancellation_supported": True,
                "max_child_depth": 0, "max_child_concurrency": 0}

    @staticmethod
    def prompt(request: WorkerRequest) -> str:
        edits = "\n".join(f"- {path}" for path in request.allowed_edits)
        return ("Complete the supplied task in the actor root. Use Graft retrieval "
                "first and edit only these files. Do not delegate or access parent "
                "directories.\n\nAllowed edits:\n" + edits + "\n\nPolicy:\n" +
                request.policy.strip() + "\n\nTask:\n" + request.issue.strip())

    def command(self, request: WorkerRequest) -> list[str]:
        root = request.actor_root.resolve()
        self.capability(root)
        if not all(isinstance(value, str) and value for value in
                   (request.admission_token, request.invocation_id, request.revision_id,
                    request.decision_digest, request.intent_digest)):
            raise CapabilityError("managed worker requires complete executor admission identity")
        if not request.allowed_edits or any(not _valid_relative(root, p) for p in request.allowed_edits):
            raise CapabilityError("allowed edits must be project-relative and inside actor root")
        if (isinstance(request.allowance_usd, bool) or
                not isinstance(request.allowance_usd, (int, float)) or
                not math.isfinite(request.allowance_usd) or request.allowance_usd <= 0):
            raise CapabilityError("allowance must be finite and positive")
        cell = model_registry.resolve_cell(request.requested_cell)
        if not cell["direct_worker"]:
            raise CapabilityError("cell is not available for direct worker dispatch")
        return ["claude", "-p", self.prompt(request), "--output-format", "stream-json",
                "--verbose", "--model", cell["cli_model"], "--effort", cell["effort"],
                "--max-budget-usd", str(request.allowance_usd), "--restricted",
                "--strict-mcp-config", "--mcp-config", str(self.mcp_config.resolve()),
                "--no-session-persistence", "--permission-mode", "acceptEdits",
                "--permission-prompts", "none", "--tools", "Read,Edit,Write,Glob,Grep",
                "--allowedTools", "mcp__graft__graft_check_freshness",
                "mcp__graft__graft_repo_map", "mcp__graft__graft_find_code",
                "mcp__graft__graft_file_api", "mcp__graft__graft_trace_calls",
                "mcp__graft__graft_find_all"]

    def run(self, request: WorkerRequest) -> dict:
        cmd = self.command(request)
        root = request.actor_root.resolve()
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root),
               "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "8192"}
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        tick = time.monotonic()
        timed_out = False
        try:
            proc = (self.transport(cmd, root, env, request.timeout_s) if self.transport
                    else self._run_process(request, cmd, root, env))
            stdout = proc.stdout or ""
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            proc = subprocess.CompletedProcess(cmd, 124, stdout, exc.stderr or "")
        parsed = parse_stream(stdout)
        final = parsed["final"]
        raw_cost = final.get("total_cost_usd")
        cost = raw_cost if type(raw_cost) in (int, float) and math.isfinite(raw_cost) and raw_cost >= 0 else None
        actual = parsed["root_models"][0] if len(parsed["root_models"]) == 1 else None
        identity_valid = model_registry.identity_matches(request.requested_cell, actual,
                                                          parsed["child_models"])
        terminal = not timed_out and final.get("type") == "result" and cost is not None
        cell = model_registry.resolve_cell(request.requested_cell)
        raw_usage = final.get("usage") if isinstance(final.get("usage"), dict) else {}
        usage = {key: raw_usage.get(key) for key in ("input_tokens", "cache_creation_input_tokens",
                                                    "cache_read_input_tokens", "output_tokens")}
        usage.update(cost_usd=cost, currency="USD" if cost is not None else None,
                     cost_source="provider_reported" if cost is not None else "unknown")
        return {"admission_token": request.admission_token, "invocation_id": request.invocation_id,
                "revision_id": request.revision_id, "decision_digest": request.decision_digest,
                "intent_digest": request.intent_digest, "requested_cell": request.requested_cell,
                "requested_effort": cell["effort"], "served_effort": None,
                "effort_evidence": f"cli-argument:{cell['effort']}", "actual_model": actual,
                "identity_valid": identity_valid, "root_models": parsed["root_models"],
                "child_models": parsed["child_models"], "billed_models": parsed["billed_models"],
                "status": "interrupted" if not terminal else
                          ("completed" if proc.returncode == 0 and final.get("subtype") == "success"
                           and identity_valid and parsed["invalid_line_count"] == 0 else "failed"),
                "terminal": terminal, "writer_stopped": terminal, "timed_out": timed_out,
                "returncode": proc.returncode, "cost_usd": cost, "usage": usage,
                "started_at": started, "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "wall_clock_s": round(time.monotonic() - tick, 6),
                "stream": {"invalid_line_count": parsed["invalid_line_count"]},
                "command_contract": {"argv_sha256": digest(cmd), "restricted": True,
                                     "strict_mcp_config": True, "graft_configured": True,
                                     "filesystem_enforcement_proven": False}}
