#!/usr/bin/env python3
"""Run the bounded live instrumentation calibration for real-world episodes."""
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
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import claudep  # noqa: E402
from dispatch_budget import DispatchBudget  # noqa: E402
from realworld_isolation import validate as validate_isolation  # noqa: E402

DEFAULT_OUTPUT = ROOT / "test" / "results" / "2026-09-17-live-calibration.json"
ISOLATION = ROOT / "test" / "results" / "2026-09-17-realworld-isolation.json"
FREEZE = ROOT / "docs" / "REAL-WORLD-EVALUATION-FREEZE-2026-09-17.json"
TOTAL_LIMIT_USD = 0.40
REQUIRED_MODEL = "claude-sonnet-5"
USAGE_FIELDS = (
    "input_tokens", "cache_creation_input_tokens",
    "cache_read_input_tokens", "output_tokens",
)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False,
                         allow_nan=False).encode("utf-8") + b"\n"
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)


def safe_number(value: object) -> float | int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(value) and value >= 0 else None


def usage_record(raw: object) -> dict:
    usage = raw if isinstance(raw, dict) else {}
    return {field: safe_number(usage.get(field)) for field in USAGE_FIELDS}


def model_usage(raw: dict) -> dict[str, dict]:
    value = raw.get("modelUsage", raw.get("model_usage", {}))
    if not isinstance(value, dict):
        return {}
    return {str(model): detail for model, detail in value.items() if isinstance(detail, dict)}


def actual_models(raw: dict) -> list[str]:
    models = sorted(model_usage(raw))
    direct = raw.get("model")
    if isinstance(direct, str) and direct and direct not in models:
        models.append(direct)
    return sorted(models)


def rollup_evidence(raw: dict) -> dict:
    """Compare aggregate usage with parent-message iterations."""
    aggregate = usage_record(raw.get("usage"))
    usage = raw.get("usage") if isinstance(raw.get("usage"), dict) else {}
    iterations = usage.get("iterations") if isinstance(usage.get("iterations"), list) else []
    parent = {field: 0 for field in USAGE_FIELDS}
    complete_iterations = bool(iterations)
    for item in iterations:
        if not isinstance(item, dict):
            complete_iterations = False
            continue
        for field in USAGE_FIELDS:
            value = safe_number(item.get(field))
            if value is None:
                complete_iterations = False
            else:
                parent[field] += value
    delta = {
        field: (aggregate[field] - parent[field]
                if aggregate[field] is not None and complete_iterations else None)
        for field in USAGE_FIELDS
    }
    models = model_usage(raw)
    model_costs = [safe_number(value.get("costUSD", value.get("cost_usd")))
                   for value in models.values()]
    cost_sum = sum(value for value in model_costs if value is not None) if model_costs else None
    total = safe_number(raw.get("total_cost_usd"))
    return {
        "aggregate": aggregate, "parent_iterations": parent if complete_iterations else None,
        "descendant_delta": delta,
        "descendant_usage_present": any(value is not None and value > 0 for value in delta.values()),
        "model_cost_sum_usd": cost_sum,
        "reported_total_cost_usd": total,
        "model_cost_matches_total": (
            cost_sum is not None and total is not None and abs(cost_sum - total) <= 0.000001
        ),
    }


class WslBridge:
    """Mediate a no-tool model response into a WSL actor and external grader."""

    def __init__(self):
        self.base = f"/tmp/orchestrator-live-calibration-{uuid.uuid4().hex}"

    @staticmethod
    def call(*args: str, input_text: str | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(["wsl.exe", "-u", "root", "--", *args], input=input_text,
                              capture_output=True, text=True, encoding="utf-8", timeout=30)

    def setup(self) -> str:
        script = (
            "from pathlib import Path; import os; "
            f"base=Path({self.base!r}); actor=base/'actor'; evaluator=base/'evaluator'; "
            "actor.mkdir(parents=True); evaluator.mkdir(); "
            "(actor/'input.txt').write_text('Return exactly CALIBRATION_OK.\\n'); "
            "(evaluator/'expected.txt').write_text('CALIBRATION_OK'); "
            "os.chmod(base,0o755); os.chmod(evaluator,0o700); "
            "os.chown(actor,65534,65534); os.chown(actor/'input.txt',65534,65534)"
        )
        created = self.call("python3", "-c", script)
        if created.returncode != 0:
            raise RuntimeError(created.stderr[-500:])
        read = self.call("runuser", "-u", "nobody", "--", "cat", f"{self.base}/actor/input.txt")
        if read.returncode != 0:
            raise RuntimeError(read.stderr[-500:])
        return read.stdout.strip()

    def grade(self, response: str) -> dict:
        writer = self.call(
            "runuser", "-u", "nobody", "--", "python3", "-c",
            f"from pathlib import Path; import sys; "
            f"(Path({self.base!r})/'actor'/'output.txt').write_text(sys.stdin.read())",
            input_text=response.strip(),
        )
        denied = self.call("runuser", "-u", "nobody", "--", "cat",
                           f"{self.base}/evaluator/expected.txt")
        evaluator = self.call(
            "python3", "-c",
            f"from pathlib import Path; base=Path({self.base!r}); "
            "actual=(base/'actor'/'output.txt').read_text().strip(); "
            "expected=(base/'evaluator'/'expected.txt').read_text().strip(); "
            "raise SystemExit(0 if actual == expected else 1)",
        )
        return {
            "actor_write": "pass" if writer.returncode == 0 else "fail",
            "actor_oracle_read": "denied" if denied.returncode != 0 else "allowed",
            "external_grade": "pass" if evaluator.returncode == 0 else "fail",
        }

    def cleanup(self) -> None:
        self.call("rm", "-rf", self.base)


def common_args(tools: str) -> list[str]:
    return ["--restricted", "--strict-mcp-config", "--no-session-persistence",
            "--system-prompt", "Follow the user instruction exactly. Keep the response minimal.",
            "--permission-mode", "dontAsk", "--tools", tools]


def invoke(budget: DispatchBudget, invocation_id: str, cap: float, prompt: str,
           *, timeout: float, extra_args: list[str]) -> dict:
    allowance = budget.reserve(invocation_id, cap, cap, {
        "requested_model": REQUIRED_MODEL, "effort": "low", "timeout_s": timeout,
    })
    budget.start(invocation_id)
    try:
        result = claudep.call_claude(
            prompt, cwd=ROOT, model=REQUIRED_MODEL, effort="low",
            max_budget_usd=allowance, timeout=timeout, max_output_tokens=256,
            extra_args=extra_args,
        )
    except claudep.ClaudeCallError as exc:
        result = exc.partial
        timed_out = isinstance(exc.__cause__, subprocess.TimeoutExpired)
        terminal = bool(result.raw.get("type") == "result"
                        and result.cost_usd is not None and not timed_out)
        budget.settle(invocation_id, result.cost_usd, final=terminal,
                      telemetry={"status": "timeout" if timed_out else "failed",
                                 "usage": usage_record(result.extras.get("usage")),
                                 "actual_models": actual_models(result.raw)},
                      evidence="terminal-error-envelope" if terminal else "incomplete-live-response")
        return {"status": "timeout" if timed_out else "failed", "error": str(exc),
                "result": result.result, "cost_usd": result.cost_usd,
                "usage": usage_record(result.extras.get("usage")),
                "actual_models": actual_models(result.raw), "raw": result.raw,
                "rollup": rollup_evidence(result.raw)}
    budget.settle(invocation_id, result.cost_usd, final=result.cost_usd is not None,
                  telemetry={"status": "completed", "usage": usage_record(result.extras.get("usage")),
                             "actual_models": actual_models(result.raw)},
                  evidence="terminal-live-response" if result.cost_usd is not None else "live-missing-cost")
    return {"status": "completed", "result": result.result, "cost_usd": result.cost_usd,
            "usage": usage_record(result.extras.get("usage")),
            "actual_models": actual_models(result.raw), "raw": result.raw,
            "rollup": rollup_evidence(result.raw)}


def execute(work: Path) -> dict:
    isolation_ok, isolation_detail = validate_isolation(ISOLATION)
    if not isolation_ok:
        raise RuntimeError(f"isolation evidence invalid: {isolation_detail}")
    budget = DispatchBudget(work / "dispatch-budget.json", TOTAL_LIMIT_USD)
    bridge = WslBridge()
    try:
        actor_instruction = bridge.setup()
        direct = invoke(
            budget, "live-direct", 0.10, actor_instruction,
            timeout=60, extra_args=common_args(""),
        )
        boundary = bridge.grade(direct.get("result", ""))
    finally:
        bridge.cleanup()

    agents = json.dumps({
        "calibration-worker": {
            "description": "Returns a fixed calibration sentinel.",
            "prompt": "Reply exactly WORKER_OK. Do not use tools.",
        }
    }, separators=(",", ":"))
    spawn = invoke(
        budget, "live-spawn", 0.25,
        "Use the Task tool once with subagent_type calibration-worker. Ask it to reply WORKER_OK. "
        "Wait for it, then reply exactly WORKER_OK.",
        timeout=120, extra_args=common_args("Task") + ["--agents", agents],
    )
    timeout = invoke(
        budget, "live-timeout", 0.05,
        "Write a detailed 10000 word technical treatise. Do not use tools.",
        timeout=1, extra_args=common_args(""),
    )
    snapshot = budget.snapshot()
    direct_complete = direct["status"] == "completed" and direct["result"].strip() == "CALIBRATION_OK"
    spawn_complete = spawn["status"] == "completed" and spawn["result"].strip() == "WORKER_OK"
    identities = sorted(set(direct["actual_models"] + spawn["actual_models"]))
    identity_ok = bool(identities) and identities == [REQUIRED_MODEL]
    usage_ok = all(direct["usage"][field] is not None and spawn["usage"][field] is not None
                   for field in USAGE_FIELDS)
    rollup_ok = spawn["rollup"]["descendant_usage_present"]
    timeout_row = snapshot["invocations"]["live-timeout"]
    timeout_ok = timeout["status"] == "timeout" and timeout_row["state"] == "uncertain"
    boundary_ok = boundary == {
        "actor_write": "pass", "actor_oracle_read": "denied", "external_grade": "pass",
    }
    result = "PASS" if all((direct_complete, spawn_complete, identity_ok, usage_ok,
                            rollup_ok, timeout_ok, boundary_ok)) else "FAIL"
    return {
        "schema_version": 1, "result": result, "live": True,
        "claude_cli_version": subprocess.run(["claude", "--version"], capture_output=True,
                                                text=True, timeout=10).stdout.strip(),
        "requested_model": REQUIRED_MODEL, "required_actual_models": [REQUIRED_MODEL],
        "observed_actual_models": identities,
        "checks": {
            "direct_terminal": direct_complete, "spawn_terminal": spawn_complete,
            "actual_model": identity_ok, "disjoint_usage": usage_ok,
            "parent_child_rollup": rollup_ok, "timeout_retained": timeout_ok,
            "wsl_mediated_boundary": boundary_ok,
        },
        "calls": {"direct": direct, "spawn": spawn, "timeout": timeout},
        "boundary": boundary,
        "budget": snapshot,
        "limits": [
            "The model call is mediated into a WSL actor; Claude itself does not run as Linux nobody.",
            "The timeout proves local uncertain accounting, not provider-side termination.",
            "Reported cost is API-equivalent telemetry under the signed-in Claude subscription.",
        ],
    }


def validate(path: Path) -> tuple[bool, str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"cannot read calibration evidence: {exc}"
    recorded = value.pop("evidence_sha256", None)
    checks = value.get("checks") or {}
    ok = (recorded == digest(value) and value.get("result") == "PASS"
          and value.get("implementation_sha256") == file_sha256(Path(__file__))
          and all(checks.get(name) is True for name in (
              "direct_terminal", "spawn_terminal", "actual_model", "disjoint_usage",
              "parent_child_rollup", "timeout_retained", "wsl_mediated_boundary")))
    return ok, f"digest={'valid' if recorded == digest(value) else 'invalid'}; result={value.get('result')}"


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
        print("dry run: 3 calls; USD 0.40 aggregate ceiling; pass --execute to run")
        return 0
    if output.exists():
        print(f"refusing to overwrite existing evidence: {output}", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="live-calibration-", dir=ROOT) as folder:
        value = execute(Path(folder))
    value.update({
        "recorded_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "host": platform.node(), "implementation_sha256": file_sha256(Path(__file__)),
        "freeze_candidate_sha256": json.loads(FREEZE.read_text(encoding="utf-8"))["candidate_sha256"],
        "cost_ceiling_usd": TOTAL_LIMIT_USD,
    })
    value["evidence_sha256"] = digest(value)
    atomic_json(output, value)
    print(f"{value['result']}: wrote {output.relative_to(ROOT)}")
    print(f"observed models: {value['observed_actual_models']}")
    print(f"reported spend: USD {value['budget']['spent_usd']}; retained: USD {value['budget']['reserved_usd']}")
    return 0 if value["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
