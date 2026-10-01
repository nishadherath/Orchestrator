#!/usr/bin/env python3
"""Exercise H03's accepted B0 to identical S/A path with a fake worker."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_h03_pilot as pilot  # noqa: E402
from task_executor import TaskExecutor  # noqa: E402
from worker_wsl_q4u_adapter import Q4UWslAdapter, isolated_public_runner  # noqa: E402


class FakeWorker:
    def __init__(self):
        self.calls = 0

    def capability(self, root):
        return {"configured": True, "actor_root": str(root.resolve()),
                "enforcement_proven": False}

    def run(self, request):
        self.calls += 1
        partial = pilot.FIXTURE / "variants/partial/system_controller.py"
        (request.actor_root / pilot.EDITABLE).write_bytes(partial.read_bytes())
        return {"admission_token": request.admission_token,
                "invocation_id": request.invocation_id,
                "revision_id": request.revision_id,
                "decision_digest": request.decision_digest,
                "intent_digest": request.intent_digest,
                "requested_cell": request.requested_cell,
                "actual_model": "claude-sonnet-5", "identity_valid": True,
                "child_models": [], "status": "completed", "terminal": True,
                "writer_stopped": True, "cost_usd": 0.1,
                "usage": {"cost_usd": 0.1, "cost_source": "provider_reported",
                          "currency": "USD", "input_tokens": 10,
                          "output_tokens": 10, "cache_creation_input_tokens": 0,
                          "cache_read_input_tokens": 0},
                "effort_evidence": "cli-argument:low",
                "started_at": "2026-10-01T00:00:00Z",
                "finished_at": "2026-10-01T00:00:01Z", "wall_clock_s": 1.0}


def main() -> None:
    row = pilot.freeze()
    suffix = uuid.uuid4().hex[:12]
    paths = {arm: pilot.SEEDS / f"h03-successor-smoke-{suffix}-{arm.lower()}"
             for arm in ("B0", "S", "A")}
    old_actor_path, old_run_dir = pilot.actor_path, pilot.RUN_DIR
    worker = FakeWorker()
    try:
        with tempfile.TemporaryDirectory(prefix="h03-successor-result-", dir=pilot.SEEDS) as raw:
            pilot.RUN_DIR = Path(raw)
            pilot.actor_path = lambda _row, arm: paths[arm]
            pilot.copy_actor(row, "B0", {
                name: (pilot.SOURCE / name).read_bytes() for name in row["actor_files"]})
            pilot.admit(row, "B0")
            adapter = Q4UWslAdapter(pilot.task(row, "B0"))
            adapter.run = worker.run
            fake = TaskExecutor(paths["B0"], adapter,
                                command_runner=isolated_public_runner(pilot.task(row, "B0")),
                                campaign_prompt=pilot.PRODUCER_PROMPT)
            state = fake.run(pilot.root_id(row, "B0"), stop_after_attempts=1)
            assert pilot.accepted_producer(state), json.dumps({
                k: v for k, v in state.items() if k != "definition"}, default=str)[:5000]
            risk = pilot.public_risk(row, paths["B0"])
            assert risk["qualified_failure"] is True, risk
            pair = pilot.prepare_successors(row, state, risk)
            assert pair["inputs"]["actor_files"]["risk_check.py"] == row["risk_check_sha256"]
            assert (paths["S"] / "REVIEW.md").read_bytes() == (
                paths["A"] / "REVIEW.md").read_bytes()
            assert (paths["S"] / "RISK-REPORT.json").read_bytes() == (
                paths["A"] / "RISK-REPORT.json").read_bytes()
            for arm in ("S", "A"):
                assert pilot.ready(row, arm).status(pilot.root_id(row, arm))["state"] == "ready"
            grades = {arm: pilot.grade_actor(row, arm)["score"] for arm in ("S", "A")}
            assert grades == {"S": 45, "A": 45}, grades
            print(json.dumps({"schema_version": 1, "fake_worker_calls": worker.calls,
                              "provider_calls": 0, "producer_state": state["state"],
                              "risk_qualified_failure": True,
                              "successor_files": len(pair["inputs"]["actor_files"]),
                              "twin_bytes_identical": True,
                              "pre_review_scores": grades}, sort_keys=True))
    finally:
        pilot.actor_path, pilot.RUN_DIR = old_actor_path, old_run_dir
        for path in paths.values():
            if path.exists():
                if path.is_symlink() or path.resolve().parent != pilot.SEEDS.resolve():
                    raise RuntimeError("unsafe smoke cleanup path")
                shutil.rmtree(path)


if __name__ == "__main__":
    main()
