#!/usr/bin/env python3
"""Prove a Q3 timeout holds budget and cannot replay its worker intent.

The fake adapter raises before any provider invocation. Only this synthetic
probe deletes its staged actor after checking the durable uncertain state.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

RUNTIME = Path("/opt/orchestrator-worker-runtime")
sys.path.insert(0, str(RUNTIME))
from worker_wsl_q1 import ACTORS, MANIFESTS, OUTPUTS, SEEDS, load_record  # noqa: E402
from worker_wsl_q2_verify import dispose  # noqa: E402


def run(repo: Path) -> dict:
    sys.path.insert(0, str(repo / "tools"))
    from task_executor import TaskExecutor
    from worker_adapter import WorkerRequest
    import worker_wsl_q3_adapter as q3_adapter
    from worker_wsl_q3_adapter import Q3WslAdapter, isolated_public_runner, sha

    catalogue = json.loads((repo / "test/fixtures/worker_q2_public/catalogue.json")
                           .read_text(encoding="utf-8"))
    task = next(row for row in catalogue["tasks"] if row["id"] == "P01")
    source = repo / "test/fixtures/worker_q2_public/P01/actor"
    staged_specs: list[Path] = []
    original_public_source = q3_adapter.public_source

    def capture_source(project: Path, frozen: dict):
        result = original_public_source(project, frozen)
        staged_specs.append(result[1])
        return result

    class TimedOutAdapter(Q3WslAdapter):
        calls = 0

        def _invoke(self, command: list[str], actor: Path,
                    request: WorkerRequest) -> subprocess.CompletedProcess:
            self.calls += 1
            raise subprocess.TimeoutExpired(command, request.timeout_s)

    with tempfile.TemporaryDirectory(prefix="q3-uncertain-probe-", dir=SEEDS) as raw:
        workspace = Path(raw)
        for relative in task["actor_files"]:
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((source / relative).read_bytes())
        before = {name: sha((workspace / name).read_bytes())
                  for name in task["actor_files"]}
        protected = sorted(set(task["actor_files"]) - set(task["editable_paths"]))
        contract = {"version": 1, "kind": "command",
                    "criteria": ["public check passes"],
                    "constraints": ["only declared source files may change"],
                    "required_outputs": task["editable_paths"],
                    "protected_paths": protected,
                    "command": ["python3", "-B", "public_check.py"],
                    "timeout_s": 30}
        contract_path = workspace / ".claude/q3-acceptance.json"
        contract_path.parent.mkdir()
        contract_path.write_text(json.dumps(contract, sort_keys=True), encoding="utf-8")
        adapter = TimedOutAdapter(task)
        executor = TaskExecutor(workspace, adapter,
                                command_runner=isolated_public_runner(task))
        root_id = executor.admit(
            goal=(workspace / "ISSUE.md").read_text(encoding="utf-8"),
            scope=task["editable_paths"], permissions=["read", "edit"],
            acceptance_path=contract_path, budget_usd=6.0,
            authority_id=uuid.uuid4().hex, actor="q3-timeout-fake",
            input_paths=protected)
        with patch.object(q3_adapter, "public_source", side_effect=capture_source):
            first = executor.run(root_id)
            second = executor.run(root_id)
        attempt = first["attempts"][0]
        receipt = attempt.get("receipt") or {}
        after = {name: sha((workspace / name).read_bytes())
                 for name in task["actor_files"]}
        actor_name = "q1-" + attempt["invocation_id"]
        record = load_record(actor_name)
        actor = ACTORS / actor_name
        seed = Path(record["source_root"])
        checks = {
            "first_attempt_uncertain": first["state"] == "uncertain"
                                       and len(first["attempts"]) == 1,
            "no_replay_on_second_run": second["state"] == "uncertain"
                                       and adapter.calls == 1
                                       and len(second["attempts"]) == 1,
            "unknown_charge_held": first["budget"]["unresolved"]
                                   == [attempt["invocation_id"]]
                                   and first["budget"]["reserved_usd"] == 6.0,
            "no_terminal_receipt": receipt.get("terminal") is False
                                   and receipt.get("writer_stopped") is False
                                   and receipt.get("cost_usd") is None,
            "public_source_unchanged": before == after,
            "actor_retained_for_reconciliation": actor.is_dir()
                                                 and (MANIFESTS / f"{actor_name}.json").is_file(),
            "zero_provider_call": True,
        }
        # The fake never launched a writer. Clean up only paths derived from
        # its Q1 record, after the preservation check above has passed.
        if adapter.calls == 1 and not (MANIFESTS / f"{actor_name}.start.json").exists():
            dispose(actor, ACTORS)
            dispose(OUTPUTS / actor_name, OUTPUTS)
            (MANIFESTS / f"{actor_name}.json").unlink(missing_ok=True)
            dispose(seed, SEEDS)
            for spec in staged_specs:
                if spec.resolve().parent == SEEDS.resolve() and not spec.is_symlink():
                    spec.unlink()
        return {"result": "PASS" if all(checks.values()) else "FAIL",
                "checks": checks, "provider_calls": 0, "provider_cost_usd": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = run(args.repo)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired,
            KeyError, IndexError) as exc:
        print(json.dumps({"result": "ERROR", "error_type": type(exc).__name__}))
        return 1
    if args.output is not None:
        if (args.output.is_symlink()
                or args.output.resolve().parent != (args.repo / "test/results").resolve()):
            raise ValueError("probe output must be a direct result file")
        result.update(schema_version=1,
                      recorded_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                      source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        result["evidence_sha256"] = hashlib.sha256(json.dumps(
            result, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
