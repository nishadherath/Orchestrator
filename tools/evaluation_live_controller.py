#!/usr/bin/env python3
"""Live Controller adapter with nested, durable provider accounting.

The episode owns one outer reservation. The Controller owns an inner
DispatchBudget with one row per role call. This adapter copies the actor into
an evaluator-owned workspace, runs the Controller there, and returns the exact
known inner subtotal plus whether every inner charge and model identity is
final. It never edits the actor supplied by the evaluation episode.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import math
import platform
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "test" / "harness"))

import evaluation_runner  # noqa: E402
import realworld  # noqa: E402
import system_controller  # noqa: E402
from dispatch_budget import DispatchBudget  # noqa: E402

DEFAULT_OUTPUT = ROOT / "test" / "results" / "2026-09-18-live-controller-adapter.json"
DEFAULT_REPORT = ROOT / "test" / "results" / "2026-09-18-live-controller-adapter.md"
USAGE_FIELDS = (
    "input_tokens", "cache_creation_input_tokens",
    "cache_read_input_tokens", "output_tokens",
)
CONTROLLER_ARGS = (
    "--restricted", "--safe-mode", "--strict-mcp-config",
    "--no-session-persistence", "--permission-mode", "acceptEdits",
    "--permission-prompts", "none", "--tools", "Read,Glob,Grep",
)


@dataclasses.dataclass(frozen=True)
class ControllerRequest:
    actor_root: Path
    controller_root: Path
    issue: str
    allowed_edits: tuple[str, ...]
    observations: tuple[dict, ...]
    allowance_usd: float
    invocation_id: str
    role_timeout_s: float = 180.0
    elapsed_limit_s: float = 900.0


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _valid_amount(value: object) -> bool:
    return (type(value) in (int, float) and math.isfinite(value) and value > 0)


def _token(value: object) -> int | None:
    return value if type(value) is int and value >= 0 else None


def _identity_view(snapshot: dict) -> dict:
    """Aggregate per-role identity and usage without inventing missing data."""
    totals = {field: 0 for field in USAGE_FIELDS}
    complete_usage = True
    launched: list[dict] = []
    model_sets = {key: set() for key in (
        "expected_models", "actual_models", "root_models", "child_models",
        "billed_models", "auxiliary_billed_models",
    )}
    for ident, row in snapshot.get("invocations", {}).items():
        telemetry = row.get("telemetry") or {}
        if telemetry.get("status") == "not_launched":
            continue
        identity = telemetry.get("identity") or {}
        usage = telemetry.get("usage") or {}
        call = {
            "invocation_id": ident,
            "state": row.get("state"),
            "identity_valid": identity.get("identity_valid") is True,
            "expected_model": identity.get("expected_model"),
            "actual_model": identity.get("actual_model"),
        }
        launched.append(call)
        for singular, plural in (("expected_model", "expected_models"),
                                 ("actual_model", "actual_models")):
            if isinstance(identity.get(singular), str) and identity[singular]:
                model_sets[plural].add(identity[singular])
        for plural in ("root_models", "child_models", "billed_models",
                       "auxiliary_billed_models"):
            values = identity.get(plural)
            if isinstance(values, list):
                model_sets[plural].update(value for value in values
                                          if isinstance(value, str) and value)
        for field in USAGE_FIELDS:
            value = _token(usage.get(field))
            if value is None:
                complete_usage = False
            else:
                totals[field] += value
    identity_valid = all(row["identity_valid"] for row in launched)
    return {
        **totals,
        "usage_complete": complete_usage,
        "identity_valid": identity_valid,
        "launched_calls": launched,
        **{key: sorted(values) for key, values in model_sets.items()},
    }


def _usage(summary: dict, cost: float | None, complete: bool) -> dict:
    identity = _identity_view(summary)
    return {
        **{field: identity[field] if identity["usage_complete"] else None
           for field in USAGE_FIELDS},
        "cost_usd": cost,
        "currency": "USD" if cost is not None else None,
        "cost_source": "provider_reported" if complete and cost is not None else "unknown",
        "price_snapshot": "test/fixtures/realworld/price-snapshot-2026-09-17.json"
        if complete and cost is not None else None,
        "includes_descendants": True if complete else None,
    }


class LiveControllerAdapter:
    """Run the existing quick Controller through an injectable entry point."""

    def __init__(self, run_quick_fn: Callable = system_controller.run_quick):
        self.run_quick = run_quick_fn

    @staticmethod
    def prompt(request: ControllerRequest) -> str:
        allowed = "\n".join(f"- {path}" for path in request.allowed_edits)
        observations = json.dumps(list(request.observations), sort_keys=True,
                                  ensure_ascii=False)
        return (
            "Analyse the repository issue and produce bounded technical guidance for a coding worker. "
            "Treat the repository as read-only. Do not inspect parent directories, hidden evaluation "
            "material, or network resources. Ground every claim in the supplied issue, allowed files, "
            "repository evidence, and observable prior attempts.\n\n"
            f"Allowed edit boundary for the later worker:\n{allowed}\n\n"
            f"Observable prior attempts:\n{observations}\n\nIssue:\n{request.issue.strip()}\n"
        )

    @staticmethod
    def _validate(request: ControllerRequest) -> tuple[Path, Path]:
        actor = request.actor_root.resolve()
        controller_root = request.controller_root.resolve()
        if not actor.is_dir():
            raise ValueError(f"actor root is not a directory: {actor}")
        if controller_root.is_relative_to(actor) or actor.is_relative_to(controller_root):
            raise ValueError("Controller workspace root must be separate from the actor root")
        if (not request.allowed_edits
                or any(Path(path).is_absolute() or ".." in Path(path).parts
                       for path in request.allowed_edits)):
            raise ValueError("allowed edits must be non-empty relative paths inside the actor root")
        if not _valid_amount(request.allowance_usd):
            raise ValueError("allowance_usd must be a positive finite number")
        if not _valid_amount(request.role_timeout_s) or not _valid_amount(request.elapsed_limit_s):
            raise ValueError("Controller time limits must be positive finite numbers")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", request.invocation_id):
            raise ValueError("invocation_id must be a simple directory name")
        return actor, controller_root

    @staticmethod
    def _snapshot(run_dir: Path) -> dict | None:
        budget_path = run_dir / "dispatch-budget.json"
        if not budget_path.is_file():
            return None
        return DispatchBudget(budget_path).snapshot()

    @staticmethod
    def _outcome(result: system_controller.RunResult | None, run_dir: Path,
                 snapshot: dict | None, started_at: dt.datetime,
                 started: float, error: BaseException | None = None) -> dict:
        finished_at = dt.datetime.now(dt.timezone.utc)
        complete = bool(snapshot is not None and not snapshot["unresolved"])
        cost = snapshot["spent_usd"] if snapshot is not None else None
        identity = _identity_view(snapshot or {"invocations": {}})
        report_path = run_dir / "REPORT.md"
        guidance = report_path.read_text(encoding="utf-8") if report_path.is_file() else ""
        controller_outcome = result.outcome if result is not None else "error"
        if controller_outcome not in {"solution", "gap", "dissolved"}:
            controller_outcome = "error"
        actual_models = identity["actual_models"]
        actual_model = ",".join(actual_models) if actual_models else "controller:no-provider-call"
        terminal = bool(complete and result is not None)
        status = "completed" if terminal and error is None else (
            "failed" if complete else "interrupted"
        )
        return {
            "status": status, "terminal": terminal, "cost_usd": cost,
            "usage": _usage(snapshot or {"invocations": {}}, cost, complete),
            "actual_model": actual_model,
            "identity_valid": identity["identity_valid"],
            "effort_evidence": f"inner-dispatch-metadata:{len(identity['launched_calls'])}-calls",
            "controller_outcome": controller_outcome,
            "guidance": guidance,
            "controller_run_dir": str(run_dir.resolve()),
            "winning_technique": result.record.get("technique")
            if result is not None and isinstance(result.record, dict) else None,
            "expected_models": identity["expected_models"],
            "served_models": actual_models,
            "root_models": identity["root_models"],
            "child_models": identity["child_models"],
            "billed_models": identity["billed_models"],
            "auxiliary_billed_models": identity["auxiliary_billed_models"],
            "inner_accounting": {
                "complete": complete,
                "known_spend_usd": cost,
                "reserved_usd": snapshot["reserved_usd"] if snapshot is not None else None,
                "unresolved": snapshot["unresolved"] if snapshot is not None else None,
                "calls": len(snapshot["invocations"]) if snapshot is not None else 0,
            },
            "error": str(error)[:1000] if error is not None else None,
            "started_at": started_at.isoformat(), "finished_at": finished_at.isoformat(),
            "wall_clock_s": round(time.monotonic() - started, 6),
        }

    def run(self, request: ControllerRequest) -> dict:
        actor, controller_root = self._validate(request)
        workspace = controller_root / request.invocation_id
        if workspace.exists():
            raise ValueError(f"Controller workspace already exists: {workspace}")
        controller_root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(actor, workspace)
        run_dir = workspace / "runs" / "controller"
        started_at = dt.datetime.now(dt.timezone.utc)
        started = time.monotonic()
        result = None
        error = None
        try:
            result = self.run_quick(
                self.prompt(request), workspace, request.allowance_usd,
                request.role_timeout_s,
                lambda remaining: system_controller.LiveRoleRunner(
                    workspace, remaining, permission_args=(), extra_args=CONTROLLER_ARGS,
                    stream_json=True, require_identity=True,
                ),
                run_id="controller", elapsed_limit_s=request.elapsed_limit_s,
            )
        except Exception as exc:  # durable accounting must survive every ordinary owned exit
            error = exc
        snapshot = self._snapshot(run_dir)
        outcome = self._outcome(result, run_dir, snapshot, started_at, started, error)
        outcome["controller_run_dir"] = f"{request.invocation_id}/runs/controller"
        return outcome


def _fake_run(outcome: str, *, mismatch: bool = False, incomplete: bool = False,
              fail_before_budget: bool = False, observed: dict | None = None) -> Callable:
    def run(problem_text: str, project: Path, budget_usd: float, timeout: float,
            runner_factory: Callable, run_id: str | None = None,
            *, elapsed_limit_s: float | None = None) -> system_controller.RunResult:
        if observed is not None:
            runner = runner_factory(lambda: budget_usd)
            observed.update({
                "problem_text": problem_text, "project": project,
                "budget_usd": budget_usd, "timeout": timeout,
                "run_id": run_id, "elapsed_limit_s": elapsed_limit_s,
                "stream_json": runner.stream_json,
                "require_identity": runner.require_identity,
                "permission_args": runner.permission_args,
                "extra_args": runner.extra_args,
            })
        if fail_before_budget:
            raise RuntimeError("synthetic failure before inner budget")
        run_dir = project / "runs" / str(run_id)
        run_dir.mkdir(parents=True)
        budget = DispatchBudget(run_dir / "dispatch-budget.json", budget_usd)
        rows = (
            ("frame-001", 0.12, "claude-opus-5", 11),
            ("verify-001", 0.08, "claude-sonnet-5", 7),
        )
        for index, (ident, cost, model, output_tokens) in enumerate(rows):
            budget.reserve(ident, 0.5, 0.01,
                           {"phase": "frame" if index == 0 else "verify",
                            "role": "framer" if index == 0 else "verifier",
                            "cell": "worker-opus-high" if index == 0 else "worker-sonnet-medium"})
            budget.start(ident)
            actual = "claude-haiku-4-5" if mismatch and index == 1 else model
            telemetry = {
                "status": "completed",
                "usage": {"input_tokens": 100 + index,
                          "cache_creation_input_tokens": 5,
                          "cache_read_input_tokens": 20,
                          "output_tokens": output_tokens},
                "identity": {
                    "expected_model": model, "actual_model": actual,
                    "identity_valid": actual == model,
                    "root_models": [actual], "child_models": [],
                    "billed_models": [actual, "claude-haiku-4-5-20251001"],
                    "auxiliary_billed_models": ["claude-haiku-4-5-20251001"],
                },
            }
            final = not (incomplete and index == 1)
            budget.settle(ident, cost, final=final, telemetry=telemetry,
                          evidence="offline-controller-fixture")
        report = "# Controller report\n\nPreserve explicit falsey values by comparing with None.\n"
        (run_dir / "REPORT.md").write_text(report, encoding="utf-8", newline="\n")
        if incomplete:
            raise RuntimeError("synthetic interruption with inner hold")
        record = {"type": "SolutionRecord", "technique": "subtract"}
        return system_controller.RunResult(outcome, record, run_dir, 0.20, 2, 0.0, True)
    return run


def run_qualification(work: Path) -> dict:
    actor = work / "actor"
    shutil.copytree(realworld.FIXTURES / "development" / "D01" / "repo", actor)
    actor_before = evaluation_runner.tree_snapshot(actor)
    issue = (realworld.FIXTURES / "development" / "D01" / "issue.md").read_text(encoding="utf-8")
    observed: dict = {}
    request = ControllerRequest(
        actor_root=actor, controller_root=work / "controllers", issue=issue,
        allowed_edits=("consumer/config.py",), observations=({"public_passed": False},),
        allowance_usd=1.0, invocation_id="qualification",
    )
    success = LiveControllerAdapter(_fake_run("solution", observed=observed)).run(request)
    mismatch = LiveControllerAdapter(_fake_run("gap", mismatch=True)).run(
        dataclasses.replace(request, invocation_id="mismatch"))
    incomplete = LiveControllerAdapter(_fake_run("gap", incomplete=True)).run(
        dataclasses.replace(request, invocation_id="incomplete"))
    missing = LiveControllerAdapter(_fake_run("error", fail_before_budget=True)).run(
        dataclasses.replace(request, invocation_id="missing"))
    actor_after = evaluation_runner.tree_snapshot(actor)
    checks = {
        "restricted_read_only_runner": observed.get("stream_json") is True
        and observed.get("require_identity") is True
        and observed.get("permission_args") == ()
        and tuple(observed.get("extra_args") or ()) == CONTROLLER_ARGS
        and "Read,Glob,Grep" in observed.get("extra_args", ())
        and "Edit" not in observed.get("extra_args", ())
        and "Bash" not in observed.get("extra_args", ()),
        "workspace_isolated_from_actor": actor_before == actor_after
        and success["controller_run_dir"] == "qualification/runs/controller",
        "aggregate_cost_exact": success["terminal"] is True
        and success["cost_usd"] == 0.20 and success["inner_accounting"]["complete"] is True,
        "aggregate_usage_exact": success["usage"]["input_tokens"] == 201
        and success["usage"]["output_tokens"] == 18
        and success["usage"]["includes_descendants"] is True,
        "per_role_identity_proven": success["identity_valid"] is True
        and success["served_models"] == ["claude-opus-5", "claude-sonnet-5"]
        and "claude-haiku-4-5-20251001" in success["auxiliary_billed_models"],
        "report_guidance_and_technique_returned": "comparing with None" in success["guidance"]
        and success["winning_technique"] == "subtract",
        "mismatch_preserves_cost_and_rejects_identity": mismatch["terminal"] is True
        and mismatch["cost_usd"] == 0.20 and mismatch["identity_valid"] is False,
        "incomplete_inner_charge_retains_outer_hold": incomplete["terminal"] is False
        and incomplete["cost_usd"] == 0.20
        and incomplete["inner_accounting"]["reserved_usd"] > 0,
        "pre_budget_failure_has_unknown_cost": missing["terminal"] is False
        and missing["cost_usd"] is None and missing["controller_outcome"] == "error",
    }
    def clean(value: dict) -> dict:
        value = json.loads(json.dumps(value))
        value["controller_run_dir"] = value["controller_run_dir"].replace(str(work.resolve()), "<qualification>")
        value["started_at"] = value["finished_at"] = "qualification-clock"
        value["wall_clock_s"] = 0.0
        return value
    return {
        "schema_version": 1, "mode": "offline-injected-controller-v1",
        "offline_only": True, "model_calls": 0,
        "result": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "cases": {"success": clean(success), "mismatch": clean(mismatch),
                  "incomplete": clean(incomplete), "missing": clean(missing)},
        "limits": [
            "Qualification injects the Controller entry point and makes no provider calls.",
            "The first paid pilot must confirm the live streamed schema and per-role model events.",
        ],
    }


def render_report(value: dict) -> str:
    lines = [
        "# Live Controller adapter offline qualification", "",
        f"Result: **{value['result']}**. Mode: `{value['mode']}`. Model calls: **0**.", "",
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
        return False, f"cannot read live Controller evidence: {exc}"
    recorded = value.pop("evidence_sha256", None)
    report = value.get("report") or {}
    report_path = (ROOT / str(report.get("path", ""))).resolve()
    checks = value.get("checks") or {}
    ok = bool(
        recorded == digest(value) and value.get("result") == "PASS"
        and value.get("offline_only") is True and value.get("model_calls") == 0
        and value.get("implementation_sha256") == file_sha256(Path(__file__))
        and len(checks) == 9 and all(checks.values())
        and report_path.is_relative_to(ROOT.resolve()) and report_path.is_file()
        and report.get("sha256") == file_sha256(report_path)
    )
    return ok, f"mode={value.get('mode')}; digest={'valid' if recorded == digest(value) else 'invalid'}"


def atomic_json(path: Path, value: dict) -> None:
    evaluation_runner.atomic_json(path, value)


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
    with tempfile.TemporaryDirectory(prefix="live-controller-adapter-") as folder:
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
    print(f"{value['result']}: live Controller adapter, 0 model calls")
    print(f"wrote {output.relative_to(ROOT)}")
    return 0 if value["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
