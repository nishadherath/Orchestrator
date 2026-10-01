#!/usr/bin/env python3
"""Freeze and validate the X3 provider-free paired campaign.

The manifest binds all 48 public and protected task packages and the runnable
first-party source. It contains no expected Controller decisions or scores.
Only development tasks may enter this small transport campaign; reserved
outcomes remain sealed for X6.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import controller_campaign_manifest
import controller_evaluation
import controller_x3_corpus

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TASKS = ("N04-D1", "C03-D1")


class X3ManifestError(ValueError):
    """A paired schedule or one of its sealed inputs is invalid."""


def _schedule(task_ids: tuple[str, ...], inventory: dict) -> list[dict]:
    if not task_ids or len(task_ids) > 6 or len(set(task_ids)) != len(task_ids):
        raise X3ManifestError("X3 pair needs one to six distinct development tasks")
    rows = {row["task_id"]: row for row in inventory["tasks"]}
    episodes = []
    for index, task_id in enumerate(task_ids):
        row = rows.get(task_id)
        if row is None or row["split"] != "development" or row["status"] != "ready":
            raise X3ManifestError(f"X3 paired task is not a ready development case: {task_id}")
        # Balance presentation order without exposing a routing label to actors.
        arms = ("S", "A") if index % 2 == 0 else ("A", "S")
        for arm in arms:
            episodes.append({"sequence": len(episodes) + 1, "task_id": task_id,
                             "arm": arm, "mode": "off" if arm == "S" else "auto"})
    return episodes


def build(task_ids: tuple[str, ...] = DEFAULT_TASKS) -> dict:
    inventory = controller_x3_corpus.inventory()
    if inventory["ready_tasks"] != 48 or inventory["pending_tasks"]:
        raise X3ManifestError("X3 corpus is not fully ready")
    body = {"schema_version": 1, "stage": "controller-x3-fake-pairs",
            "inventory_sha256": inventory["inventory_sha256"],
            "runtime_package": controller_campaign_manifest.package_record(ROOT),
            "episodes": _schedule(task_ids, inventory),
            "interpreter": "public-packet-deterministic-double",
            "worker": "reference-overlay-adapter-double",
            "assessment_charge_usd": 0.04,
            "provider_calls": 0}
    body["manifest_sha256"] = controller_evaluation.digest(body)
    return body


def validate(manifest: dict) -> None:
    if (not isinstance(manifest, dict) or manifest.get("schema_version") != 1
            or manifest.get("stage") != "controller-x3-fake-pairs"
            or manifest.get("manifest_sha256") != controller_evaluation.digest(
                {key: value for key, value in manifest.items() if key != "manifest_sha256"})):
        raise X3ManifestError("X3 manifest seal is invalid")
    inventory = controller_x3_corpus.inventory()
    if inventory["ready_tasks"] != 48 or inventory["pending_tasks"]:
        raise X3ManifestError("X3 corpus is no longer fully ready")
    if manifest.get("inventory_sha256") != inventory["inventory_sha256"]:
        raise X3ManifestError("X3 corpus differs from frozen inventory")
    episodes = manifest.get("episodes")
    if not isinstance(episodes, list) or not episodes:
        raise X3ManifestError("X3 episode schedule is absent")
    task_ids = tuple(dict.fromkeys(row.get("task_id") for row in episodes
                                  if isinstance(row, dict)))
    if episodes != _schedule(task_ids, inventory):
        raise X3ManifestError("X3 episode schedule differs from balanced pairs")
    if (manifest.get("interpreter") != "public-packet-deterministic-double"
            or manifest.get("worker") != "reference-overlay-adapter-double"
            or manifest.get("assessment_charge_usd") != 0.04
            or manifest.get("provider_calls") != 0):
        raise X3ManifestError("X3 adapter or accounting contract changed")
    controller_campaign_manifest.verify_package(
        ROOT, manifest.get("runtime_package"), require_materialised=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--task", action="append", dest="tasks")
    args = parser.parse_args()
    output = args.out.resolve()
    if output.exists():
        parser.error("X3 manifest output must be a new file")
    manifest = build(tuple(args.tasks) if args.tasks else DEFAULT_TASKS)
    validate(manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8", newline="\n")
    print(json.dumps({"manifest_sha256": manifest["manifest_sha256"],
                      "episodes": len(manifest["episodes"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
