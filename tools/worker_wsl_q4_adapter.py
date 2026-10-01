#!/usr/bin/env python3
"""Q4 WSL evaluation adapter with report evidence and three admitted cells."""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from worker_adapter import CapabilityError, WorkerAdapter, WorkerRequest, digest
from worker_q4_adapter import EvaluationEvidenceMixin
from worker_wsl_q1 import ACTORS, SEEDS, collect, stage
from worker_wsl_q3_adapter import (MCP, Q3_AUTH, Q3BoundaryError, Q3WslAdapter,
                                   apply_collected, build_actor_graph,
                                   public_source, sha)
from worker_wsl_transport import _has_terminal_event, _linux_command

RUNTIME = Path("/opt/orchestrator-worker-runtime")
LAUNCHER = RUNTIME / "bin/worker-wsl-namespace-q4"
SUPPORTED_CELLS = {"worker-sonnet-low", "worker-sonnet-xhigh", "worker-opus-high"}


class Q4WslAdapter(EvaluationEvidenceMixin, Q3WslAdapter):
    """Retain Q3 isolation while versioning cell admission and report capture."""

    def capability(self, actor_root: Path) -> dict:
        if os.geteuid() != 0 or not LAUNCHER.is_file() or not Q3_AUTH.is_file():
            raise CapabilityError("attested Q4 WSL root runtime is unavailable")
        if (actor_root.is_symlink() or actor_root.resolve().parent != SEEDS.resolve()
                or actor_root.stat().st_uid != 0 or actor_root.stat().st_mode & 0o077):
            raise CapabilityError("Q4 project must be a private root-owned seed")
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
                      q4_launcher_sha256=sha(LAUNCHER.read_bytes()),
                      report_contract="worker-quality-v2")
        return result

    def _invoke(self, command: list[str], actor: Path,
                request: WorkerRequest) -> subprocess.CompletedProcess:
        argv = [str(LAUNCHER), "--subscription", str(actor), "--", *command]
        with self._active_lock:
            if request.invocation_id in self._cancelled:
                raise subprocess.TimeoutExpired(argv, request.timeout_s)
            process = subprocess.Popen(argv, cwd="/", stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True,
                                       encoding="utf-8", errors="replace")
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
            raise CapabilityError("Q4 request is outside the frozen evaluation contract")
        linux_command = _linux_command(cmd)
        package, manifest_path, manifest = public_source(root, self.task)
        name = "q1-" + request.invocation_id
        actor = ACTORS / name
        staged = stage(package, manifest_path, name)
        if staged["actor_root"] != str(actor):
            raise Q3BoundaryError("Q1 stage returned another actor")
        build_actor_graph(actor)
        process = self._invoke(linux_command, actor, request)
        if not _has_terminal_event(process.stdout):
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
        receipt = super().run(request)
        contract = receipt["command_contract"]
        boundary = contract.pop("q3_boundary", None)
        if boundary is not None:
            contract["q4_boundary"] = boundary
            contract["transport"] = "wsl-q1-q4-multifile-subscription"
        contract["q4_launcher_sha256"] = sha(LAUNCHER.read_bytes())
        # Ensure the evaluation report binds the exact collected source revision.
        if boundary is not None and "evaluation_report" in receipt:
            after = boundary["after_sha256"]
            binding = receipt["evaluation_report"]["binding"]
            binding["final_revision_sha256"] = digest(after)
            receipt["evaluation_report_digest"] = digest(receipt["evaluation_report"])
        return receipt
