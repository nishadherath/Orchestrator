#!/usr/bin/env python3
"""Q3 TaskExecutor adapter for a private WSL multi-file project.

The root process stages only the frozen public package. A provider call gets
one Q1 actor and one start/stop record. A terminal stream is not returned to
TaskExecutor until collection and the scoped write-back have both succeeded.
Any ambiguous process or copy leaves the root attempt uncertain and retains
the staged WSL evidence for reconciliation.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import resource
import subprocess
import tempfile
from pathlib import Path

from worker_adapter import CapabilityError, WorkerAdapter, WorkerRequest, digest
from worker_wsl_transport import _has_terminal_event, _linux_command
from worker_wsl_q1 import (ACTORS, MANIFESTS, OUTPUTS, SEEDS, MAX_FILE_BYTES,
                           MAX_TOTAL_BYTES, collect, path_parts, stage)
from worker_wsl_q2_verify import UncertainActorError, run_isolated

RUNTIME = Path("/opt/orchestrator-worker-runtime")
LAUNCHER = RUNTIME / "bin/worker-wsl-namespace-q3"
NODE = RUNTIME / "bin/node"
GRAFT = RUNTIME / "lib/node_modules/@nanonets/graft/dist/cli.js"
MCP = RUNTIME / "actor-mcp.json"
Q3_AUTH = RUNTIME / "worker_wsl_q3_auth.py"


class Q3BoundaryError(RuntimeError):
    """The Q3 actor or collection could not be proven safe."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cap_output() -> None:
    resource.setrlimit(resource.RLIMIT_FSIZE, (1_000_000, 1_000_000))


def cap_graph_output() -> None:
    """Allow a bounded graph file larger than the actor's ordinary output cap."""
    resource.setrlimit(resource.RLIMIT_FSIZE, (16_000_000, 16_000_000))


def public_source(project: Path, task: dict) -> tuple[Path, Path, dict]:
    """Copy the current public revision while enforcing frozen protected bytes."""
    expected = task["actor_files"]
    editable = set(task["editable_paths"])
    if (project.is_symlink() or not project.is_dir()
            or project.resolve().parent != SEEDS.resolve()
            or project.stat().st_uid != 0 or project.stat().st_mode & 0o077
            or len(expected) > 200
            or len(editable) < 2 or len(editable) > 8):
        raise Q3BoundaryError("public project or edit contract is invalid")
    package = Path(tempfile.mkdtemp(prefix="q3-public-", dir=SEEDS))
    manifest_path: Path | None = None
    try:
        rows = []
        total = 0
        for relative, original_sha in sorted(expected.items()):
            parts = path_parts(relative)
            for depth in range(1, len(parts)):
                if (project.joinpath(*parts[:depth])).is_symlink():
                    raise Q3BoundaryError(f"public path has a symlink parent: {relative}")
            source = project / relative
            if (source.is_symlink() or not source.is_file()
                    or source.stat().st_nlink != 1 or source.stat().st_size > MAX_FILE_BYTES):
                raise Q3BoundaryError(f"public file is missing or unsafe: {relative}")
            data = source.read_bytes()
            if relative not in editable and sha(data) != original_sha:
                raise Q3BoundaryError(f"protected public file drifted: {relative}")
            total += len(data)
            target = package.joinpath(*path_parts(relative))
            target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
            target.write_bytes(data)
            rows.append({"path": relative, "sha256": sha(data),
                         "editable": relative in editable})
        if total > MAX_TOTAL_BYTES or {row["path"] for row in rows if row["editable"]} != editable:
            raise Q3BoundaryError("public package exceeds Q1 contract")
        manifest = {"schema_version": 1, "files": rows}
        fd, raw = tempfile.mkstemp(prefix="q3-spec-", suffix=".json", dir=SEEDS)
        manifest_path = Path(raw)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(manifest, stream, sort_keys=True)
        return package, manifest_path, manifest
    except Exception:
        # Only this newly created private package is removed on failed input
        # preparation; no actor or provider process has yet been started.
        import shutil
        shutil.rmtree(package)
        if manifest_path is not None:
            manifest_path.unlink(missing_ok=True)
        raise


def build_actor_graph(actor: Path) -> None:
    """Build Graft inside the restricted namespace before the paid launch."""
    command = ["unshare", "--mount", "--pid", "--fork", "--kill-child", "--",
               str(LAUNCHER), "--inside", str(actor), "--", str(NODE), str(GRAFT),
               "build", str(actor)]
    result = subprocess.run(command, cwd="/", capture_output=True, text=True,
                            timeout=120, preexec_fn=cap_graph_output)
    if result.returncode:
        raise Q3BoundaryError("isolated Graft build failed: " + result.stderr[-300:])
    if not (actor / "graft").is_dir():
        raise Q3BoundaryError("isolated Graft build produced no graph")


def apply_collected(project: Path, task: dict, collected: dict, manifest: dict) -> None:
    """Commit only declared edits after rechecking both sides of the boundary."""
    output = Path(collected["output_root"])
    editable = set(task["editable_paths"])
    rows = {row["path"]: row for row in manifest["files"]}
    if (output.is_symlink() or output.resolve().parent != OUTPUTS.resolve()
            or set(collected["after_sha256"]) != set(rows)
            or not set(collected["changed_paths"]) <= editable):
        raise Q3BoundaryError("collected output inventory or edit scope differs")
    payload = {}
    for relative, row in sorted(rows.items()):
        parts = path_parts(relative)
        if any(project.joinpath(*parts[:depth]).is_symlink()
               for depth in range(1, len(parts))):
            raise Q3BoundaryError("public source parent changed during paid invocation")
        source = project / relative
        if (source.is_symlink() or not source.is_file()
                or source.stat().st_nlink != 1
                or sha(source.read_bytes()) != row["sha256"]):
            raise Q3BoundaryError("public source changed during paid invocation")
        if relative not in editable:
            continue
        target = output / relative
        if target.is_symlink() or not target.is_file():
            raise Q3BoundaryError("collected edit is unsafe")
        data = target.read_bytes()
        if len(data) > MAX_FILE_BYTES or sha(data) != collected["after_sha256"][relative]:
            raise Q3BoundaryError("collected edit digest differs")
        payload[relative] = data
    # Atomic per-file replacements may leave a partial multi-file revision if
    # the root host crashes. The corresponding task attempt remains uncertain;
    # no restart may dispatch it again without explicit reconciliation.
    for relative, data in payload.items():
        target = project / relative
        fd, raw = tempfile.mkstemp(prefix=".q3-edit-", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(raw, 0o644)
            os.replace(raw, target)
            directory = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            Path(raw).unlink(missing_ok=True)


def isolated_public_runner(task: dict):
    """Return an acceptance.verify runner with a fresh, sealed Q1 actor."""
    def run(argv: list[str], *, cwd: Path, capture_output: bool,
            timeout: float, shell: bool) -> subprocess.CompletedProcess:
        if (argv != ["python3", "-B", "public_check.py"] or capture_output is not True
                or shell is not False or timeout != 30):
            raise Q3BoundaryError("only the frozen public command is accepted")
        package, manifest_path, manifest = public_source(cwd, task)
        preserve_source = False
        try:
            before = {row["path"]: row["sha256"] for row in manifest["files"]}
            result = run_isolated(package, manifest_path, manifest,
                                  ["/usr/bin/python3", "-B", "public_check.py"])
            after = {row["path"]: sha((cwd / row["path"]).read_bytes())
                     for row in manifest["files"]}
            if after != before:
                raise Q3BoundaryError("public source changed during isolated check")
            import acceptance
            artefacts = acceptance.snapshot(cwd, task["editable_paths"])
            protected = acceptance.snapshot(
                cwd, sorted(set(task["actor_files"]) - set(task["editable_paths"])))
            proof = {"boundary": "fresh Q1 WSL namespace, uid 65534, no credentials",
                     "manifest_sha256": digest(manifest),
                     "artefacts_digest": artefacts["digest"],
                     "protected_digest": protected["digest"]}
            process = subprocess.CompletedProcess(argv, result.returncode,
                                                  result.stdout.encode(), result.stderr.encode())
            process.isolation_evidence = {**proof, "sha256": digest(proof)}
            return process
        except UncertainActorError:
            preserve_source = True
            raise
        finally:
            # This seed holds only copied public input; the isolated actor is
            # removed by run_isolated after its stopped-writer receipt. Keep
            # the source when the launcher stop is ambiguous.
            if not preserve_source:
                import shutil
                shutil.rmtree(package)
                manifest_path.unlink(missing_ok=True)
    return run


class Q3WslAdapter(WorkerAdapter):
    """Bridge one TaskExecutor worker attempt to a Q1 paid actor in WSL."""

    def __init__(self, task: dict):
        super().__init__(mcp_config=MCP)
        self.task = task
        self.last_boundary: dict | None = None

    def capability(self, actor_root: Path) -> dict:
        if os.geteuid() != 0 or not LAUNCHER.is_file() or not Q3_AUTH.is_file():
            raise CapabilityError("attested Q3 WSL root runtime is unavailable")
        if (actor_root.is_symlink() or actor_root.resolve().parent != SEEDS.resolve()
                or actor_root.stat().st_uid != 0 or actor_root.stat().st_mode & 0o077):
            raise CapabilityError("Q3 project must be a private root-owned seed")
        public_source_check = self.task["actor_files"]
        if not isinstance(public_source_check, dict):
            raise CapabilityError("frozen public inventory is unavailable")
        # This does not invoke a provider or duplicate a staged package.
        for relative, expected in public_source_check.items():
            parts = path_parts(relative)
            if any(actor_root.joinpath(*parts[:depth]).is_symlink()
                   for depth in range(1, len(parts))):
                raise CapabilityError(f"public path has a symlink parent: {relative}")
            source = actor_root / relative
            if source.is_symlink() or not source.is_file():
                raise CapabilityError(f"public file is unsafe: {relative}")
            if (relative not in self.task["editable_paths"]
                    and sha(source.read_bytes()) != expected):
                raise CapabilityError(f"protected public file drifted: {relative}")
        result = super().capability(actor_root)
        result.update(enforcement_proven=True, managed_delegation_enforced=True,
                      supported_cells=["worker-sonnet-low", "worker-opus-high"],
                      budget_enforced=True, max_single_call_usd=6.0,
                      credential_method="subscription",
                      q3_launcher_sha256=sha(LAUNCHER.read_bytes()))
        return result

    def _invoke(self, command: list[str], actor: Path,
                request: WorkerRequest) -> subprocess.CompletedProcess:
        """Only this method crosses the paid boundary; tests override it."""
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
                raise subprocess.TimeoutExpired(argv, request.timeout_s,
                                                stdout, stderr)
            return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)
        finally:
            with self._active_lock:
                self._active.pop(request.invocation_id, None)
                self._cancelled.discard(request.invocation_id)

    def _run_process(self, request: WorkerRequest, cmd: list[str], root: Path,
                     env: dict) -> subprocess.CompletedProcess:
        if (not re.fullmatch(r"[0-9a-f]{32}", request.invocation_id)
                or set(request.allowed_edits) != set(self.task["editable_paths"])
                or request.requested_cell not in {"worker-sonnet-low", "worker-opus-high"}):
            raise CapabilityError("Q3 request is outside the frozen B0 contract")
        linux_command = _linux_command(cmd)
        package, manifest_path, manifest = public_source(root, self.task)
        name = "q1-" + request.invocation_id
        actor = ACTORS / name
        staged = stage(package, manifest_path, name)
        if staged["actor_root"] != str(actor):
            raise Q3BoundaryError("Q1 stage returned another actor")
        build_actor_graph(actor)
        try:
            process = self._invoke(linux_command, actor, request)
        except subprocess.TimeoutExpired:
            raise
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
            # Preserve the provider stream, actor, source and budget hold. A
            # root callback must never see a completed attempt without an
            # exact collected multi-file revision.
            raise subprocess.TimeoutExpired(cmd, request.timeout_s,
                                            process.stdout, str(exc)) from exc
        return process

    def run(self, request: WorkerRequest) -> dict:
        self.last_boundary = None
        command = self.command(request)
        receipt = super().run(request)
        receipt["command_contract"]["requested_argv_sha256"] = digest(command)
        receipt["command_contract"]["argv_sha256"] = digest(_linux_command(command))
        if self.last_boundary is not None:
            receipt["command_contract"].update(
                q3_boundary=self.last_boundary,
                transport="wsl-q1-multifile-subscription",
                credential_method="subscription",
                filesystem_enforcement_proven=True)
        return receipt
