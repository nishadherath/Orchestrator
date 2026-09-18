#!/usr/bin/env python3
"""Claude Code attempt adapter for real-world evaluation episodes.

This module owns one model attempt only.  It builds a restricted, exact-model
Claude CLI invocation, attributes model identity from stream messages, retains
aggregate billing (including auxiliary models), and represents incomplete
telemetry as unknown.  Policy sequencing and durable episode recovery remain
the evaluation runner's responsibility.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "test" / "harness"))

import model_registry  # noqa: E402
import realworld  # noqa: E402

CALIBRATION = ROOT / "test" / "results" / "2026-09-17-live-calibration-adjudication.json"
ORIGINAL_CALIBRATION = ROOT / "test" / "results" / "2026-09-17-live-calibration.json"
DEFAULT_OUTPUT = ROOT / "test" / "results" / "2026-09-17-live-worker-adapter.json"
DEFAULT_REPORT = ROOT / "test" / "results" / "2026-09-17-live-worker-adapter.md"
USAGE_FIELDS = (
    "input_tokens", "cache_creation_input_tokens",
    "cache_read_input_tokens", "output_tokens",
)
Transport = Callable[[list[str], Path, dict[str, str], float], subprocess.CompletedProcess]


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_number(value: object) -> float | int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(value) and value >= 0 else None


def cell_identity(cell: str) -> tuple[str, str]:
    resolved = model_registry.resolve_cell(cell)
    return resolved["cli_model"], resolved["effort"]


@dataclasses.dataclass(frozen=True)
class WorkerRequest:
    actor_root: Path
    issue: str
    allowed_edits: tuple[str, ...]
    requested_cell: str
    allowance_usd: float
    policy: str
    timeout_s: float = 900.0


def parse_stream(text: str) -> dict:
    events: list[dict] = []
    invalid = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            invalid += 1
            continue
        if isinstance(row, dict):
            events.append(row)
        else:
            invalid += 1
    root_models: set[str] = set()
    child_models: set[str] = set()
    final: dict = {}
    for event in events:
        if event.get("type") == "assistant" and isinstance(event.get("message"), dict):
            model = event["message"].get("model")
            if isinstance(model, str) and model:
                (child_models if event.get("parent_tool_use_id") else root_models).add(model)
        if event.get("type") == "result":
            final = event
    billed = final.get("modelUsage", final.get("model_usage", {}))
    billed_models = sorted(billed) if isinstance(billed, dict) else []
    return {
        "event_count": len(events), "invalid_line_count": invalid,
        "root_models": sorted(root_models), "child_models": sorted(child_models),
        "billed_models": billed_models,
        "auxiliary_billed_models": sorted(set(billed_models) - root_models - child_models),
        "final": final,
    }


def _default_transport(cmd: list[str], cwd: Path, env: dict[str, str],
                       timeout: float) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                          encoding="utf-8", timeout=timeout)


class LiveWorkerAdapter:
    """Run one restricted Claude coding attempt through an injectable transport."""

    def __init__(self, transport: Transport | None = None):
        self.transport = transport or _default_transport

    @staticmethod
    def prompt(request: WorkerRequest) -> str:
        allowed = "\n".join(f"- {path}" for path in request.allowed_edits)
        return (
            "Solve the issue in the current working directory. Work only on the allowed files. "
            "Do not inspect parent directories, hidden evaluation material, or network resources. "
            "Finish after making the smallest complete repair.\n\n"
            f"Policy for this attempt:\n{request.policy.strip()}\n\n"
            f"Allowed edits:\n{allowed}\n\nIssue:\n{request.issue.strip()}\n"
        )

    @staticmethod
    def command(request: WorkerRequest) -> list[str]:
        model, effort = cell_identity(request.requested_cell)
        return [
            "claude", "-p", LiveWorkerAdapter.prompt(request),
            "--output-format", "stream-json", "--verbose",
            "--model", model, "--effort", effort,
            "--max-budget-usd", str(request.allowance_usd),
            "--restricted", "--safe-mode", "--strict-mcp-config",
            "--no-session-persistence", "--permission-mode", "acceptEdits",
            "--permission-prompts", "none",
            "--system-prompt",
            "Repair the supplied repository task exactly. Keep explanations concise.",
            "--tools", "Read,Edit,Write,Glob,Grep",
        ]

    def run(self, request: WorkerRequest) -> dict:
        actor = request.actor_root.resolve()
        if not actor.is_dir():
            raise ValueError(f"actor root is not a directory: {actor}")
        if not request.allowed_edits or any(Path(path).is_absolute() or ".." in Path(path).parts
                                            for path in request.allowed_edits):
            raise ValueError("allowed edits must be non-empty relative paths inside the actor root")
        if not isinstance(request.allowance_usd, (int, float)) or isinstance(request.allowance_usd, bool):
            raise ValueError("allowance_usd must be a positive finite number")
        if not math.isfinite(request.allowance_usd) or request.allowance_usd <= 0:
            raise ValueError("allowance_usd must be a positive finite number")
        expected_model, effort = cell_identity(request.requested_cell)
        cmd = self.command(request)
        env = {**os.environ, "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "8192"}
        started_at = dt.datetime.now(dt.timezone.utc)
        started = time.monotonic()
        timed_out = False
        try:
            proc = self.transport(cmd, actor, env, request.timeout_s)
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            proc = subprocess.CompletedProcess(cmd, 124, stdout, stderr)
        finished_at = dt.datetime.now(dt.timezone.utc)
        parsed = parse_stream(stdout)
        final = parsed["final"]
        cost = safe_number(final.get("total_cost_usd"))
        terminal = bool(not timed_out and final.get("type") == "result" and cost is not None)
        root_models = parsed["root_models"]
        actual_model = root_models[0] if len(root_models) == 1 else None
        identity_valid = model_registry.identity_matches(
            request.requested_cell, actual_model, parsed["child_models"]
        )
        successful = bool(
            terminal and proc.returncode == 0 and final.get("subtype") == "success"
            and identity_valid
        )
        raw_usage = final.get("usage") if isinstance(final.get("usage"), dict) else {}
        usage = {field: safe_number(raw_usage.get(field)) for field in USAGE_FIELDS}
        usage.update({
            "cost_usd": cost, "currency": "USD" if cost is not None else None,
            "cost_source": "provider_reported" if cost is not None else "unknown",
            "price_snapshot": "test/fixtures/realworld/price-snapshot-2026-09-17.json"
            if cost is not None else None,
            "includes_descendants": False if terminal and not parsed["child_models"] else None,
        })
        return {
            "status": "interrupted" if timed_out else ("completed" if successful else "failed"),
            "terminal": terminal, "timed_out": timed_out,
            "result": str(final.get("result", "")), "returncode": proc.returncode,
            "requested_cell": request.requested_cell, "expected_model": expected_model,
            "actual_model": actual_model, "identity_valid": identity_valid,
            "effort_evidence": f"cli-argument:{effort}",
            "usage": usage, "cost_usd": cost,
            "root_models": root_models, "child_models": parsed["child_models"],
            "billed_models": parsed["billed_models"],
            "auxiliary_billed_models": parsed["auxiliary_billed_models"],
            "stream": {"event_count": parsed["event_count"],
                       "invalid_line_count": parsed["invalid_line_count"]},
            "started_at": started_at.isoformat(), "finished_at": finished_at.isoformat(),
            "wall_clock_s": round(time.monotonic() - started, 6),
            "stderr_tail": stderr.strip()[-500:],
            "command_contract": {
                "cwd": str(actor), "argv_sha256": digest(cmd),
                "restricted": "--restricted" in cmd, "safe_mode": "--safe-mode" in cmd,
                "no_session_persistence": "--no-session-persistence" in cmd,
                "permission_prompts_none": (
                    cmd[cmd.index("--permission-prompts") + 1] == "none"
                ),
                "tools": cmd[cmd.index("--tools") + 1],
            },
        }


def _stream(model: str, call: dict, *, cost: object = "recorded") -> str:
    final_cost = call["cost_usd"] if cost == "recorded" else cost
    model_usage = json.loads(json.dumps(call["model_usage"]))
    if model != "claude-sonnet-5":
        model_usage[model] = model_usage.pop("claude-sonnet-5")
        model_usage[model]["canonicalModel"] = model
    rows = [
        {"type": "assistant", "parent_tool_use_id": None,
         "message": {"model": model, "content": []}},
        {"type": "result", "subtype": "success", "result": "repair complete",
         "total_cost_usd": final_cost, "usage": call["usage"],
         "modelUsage": model_usage},
    ]
    return "\n".join(json.dumps(row, separators=(",", ":")) for row in rows) + "\n"


def run_qualification(work: Path) -> dict:
    calibration = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    original_calibration = json.loads(ORIGINAL_CALIBRATION.read_text(encoding="utf-8"))
    direct = original_calibration["calls"]["direct"]
    direct_call = {
        "cost_usd": direct["cost_usd"], "usage": direct["raw"]["usage"],
        "model_usage": direct["raw"]["modelUsage"],
    }
    actor = work / "actor"
    shutil.copytree(realworld.FIXTURES / "development" / "D01" / "repo", actor)
    issue = (realworld.FIXTURES / "development" / "D01" / "issue.md").read_text(encoding="utf-8")
    observed: dict = {}

    def success_transport(cmd: list[str], cwd: Path, env: dict[str, str],
                          timeout: float) -> subprocess.CompletedProcess:
        observed.update({"cmd": cmd, "cwd": cwd, "env": env, "timeout": timeout})
        realworld.overlay(realworld.FIXTURES / "development" / "D01" / "variants" / "reference", cwd)
        return subprocess.CompletedProcess(cmd, 0, _stream("claude-sonnet-5", direct_call), "")

    request = WorkerRequest(
        actor_root=actor, issue=issue, allowed_edits=("consumer/config.py",),
        requested_cell="worker-sonnet-low", allowance_usd=4.0,
        policy="Run one bounded repair and stop after the smallest complete change.", timeout_s=900,
    )
    success = LiveWorkerAdapter(success_transport).run(request)
    public = realworld.run_checks(actor, actor / "public_checks", False)
    hidden = realworld.run_checks(actor, realworld.ORACLES / "D01", True)
    command = observed["cmd"]
    command_ok = all((
        observed["cwd"] == actor.resolve(), command[0] == "claude",
        command[command.index("--model") + 1] == "claude-sonnet-5",
        command[command.index("--effort") + 1] == "low",
        command[command.index("--max-budget-usd") + 1] == "4.0",
        command[command.index("--tools") + 1] == "Read,Edit,Write,Glob,Grep",
        "Task" not in command[command.index("--tools") + 1],
        "Bash" not in command[command.index("--tools") + 1],
        str(realworld.ORACLES) not in " ".join(command),
    ))

    def timeout_transport(cmd: list[str], cwd: Path, env: dict[str, str],
                          timeout: float) -> subprocess.CompletedProcess:
        raise subprocess.TimeoutExpired(cmd, timeout)

    timeout_actor = work / "timeout-actor"
    shutil.copytree(realworld.FIXTURES / "development" / "D01" / "repo", timeout_actor)
    timeout = LiveWorkerAdapter(timeout_transport).run(dataclasses.replace(request, actor_root=timeout_actor))

    mismatch_actor = work / "mismatch-actor"
    shutil.copytree(realworld.FIXTURES / "development" / "D01" / "repo", mismatch_actor)
    mismatch = LiveWorkerAdapter(lambda cmd, cwd, env, timeout: subprocess.CompletedProcess(
        cmd, 0, _stream("claude-opus-5", direct_call), ""
    )).run(dataclasses.replace(request, actor_root=mismatch_actor))

    missing_actor = work / "missing-cost-actor"
    shutil.copytree(realworld.FIXTURES / "development" / "D01" / "repo", missing_actor)
    missing = LiveWorkerAdapter(lambda cmd, cwd, env, timeout: subprocess.CompletedProcess(
        cmd, 0, _stream("claude-sonnet-5", direct_call, cost=None), ""
    )).run(dataclasses.replace(request, actor_root=missing_actor))

    checks = {
        "restricted_command": command_ok,
        "successful_edit_and_external_grade": success["status"] == "completed"
        and public["passed"] and hidden["passed"],
        "exact_model_attribution": success["identity_valid"] is True
        and success["actual_model"] == "claude-sonnet-5",
        "auxiliary_billing_retained": "claude-haiku-4-5-20251001"
        in success["auxiliary_billed_models"],
        "timeout_cost_unknown": timeout["status"] == "interrupted"
        and timeout["terminal"] is False and timeout["cost_usd"] is None,
        "model_mismatch_rejected": mismatch["identity_valid"] is False
        and mismatch["status"] == "failed" and mismatch["cost_usd"] is not None,
        "missing_cost_nonterminal": missing["terminal"] is False
        and missing["usage"]["cost_usd"] is None,
    }
    def evidence_view(outcome: dict, actor_name: str) -> dict:
        clean = json.loads(json.dumps(outcome))
        clean["command_contract"]["cwd"] = f"<qualification>/{actor_name}"
        clean["started_at"] = "qualification-clock"
        clean["finished_at"] = "qualification-clock"
        clean["wall_clock_s"] = 0.0
        return clean

    return {
        "schema_version": 1, "mode": "offline-fake-transport-v1",
        "offline_only": True, "model_calls": 0,
        "scope": "single live worker attempt adapter; policy sequencing remains external",
        "result": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
        "success": evidence_view(success, "actor"),
        "failure_paths": {
            "timeout": evidence_view(timeout, "timeout-actor"),
            "identity_mismatch": evidence_view(mismatch, "mismatch-actor"),
            "missing_cost": evidence_view(missing, "missing-cost-actor"),
        },
        "calibration": {
            "path": CALIBRATION.relative_to(ROOT).as_posix(),
            "file_sha256": file_sha256(CALIBRATION),
            "evidence_sha256": calibration["evidence_sha256"],
            "original_path": ORIGINAL_CALIBRATION.relative_to(ROOT).as_posix(),
            "original_file_sha256": file_sha256(ORIGINAL_CALIBRATION),
            "original_evidence_sha256": original_calibration["evidence_sha256"],
            "derivation": "root stream shape reconstructed from recorded direct-call telemetry",
        },
        "limits": [
            "Fake transport proves command, parsing and failure contracts without a model call.",
            "This adapter does not implement policy sequencing or durable dispatch recovery.",
            "The live calibration, not this qualification, is the source of model and billing observations.",
        ],
    }


def render_report(value: dict) -> str:
    lines = [
        "# Live worker adapter offline qualification", "",
        f"Result: **{value['result']}**. Mode: `{value['mode']}`. Model calls: **0**.", "",
        "The fake transport exercised the exact command boundary, model attribution, billing",
        "retention, an accepted D01 repair, timeout, identity mismatch and missing-cost paths.", "",
        "| Check | Result |", "| :--- | :--- |",
    ]
    lines.extend(f"| {name.replace('_', ' ')} | {'pass' if passed else 'fail'} |"
                 for name, passed in value["checks"].items())
    lines.extend(["", "## Limits", ""])
    lines.extend(f"- {item}" for item in value["limits"])
    return "\n".join(lines) + "\n"


def validate(path: Path) -> tuple[bool, str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"cannot read adapter evidence: {exc}"
    recorded = value.pop("evidence_sha256", None)
    report = value.get("report") or {}
    report_path = (ROOT / str(report.get("path", ""))).resolve()
    calibration = value.get("calibration") or {}
    checks = value.get("checks") or {}
    ok = bool(
        recorded == digest(value) and value.get("result") == "PASS"
        and value.get("offline_only") is True and value.get("model_calls") == 0
        and value.get("implementation_sha256") == file_sha256(Path(__file__))
        and calibration.get("file_sha256") == file_sha256(CALIBRATION)
        and calibration.get("original_file_sha256") == file_sha256(ORIGINAL_CALIBRATION)
        and all(checks.values()) and len(checks) == 7
        and report_path.is_relative_to(ROOT.resolve()) and report_path.is_file()
        and report.get("sha256") == file_sha256(report_path)
    )
    return ok, f"mode={value.get('mode')}; digest={'valid' if recorded == digest(value) else 'invalid'}"


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False,
                         allow_nan=False).encode("utf-8") + b"\n"
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    report = args.report if args.report.is_absolute() else ROOT / args.report
    if args.check:
        ok, detail = validate(output)
        print(f"{'PASS' if ok else 'FAIL'}: {detail}")
        return 0 if ok else 1
    with tempfile.TemporaryDirectory(prefix="live-worker-adapter-") as folder:
        value = run_qualification(Path(folder))
    value.update({
        "recorded_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "host": platform.node(), "implementation_sha256": file_sha256(Path(__file__)),
    })
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(value), encoding="utf-8", newline="\n")
    value["report"] = {"path": report.relative_to(ROOT).as_posix(),
                       "sha256": file_sha256(report)}
    value["evidence_sha256"] = digest(value)
    atomic_json(output, value)
    print(f"{value['result']}: live worker adapter, 0 model calls")
    print(f"wrote {output.relative_to(ROOT)}")
    return 0 if value["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
