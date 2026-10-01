#!/usr/bin/env python3
"""Read-only public baseline probes for three possible X5 development cases.

This file lives outside the frozen runtime inventory. It never imports a
protected oracle, edits an actor, or invokes an AI provider.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "test/fixtures/controller_x3/development"
CASES = {
    "C01-D1": {
        "input": {
            "orders": [
                {"account": "west", "id": "PO-007"},
                {"account": "east", "id": "PO-007"},
            ],
            "receipts": [{"account": "west", "id": "po-7"}],
        },
        "expected_baseline": {"settled": [], "pending": ["PO-007", "PO-007"]},
        "source_files": ("app.py", "reconcile.py"),
    },
    "C06-D1": {
        "input": {
            "leases": [
                {"id": "w-east", "server_now": 80, "worker_now": 103,
                 "expires_at": 100},
                {"id": "w-west", "server_now": 80, "worker_now": 80,
                 "expires_at": 100},
                {"id": "w-slow", "server_now": 103, "worker_now": 80,
                 "expires_at": 100},
            ],
        },
        "expected_baseline": {"renewable": ["w-west", "w-slow"],
                              "expired": ["w-east"]},
        "source_files": ("app.py", "lease.py"),
    },
    "C07-D1": {
        "input": {"amounts": ["0.005", "0.005"]},
        "expected_baseline": {"ledger": "0.00", "statement": "0.01"},
        "source_files": ("app.py", "money.py", "ledger.py", "statement.py"),
    },
}


def main() -> None:
    result = {"schema_version": 1, "provider_calls": 0, "cases": []}
    for case_id, spec in CASES.items():
        actor = BASE / case_id / "actor"
        completed = subprocess.run(
            [sys.executable, "-B", "app.py"], cwd=actor,
            input=json.dumps(spec["input"]) + "\n", text=True,
            capture_output=True, timeout=5, check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"{case_id} baseline failed to run")
        observed = json.loads(completed.stdout)
        if observed != spec["expected_baseline"]:
            raise RuntimeError(f"{case_id} baseline changed")
        result["cases"].append({
            "task_id": case_id,
            "input": spec["input"],
            "observed": observed,
            "source_sha256": {name: hashlib.sha256((actor / name).read_bytes()).hexdigest()
                              for name in spec["source_files"]},
        })
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
