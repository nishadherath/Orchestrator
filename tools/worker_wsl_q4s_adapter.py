#!/usr/bin/env python3
"""Q4S WSL evaluation adapter with bounded, schema-bound receipts."""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from worker_adapter import CapabilityError, WorkerAdapter, WorkerRequest, digest
from worker_q4r_structured import schema_argument
from worker_q4s_structured import Q4SEvidenceMixin
from worker_wsl_q1 import ACTORS, SEEDS, collect, stage
from worker_wsl_q3_adapter import (MCP, Q3_AUTH, Q3BoundaryError, Q3WslAdapter,
                                   apply_collected, build_actor_graph,
                                   public_source, sha)
from worker_wsl_transport import _has_terminal_event, _linux_command

RUNTIME = Path("/opt/orchestrator-worker-runtime")
LAUNCHER = RUNTIME / "bin/worker-wsl-namespace-q4s"
SUPPORTED_CELLS = {"worker-sonnet-low", "worker-sonnet-medium", "worker-opus-high"}


class Q4SWslAdapter(Q4SEvidenceMixin, Q3WslAdapter):
    """Retain Q3 isolation while adding exact Q4S schema and cost guards."""

    def capability(self, actor_root: Path) -> dict:
        if os.geteuid() != 0 or not LAUNCHER.is_file() or not Q3_AUTH.is_file():
            raise CapabilityError("attested Q4S WSL root runtime is unavailable")
        if (actor_root.is_symlink() or actor_root.resolve().parent != SEEDS.resolve()
                or actor_root.stat().st_uid != 0 or actor_root.stat().st_mode & 0o077):
            raise CapabilityError("Q4S project must be a private root-owned seed")
        inventory = self.task.get("actor_files")
        if not isinstance(inventory, dict):
            raise CapabilityError("frozen public inventory is unavailable")
        for relative, expected in inventory.items():
            source = actor_root / relative
            if source.is_symlink() or not source.is_file():
                raise CapabilityError(f"public file is unsafe: {relative}")
            if (relative not in self.task["editable_paths"]
                    and sha(source.read_bytes()) != expected):
                raise CapabilityError(f"protected public file drifted: {relative}")
        result = WorkerAdapter.capability(self, actor_root)
        result.update(enforcement_proven=True, managed_delegation_enforced=True,
                      supported_cells=sorted(SUPPORTED_CELLS), budget_enforced=True,
                      credential_method="subscription",
                      q4s_launcher_sha256=sha(LAUNCHER.read_bytes()),
                      report_contract="worker-quality-v2-structured")
        return result

    def _invoke(self, command: list[str], actor: Path,
                request: WorkerRequest) -> subprocess.CompletedProcess:
        argv = [str(LAUNCHER), "--subscription", str(actor), "--", *command]
        with self._active_lock:
            if request.invocation_id in self._cancelled:
                raise subprocess.TimeoutExpired(argv, request.timeout_s)
            process = subprocess.Popen(argv, cwd="/", stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            self._active[request.invocation_id] = process
        try:
            try:
                stdout, stderr = process.communicate(timeout=request.timeout_s)
            except subprocess.TimeoutExpired as exc:
                process.kill()
                stdout, stderr = process.communicate()
                raise subprocess.TimeoutExpired(argv, request.timeout_s,
                                                stdout, stderr) from exc
            if request.invocation_id in self._cancelled:
                raise subprocess.TimeoutExpired(argv, request.timeout_s, stdout, stderr)
            return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)
        finally:
            with self._active_lock:
                self._active.pop(request.invocation_id, None)
                self._cancelled.discard(request.invocation_id)

    def _run_process(self, request: WorkerRequest, cmd: list[str], root: Path,
                     env: dict) -> subprocess.CompletedProcess:
        if (not re.fullmatch(r"[0-9a-f]{32}", request.invocation_id)
                or set(request.allowed_edits) != set(self.task["editable_paths"])
                or request.requested_cell not in SUPPORTED_CELLS):
            raise CapabilityError("Q4S request is outside the prospective evaluation contract")
        if len(cmd) != 20 or cmd[-1] != schema_argument():
            raise CapabilityError("Q4S command differs from the pinned report contract")
        linux_command = [*_linux_command(cmd[:-1]), cmd[-1]]
        package, manifest_path, manifest = public_source(root, self.task)
        name = "q1-" + request.invocation_id
        actor = ACTORS / name
        staged = stage(package, manifest_path, name)
        if staged["actor_root"] != str(actor):
            raise Q3BoundaryError("Q1 stage returned another actor")
        build_actor_graph(actor)
        process = self._invoke(linux_command, actor, request)
        stream = (process.stdout.decode("utf-8", errors="replace")
                  if isinstance(process.stdout, bytes) else process.stdout)
        if not _has_terminal_event(stream):
            return process
        try:
            collected = collect(name, package)
            if (collected["record_sha256"] != staged["record_sha256"]
                    or collected["spec_sha256"] != staged["spec_sha256"]):
                raise Q3BoundaryError("Q1 collection differs from staged actor")
            apply_collected(root, self.task, collected, manifest)
            self.last_boundary = {"actor_name": name,
                                  "q1_record_sha256": staged["record_sha256"],
                                  "q1_spec_sha256": staged["spec_sha256"],
                                  "changed_paths": collected["changed_paths"],
                                  "after_sha256": collected["after_sha256"]}
        except (OSError, ValueError, KeyError, Q3BoundaryError) as exc:
            raise subprocess.TimeoutExpired(cmd, request.timeout_s,
                                            process.stdout, str(exc)) from exc
        return process

    def run(self, request: WorkerRequest) -> dict:
        self.last_boundary = None
        command = self.command(request)
        receipt = Q4SEvidenceMixin.run(self, request)
        contract = receipt["command_contract"]
        contract["requested_argv_sha256"] = digest(command)
        contract["argv_sha256"] = digest([*_linux_command(command[:-1]),
                                           command[-1]])
        boundary = self.last_boundary
        if boundary is not None:
            contract["q4s_boundary"] = boundary
            contract["transport"] = "wsl-q1-q4s-structured-subscription"
            contract["credential_method"] = "subscription"
            contract["filesystem_enforcement_proven"] = True
        contract["q4s_launcher_sha256"] = sha(LAUNCHER.read_bytes())
        # Ensure the evaluation report binds the exact collected source revision.
        if boundary is not None and "evaluation_report" in receipt:
            after = boundary["after_sha256"]
            binding = receipt["evaluation_report"]["binding"]
            binding["final_revision_sha256"] = digest(after)
            receipt["evaluation_report_digest"] = digest(receipt["evaluation_report"])
        return receipt
