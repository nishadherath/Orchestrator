#!/usr/bin/env python3
"""Evidence-bounded public assessment shared by worker and Controller policy.

The collector sees only explicitly listed actor-visible files. An interpreter
(deterministic or paid) receives this packet, never a benchmark family, split,
oracle or expected decision. This module validates cited classifications and
passes the same evidence to N3 and the rigour policy. X4 must supply the live
interpreter and charge its telemetry to the N1 root before routing; a fake
interpreter here does not qualify a Controller default or live comparison.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Callable

import controller_policy
import worker_selector

MAX_PUBLIC_FILES = 12
MAX_PUBLIC_BYTES = 32_000
MAX_CITATIONS = 32
WORKER_CLASSIFICATIONS = {"task_kind", "complexity", "verification",
                          "failure_cause", "frame_confidence"}
RIGOUR_CLASSIFICATIONS = {
    "consequence", "premise_uncertainty", "alternatives", "constraint_coupling",
    "verification_gap", "observed_failure_cause", "required_output",
    "evidence_availability",
}
CLASSIFICATIONS = WORKER_CLASSIFICATIONS | RIGOUR_CLASSIFICATIONS
DENIED_PARTS = {".git", ".claude", "test", "oracles", "oracle", "variants",
                "reference", "evaluator", "results"}


class PublicAssessmentError(ValueError):
    """Public input, citation, interpretation or accounting is incomplete."""


class PublicInterpreterError(PublicAssessmentError):
    """A failed provider call with any recoverable final or partial charge."""

    def __init__(self, message: str, *, cost_usd: float | None = None,
                 terminal: bool = False):
        if (cost_usd is not None and
                (type(cost_usd) not in (int, float) or not math.isfinite(cost_usd)
                 or cost_usd < 0)):
            raise ValueError("interpreter error cost must be finite and non-negative")
        if terminal and cost_usd is None:
            raise ValueError("terminal interpreter error needs a known charge")
        super().__init__(message)
        self.cost_usd = cost_usd
        self.terminal = terminal


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _public_relative(relative: object) -> bool:
    if (not isinstance(relative, str) or not relative
            or "\\" in relative or ":" in relative):
        return False
    path = Path(relative)
    parts = path.parts
    return (not path.is_absolute() and ".." not in parts and "." not in parts
            and not any(part.lower() in DENIED_PARTS for part in parts))


def _safe_file(root: Path, relative: str) -> Path:
    if (root.is_symlink() or not root.is_dir()
            or not _public_relative(relative)):
        raise PublicAssessmentError("public path is invalid")
    parts = Path(relative).parts
    target = root / relative
    if not target.resolve().is_relative_to(root.resolve()):
        raise PublicAssessmentError("public path escapes actor root")
    if any((root.joinpath(*parts[:depth])).is_symlink()
           for depth in range(1, len(parts) + 1)):
        raise PublicAssessmentError("public path contains a symlink")
    if not target.is_file() or target.stat().st_size > MAX_PUBLIC_BYTES:
        raise PublicAssessmentError("public source missing or oversized")
    return target


def collect(actor_root: Path, *, issue: str, source_paths: list[str],
            quote_requests: list[dict], input_revision: dict) -> dict:
    """Hash bounded public sources and locate exact, unique quoted lines."""
    if (not isinstance(source_paths, list) or not 1 <= len(source_paths) <= MAX_PUBLIC_FILES
            or any(not isinstance(path, str) for path in source_paths)
            or len(set(source_paths)) != len(source_paths) or issue not in source_paths
            or not isinstance(quote_requests, list)
            or not 1 <= len(quote_requests) <= MAX_CITATIONS
            or not isinstance(input_revision, dict)):
        raise PublicAssessmentError("public packet request is incomplete")
    sources = {}
    total_bytes = 0
    for relative in source_paths:
        path = _safe_file(actor_root, relative)
        raw = path.read_bytes()
        total_bytes += len(raw)
        if total_bytes > MAX_PUBLIC_BYTES:
            raise PublicAssessmentError("public packet exceeds byte ceiling")
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PublicAssessmentError("public source is not UTF-8") from exc
        sources[relative] = {"sha256": hashlib.sha256(raw).hexdigest(),
                             "content": content}
    citations = []
    seen = set()
    for request in quote_requests:
        if not isinstance(request, dict) or set(request) != {"source", "quote"}:
            raise PublicAssessmentError("citation request fields are invalid")
        relative, quote = request["source"], request["quote"]
        if (not isinstance(relative, str) or relative not in sources
                or not isinstance(quote, str)
                or not quote.strip() or "\n" in quote):
            raise PublicAssessmentError("citation is not a public source line")
        matches = [(number, line) for number, line in enumerate(
            sources[relative]["content"].splitlines(), 1) if quote in line]
        if len(matches) != 1 or (relative, quote) in seen:
            raise PublicAssessmentError("citation is absent, ambiguous or duplicated")
        seen.add((relative, quote))
        number, line = matches[0]
        citations.append({"id": f"e{len(citations) + 1}", "source": relative,
                          "line": number, "quote": line,
                          "sha256": sources[relative]["sha256"]})
    goal = sources[issue]["content"]
    body = {"schema_version": 2, "issue_path": issue,
            "task_revision": controller_policy.derive_task_revision(
                goal, actor_root, input_revision),
            "sources": [{"path": relative, "sha256": value["sha256"],
                         "content": value["content"]}
                        for relative, value in sources.items()],
            "citations": citations}
    body["packet_sha256"] = _digest(body)
    return body


def _operational(value: dict) -> dict:
    required = {"context_tokens", "deadline_seconds", "prior_local_repairs",
                "required_artefacts", "deadline", "authorised_task_budget_usd",
                "observed_at"}
    if not isinstance(value, dict) or set(value) != required:
        raise PublicAssessmentError("operational facts must match the N1 root")
    # N3 and rigour validators check the individual values; this bridge also
    # requires an explicit observation time for source-backed evidence.
    if not isinstance(value["observed_at"], str) or not value["observed_at"].strip():
        raise PublicAssessmentError("public observation time is missing")
    return value


def _validate_packet(packet: object) -> dict:
    """Recheck source bytes and citations even when assess() is called directly."""
    if (not isinstance(packet, dict) or set(packet) != {
            "schema_version", "issue_path", "task_revision", "sources",
            "citations", "packet_sha256"} or packet.get("schema_version") != 2
            or not _public_relative(packet["issue_path"])
            or not isinstance(packet["task_revision"], str)
            or len(packet["task_revision"]) != 64
            or any(char not in "0123456789abcdef" for char in packet["task_revision"])
            or not isinstance(packet["sources"], list)
            or not 1 <= len(packet["sources"]) <= MAX_PUBLIC_FILES
            or not isinstance(packet["citations"], list)
            or not 1 <= len(packet["citations"]) <= MAX_CITATIONS):
        raise PublicAssessmentError("public packet schema is invalid")
    sources = {}
    total_bytes = 0
    for row in packet["sources"]:
        if (not isinstance(row, dict) or set(row) != {"path", "sha256", "content"}
                or not _public_relative(row["path"])
                or row["path"] in sources
                or not isinstance(row["content"], str)
                or not isinstance(row["sha256"], str)):
            raise PublicAssessmentError("public source record is invalid")
        raw = row["content"].encode("utf-8")
        total_bytes += len(raw)
        if (total_bytes > MAX_PUBLIC_BYTES
                or hashlib.sha256(raw).hexdigest() != row["sha256"]):
            raise PublicAssessmentError("public source digest or byte ceiling is invalid")
        sources[row["path"]] = row
    if packet["issue_path"] not in sources:
        raise PublicAssessmentError("public issue source is missing")
    seen = set()
    for number, row in enumerate(packet["citations"], 1):
        if (not isinstance(row, dict)
                or set(row) != {"id", "source", "line", "quote", "sha256"}
                or row["id"] != f"e{number}"
                or not isinstance(row["source"], str)
                or row["source"] not in sources
                or type(row["line"]) is not int
                or not isinstance(row["quote"], str)
                or not row["quote"].strip()
                or row["sha256"] != sources[row["source"]]["sha256"]
                or (row["source"], row["line"]) in seen):
            raise PublicAssessmentError("public citation is invalid")
        lines = sources[row["source"]]["content"].splitlines()
        if not 1 <= row["line"] <= len(lines) or lines[row["line"] - 1] != row["quote"]:
            raise PublicAssessmentError("public citation no longer matches source")
        seen.add((row["source"], row["line"]))
    if packet["packet_sha256"] != _digest({
            key: value for key, value in packet.items() if key != "packet_sha256"}):
        raise PublicAssessmentError("public packet digest is invalid")
    return packet


def assess(packet: dict, interpretation: dict, operational: dict,
           telemetry: dict) -> dict:
    """Validate one cited interpretation and call both production validators."""
    packet = _validate_packet(packet)
    if (not isinstance(interpretation, dict) or set(interpretation) != {
            "schema_version", "classifications", "field_evidence", "material_evidence"}
            or interpretation["schema_version"] != 1
            or not isinstance(interpretation["classifications"], dict)
            or set(interpretation["classifications"]) != CLASSIFICATIONS
            or not isinstance(interpretation["field_evidence"], dict)
            or set(interpretation["field_evidence"]) != CLASSIFICATIONS):
        raise PublicAssessmentError("interpreter returned missing or hidden fields")
    citations = {row["id"]: row for row in packet["citations"]}
    material = interpretation["material_evidence"]
    if (not isinstance(material, list)
            or any(not isinstance(ident, str) for ident in material)
            or len(set(material)) != len(material)
            or any(ident not in citations for ident in material)):
        raise PublicAssessmentError("materiality must cite public evidence")
    for field, ids in interpretation["field_evidence"].items():
        if (not isinstance(ids, list) or not ids
                or any(not isinstance(ident, str) for ident in ids)
                or len(set(ids)) != len(ids)
                or any(ident not in citations for ident in ids)):
            raise PublicAssessmentError(f"{field} lacks verifiable public evidence")
    telemetry = validate_telemetry(telemetry)
    operational = _operational(operational)
    classified = interpretation["classifications"]
    used = sorted({ident for ids in interpretation["field_evidence"].values()
                   for ident in ids})
    worker_evidence = [{"source": "repository", "reference":
                        f"{citations[ident]['source']}:{citations[ident]['line']}:"
                        f"{citations[ident]['sha256']}",
                        "claim": citations[ident]["quote"]} for ident in used]
    worker = worker_selector.assess({
        **{name: classified[name] for name in WORKER_CLASSIFICATIONS},
        "context_tokens": operational["context_tokens"],
        "deadline_seconds": operational["deadline_seconds"],
        "prior_local_repairs": operational["prior_local_repairs"],
        "required_artefacts": operational["required_artefacts"],
        "evidence": worker_evidence,
    })
    provenance = ("model-inference" if telemetry["provider_calls"] else
                  "repository-artefact")
    rigour_evidence = [{"id": ident, "provenance": provenance,
                        "observed_at": operational["observed_at"],
                        "scope": f"{citations[ident]['source']}:{citations[ident]['line']}:"
                                 f"{citations[ident]['sha256']}",
                        "claim": citations[ident]["quote"][:600],
                        "material": ident in material} for ident in used]
    rigour = controller_policy.validate_assessment({
        "assessment_version": 1, "task_revision": packet["task_revision"],
        **{name: classified[name] for name in RIGOUR_CLASSIFICATIONS},
        "deadline": operational["deadline"],
        "authorised_task_budget_usd": operational["authorised_task_budget_usd"],
        "evidence": rigour_evidence,
    })
    body = {"schema_version": 1, "packet_sha256": packet["packet_sha256"],
            "interpretation_sha256": _digest(interpretation),
            "worker": worker, "rigour": rigour, "telemetry": telemetry}
    body["assessment_sha256"] = _digest(body)
    return body


def validate_telemetry(telemetry: object) -> dict:
    """Validate a terminal charge independently of interpretation quality."""
    if (not isinstance(telemetry, dict) or set(telemetry) != {
            "provider_calls", "model", "cost_usd", "input_tokens", "output_tokens"}
            or type(telemetry["provider_calls"]) is not int
            or telemetry["provider_calls"] not in {0, 1}
            or type(telemetry["cost_usd"]) not in {int, float}
            or not math.isfinite(telemetry["cost_usd"])
            or telemetry["cost_usd"] < 0
            or any(type(telemetry[key]) is not int or telemetry[key] < 0
                   for key in ("input_tokens", "output_tokens"))
            or (telemetry["provider_calls"] == 0 and (
                telemetry["model"] is not None or telemetry["cost_usd"] != 0))
            or (telemetry["provider_calls"] == 1 and
                (not isinstance(telemetry["model"], str)
                   or not telemetry["model"].strip()))):
        raise PublicAssessmentError("assessment cost or model identity is uncertain")
    return telemetry


def assess_with(actor_root: Path, *, issue: str, source_paths: list[str],
                quote_requests: list[dict], input_revision: dict,
                interpreter: Callable[[dict], dict], operational: dict) -> dict:
    """Collect inside the trusted boundary, then call one interpreter once."""
    packet = collect(actor_root, issue=issue, source_paths=source_paths,
                     quote_requests=quote_requests,
                     input_revision=input_revision)
    result = interpreter(packet)
    if not isinstance(result, dict) or set(result) != {"interpretation", "telemetry"}:
        raise PublicAssessmentError("interpreter response fields are invalid")
    return assess(packet, result["interpretation"], operational,
                  result["telemetry"])
