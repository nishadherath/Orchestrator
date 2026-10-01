#!/usr/bin/env python3
"""Q4S-only structured worker receipt with bounded transport diagnostics.

The production adapter and frozen Q4R evaluation keep their original receipt
contracts. This snapshot retains hashes and bounded event metadata, never
model text or stderr content.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import re
import subprocess
import time
from collections import Counter

import model_registry
from worker_adapter import (CapabilityError, WorkerAdapter, WorkerRequest,
                            digest, parse_stream)
from worker_q4r_structured import StructuredEvaluationMixin, schema_argument

MAX_TURNS = 20
STRUCTURED_RETRIES = 2
OUTPUT_TOKENS = 8192
_SAFE_CODE = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,79}\Z")
_SAFE_EVENT = re.compile(r"[a-z][a-z0-9_]{0,39}\Z")


def _text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value if isinstance(value, str) else ""


def _error_codes(final: dict) -> list[str]:
    """Retain machine codes only; CLI error messages can contain task text."""
    raw = final.get("errors")
    entries = raw if isinstance(raw, list) else [raw]
    found: set[str] = set()
    for entry in entries[:16]:
        candidates = ([entry.get(key) for key in ("code", "type", "error_type")]
                      if isinstance(entry, dict) else [])
        for candidate in candidates:
            if isinstance(candidate, str) and _SAFE_CODE.fullmatch(candidate):
                found.add(candidate)
    return sorted(found)[:8]


def transport_diagnostics(stdout: str, stderr: str, parsed: dict,
                          returncode: int, *, raw_stdout: bytes | None = None,
                          raw_stderr: bytes | None = None) -> dict:
    """Summarise one stream without retaining prompts, results or credentials."""
    counts: Counter[str] = Counter()
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        raw_type = event.get("type")
        event_type = (raw_type if isinstance(raw_type, str)
                      and _SAFE_EVENT.fullmatch(raw_type) else "other")
        if event_type not in counts and len(counts) >= 15:
            event_type = "other"
        counts[event_type] += 1
    final = parsed["final"]
    roots = parsed["root_models"]
    real_roots = [model for model in roots if model != "<synthetic>"]
    turns = final.get("num_turns")
    raw_usage = final.get("usage") if isinstance(final.get("usage"), dict) else {}
    reported_usage = {}
    for key in ("input_tokens", "cache_creation_input_tokens",
                "cache_read_input_tokens", "output_tokens"):
        value = raw_usage.get(key)
        if type(value) is int and value >= 0:
            reported_usage[key] = value
    stdout_bytes = raw_stdout if raw_stdout is not None else stdout.encode("utf-8")
    stderr_bytes = raw_stderr if raw_stderr is not None else stderr.encode("utf-8")
    return {
        "stdout_sha256": hashlib.sha256(stdout_bytes).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr_bytes).hexdigest(),
        "stdout_bytes": len(stdout_bytes),
        "stderr_bytes": len(stderr_bytes),
        "event_types": dict(sorted(counts.items())),
        "invalid_line_count": parsed["invalid_line_count"],
        "result_subtype": final.get("subtype")
        if isinstance(final.get("subtype"), str)
        and _SAFE_CODE.fullmatch(final["subtype"]) else None,
        "structured_output_field_present": "structured_output" in final,
        "error_codes": _error_codes(final),
        "num_turns": turns if type(turns) is int and turns >= 0 else None,
        "returncode": returncode,
        "real_root_models": real_roots,
        "synthetic_root_markers": [model for model in roots if model == "<synthetic>"],
        "child_models": parsed["child_models"],
        "billed_models": parsed["billed_models"],
        "reported_usage": reported_usage,
        "reported_cost_usd": final.get("total_cost_usd")
        if type(final.get("total_cost_usd")) in (int, float)
        and math.isfinite(final["total_cost_usd"]) else None,
    }


class Q4SEvidenceMixin(StructuredEvaluationMixin):
    """Keep Q4S diagnostics and treat an absent or invalid report as failure."""

    def command(self, request: WorkerRequest) -> list[str]:
        command = super().command(request)
        if command[-1] != schema_argument():
            raise CapabilityError("Q4S report schema is not the pinned contract")
        return command

    def run(self, request: WorkerRequest) -> dict:
        # A separate run path avoids changing the production and frozen Q4R
        # adapters, which discard stderr and additional final-event metadata.
        command = self.command(request)
        root = request.actor_root.resolve()
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root),
               "CLAUDE_CODE_MAX_OUTPUT_TOKENS": str(OUTPUT_TOKENS),
               "CLAUDE_CODE_MAX_TURNS": str(MAX_TURNS),
               "MAX_STRUCTURED_OUTPUT_RETRIES": str(STRUCTURED_RETRIES)}
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        tick = time.monotonic()
        timed_out = False
        try:
            process = (self.transport(command, root, env, request.timeout_s)
                       if self.transport else self._run_process(request, command, root, env))
            stdout, stderr = _text(process.stdout), _text(process.stderr)
            raw_stdout = process.stdout if isinstance(process.stdout, bytes) else None
            raw_stderr = process.stderr if isinstance(process.stderr, bytes) else None
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout, stderr = _text(exc.stdout), _text(exc.stderr)
            raw_stdout = exc.stdout if isinstance(exc.stdout, bytes) else None
            raw_stderr = exc.stderr if isinstance(exc.stderr, bytes) else None
            process = subprocess.CompletedProcess(command, 124, stdout, stderr)
        parsed = parse_stream(stdout)
        final = parsed["final"]
        raw_cost = final.get("total_cost_usd")
        cost = (raw_cost if type(raw_cost) in (int, float)
                and math.isfinite(raw_cost) and raw_cost >= 0 else None)
        diagnostics = transport_diagnostics(
            stdout, stderr, parsed, process.returncode,
            raw_stdout=raw_stdout, raw_stderr=raw_stderr)
        roots = diagnostics["real_root_models"]
        actual = roots[0] if len(roots) == 1 else None
        identity_valid = model_registry.identity_matches(
            request.requested_cell, actual, parsed["child_models"])
        terminal = not timed_out and final.get("type") == "result" and cost is not None
        cell = model_registry.resolve_cell(request.requested_cell)
        raw_usage = final.get("usage") if isinstance(final.get("usage"), dict) else {}
        usage = {key: raw_usage.get(key) for key in
                 ("input_tokens", "cache_creation_input_tokens",
                  "cache_read_input_tokens", "output_tokens")}
        usage.update(cost_usd=cost, currency="USD" if cost is not None else None,
                     cost_source="provider_reported" if cost is not None else "unknown")
        extensions = self._receipt_extensions(request, parsed, stdout)
        if not isinstance(extensions, dict) or "evaluation_report" not in extensions:
            raise CapabilityError("Q4S evaluation receipt extension is invalid")
        report = extensions.get("evaluation_report") or {}
        completed = (terminal and process.returncode == 0
                     and final.get("subtype") == "success" and identity_valid
                     and parsed["invalid_line_count"] == 0
                     and diagnostics["event_types"].get("result") == 1
                     and report.get("observability") == "present")
        receipt = {
            "admission_token": request.admission_token,
            "invocation_id": request.invocation_id,
            "revision_id": request.revision_id,
            "decision_digest": request.decision_digest,
            "intent_digest": request.intent_digest,
            "requested_cell": request.requested_cell,
            "requested_effort": cell["effort"],
            "served_effort": None,
            "effort_evidence": f"cli-argument:{cell['effort']}",
            "actual_model": actual,
            "identity_valid": identity_valid,
            "root_models": parsed["root_models"],
            "child_models": parsed["child_models"],
            "billed_models": parsed["billed_models"],
            "status": "interrupted" if not terminal else ("completed" if completed else "failed"),
            "terminal": terminal,
            "writer_stopped": terminal,
            "timed_out": timed_out,
            "returncode": process.returncode,
            "cost_usd": cost,
            "usage": usage,
            "started_at": started,
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "wall_clock_s": round(time.monotonic() - tick, 6),
            "stream": {"invalid_line_count": parsed["invalid_line_count"]},
            "command_contract": {"argv_sha256": digest(command), "restricted": True,
                                 "strict_mcp_config": True, "graft_configured": True,
                                 "filesystem_enforcement_proven": False},
            "q4s_diagnostics": diagnostics,
        }
        if not isinstance(extensions, dict) or set(extensions) & set(receipt):
            raise CapabilityError("Q4S receipt extensions are invalid")
        receipt.update(extensions)
        return receipt


class Q4SStructuredWorkerAdapter(Q4SEvidenceMixin, WorkerAdapter):
    """Fake-transport target; the live WSL adapter adds host enforcement."""
