#!/usr/bin/env python3
"""Prospective schema-bound report transport for a new public worker screen.

The Q4 M3 receipts and grader remain immutable. This adapter is evaluation
only: production worker receipts still discard model-authored final text.
"""
from __future__ import annotations

import hashlib
import json

from worker_adapter import WorkerAdapter, WorkerRequest, digest
from worker_q4_adapter import EvaluationEvidenceMixin, _revision_digest
from worker_quality_v2 import REPORT_FIELDS, report_evidence


def report_schema() -> dict:
    """Use only schema features supported by Claude Code structured output.

    Byte, item and string bounds remain enforced by ``parse_report`` after
    delivery because the provider schema does not enforce those constraints.
    """
    string_list = {"type": "array", "items": {"type": "string"}}
    return {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["completed", "partial", "blocked"]},
            "diagnosis": {"type": "string"},
            "evidence": string_list,
            "checks": {"type": "array", "items": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "outcome": {"type": "string",
                                "enum": ["passed", "failed", "not_run"]},
                },
                "required": ["command", "outcome"],
                "additionalProperties": False,
            }},
            "remaining": string_list,
            "clarification": {"type": ["string", "null"]},
        },
        "required": sorted(REPORT_FIELDS),
        "additionalProperties": False,
    }


def schema_argument() -> str:
    return "--json-schema=" + json.dumps(report_schema(), sort_keys=True,
                                         separators=(",", ":"), ensure_ascii=False)


class StructuredEvaluationMixin(EvaluationEvidenceMixin):
    """Capture the CLI's validated structured_output with explicit provenance."""

    def command(self, request: WorkerRequest) -> list[str]:
        return [*super().command(request), schema_argument()]

    def _receipt_extensions(self, request: WorkerRequest, parsed: dict,
                            stdout: str) -> dict:
        root = request.actor_root.resolve()
        binding = {
            "invocation_id": request.invocation_id,
            "revision_id": request.revision_id,
            "final_revision_sha256": _revision_digest(root, request.allowed_edits),
            "stream_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
            "task_sha256": digest({"issue": request.issue,
                                   "allowed_edits": request.allowed_edits}),
            "prompt_sha256": hashlib.sha256(
                self.prompt(request).encode("utf-8")).hexdigest(),
            "requested_cell": request.requested_cell,
        }
        final = parsed.get("final") if isinstance(parsed, dict) else None
        valid_stream = (isinstance(final, dict) and final.get("type") == "result"
                        and parsed.get("invalid_line_count") == 0)
        structured = final.get("structured_output") if valid_stream else None
        valid_output = (valid_stream and final.get("subtype") == "success"
                        and isinstance(structured, dict))
        if valid_output:
            # This is a canonical encoding of the CLI's structured object, not
            # a claim that the model emitted these exact bytes on the wire.
            try:
                encoded = json.dumps(structured, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False)
            except (TypeError, ValueError):
                valid_output = False
                evidence = report_evidence(None, binding, transport_valid=False)
            else:
                evidence = report_evidence(encoded, binding)
        else:
            evidence = report_evidence(None, binding, transport_valid=False)
        raw_result = final.get("result") if valid_stream else None
        transport = {
            "mode": "claude-code-json-schema-v1",
            "schema_sha256": digest(report_schema()),
            "structured_output_present": valid_output,
            "result_subtype": final.get("subtype") if valid_stream else None,
            "raw_result_sha256": (hashlib.sha256(raw_result.encode("utf-8")).hexdigest()
                                  if isinstance(raw_result, str) else None),
            "canonicalised": valid_output,
        }
        return {"evaluation_report": evidence,
                "evaluation_report_digest": digest(evidence),
                "evaluation_transport": transport}


class StructuredEvaluationWorkerAdapter(StructuredEvaluationMixin, WorkerAdapter):
    """Provider-free test target; live WSL admission needs its own boundary."""
