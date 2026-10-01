#!/usr/bin/env python3
"""Evaluation-only adapter mixin that retains one bounded final report."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from worker_adapter import WorkerAdapter, WorkerRequest, digest
from worker_quality_v2 import report_evidence


REPORT_INSTRUCTION = """
Return only one JSON object as your final response with exactly these fields:
status (completed, partial, or blocked), diagnosis (string), evidence (list of
strings), checks (list of {command, outcome}, where outcome is passed, failed,
or not_run), remaining (list of strings), and clarification (string or null).
Keep the encoded JSON at or below 16 KiB. Report only checks actually run.
""".strip()


def _revision_digest(root: Path, allowed: tuple[str, ...]) -> str:
    rows = {}
    for relative in sorted(allowed):
        path = root / relative
        rows[relative] = (hashlib.sha256(path.read_bytes()).hexdigest()
                          if path.is_file() and not path.is_symlink() else None)
    return digest(rows)


class EvaluationEvidenceMixin:
    """Add report capture while leaving the ordinary adapter receipt unchanged."""

    @staticmethod
    def prompt(request: WorkerRequest) -> str:
        return WorkerAdapter.prompt(request) + "\n\nFinal report contract:\n" + REPORT_INSTRUCTION

    def _receipt_extensions(self, request: WorkerRequest, parsed: dict,
                            stdout: str) -> dict:
        root = request.actor_root.resolve()
        binding = {"invocation_id": request.invocation_id,
                   "revision_id": request.revision_id,
                   "final_revision_sha256": _revision_digest(root, request.allowed_edits),
                   "stream_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
                   "task_sha256": digest({"issue": request.issue,
                                           "allowed_edits": request.allowed_edits}),
                   "prompt_sha256": hashlib.sha256(
                       self.prompt(request).encode("utf-8")).hexdigest(),
                   "requested_cell": request.requested_cell}
        final = parsed.get("final") if isinstance(parsed, dict) else None
        transport_valid = (isinstance(final, dict) and final.get("type") == "result"
                           and parsed.get("invalid_line_count") == 0)
        raw = final.get("result") if transport_valid else None
        evidence = report_evidence(raw, binding, transport_valid=transport_valid)
        return {"evaluation_report": evidence,
                "evaluation_report_digest": digest(evidence)}


class EvaluationWorkerAdapter(EvaluationEvidenceMixin, WorkerAdapter):
    """Provider adapter for fake-tested Q4 report capture."""
