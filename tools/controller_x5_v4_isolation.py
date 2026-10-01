#!/usr/bin/env python3
"""Probe X5 v4 public actor isolation without a provider call."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tools/controller_x5_v4_actor_probe.py"
CASES = {
    "payment_replay": ("parallel_retry",
                       "Payment incident after an uncertain response"),
    "tenant_feature": ("update_invalidation",
                       "Feature result seen by the wrong tenant"),
    "lease_lag": ("stale_ack",
                  "Lease queue lag during ownership changes"),
    "monetary_discrepancy": ("binary_boundary",
                            "Ledger and statement disagree at cent boundaries"),
}
sys.path.insert(0, "/opt/orchestrator-worker-runtime")
import worker_wsl_q2_verify as q2  # noqa: E402


def run(case: str) -> dict:
    if os.name != "posix" or os.geteuid() != 0 or case not in CASES:
        raise RuntimeError("X5 isolation requires WSL root and a known case")
    actor = ROOT / "test/fixtures/controller_x5_v4" / case / "actor"
    oracle = ROOT / "test/oracles/controller_x5_v4" / case / "acceptance.json"
    oracle_sha = hashlib.sha256(oracle.read_bytes()).hexdigest()
    source = Path(tempfile.mkdtemp(prefix="x5-v4-isolation-", dir=q2.SEEDS))
    package = manifest_path = None
    uncertain = False
    try:
        shutil.copytree(actor, source, dirs_exist_ok=True)
        shutil.copy2(PROBE, source / "x5_probe.py")
        package, manifest_path, manifest = q2.copy_package(source, None)
        result = q2.run_isolated(
            package, manifest_path, manifest,
            ["/usr/bin/python3", "-B", "x5_probe.py", str(oracle),
             *CASES[case]])
        if result.returncode:
            raise RuntimeError(f"{case}: isolated probe exit {result.returncode}: "
                               + result.stderr[-400:])
        value = json.loads(result.stdout)
        if value.get("result") != "PASS" or value.get("provider_calls") != 0:
            raise RuntimeError(f"{case}: isolation failed: {value.get('checks')}; "
                               f"diagnostic={value.get('diagnostic')}")
        if hashlib.sha256(oracle.read_bytes()).hexdigest() != oracle_sha:
            raise RuntimeError(f"{case}: protected oracle changed during probe")
        return {"schema_version": 1, "case": case, "result": "PASS",
                "oracle_sha256": oracle_sha, **value}
    except q2.UncertainActorError:
        uncertain = True
        raise
    finally:
        if not uncertain:
            if package is not None:
                q2.dispose(package, q2.SEEDS)
            if manifest_path is not None:
                manifest_path.unlink(missing_ok=True)
            q2.dispose(source, q2.SEEDS)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=CASES)
    args = parser.parse_args()
    print(json.dumps(run(args.case), sort_keys=True))
