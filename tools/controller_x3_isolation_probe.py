#!/usr/bin/env python3
"""Stage a registered X3 case under Q1 and probe its actor-scoped boundary.

This file runs as WSL root without invoking a provider. It copies the public
package to a private evaluator seed, adds only the probe script, then launches
the actor as UID 65534 in the existing Q1 namespace. A timeout preserves the
staged material for reconciliation rather than pretending the actor stopped.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROBE = ROOT / "tools" / "controller_x3_actor_probe.py"
TASKS = {
    "N04-R2": ("stale-generated-fixture-pair-from-source",
                "Generated service fixtures lag their declared source"),
    "N04-R1": ("feature-disable-audit-step-omitted",
                "Feature disable must retain audit and other flags"),
    "N03-R2": ("approved-destructive-cutover-time-absent",
                "Store cutover has no approved execution time"),
    "N03-R1": ("minimum-client-version-for-mandatory-trace-absent",
                "Trace requirement lacks an approved client version floor"),
    "N02-R2": ("mutable-default-lists-across-independent-calls",
                "UI section helpers retain parts from earlier calls"),
    "N02-R1": ("strict-threshold-excludes-boundary",
                "UI warning misses the exact configured threshold"),
    "N01-R2": ("stale-generated-header-and-hardcoded-generator",
                "Wire header was not regenerated from its source schema"),
    "N01-R1": ("stale-legacy-package-import-paths",
                "Shared label formatter moved to a new package path"),
    "C08-R2": ("same-term-dual-writer-and-unfenced-expired-write",
                "Writer failover can briefly create two active writers"),
    "C08-R1": ("unbounded-replay-buffer-and-arrival-order-output",
                "Replay buffer grows and emits out of order"),
    "C07-R2": ("transport-sequence-watermark-overrides-state-revision",
                "Transport order can hide a newer state revision"),
    "C07-R1": ("unicode-character-count-shifts-following-frame-boundary",
                "Unicode length breaks following transport frames"),
    "C06-R2": ("new-reader-old-row-fallback-and-new-writer-legacy-projection",
                "Mixed schema deploy strands old and new readers"),
    "C06-R1": ("broad-cache-eviction-and-uncoalesced-refills",
                "Broad cache eviction causes a load spike"),
    "C05-R2": ("little-endian-length-header-breaks-published-big-endian-frame",
                "Length header byte order breaks legacy frames"),
    "C05-R1": ("pending-queue-depth-confused-with-batch-size",
                "Producer bursts grow the pending batch queue"),
    "C04-R2": ("pooled-tenant-session-state-survives-return",
                "Pooled connections retain a prior tenant's session state"),
    "C04-R1": ("object-id-lookup-missing-tenant-ownership",
                "A report lookup can cross tenant ownership"),
    "C03-R2": ("sequence-watermark-confused-with-delivery-identity",
                "Webhook receipts can repeat or arrive out of order"),
    "C03-R1": ("unfenced-lease-owner-transfer",
                "Lease transfer can accept an old worker's completion"),
    "C02-R2": ("checkpoint-overlap-and-prefix-tombstone-resurrection",
                "Compaction changes replayed state"),
    "C02-R1": ("shadow-write-breaks-rollback-reader", "Shadow-column writes break rollback reads"),
    "C01-R2": ("stale-index-overrides-authoritative-row", "Search results lag authoritative row revisions"),
    "C01-R1": ("sequence-dedup-scope-too-broad", "Replayed sequence numbers lose independent events"),
    "C05-D2": ("unbounded-index-page-fetch", "Page selection reads the whole index"),
    "C06-D2": ("retry-storm-pool-starvation", "Retry storms starve foreground work in the pool"),
    "C07-D2": ("utc-date-used-for-sydney-window", "Sydney reporting windows misclassify boundary events"),
    "C08-D2": ("immutable-api-contract-conflict", "Proposed trace field conflicts with the stable response contract"),
    "C04-D2": ("retry-job-context-lost", "Retried jobs lose request context"),
    "C02-D2": ("versioned-envelope-fields-dropped", "Preserve fields in versioned envelope rewrites"),
    "C01-D2": ("ambiguous-composite-cache-key", "Composite cache keys collide across namespaces"),
    "N04-D2": ("staged-key-rotation-incomplete", "Complete the staged signing-key rotation"),
    "N01-D2": ("legacy-timeout-key-and-unit", "Move the request timeout setting to seconds"),
    "N03-D2": ("operator-target-region-absent", "Region change without an approved destination"),
    "N02-D2": ("nullable-profile-dereference", "Handle absent profile data in the email adapter"),
    "N04-D1": ("manifest-pin-drift", "Refresh the release pins in two manifests"),
    "N01-D1": ("stale-cross-module-symbol-imports", "Rename the money formatter across its consumers"),
    "C05-D1": ("unbounded-cartesian-window-join", "Window join must preserve a bounded streaming path"),
    "C08-D1": ("incompatible-lock-order-contracts", "Opposing lock-order contracts in one transaction path"),
    "C07-D1": ("inconsistent-decimal-aggregation-across-consumers", "Ledger and statement totals disagree at cent boundaries"),
    "C06-D1": ("worker-clock-used-for-lease-expiry", "Queue lag after a lease-service deploy"),
    "N03-D1": ("operator-retention-duration-absent", "Retention change without an approved duration"),
    "N02-D1": ("inclusive-slice-upper-bound", "Select at most the requested number of rows"),
    "C04-D1": ("tenant-omitted-from-feature-cache-key", "Feature cache returns another tenant's value"),
    "C02-D1": ("dual-read-backfill-precedence", "Online profile migration read regression"),
    "C01-D1": ("un-normalised-order-id-join", "Missing receipts after a queue reorder"),
    "C03-D1": ("tenant receipts remain separate", "Faulty baseline"),
    "C03-D2": ("unfenced-outbox-delivery-lease", "Outbox delivery lease race"),
}
sys.path.insert(0, "/opt/orchestrator-worker-runtime")
import worker_wsl_q2_verify as q2  # noqa: E402


def run(task_id: str) -> dict:
    if os.geteuid() != 0:
        raise RuntimeError("WSL root is required")
    split = "reserved" if "-R" in task_id else "development"
    fixture = (ROOT / "test" / "fixtures" / "controller_x3" /
               split / task_id / "actor")
    oracle = ROOT / "test" / "oracles" / "controller_x3" / f"{task_id}.json"
    protected_phrase, visible_phrase = TASKS[task_id]
    oracle_sha = hashlib.sha256(oracle.read_bytes()).hexdigest()
    raw = tempfile.mkdtemp(prefix="x3-isolation-source-", dir=q2.SEEDS)
    source = Path(raw)
    package = manifest_path = None
    uncertain = False
    try:
        attack_root = Path(tempfile.mkdtemp(prefix="x3-extra-edit-", dir=q2.SEEDS))
        try:
            shutil.copytree(ROOT / "test" / "fixtures" / "controller_x3" /
                            split / task_id / "variants" / "reference",
                            attack_root, dirs_exist_ok=True)
            (attack_root / "public_check.py").write_text(
                "# weakened\n", encoding="utf-8")
            try:
                forged_package, forged_manifest, _ = q2.copy_package(fixture, attack_root)
            except ValueError:
                extra_edit_rejected = True
            else:
                q2.dispose(forged_package, q2.SEEDS)
                forged_manifest.unlink(missing_ok=True)
                extra_edit_rejected = False
        finally:
            q2.dispose(attack_root, q2.SEEDS)
        if not extra_edit_rejected:
            raise RuntimeError("extra protected-file edit entered the actor package")
        shutil.copytree(fixture, source, dirs_exist_ok=True)
        shutil.copy2(PROBE, source / "x3_probe.py")
        package, manifest_path, manifest = q2.copy_package(source, None)
        result = q2.run_isolated(
            package, manifest_path, manifest,
            ["/usr/bin/python3", "-B", "x3_probe.py", str(oracle),
             protected_phrase, visible_phrase])
        if result.returncode:
            raise RuntimeError("X3 actor isolation probe failed: " + result.stderr[-400:])
        value = json.loads(result.stdout)
        if value.get("result") != "PASS" or value.get("provider_calls") != 0:
            raise RuntimeError(f"X3 actor isolation checks failed: {value.get('checks')}; "
                               f"diagnostic={value.get('diagnostic')}")
        if hashlib.sha256(oracle.read_bytes()).hexdigest() != oracle_sha:
            raise RuntimeError("protected X3 oracle changed during isolation probe")
        return {"schema_version": 1, "mode": "controller-x3-actor-isolation",
                "result": "PASS", "task_id": task_id, "oracle_sha256": oracle_sha,
                "extra_protected_edit_rejected": extra_edit_rejected, **value}
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
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--task-id", choices=sorted(TASKS), required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.task_id), sort_keys=True))
