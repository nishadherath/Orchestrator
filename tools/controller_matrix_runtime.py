#!/usr/bin/env python3
"""Crash-safe R5 15-cell identity and microtask campaign runtime."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import controller_evaluation  # noqa: E402
import controller_campaign_state  # noqa: E402
import controller_campaign_manifest  # noqa: E402
import evaluation_live_worker  # noqa: E402
import evaluation_runner  # noqa: E402
import model_registry  # noqa: E402
import route  # noqa: E402
from dispatch_budget import BudgetExhausted, DispatchBudget  # noqa: E402

Transport = Callable[[list[str], Path, dict[str, str], float], subprocess.CompletedProcess]
DEFAULT_AUTHORISATION = ROOT / "docs" / "CONTROLLER-ROUTING-R5-MATRIX-AUTHORISATION.json"
DEFAULT_RUN_ROOT = ROOT / "pilot-runs" / "controller-routing-v1-matrix"


class MatrixRuntimeError(RuntimeError):
    """The matrix is unqualified, unauthorised or unsafe to continue."""


def _default_transport(cmd: list[str], cwd: Path, env: dict[str, str],
                       timeout: float) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                          encoding="utf-8", timeout=timeout)


class MatrixAdapter:
    """Run one no-tool calibration call with exact model and effort flags."""

    def __init__(self, transport: Transport | None = None):
        self.transport = transport or _default_transport

    @staticmethod
    def command(episode: dict) -> list[str]:
        cell = model_registry.resolve_cell(episode["cell"])
        prompt = episode.get("prompt") or episode["task"]["prompt"]
        return [
            "claude", "-p", prompt, "--output-format", "stream-json", "--verbose",
            "--model", cell["cli_model"], "--effort", cell["effort"],
            "--max-budget-usd", str(episode["maximum_usd"]),
            "--restricted", "--safe-mode", "--strict-mcp-config",
            "--no-session-persistence", "--permission-mode", "dontAsk",
            "--permission-prompts", "none", "--system-prompt",
            "Complete only the supplied calibration task. Do not use tools.",
            "--tools", "",
        ]

    def run(self, episode: dict, cwd: Path) -> dict:
        command = self.command(episode)
        resolved = model_registry.resolve_cell(episode["cell"])
        started_at = dt.datetime.now(dt.timezone.utc)
        started = time.monotonic()
        timed_out = False
        try:
            proc = self.transport(command, cwd.resolve(), {**os.environ}, episode["timeout_seconds"])
            stdout, stderr = proc.stdout or "", proc.stderr or ""
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            proc = subprocess.CompletedProcess(command, 124, stdout, stderr)
        parsed = evaluation_live_worker.parse_stream(stdout)
        final = parsed["final"]
        cost = evaluation_live_worker.safe_number(final.get("total_cost_usd"))
        actual = parsed["root_models"][0] if len(parsed["root_models"]) == 1 else None
        identity_valid = model_registry.identity_matches(episode["cell"], actual,
                                                         parsed["child_models"])
        terminal = bool(not timed_out and final.get("type") == "result" and cost is not None)
        success = bool(terminal and proc.returncode == 0 and final.get("subtype") == "success"
                       and identity_valid and parsed["invalid_line_count"] == 0
                       and cost <= episode["maximum_usd"])
        return {
            "status": "completed" if success else ("interrupted" if timed_out else "failed"),
            "terminal": terminal, "identity_valid": identity_valid,
            "requested_cell": episode["cell"], "expected_model": resolved["expected_provider_model"],
            "actual_model": actual, "requested_effort": resolved["effort"],
            "effort_evidence": f"cli-argument:{resolved['effort']}",
            "served_effort_observable": False,
            "cost_usd": cost, "usage": final.get("usage") if isinstance(final.get("usage"), dict) else {},
            "result": str(final.get("result", "")),
            "root_models": parsed["root_models"], "child_models": parsed["child_models"],
            "billed_models": parsed["billed_models"], "invalid_line_count": parsed["invalid_line_count"],
            "returncode": proc.returncode, "timed_out": timed_out,
            "started_at": started_at.isoformat(),
            "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "wall_clock_s": round(time.monotonic() - started, 6),
            "stderr_tail": stderr.strip()[-500:],
            "command_sha256": controller_evaluation.digest(command),
        }


def validate_manifest(value: dict, *, require_materialised: bool = False) -> None:
    if value.get("schema_version") != 2:
        raise MatrixRuntimeError("archived R5 manifest is not runnable; freeze a new v2 package")
    recorded = value.get("manifest_sha256")
    unsigned = {key: item for key, item in value.items() if key != "manifest_sha256"}
    if recorded != controller_evaluation.digest(unsigned):
        raise MatrixRuntimeError("manifest digest is invalid")
    if (value.get("stage") != "matrix-calibration" or value.get("execution_enabled") is not True
            or value.get("launch_readiness") != "authorisation-required"):
        raise MatrixRuntimeError("matrix manifest is not launch-ready")
    continuation = value.get("continuation")
    count = len(value.get("episodes", ()))
    ceiling = value.get("maximum_authorised_usd")
    if ((continuation is None and (count != 60 or ceiling != 48.75))
            or (continuation is not None and not (1 <= count < 60
                                                  and type(ceiling) in (int, float)
                                                  and 0 < ceiling <= 48.75))):
        raise MatrixRuntimeError("matrix schedule or ceiling is invalid")
    rows = value["episodes"]
    sequences = [row.get("sequence") for row in rows]
    if ((continuation is None and sequences != list(range(1, 61)))
            or (continuation is not None and (any(type(n) is not int or n < 1 or n > 60
                                                  for n in sequences)
                                              or sequences != sorted(set(sequences))))
            or any(type(row.get("maximum_usd")) not in (int, float)
                   or row["maximum_usd"] <= 0 for row in rows)
            or sum(row["maximum_usd"] for row in rows) > ceiling + 1e-9):
        raise MatrixRuntimeError("matrix sequence or per-call allocation is invalid")
    package = value.get("runtime_package")
    if not isinstance(package, dict) or value.get("bound_files") != package.get("files"):
        raise MatrixRuntimeError("complete runtime inventory is absent")
    try:
        controller_campaign_manifest.verify_package(
            ROOT, package, require_materialised=require_materialised)
        controller_campaign_manifest.verify_host(
            value.get("host_record"), require_live=require_materialised)
        controller_campaign_manifest.verify_continuation(value)
    except controller_campaign_manifest.CampaignManifestError as exc:
        raise MatrixRuntimeError(str(exc)) from exc
    for relative, expected in value.get("bound_files", {}).items():
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            raise MatrixRuntimeError(f"bound file is missing or unsafe: {relative}")
        if controller_evaluation.file_digest(path) != expected:
            raise MatrixRuntimeError(f"bound file changed: {relative}")


def execute(manifest_path: Path, authorisation_path: Path, run_root: Path,
            adapter: MatrixAdapter | None = None, *,
            driver_lock_timeout_s: float = 10.0) -> dict:
    run_root.mkdir(parents=True, exist_ok=True)
    with route.ledger_lock(run_root / "campaign-driver.json", driver_lock_timeout_s):
        return _execute_owned(manifest_path, authorisation_path, run_root, adapter)


def cancel(run_root: Path) -> dict:
    return controller_campaign_state.cancel(run_root)


def reconcile(run_root: Path, manifest_sha256: str) -> dict:
    return controller_campaign_state.reconcile(
        run_root, manifest_sha256, kind="matrix")


def _execute_owned(manifest_path: Path, authorisation_path: Path, run_root: Path,
                   adapter: MatrixAdapter | None) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    live = adapter is None or (isinstance(adapter, MatrixAdapter)
                               and adapter.transport is _default_transport)
    validate_manifest(manifest, require_materialised=live)
    controller_campaign_manifest.verify_continuation(manifest, run_root)
    authorisation = json.loads(authorisation_path.read_text(encoding="utf-8"))
    if not controller_evaluation.validate_authorisation(authorisation, manifest):
        raise MatrixRuntimeError("exact active authorisation is absent or invalid")
    if manifest.get("continuation") and (authorisation.get("authority_id")
            != manifest["continuation"]["authority_id"]
            or authorisation.get("authority_sha256")
            != manifest["continuation"]["authority_sha256"]):
        raise MatrixRuntimeError("continuation authority differs from its grant")
    adapter = adapter or MatrixAdapter()
    run_root.mkdir(parents=True, exist_ok=True)
    state_path = run_root / "state.json"
    if state_path.is_file():
        state = controller_campaign_state.load(state_path)
        if state.get("manifest_sha256") != manifest["manifest_sha256"]:
            raise MatrixRuntimeError("run root belongs to another manifest")
        current = state.get("current")
        if current and current.get("stage") != "complete":
            state["status"] = "stopped"
            state["stop_reason"] = "persisted dispatch may have billed; reconcile without replay"
            controller_campaign_state.save(state_path, state)
            return state
    else:
        state = {"schema_version": 2, "manifest_sha256": manifest["manifest_sha256"],
                 "status": "running", "episodes": {}, "current": None,
                 "known_spend_usd": 0.0}
        controller_campaign_state.save(state_path, state)
    # A settled failure is terminal for this immutable schedule. Clearing
    # current after settlement must never make ordinary execute a continuation.
    if state["status"] != "running":
        return state
    for episode in manifest["episodes"]:
        if controller_campaign_state.cancelled(state_path):
            return controller_campaign_state.load(state_path)
        episode_id = f"matrix-{episode['sequence']:03d}-{episode['cell']}-{episode['kind']}"
        if episode_id in state["episodes"]:
            continue
        episode_root = run_root / episode_id
        episode_root.mkdir(parents=True, exist_ok=True)
        budget = DispatchBudget(episode_root / "budget.json", episode["maximum_usd"])
        invocation_id = f"call-{episode['sequence']:03d}"
        allowance = budget.reserve(invocation_id, episode["maximum_usd"], 0.001,
                                   {"cell": episode["cell"], "kind": episode["kind"]})
        state["current"] = {"episode_id": episode_id, "invocation_id": invocation_id,
                            "stage": "dispatch-intent", "allowance_usd": allowance,
                            "intent_sha256": controller_evaluation.digest({
                                "manifest": manifest["manifest_sha256"],
                                "episode": episode, "invocation": invocation_id,
                                "allowance_usd": allowance})}
        controller_campaign_state.save(state_path, state)
        try:
            budget.start(invocation_id)
        except BudgetExhausted:
            budget.settle(invocation_id, 0.0, final=True,
                          telemetry={"status": "not_launched"},
                          evidence="matrix-admission-closed-before-adapter")
            state["current"] = None
            state["status"] = "stopped"
            state["stop_reason"] = "budget or cancellation closed admission"
            return controller_campaign_state.save(state_path, state)
        state["current"]["stage"] = "running"
        controller_campaign_state.save(state_path, state)
        if controller_campaign_state.cancelled(state_path):
            budget.settle(invocation_id, 0.0, final=True,
                          telemetry={"status": "not_launched"},
                          evidence="matrix-cancelled-before-adapter")
            budget.cancel()
            state["current"] = None
            return controller_campaign_state.save(state_path, state)
        try:
            result = adapter.run(episode, episode_root)
        except Exception as exc:
            budget.settle(invocation_id, None, final=False,
                          telemetry={"exception_type": type(exc).__name__},
                          evidence="adapter exception; provider billing unknown")
            state["status"] = "stopped"
            state["stop_reason"] = f"{episode_id} adapter failed with uncertain billing"
            controller_campaign_state.save(state_path, state)
            return state
        final = bool(result["terminal"] and result["cost_usd"] is not None)
        budget.settle(invocation_id, result["cost_usd"], final=final,
                      telemetry={"status": result["status"],
                                 "identity_valid": result["identity_valid"]},
                      evidence=f"{episode_id}/result.json")
        evaluation_runner.atomic_json(episode_root / "result.json", result)
        state["episodes"][episode_id] = result
        state["known_spend_usd"] = round(sum(
            row["cost_usd"] for row in state["episodes"].values()
            if isinstance(row.get("cost_usd"), (int, float)) and not isinstance(row.get("cost_usd"), bool)), 9)
        state["current"] = None
        if result["status"] != "completed":
            state["status"] = "stopped"
            state["stop_reason"] = f"{episode_id} failed; later calls were not admitted"
            controller_campaign_state.save(state_path, state)
            return state
        controller_campaign_state.save(state_path, state)
    state["status"] = "completed"
    state["stop_reason"] = None
    controller_campaign_state.save(state_path, state)
    return state


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=Path, default=controller_evaluation.MATRIX_MANIFEST)
    parser.add_argument("--authorisation", type=Path, default=DEFAULT_AUTHORISATION)
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args(argv)
    state = execute(args.manifest, args.authorisation, args.run_root)
    print(json.dumps(state, indent=2))
    return 0 if state["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
