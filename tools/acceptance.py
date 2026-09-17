#!/usr/bin/env python3
"""Freeze acceptance contracts and bind verification to exact artefacts.

Standard-library only. Commands are argument vectors and never use a shell.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

CONTRACT_VERSION = "acceptance-v2"
MAX_CAPTURE_CHARS = 20_000


class AcceptanceError(RuntimeError):
    """The contract or its evidence is unsafe, malformed or inconsistent."""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False).encode("utf-8") + b"\n"
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        tmp.replace(path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise


def _strings(value: object, name: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise AcceptanceError(f"{name} must be a {'possibly empty ' if allow_empty else 'non-empty '}array")
    if any(not isinstance(item, str) or not item.strip() or len(item) > 500 for item in value):
        raise AcceptanceError(f"{name} values must be non-empty strings of at most 500 characters")
    return [item.strip() for item in value]


def _relative(project: Path, raw: str) -> tuple[str, Path]:
    candidate = Path(raw)
    if candidate.is_absolute():
        raise AcceptanceError(f"acceptance path {raw!r} must be project-relative")
    project = project.resolve()
    resolved = (project / candidate).resolve(strict=False)
    try:
        relative = resolved.relative_to(project).as_posix()
    except ValueError as exc:
        raise AcceptanceError(f"acceptance path {raw!r} escapes the project") from exc
    if relative in ("", "."):
        raise AcceptanceError("the project root is too broad for an acceptance path")
    return relative, resolved


def _normalise_paths(project: Path, values: object, name: str, *, allow_empty: bool = False) -> list[str]:
    return [_relative(project, raw)[0] for raw in _strings(values, name, allow_empty=allow_empty)]


def load_contract(project: Path, path: Path) -> dict:
    """Validate and freeze a command or rubric contract before dispatch."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AcceptanceError(f"cannot read acceptance contract {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise AcceptanceError("acceptance contract must be a JSON object")
    allowed = {"version", "kind", "criteria", "constraints", "required_outputs",
               "protected_paths", "command", "rubric", "timeout_s"}
    unknown = set(raw) - allowed
    if unknown:
        raise AcceptanceError(f"acceptance contract has unsupported field(s) {sorted(unknown)}")
    if raw.get("version") != 1 or raw.get("kind") not in ("command", "rubric"):
        raise AcceptanceError("acceptance contract needs version 1 and kind command or rubric")
    kind = raw["kind"]
    command = _strings(raw.get("command", []), "command", allow_empty=kind == "rubric")
    rubric = _strings(raw.get("rubric", []), "rubric", allow_empty=kind == "command")
    if kind == "command" and rubric:
        raise AcceptanceError("a command contract cannot also carry a rubric")
    if kind == "rubric" and command:
        raise AcceptanceError("a rubric contract cannot also carry a command")
    timeout = raw.get("timeout_s", 300)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 3600:
        raise AcceptanceError("timeout_s must be a positive number no greater than 3600")
    contract = {
        "version": 1, "kind": kind,
        "criteria": _strings(raw.get("criteria"), "criteria"),
        "constraints": _strings(raw.get("constraints", []), "constraints", allow_empty=True),
        "required_outputs": _normalise_paths(project, raw.get("required_outputs"), "required_outputs"),
        "protected_paths": _normalise_paths(project, raw.get("protected_paths", []),
                                              "protected_paths", allow_empty=True),
        "command": command, "rubric": rubric, "timeout_s": float(timeout),
    }
    baseline = snapshot(project, contract["protected_paths"])
    if baseline["missing"]:
        raise AcceptanceError(f"protected paths are missing before dispatch: {baseline['missing']}")
    return {"status": "pending", "contract_version": CONTRACT_VERSION,
            "contract": contract, "contract_digest": digest(contract),
            "protected_baseline": baseline, "evidence": None, "review": None}


def snapshot(project: Path, paths: list[str]) -> dict:
    """Hash every named file and every file below named directories."""
    files: list[dict] = []
    missing: list[str] = []
    for raw in paths:
        relative, resolved = _relative(project, raw)
        if not resolved.exists():
            missing.append(relative)
            continue
        candidates = [resolved] if resolved.is_file() else sorted(p for p in resolved.rglob("*") if p.is_file())
        if resolved.is_dir() and not candidates:
            files.append({"path": relative + "/", "sha256": hashlib.sha256(b"").hexdigest(), "size": 0})
        for candidate in candidates:
            actual = candidate.resolve(strict=True)
            try:
                rel = actual.relative_to(project.resolve()).as_posix()
            except ValueError as exc:
                raise AcceptanceError(f"acceptance file {candidate} resolves outside the project") from exc
            data = actual.read_bytes()
            files.append({"path": rel, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)})
    files.sort(key=lambda row: row["path"])
    return {"files": files, "missing": sorted(set(missing)),
            "digest": digest({"files": files, "missing": sorted(set(missing))})}


def _revision(project: Path) -> dict:
    def git(*args: str) -> str | None:
        try:
            proc = subprocess.run(["git", "-c", f"safe.directory={project.resolve()}", "-C", str(project), *args],
                                  capture_output=True, timeout=20)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return proc.stdout.decode("utf-8", errors="replace") if proc.returncode == 0 else None
    head = git("rev-parse", "HEAD")
    diff = git("diff", "--binary", "HEAD", "--")
    status = git("status", "--porcelain=v1", "--untracked-files=all")
    return {"head": head.strip() if head else None,
            "diff_sha256": hashlib.sha256((diff or "").encode("utf-8")).hexdigest() if diff is not None else None,
            "status_sha256": hashlib.sha256((status or "").encode("utf-8")).hexdigest() if status is not None else None}


def _evidence_path(project: Path, entry_id: str) -> Path:
    safe = "".join(ch for ch in entry_id if ch.isalnum() or ch in "-_")
    if not safe or safe != entry_id:
        raise AcceptanceError(f"unsafe ledger id {entry_id!r}")
    return project.resolve() / ".claude" / "acceptance" / f"{safe}.json"


def _result_valid(project: Path, acceptance: dict, result: dict) -> bool:
    recorded_sha = result.get("sha256")
    unsigned = {key: value for key, value in result.items() if key != "sha256"}
    if not isinstance(recorded_sha, str) or digest(unsigned) != recorded_sha:
        return False
    if result.get("contract_digest") != acceptance.get("contract_digest"):
        return False
    evidence = result.get("acceptance")
    if not isinstance(evidence, dict):
        return False
    current = snapshot(project, acceptance["contract"]["required_outputs"])
    protected = snapshot(project, acceptance["contract"]["protected_paths"])
    return (current["digest"] == (evidence.get("evidence") or {}).get("artefacts", {}).get("digest")
            and protected["digest"] == (evidence.get("evidence") or {}).get("protected", {}).get("digest"))


def verify(project: Path, acceptance: dict, entry_id: str) -> dict:
    """Run or stage review once, persisting evidence before ledger completion."""
    contract = acceptance.get("contract") or {}
    if digest(contract) != acceptance.get("contract_digest"):
        raise AcceptanceError("stored acceptance contract digest does not match its content")
    result_path = _evidence_path(project, entry_id)
    if result_path.is_file():
        try:
            prior = json.loads(result_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            prior = None
        if isinstance(prior, dict) and _result_valid(project, acceptance, prior):
            return prior["acceptance"]

    started = utc_now()
    command_result = {"argv": contract["command"], "exit_code": None,
                      "stdout": "", "stderr": "", "timed_out": False}
    blocked_reason = None
    if contract["kind"] == "command":
        try:
            proc = subprocess.run(contract["command"], cwd=project, capture_output=True,
                                  timeout=contract["timeout_s"], shell=False)
            command_result.update(exit_code=proc.returncode,
                                  stdout=proc.stdout.decode("utf-8", errors="replace")[-MAX_CAPTURE_CHARS:],
                                  stderr=proc.stderr.decode("utf-8", errors="replace")[-MAX_CAPTURE_CHARS:])
        except subprocess.TimeoutExpired as exc:
            command_result.update(timed_out=True,
                                  stdout=(exc.stdout or b"").decode("utf-8", errors="replace")[-MAX_CAPTURE_CHARS:],
                                  stderr=(exc.stderr or b"").decode("utf-8", errors="replace")[-MAX_CAPTURE_CHARS:])
            blocked_reason = "verification timed out"
        except OSError as exc:
            blocked_reason = f"verification could not start: {exc}"

    artefacts = snapshot(project, contract["required_outputs"])
    protected = snapshot(project, contract["protected_paths"])
    protected_unchanged = protected["digest"] == acceptance["protected_baseline"]["digest"]
    if contract["kind"] == "rubric":
        status = "review_required"
    elif blocked_reason:
        status = "blocked"
    elif command_result["exit_code"] == 0 and not artefacts["missing"] and protected_unchanged:
        status = "pass"
    else:
        status = "fail"
    evidence = {"kind": contract["kind"], "started_at": started, "finished_at": utc_now(),
                "command": command_result if contract["kind"] == "command" else None,
                "artefacts": artefacts, "protected": protected,
                "protected_unchanged": protected_unchanged,
                "revision": _revision(project), "blocked_reason": blocked_reason,
                "result_path": _evidence_path(project, entry_id).relative_to(project.resolve()).as_posix()}
    evidence["result_digest"] = digest(evidence)
    resolved = {**acceptance, "status": status, "evidence": evidence}
    payload = {"version": 1, "entry_id": entry_id,
               "contract_digest": acceptance["contract_digest"], "acceptance": resolved}
    payload["sha256"] = digest(payload)
    _atomic_json(result_path, payload)
    return resolved


def review(project: Path, acceptance: dict, entry_id: str, decision: str,
           reviewer: str, notes: str = "") -> dict:
    """Settle rubric evidence with explicit human provenance."""
    if decision not in ("pass", "fail") or not reviewer.strip():
        raise AcceptanceError("review needs pass or fail and a non-empty reviewer")
    if (acceptance.get("contract") or {}).get("kind") != "rubric":
        raise AcceptanceError("only rubric contracts accept a human review")
    if digest(acceptance["contract"]) != acceptance.get("contract_digest"):
        raise AcceptanceError("stored acceptance contract digest does not match its content")
    existing = acceptance.get("review")
    proposed = {"decision": decision, "reviewer": reviewer.strip(), "notes": notes[:1000]}
    if existing:
        if all(existing.get(key) == value for key, value in proposed.items()):
            return acceptance
        raise AcceptanceError("acceptance review is already settled with different evidence")
    current = snapshot(project, acceptance["contract"]["required_outputs"])
    protected = snapshot(project, acceptance["contract"]["protected_paths"])
    if current["missing"] or protected["digest"] != acceptance["protected_baseline"]["digest"]:
        decision = "fail"
    proposed.update(decision=decision, reviewed_at=utc_now(), artefacts=current,
                    protected=protected, revision=_revision(project),
                    result_path=_evidence_path(project, entry_id).relative_to(project.resolve()).as_posix())
    proposed["result_digest"] = digest(proposed)
    resolved = {**acceptance, "status": decision, "review": proposed}
    path = _evidence_path(project, entry_id)
    payload = {"version": 1, "entry_id": entry_id,
               "contract_digest": acceptance["contract_digest"], "acceptance": resolved}
    payload["sha256"] = digest(payload)
    _atomic_json(path, payload)
    return resolved


def qualified(value: object) -> bool:
    """Return whether evidence may train capability, without trusting a flag."""
    if not isinstance(value, dict) or value.get("status") not in ("pass", "fail"):
        return False
    contract = value.get("contract")
    if not isinstance(contract, dict) or value.get("contract_version") != CONTRACT_VERSION:
        return False
    if digest(contract) != value.get("contract_digest"):
        return False
    evidence = value.get("evidence")
    review_value = value.get("review")
    if contract.get("kind") == "command":
        if not (isinstance(evidence, dict) and evidence.get("kind") == "command"
                and isinstance(evidence.get("artefacts"), dict)
                and isinstance(evidence.get("protected"), dict)):
            return False
        recorded = evidence.get("result_digest")
        unsigned = {key: item for key, item in evidence.items() if key != "result_digest"}
        if not isinstance(recorded, str) or digest(unsigned) != recorded:
            return False
        command = evidence.get("command") or {}
        passed = (command.get("exit_code") == 0 and not command.get("timed_out")
                  and not evidence["artefacts"].get("missing")
                  and evidence.get("protected_unchanged") is True
                  and not evidence.get("blocked_reason"))
        failed = (isinstance(command.get("exit_code"), int)
                  and (command["exit_code"] != 0 or bool(evidence["artefacts"].get("missing"))
                       or evidence.get("protected_unchanged") is not True))
        return passed if value["status"] == "pass" else failed
    if contract.get("kind") != "rubric" or not isinstance(review_value, dict):
        return False
    recorded = review_value.get("result_digest")
    unsigned = {key: item for key, item in review_value.items() if key != "result_digest"}
    return (isinstance(recorded, str) and digest(unsigned) == recorded
            and review_value.get("decision") == value.get("status")
            and bool(review_value.get("reviewer")))


def diagnostic(project: Path, entry: dict) -> list[str]:
    """Describe the exact next action for incomplete or stale acceptance."""
    value = entry.get("acceptance") or {}
    ident = entry.get("id", "(unknown)")
    status = value.get("status", "missing")
    if entry.get("final_outcome") == "unknown":
        orphan = _evidence_path(project, ident)
        suffix = f"; reusable evidence exists at {orphan.relative_to(project.resolve())}" if orphan.is_file() else ""
        return [f"{ident}: execution pending; complete with route.py --record --pending {ident}{suffix}"]
    if status == "review_required":
        return [f"{ident}: human review required; use route.py --review-acceptance {ident} --review-decision pass|fail --reviewer <name>"]
    if status in ("blocked", "pending", "unverified", "missing"):
        reason = (value.get("evidence") or {}).get("blocked_reason")
        return [f"{ident}: acceptance {status}; {reason or 'inspect the contract and rerun completion'}"]
    return []
