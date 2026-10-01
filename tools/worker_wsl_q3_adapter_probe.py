#!/usr/bin/env python3
"""Exercise Q3's real multi-file transport with a zero-provider fake actor."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path


def run(repo: Path) -> dict:
    sys.path.insert(0, str(repo / "tools"))
    import model_registry
    from worker_adapter import WorkerRequest
    from worker_wsl_q1 import MANIFESTS, OUTPUTS
    from worker_wsl_q3_adapter import (LAUNCHER, Q3BoundaryError, Q3WslAdapter,
                                       apply_collected, isolated_public_runner, sha)

    catalogue = json.loads((repo / "test/fixtures/worker_q2_public/catalogue.json")
                           .read_text(encoding="utf-8"))
    task = next(row for row in catalogue["tasks"] if row["id"] == "P01")
    source = repo / "test/fixtures/worker_q2_public/P01/actor"

    class FakeAdapter(Q3WslAdapter):
        def _invoke(self, command: list[str], actor: Path,
                    request: WorkerRequest) -> subprocess.CompletedProcess:
            # This override cannot call Claude. It edits the two declared
            # files and emits a synthetic stream for receipt parsing.
            model = model_registry.resolve_cell("worker-sonnet-low")["cli_model"]
            code = ("import json; from pathlib import Path; "
                    "[p.write_bytes(p.read_bytes()+b'\\n# q3 probe\\n') "
                    "for p in (Path('cachetools/func.py'),Path('cachetools/keys.py'))]; "
                    f"print(json.dumps({{'type':'assistant','message':{{'model':'{model}'}}}})); "
                    "print(json.dumps({'type':'result','subtype':'success',"
                    "'total_cost_usd':0.0,'usage':{'input_tokens':0,'output_tokens':0}}))")
            argv = [str(LAUNCHER), str(actor), "--", "/usr/bin/python3", "-B", "-c", code]
            return subprocess.run(argv, cwd="/", capture_output=True, text=True,
                                  timeout=30)

    parent = Path("/var/lib/orchestrator-worker-n4/seed")
    with tempfile.TemporaryDirectory(prefix="q3-adapter-probe-", dir=parent) as directory:
        workspace = Path(directory)
        for relative in task["actor_files"]:
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((source / relative).read_bytes())
        protected_before = {relative: sha((workspace / relative).read_bytes())
                            for relative in task["actor_files"]
                            if relative not in task["editable_paths"]}
        adapter = FakeAdapter(task)
        request = WorkerRequest(workspace, "Provider-free Q3 transport probe",
                                tuple(task["editable_paths"]), "worker-sonnet-low",
                                6.0, "Probe only", timeout_s=60,
                                admission_token=uuid.uuid4().hex,
                                invocation_id=uuid.uuid4().hex,
                                revision_id=uuid.uuid4().hex,
                                decision_digest=uuid.uuid4().hex,
                                intent_digest=uuid.uuid4().hex)
        receipt = adapter.run(request)
        boundary = receipt["command_contract"]["q3_boundary"]
        actor_name = boundary["actor_name"]
        spec = json.loads((MANIFESTS / f"{actor_name}.json").read_text(
            encoding="utf-8"))["spec"]
        collected = {"output_root": str(OUTPUTS / actor_name),
                     "after_sha256": boundary["after_sha256"],
                     "changed_paths": boundary["changed_paths"]}
        for relative in task["editable_paths"]:
            (workspace / relative).write_bytes((source / relative).read_bytes())
        issue = workspace / "ISSUE.md"
        original_issue = issue.read_bytes()
        issue.write_bytes(original_issue + b"\nQ3 drift probe\n")
        try:
            apply_collected(workspace, task, collected, spec)
        except Q3BoundaryError:
            protected_drift_rejected = True
        else:
            protected_drift_rejected = False
        issue.write_bytes(original_issue)
        for relative in task["editable_paths"]:
            (workspace / relative).write_bytes((OUTPUTS / actor_name / relative).read_bytes())
        public = isolated_public_runner(task)
        broken = public(["python3", "-B", "public_check.py"], cwd=workspace,
                        capture_output=True, timeout=30, shell=False)
        reference = repo / "test/fixtures/worker_q2_public/P01/reference"
        for relative in task["editable_paths"]:
            (workspace / relative).write_bytes((reference / relative).read_bytes())
        repaired = public(["python3", "-B", "public_check.py"], cwd=workspace,
                          capture_output=True, timeout=30, shell=False)
        protected_after = {relative: sha((workspace / relative).read_bytes())
                           for relative in protected_before}
        checks = {
            "terminal_fake_receipt": receipt["terminal"] is True
                                     and receipt["status"] == "completed",
            "exact_model_identity": model_registry.model_class_for_provider_id(
                receipt["actual_model"]) == "sonnet"
                                    and receipt["identity_valid"] is True,
            "two_edits_collected": set(receipt["command_contract"].get(
                "q3_boundary", {}).get("changed_paths", [])) == set(task["editable_paths"]),
            "protected_public_source_unchanged": protected_before == protected_after,
            "protected_drift_before_copy_rejected": protected_drift_rejected,
            "q1_boundary_bound": set(receipt["command_contract"].get(
                "q3_boundary", {}).get("changed_paths", [])) == set(task["editable_paths"]),
            "isolated_public_fails_on_broken": broken.returncode == 1,
            "isolated_public_passes_reference": repaired.returncode == 0,
            "public_proofs_sealed": all(isinstance(getattr(result, "isolation_evidence", None), dict)
                                        and "sha256" in result.isolation_evidence
                                        for result in (broken, repaired)),
            "zero_provider_call": receipt["cost_usd"] == 0,
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
