#!/usr/bin/env python3
"""Q4U WSL adapter for one-or-more existing editable files.

The Q1/Q4T snapshots remain unchanged. This boundary widens only the edit
cardinality; it retains their private seed, stop receipt, protected-file,
structured-report, subscription-auth and namespace checks.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

from worker_adapter import CapabilityError, WorkerAdapter, WorkerRequest, digest
from worker_q4r_structured import schema_argument
from worker_q4t_structured import Q4TEvidenceMixin
from worker_wsl_q1 import (ACTORS, MANIFESTS, OUTPUTS, SEEDS, MAX_FILE_BYTES,
                           MAX_TOTAL_BYTES, path_parts)
from worker_wsl_q3_adapter import (Q3_AUTH, Q3BoundaryError, Q3WslAdapter,
                                   apply_collected, build_actor_graph,
                                   cap_output, sha)
from worker_wsl_q4u import check_q1, stage
from worker_wsl_q1 import collect
from worker_wsl_q2_verify import dispose
from worker_wsl_transport import _has_terminal_event, _linux_command


RUNTIME = Path("/opt/orchestrator-worker-runtime")
LAUNCHER = RUNTIME / "bin/worker-wsl-namespace-q4u"
SUPPORTED_CELLS = {"worker-sonnet-low", "worker-sonnet-medium", "worker-opus-high"}
# Mirrors the admission check in worker_wsl_namespace_q4u.sh.
MAX_SINGLE_CALL_USD = 4.0


def public_source(project: Path, task: dict) -> tuple[Path, Path, dict]:
    """Freeze the current actor revision with one to eight existing editables."""
    expected = task["actor_files"]
    editable = set(task["editable_paths"])
    if (project.is_symlink() or not project.is_dir()
            or project.resolve().parent != SEEDS.resolve()
            or project.stat().st_uid != 0 or project.stat().st_mode & 0o077
            or len(expected) > 200 or not 1 <= len(editable) <= 8):
        raise Q3BoundaryError("Q4U public project or edit contract is invalid")
    package = Path(tempfile.mkdtemp(prefix="q4u-public-", dir=SEEDS))
    manifest_path: Path | None = None
    try:
        rows = []
        total = 0
        for relative, original_sha in sorted(expected.items()):
            parts = path_parts(relative)
            if any(project.joinpath(*parts[:depth]).is_symlink()
                   for depth in range(1, len(parts))):
                raise Q3BoundaryError(f"public path has a symlink parent: {relative}")
            source = project / relative
            if (source.is_symlink() or not source.is_file()
                    or source.stat().st_nlink != 1
                    or source.stat().st_size > MAX_FILE_BYTES):
                raise Q3BoundaryError(f"public file is missing or unsafe: {relative}")
            data = source.read_bytes()
            if relative not in editable and sha(data) != original_sha:
                raise Q3BoundaryError(f"protected public file drifted: {relative}")
            total += len(data)
            target = package.joinpath(*parts)
            target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
            target.write_bytes(data)
            rows.append({"path": relative, "sha256": sha(data),
                         "editable": relative in editable})
        if total > MAX_TOTAL_BYTES or {row["path"] for row in rows if row["editable"]} != editable:
            raise Q3BoundaryError("public package exceeds Q4U contract")
        manifest = {"schema_version": 1, "files": rows}
        fd, raw = tempfile.mkstemp(prefix="q4u-spec-", suffix=".json", dir=SEEDS)
        manifest_path = Path(raw)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(manifest, stream, sort_keys=True)
        return package, manifest_path, manifest
    except Exception:
        shutil.rmtree(package)
        if manifest_path is not None:
            manifest_path.unlink(missing_ok=True)
        raise


def isolated_public_runner(task: dict):
    """Run the frozen public check in a fresh credential-free Q4U namespace."""
    def run(argv: list[str], *, cwd: Path, capture_output: bool,
            timeout: float, shell: bool) -> subprocess.CompletedProcess:
        if (argv != ["python3", "-B", "public_check.py"]
                or capture_output is not True or shell is not False
                or timeout != 30):
            raise Q3BoundaryError("only the frozen Q4U public command is accepted")
        package, manifest_path, manifest = public_source(cwd, task)
        name = "q1-" + uuid.uuid4().hex
        actor = ACTORS / name
        staged = False
        collected = False
        try:
            before = {row["path"]: row["sha256"] for row in manifest["files"]}
            stage(package, manifest_path, name)
            staged = True
            try:
                process = subprocess.run(
                    [str(LAUNCHER), str(actor), "--", "/usr/bin/python3",
                     "-B", "public_check.py"], cwd="/", capture_output=True,
                    timeout=timeout, preexec_fn=cap_output)
            except subprocess.TimeoutExpired as exc:
                raise Q3BoundaryError(
                    f"Q4U public actor {name} timed out; preserve for reconciliation") from exc
            result = collect(name, package)
            collected = True
            if result["changed_paths"]:
                raise Q3BoundaryError("Q4U public command changed an editable file")
            after = {row["path"]: sha((cwd / row["path"]).read_bytes())
                     for row in manifest["files"]}
            if after != before:
                raise Q3BoundaryError("Q4U public source changed during isolated check")
            import acceptance
            artefacts = acceptance.snapshot(cwd, task["editable_paths"])
            protected = acceptance.snapshot(
                cwd, sorted(set(task["actor_files"]) - set(task["editable_paths"])))
            proof = {"boundary": "fresh Q4U WSL namespace, uid 65534, no credentials",
                     "manifest_sha256": digest(manifest),
                     "artefacts_digest": artefacts["digest"],
                     "protected_digest": protected["digest"]}
            answer = subprocess.CompletedProcess(argv, process.returncode,
                                                 process.stdout, process.stderr)
            answer.isolation_evidence = {**proof, "sha256": digest(proof)}
            return answer
        finally:
            # A started but uncollected actor may have an uncertain writer.
            # Preserve its seed and actor for explicit recovery.
            if not staged or collected:
                if staged:
                    dispose(actor, ACTORS)
                    dispose(OUTPUTS / name, OUTPUTS)
                    for suffix in (".json", ".start.json", ".stop.json"):
                        (MANIFESTS / f"{name}{suffix}").unlink(missing_ok=True)
                dispose(package, SEEDS)
                manifest_path.unlink(missing_ok=True)
    return run


class Q4UWslAdapter(Q4TEvidenceMixin, Q3WslAdapter):
    """Attested Q4U subscription transport and structured receipt."""

    def capability(self, actor_root: Path) -> dict:
        check_q1()
        if os.geteuid() != 0 or not LAUNCHER.is_file() or not Q3_AUTH.is_file():
            raise CapabilityError("attested Q4U WSL root runtime is unavailable")
        if (actor_root.is_symlink() or actor_root.resolve().parent != SEEDS.resolve()
                or actor_root.stat().st_uid != 0 or actor_root.stat().st_mode & 0o077):
            raise CapabilityError("Q4U project must be a private root-owned seed")
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
                      max_single_call_usd=MAX_SINGLE_CALL_USD,
                      credential_method="subscription",
                      q4u_launcher_sha256=sha(LAUNCHER.read_bytes()),
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
            raise CapabilityError("Q4U request is outside the prospective evaluation contract")
        if len(cmd) != 20 or cmd[-1] != schema_argument():
            raise CapabilityError("Q4U command differs from the pinned report contract")
        linux_command = [*_linux_command(cmd[:-1]), cmd[-1]]
        package, manifest_path, manifest = public_source(root, self.task)
        name = "q1-" + request.invocation_id
        actor = ACTORS / name
        staged = stage(package, manifest_path, name)
        if staged["actor_root"] != str(actor):
            raise Q3BoundaryError("Q4U stage returned another actor")
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
                raise Q3BoundaryError("Q4U collection differs from staged actor")
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
        receipt = Q4TEvidenceMixin.run(self, request)
        contract = receipt["command_contract"]
        contract["requested_argv_sha256"] = digest(command)
        contract["argv_sha256"] = digest([*_linux_command(command[:-1]),
                                           command[-1]])
        boundary = self.last_boundary
        if boundary is not None:
            contract["q4u_boundary"] = boundary
            contract["transport"] = "wsl-q1-q4u-structured-subscription"
            contract["credential_method"] = "subscription"
            contract["filesystem_enforcement_proven"] = True
        contract["q4u_launcher_sha256"] = sha(LAUNCHER.read_bytes())
        contract["structured_retry_limit"] = 5
        if boundary is not None and "evaluation_report" in receipt:
            receipt["evaluation_report"]["binding"]["final_revision_sha256"] = digest(
                boundary["after_sha256"])
            receipt["evaluation_report_digest"] = digest(receipt["evaluation_report"])
        return receipt
