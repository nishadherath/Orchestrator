#!/usr/bin/env python3
"""Adjudicate Claude model identity with per-message stream evidence.

The first live calibration correctly captured aggregate billing, but Claude
Code's final ``modelUsage`` map contains auxiliary internal model usage as
well as task messages.  This narrow rerun uses stream-json and forwarded
subagent messages so root and worker model identities can be attributed
directly.  It preserves and binds the original calibration evidence.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from dispatch_budget import DispatchBudget  # noqa: E402

ORIGINAL = ROOT / "test" / "results" / "2026-09-17-live-calibration.json"
DEFAULT_OUTPUT = (
    ROOT / "test" / "results" / "2026-09-17-live-calibration-adjudication.json"
)
REQUIRED_MODEL = "claude-sonnet-5"
TOTAL_LIMIT_USD = 0.10
INVOCATION_ID = "live-model-attribution"


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


def parse_stream(text: str) -> dict:
    """Extract attributed assistant models and the final result envelope."""
    events: list[dict] = []
    invalid_lines = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            invalid_lines += 1
            continue
        if isinstance(event, dict):
            events.append(event)
        else:
            invalid_lines += 1

    root_models: set[str] = set()
    worker_models: set[str] = set()
    assistant_messages = 0
    forwarded_messages = 0
    final: dict = {}
    for event in events:
        if event.get("type") == "assistant" and isinstance(event.get("message"), dict):
            assistant_messages += 1
            model = event["message"].get("model")
            if not isinstance(model, str) or not model:
                continue
            if event.get("parent_tool_use_id"):
                worker_models.add(model)
                forwarded_messages += 1
            else:
                root_models.add(model)
        if event.get("type") == "result":
            final = event

    billed = final.get("modelUsage", final.get("model_usage", {}))
    billed_models = sorted(billed) if isinstance(billed, dict) else []
    attributed = root_models | worker_models
    return {
        "event_count": len(events),
        "invalid_line_count": invalid_lines,
        "assistant_message_count": assistant_messages,
        "forwarded_message_count": forwarded_messages,
        "root_models": sorted(root_models),
        "worker_models": sorted(worker_models),
        "billed_models": billed_models,
        "auxiliary_billed_models": sorted(set(billed_models) - attributed),
        "final": final,
    }


def original_evidence() -> tuple[dict, bool]:
    value = json.loads(ORIGINAL.read_text(encoding="utf-8"))
    recorded = value.get("evidence_sha256")
    unsigned = {key: item for key, item in value.items() if key != "evidence_sha256"}
    checks = value.get("checks") or {}
    expected_passes = (
        "direct_terminal", "spawn_terminal", "disjoint_usage",
        "parent_child_rollup", "timeout_retained", "wsl_mediated_boundary",
    )
    valid = bool(
        recorded == digest(unsigned)
        and value.get("result") == "FAIL"
        and checks.get("actual_model") is False
        and all(checks.get(name) is True for name in expected_passes)
    )
    return value, valid


def command() -> list[str]:
    agents = json.dumps({
        "calibration-worker": {
            "description": "Returns a fixed calibration sentinel.",
            "prompt": "Reply exactly WORKER_OK. Do not use tools.",
            "model": REQUIRED_MODEL,
        }
    }, separators=(",", ":"))
    prompt = (
        "Use the Task tool once with subagent_type calibration-worker. "
        "Ask it to reply WORKER_OK. Wait for it, then reply exactly WORKER_OK."
    )
    return [
        "claude", "-p", prompt,
        "--output-format", "stream-json", "--verbose", "--forward-subagent-text",
        "--model", REQUIRED_MODEL, "--effort", "low",
        "--max-budget-usd", str(TOTAL_LIMIT_USD),
        "--restricted", "--strict-mcp-config", "--no-session-persistence",
        "--system-prompt", "Follow the user instruction exactly. Keep the response minimal.",
        "--permission-mode", "dontAsk", "--tools", "Task", "--agents", agents,
    ]


def execute(work: Path) -> dict:
    original, original_valid = original_evidence()
    if not original_valid:
        raise RuntimeError("original calibration evidence is missing or invalid")

    budget = DispatchBudget(work / "dispatch-budget.json", TOTAL_LIMIT_USD)
    allowance = budget.reserve(INVOCATION_ID, TOTAL_LIMIT_USD, TOTAL_LIMIT_USD, {
        "requested_root_model": REQUIRED_MODEL,
        "requested_worker_model": REQUIRED_MODEL,
        "effort": "low",
        "timeout_s": 120,
    })
    budget.start(INVOCATION_ID)
    cmd = command()
    env = {**os.environ, "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "256"}
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", timeout=120, env=env)
        elapsed_s = time.monotonic() - started
        parsed = parse_stream(proc.stdout)
        final = parsed["final"]
        cost = safe_number(final.get("total_cost_usd"))
        terminal = bool(proc.returncode == 0 and final.get("type") == "result"
                        and cost is not None)
        budget.settle(
            INVOCATION_ID, cost, final=terminal,
            telemetry={
                "returncode": proc.returncode,
                "root_models": parsed["root_models"],
                "worker_models": parsed["worker_models"],
                "billed_models": parsed["billed_models"],
            },
            evidence="terminal-stream-response" if terminal else "incomplete-stream-response",
        )
    except subprocess.TimeoutExpired as exc:
        elapsed_s = time.monotonic() - started
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        parsed = parse_stream(stdout)
        final = parsed["final"]
        cost = safe_number(final.get("total_cost_usd"))
        budget.settle(INVOCATION_ID, cost, final=False,
                      telemetry={"status": "timeout"}, evidence="incomplete-stream-response")
        proc = subprocess.CompletedProcess(cmd, 124, stdout, "timeout")

    final = parsed["final"]
    stats = final.get("subagent_stats") if isinstance(final.get("subagent_stats"), dict) else {}
    root_ok = parsed["root_models"] == [REQUIRED_MODEL]
    worker_ok = parsed["worker_models"] == [REQUIRED_MODEL]
    terminal_ok = bool(
        proc.returncode == 0 and final.get("subtype") == "success"
        and str(final.get("result", "")).strip() == "WORKER_OK"
    )
    one_worker = bool(
        stats.get("spawned") == 1 and stats.get("completed") == 1
        and (stats.get("by_type") or {}).get("calibration-worker") == 1
    )
    billing_ok = bool(
        cost is not None and REQUIRED_MODEL in parsed["billed_models"]
        and final.get("usage") is not None
    )
    checks = {
        "original_evidence_valid": original_valid,
        "terminal_result": terminal_ok,
        "one_worker_completed": one_worker,
        "root_model_attributed": root_ok,
        "worker_model_attributed": worker_ok,
        "billing_telemetry_present": billing_ok,
        "stream_well_formed": parsed["invalid_line_count"] == 0,
    }
    return {
        "schema_version": 1,
        "result": "PASS" if all(checks.values()) else "FAIL",
        "live": True,
        "purpose": "per-message model identity adjudication",
        "requested_models": {"root": REQUIRED_MODEL, "worker": REQUIRED_MODEL},
        "checks": checks,
        "attribution": {key: parsed[key] for key in (
            "event_count", "invalid_line_count", "assistant_message_count",
            "forwarded_message_count", "root_models", "worker_models",
            "billed_models", "auxiliary_billed_models",
        )},
        "call": {
            "elapsed_s": round(elapsed_s, 3),
            "returncode": proc.returncode,
            "result": final.get("result"),
            "cost_usd": cost,
            "usage": final.get("usage"),
            "model_usage": final.get("modelUsage", final.get("model_usage")),
            "subagent_stats": stats,
            "session_id": final.get("session_id"),
        },
        "budget": budget.snapshot(),
        "original": {
            "path": ORIGINAL.relative_to(ROOT).as_posix(),
            "file_sha256": file_sha256(ORIGINAL),
            "evidence_sha256": original["evidence_sha256"],
            "reported_spend_usd": original["budget"]["spent_usd"],
            "retained_timeout_allowance_usd": original["budget"]["reserved_usd"],
        },
        "interpretation": (
            "modelUsage is an aggregate billing map. Per-message stream metadata is the "
            "identity source for root and forwarded worker task messages; billed models absent "
            "from those messages are recorded as auxiliary Claude Code overhead."
        ),
        "limits": [
            "The rerun attributes emitted task messages; it cannot identify undocumented internal calls.",
            "Reported cost is API-equivalent telemetry under the signed-in Claude subscription.",
            "The original uncertain timeout allowance remains unresolved and reserved in its own ledger.",
        ],
    }


def validate(path: Path) -> tuple[bool, str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"cannot read adjudication evidence: {exc}"
    recorded = value.pop("evidence_sha256", None)
    checks = value.get("checks") or {}
    original = value.get("original") or {}
    expected = (
        "original_evidence_valid", "terminal_result", "one_worker_completed",
        "root_model_attributed", "worker_model_attributed",
        "billing_telemetry_present", "stream_well_formed",
    )
    ok = bool(
        recorded == digest(value)
        and value.get("result") == "PASS"
        and value.get("implementation_sha256") == file_sha256(Path(__file__))
        and original.get("file_sha256") == file_sha256(ORIGINAL)
        and all(checks.get(name) is True for name in expected)
    )
    return ok, f"digest={'valid' if recorded == digest(value) else 'invalid'}; result={value.get('result')}"


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
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if args.check:
        ok, detail = validate(output)
        print(f"{'PASS' if ok else 'FAIL'}: {detail}")
        return 0 if ok else 1
    if not args.execute:
        print("dry run: 1 streamed spawn call; USD 0.10 hard ceiling")
        return 0
    if output.exists():
        print(f"refusing to overwrite existing evidence: {output}", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="model-adjudication-", dir=ROOT) as folder:
        value = execute(Path(folder))
    value.update({
        "recorded_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "host": platform.node(),
        "claude_cli_version": subprocess.run(
            ["claude", "--version"], capture_output=True, text=True, timeout=10
        ).stdout.strip(),
        "implementation_sha256": file_sha256(Path(__file__)),
        "cost_ceiling_usd": TOTAL_LIMIT_USD,
    })
    value["evidence_sha256"] = digest(value)
    atomic_json(output, value)
    print(f"{value['result']}: wrote {output.relative_to(ROOT)}")
    print(f"root={value['attribution']['root_models']}; worker={value['attribution']['worker_models']}")
    print(f"billed={value['attribution']['billed_models']}; cost=USD {value['call']['cost_usd']}")
    return 0 if value["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
