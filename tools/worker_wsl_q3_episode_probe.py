#!/usr/bin/env python3
"""Prove B0 TaskExecutor accounting and acceptance with a fake WSL worker."""
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path


def run(repo: Path) -> dict:
    sys.path.insert(0, str(repo / "tools"))
    import model_registry
    from task_executor import TaskExecutor
    from worker_adapter import WorkerRequest
    from worker_wsl_q3_adapter import LAUNCHER, Q3WslAdapter, isolated_public_runner, sha

    catalogue = json.loads((repo / "test/fixtures/worker_q2_public/catalogue.json")
                           .read_text(encoding="utf-8"))
    task = next(row for row in catalogue["tasks"] if row["id"] == "P01")
    source = repo / "test/fixtures/worker_q2_public/P01/actor"
    reference = repo / "test/fixtures/worker_q2_public/P01/reference"
    payload = {relative: base64.b64encode((reference / relative).read_bytes()).decode("ascii")
               for relative in task["editable_paths"]}

    class FakeAdapter(Q3WslAdapter):
        def _invoke(self, command: list[str], actor: Path,
                    request: WorkerRequest) -> subprocess.CompletedProcess:
            # Only the provider-free test overrides the paid call. The clean
            # upstream bytes stand in for a worker's two-file repair.
            encoded = json.dumps(payload, sort_keys=True)
            model = model_registry.resolve_cell("worker-sonnet-low")["cli_model"]
            code = ("import base64,json; from pathlib import Path; "
                    f"data=json.loads({json.dumps(encoded)}); "
                    "[Path(p).write_bytes(base64.b64decode(v)) for p,v in data.items()]; "
                    f"print(json.dumps({{'type':'assistant','message':{{'model':'{model}'}}}})); "
                    "print(json.dumps({'type':'result','subtype':'success',"
                    "'total_cost_usd':0.0,'usage':{'input_tokens':0,'output_tokens':0}}))")
            argv = [str(LAUNCHER), str(actor), "--", "/usr/bin/python3", "-B", "-c", code]
            return subprocess.run(argv, cwd="/", capture_output=True, text=True,
                                  timeout=30)

    parent = Path("/var/lib/orchestrator-worker-n4/seed")
    with tempfile.TemporaryDirectory(prefix="q3-episode-probe-", dir=parent) as directory:
        workspace = Path(directory)
        for relative in task["actor_files"]:
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((source / relative).read_bytes())
        protected = sorted(set(task["actor_files"]) - set(task["editable_paths"]))
        protected_before = {relative: sha((workspace / relative).read_bytes())
                            for relative in protected}
        contract = {"version": 1, "kind": "command",
                    "criteria": ["public check passes"],
                    "constraints": ["only the two declared source files may change"],
                    "required_outputs": task["editable_paths"],
                    "protected_paths": protected,
                    "command": ["python3", "-B", "public_check.py"],
                    "timeout_s": 30}
        contract_path = workspace / ".claude/q3-acceptance.json"
        contract_path.parent.mkdir()
        contract_path.write_text(json.dumps(contract, sort_keys=True), encoding="utf-8")
        executor = TaskExecutor(workspace, FakeAdapter(task),
                                command_runner=isolated_public_runner(task))
        root_id = executor.admit(goal=(workspace / "ISSUE.md").read_text(encoding="utf-8"),
                                 scope=task["editable_paths"], permissions=["read", "edit"],
                                 acceptance_path=contract_path, budget_usd=6.0,
                                 authority_id=uuid.uuid4().hex, actor="q3-provider-free-probe",
                                 input_paths=protected)
        outcome = executor.run(root_id)
        attempts = outcome["attempts"]
        receipt = attempts[0].get("receipt") if attempts else None
        protected_after = {relative: sha((workspace / relative).read_bytes())
                           for relative in protected}
        checks = {
            "b0_accepted_after_one_fake_call": outcome["state"] == "accepted"
                                               and len(attempts) == 1,
            "first_cell_sonnet_low": attempts[0]["requested_cell"] == "worker-sonnet-low",
            "zero_cost_settled": outcome["budget"]["spent_usd"] == 0
                                 and outcome["budget"]["unresolved"] == [],
            "terminal_receipt_bound": bool(receipt and receipt["terminal"]
                                           and receipt["writer_stopped"]
                                           and receipt["command_contract"].get("q3_boundary")),
            "isolated_acceptance": attempts[0]["verification"]["status"] == "pass"
                                   and bool(attempts[0]["verification"]["evidence"]
                                            ["command"].get("isolation_evidence")),
            "two_reference_edits_collected": all((workspace / relative).read_bytes()
                                                 == (reference / relative).read_bytes()
                                                 for relative in task["editable_paths"]),
            "protected_source_unchanged": protected_before == protected_after,
        }
        return {"result": "PASS" if all(checks.values()) else "FAIL",
                "checks": checks, "provider_calls": 0, "provider_cost_usd": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.repo)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired, KeyError) as exc:
        print(json.dumps({"result": "ERROR", "error": str(exc)[:500]}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
