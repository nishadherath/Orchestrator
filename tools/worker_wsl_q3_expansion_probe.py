#!/usr/bin/env python3
"""Provider-free four-file Q3 paid-adapter transport probe in WSL."""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import tempfile
import uuid
from pathlib import Path

from worker_adapter import WorkerRequest, digest
from worker_q3_public_catalogue import FIXTURES, ROOT, build, sha
from worker_wsl_q1 import SEEDS
from worker_wsl_q3_adapter import LAUNCHER, Q3WslAdapter


def run() -> dict:
    task = build("P03")
    frozen = json.loads((FIXTURES / "P03/task.json").read_text(encoding="utf-8"))
    if task != frozen:
        raise RuntimeError("P03 task differs from its freeze")

    class FakeAdapter(Q3WslAdapter):
        def _invoke(self, command, actor, request):
            edits = repr(task["editable_paths"])
            code = ("import json; from pathlib import Path; "
                    f"[p.write_bytes(p.read_bytes()+b'\\n# fake four-file edit\\n') for p in map(Path,{edits})]; "
                    "print(json.dumps({'type':'assistant','message':{'model':'claude-sonnet-5'}})); "
                    "print(json.dumps({'type':'result','subtype':'success',"
                    "'total_cost_usd':0.0,'usage':{'input_tokens':0,'output_tokens':0}}))")
            return subprocess.run([str(LAUNCHER), str(actor), "--",
                "/usr/bin/python3", "-B", "-c", code], cwd="/",
                capture_output=True, text=True, timeout=45)

    with tempfile.TemporaryDirectory(prefix="q3-four-file-probe-", dir=SEEDS) as raw:
        workspace = Path(raw)
        for relative in task["actor_files"]:
            target = workspace / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((FIXTURES / "P03/actor" / relative).read_bytes())
        protected = sorted(set(task["actor_files"]) - set(task["editable_paths"]))
        before = {name: sha(workspace / name) for name in protected}
        adapter = FakeAdapter(task)
        request = WorkerRequest(workspace, "Provider-free four-file boundary probe",
                                tuple(task["editable_paths"]), "worker-sonnet-low",
                                6.0, "Probe only", timeout_s=60,
                                admission_token=uuid.uuid4().hex,
                                invocation_id=uuid.uuid4().hex,
                                revision_id=uuid.uuid4().hex,
                                decision_digest=uuid.uuid4().hex,
                                intent_digest=uuid.uuid4().hex)
        receipt = adapter.run(request)
        boundary = receipt.get("command_contract", {}).get("q3_boundary", {})
        checks = {
            "fake_provider_only": receipt.get("cost_usd") == 0.0,
            "model_identity": receipt.get("actual_model") == "claude-sonnet-5"
                              and receipt.get("identity_valid") is True,
            "writer_stopped": receipt.get("terminal") is True
                              and receipt.get("writer_stopped") is True,
            "four_edits_collected": boundary.get("changed_paths") == sorted(task["editable_paths"]),
            "protected_unchanged": before == {name: sha(workspace / name)
                                                for name in protected},
            "four_source_edits_visible": all((workspace / name).read_bytes().endswith(
                b"# fake four-file edit\n") for name in task["editable_paths"]),
            "q1_receipt_bound": bool(boundary.get("q1_record_sha256")
                                      and boundary.get("q1_spec_sha256")),
        }
    value = {"schema_version": 1, "recorded_at_utc": dt.datetime.now(
                 dt.timezone.utc).isoformat(timespec="seconds"),
             "task_id": "P03", "task_sha256": task["task_sha256"],
             "provider_calls": 0, "provider_cost_usd": 0,
             "checks": checks,
             "source_sha256": {name: sha(ROOT / name) for name in (
                 "tools/worker_wsl_q3_expansion_probe.py",
                 "tools/worker_wsl_q3_adapter.py")},
             "result": "PASS" if all(checks.values()) else "FAIL"}
    value["evidence_sha256"] = digest(value)
    output = ROOT / "test/results" / (dt.datetime.now(dt.timezone.utc).date().isoformat()
                                    + "-worker-q3-expansion-transport.json")
    if output.exists():
        raise RuntimeError("transport evidence already exists; no overwrite")
    output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8", newline="\n")
    return value


if __name__ == "__main__":
    evidence = run()
    print(evidence["result"], evidence["checks"], evidence["evidence_sha256"])
    raise SystemExit(0 if evidence["result"] == "PASS" else 2)
