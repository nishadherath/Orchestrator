"""X5-only Q3 transport with the three N3 prior cells.

Q3's historical B0 adapter stays byte-for-byte unchanged. This extension
uses the same isolated actor, credential and collection boundary, but admits
Sonnet High when N3's moderate-task prior selects it. Live use still needs a
served-model canary; capability alone is not an identity attestation.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import worker_wsl_q3_adapter as q3
from worker_adapter import CapabilityError, WorkerRequest


SUPPORTED_CELLS = frozenset({
    "worker-sonnet-low", "worker-sonnet-high", "worker-opus-high",
})


class X5WslAdapter(q3.Q3WslAdapter):
    """Single-call experimental N3 host, pinned to Q3's isolation boundary."""

    def capability(self, actor_root: Path) -> dict:
        result = super().capability(actor_root)
        result["supported_cells"] = sorted(SUPPORTED_CELLS)
        result["experimental_host_profile"] = "x5-n3-three-cell-v1"
        return result

    def _run_process(self, request: WorkerRequest, cmd: list[str], root: Path,
                     env: dict) -> subprocess.CompletedProcess:
        # Q3's B0-only guard is intentionally retained in its source. Keep
        # this small fork isolated to X5 so old source-bound attestations
        # remain valid; all staging and collection helpers are the Q3 ones.
        if (not re.fullmatch(r"[0-9a-f]{32}", request.invocation_id)
                or set(request.allowed_edits) != set(self.task["editable_paths"])
                or request.requested_cell not in SUPPORTED_CELLS):
            raise CapabilityError("X5 request is outside the frozen N3 host profile")
        linux_command = q3._linux_command(cmd)
        package, manifest_path, manifest = q3.public_source(root, self.task)
        name = "q1-" + request.invocation_id
        actor = q3.ACTORS / name
        staged = q3.stage(package, manifest_path, name)
        if staged["actor_root"] != str(actor):
            raise q3.Q3BoundaryError("Q1 stage returned another actor")
        q3.build_actor_graph(actor)
        try:
            process = self._invoke(linux_command, actor, request)
        except subprocess.TimeoutExpired:
            raise
        if not q3._has_terminal_event(process.stdout):
            return process
        try:
            collected = q3.collect(name, package)
            if (collected["record_sha256"] != staged["record_sha256"]
                    or collected["spec_sha256"] != staged["spec_sha256"]):
                raise q3.Q3BoundaryError("Q1 collection differs from staged actor")
            q3.apply_collected(root, self.task, collected, manifest)
            self.last_boundary = {
                "actor_name": name,
                "q1_record_sha256": staged["record_sha256"],
                "q1_spec_sha256": staged["spec_sha256"],
                "changed_paths": collected["changed_paths"],
                "after_sha256": collected["after_sha256"],
            }
        except (OSError, ValueError, KeyError, q3.Q3BoundaryError) as exc:
            raise subprocess.TimeoutExpired(cmd, request.timeout_s,
                                            process.stdout, str(exc)) from exc
        return process
