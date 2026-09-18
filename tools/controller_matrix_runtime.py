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
import evaluation_live_worker  # noqa: E402
import evaluation_runner  # noqa: E402
import model_registry  # noqa: E402
from dispatch_budget import DispatchBudget  # noqa: E402

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


def validate_manifest(value: dict) -> None:
    recorded = value.get("manifest_sha256")
    unsigned = {key: item for key, item in value.items() if key != "manifest_sha256"}
    if recorded != controller_evaluation.digest(unsigned):
        raise MatrixRuntimeError("manifest digest is invalid")
    if (value.get("stage") != "matrix-calibration" or value.get("execution_enabled") is not True
            or value.get("launch_readiness") != "authorisation-required"):
        raise MatrixRuntimeError("matrix manifest is not launch-ready")
    if len(value.get("episodes", ())) != 60 or value.get("maximum_authorised_usd") != 48.75:
        raise MatrixRuntimeError("matrix schedule or ceiling is invalid")
    for relative, expected in value.get("bound_files", {}).items():
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            raise MatrixRuntimeError(f"bound file is missing or unsafe: {relative}")
        if controller_evaluation.file_digest(path) != expected:
            raise MatrixRuntimeError(f"bound file changed: {relative}")


def execute(manifest_path: Path, authorisation_path: Path, run_root: Path,
            adapter: MatrixAdapter | None = None) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_manifest(manifest)
    authorisation = json.loads(authorisation_path.read_text(encoding="utf-8"))
    if not controller_evaluation.validate_authorisation(authorisation, manifest):
        raise MatrixRuntimeError("exact active authorisation is absent or invalid")
    adapter = adapter or MatrixAdapter()
    run_root.mkdir(parents=True, exist_ok=True)
    state_path = run_root / "state.json"
    if state_path.is_file():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("manifest_sha256") != manifest["manifest_sha256"]:
            raise MatrixRuntimeError("run root belongs to another manifest")
        current = state.get("current")
        if current and current.get("stage") != "complete":
            state["status"] = "stopped"
            state["stop_reason"] = "persisted dispatch may have billed; reconcile without replay"
            evaluation_runner.atomic_json(state_path, state)
            return state
    else:
        state = {"schema_version": 1, "manifest_sha256": manifest["manifest_sha256"],
                 "status": "running", "episodes": {}, "current": None,
                 "known_spend_usd": 0.0}
        evaluation_runner.atomic_json(state_path, state)
    if state["status"] == "completed":
        return state
    for episode in manifest["episodes"]:
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
                            "stage": "dispatch-intent", "allowance_usd": allowance}
        evaluation_runner.atomic_json(state_path, state)
        budget.start(invocation_id)
        state["current"]["stage"] = "running"
        evaluation_runner.atomic_json(state_path, state)
        try:
            result = adapter.run(episode, episode_root)
        except Exception as exc:
            budget.settle(invocation_id, None, final=False,
                          telemetry={"exception_type": type(exc).__name__},
                          evidence="adapter exception; provider billing unknown")
            state["status"] = "stopped"
            state["stop_reason"] = f"{episode_id} adapter failed with uncertain billing"
            evaluation_runner.atomic_json(state_path, state)
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
            evaluation_runner.atomic_json(state_path, state)
            return state
        evaluation_runner.atomic_json(state_path, state)
    state["status"] = "completed"
    state["stop_reason"] = None
    evaluation_runner.atomic_json(state_path, state)
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
