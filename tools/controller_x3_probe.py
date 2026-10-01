#!/usr/bin/env python3
"""Run registered X3 controls through the provider-free protected WSL grader.

This is an explicit host probe, not part of the portable default harness.
Every control is a fresh isolated actor. A timeout or malformed result stops
without silently replaying a previous invocation.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRADER = ROOT / "tools" / "controller_x3_grade.py"
EXPECTED = {
    "N04-R2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 76.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "N04-R1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 78.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "N03-R2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 0.0, False),
        "baseline": (False, 40.0, True),
        "label_copy": (False, 0.0, False),
        "poison_json": (False, 0.0, False),
    },
    "N03-R1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 0.0, False),
        "baseline": (False, 40.0, True),
        "label_copy": (False, 0.0, False),
        "poison_json": (False, 0.0, False),
    },
    "N02-R2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 88.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "N02-R1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 88.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "N01-R2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 70.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "N01-R1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 80.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C08-R2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 75.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C08-R1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 67.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C07-R2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 67.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C07-R1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 71.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C06-R2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 67.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C06-R1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 61.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C05-R2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 79.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C05-R1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 94.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C04-R2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 67.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C04-R1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 75.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C03-R2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 71.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C03-R1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 92.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C02-R2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 73.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C02-R1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 88.0, False),
        "baseline": (False, 16.0, True),
        "label_copy": (False, 28.5, True),
        "poison_json": (False, 0.0, True),
    },
    "C01-R2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 88.0, False),
        "baseline": (False, 16.0, True),
        "label_copy": (False, 28.5, True),
        "poison_json": (False, 0.0, True),
    },
    "C01-R1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 88.0, False),
        "baseline": (False, 16.0, True),
        "label_copy": (False, 28.5, True),
        "poison_json": (False, 0.0, True),
    },
    "C05-D2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 88.0, False),
        "baseline": (False, 16.0, True),
        "label_copy": (False, 28.5, True),
        "poison_json": (False, 0.0, True),
    },
    "C06-D2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 88.0, False),
        "baseline": (False, 16.0, True),
        "label_copy": (False, 28.5, True),
        "poison_json": (False, 0.0, True),
    },
    "C07-D2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 73.0, False),
        "baseline": (False, 16.0, True),
        "label_copy": (False, 16.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C08-D2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 72.5, False),
        "baseline": (False, 40.0, True),
        "label_copy": (False, 0.0, False),
        "poison_json": (False, 0.0, False),
    },
    "C04-D2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 88.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C02-D2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 88.0, False),
        "baseline": (False, 16.0, True),
        "label_copy": (False, 28.5, True),
        "poison_json": (False, 0.0, True),
    },
    "C01-D2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 88.0, False),
        "baseline": (False, 16.0, True),
        "label_copy": (False, 28.5, True),
        "poison_json": (False, 0.0, True),
    },
    "N04-D2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 88.0, False),
        "baseline": (False, 16.0, True),
        "label_copy": (False, 28.5, True),
        "poison_json": (False, 0.0, True),
    },
    "N01-D2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 61.0, False),
        "baseline": (False, 16.0, True),
        "label_copy": (False, 28.5, True),
        "poison_json": (False, 0.0, True),
    },
    "N03-D2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 72.5, False),
        "baseline": (False, 40.0, True),
        "label_copy": (False, 0.0, False),
        "poison_json": (False, 0.0, False),
    },
    "N02-D2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 80.0, False),
        "baseline": (False, 10.0, True),
        "label_copy": (False, 22.5, True),
        "poison_json": (False, 0.0, True),
    },
    "N04-D1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 88.0, False),
        "baseline": (False, 16.0, True),
        "label_copy": (False, 28.5, True),
        "poison_json": (False, 0.0, True),
    },
    "N01-D1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 92.0, False),
        "baseline": (False, 16.0, True),
        "label_copy": (False, 16.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C05-D1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 92.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C08-D1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 72.5, False),
        "baseline": (False, 40.0, True),
        "label_copy": (False, 0.0, False),
        "poison_json": (False, 0.0, False),
    },
    "C07-D1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 92.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C06-D1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 92.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "N03-D1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 72.5, False),
        "baseline": (False, 40.0, True),
        "label_copy": (False, 0.0, False),
        "poison_json": (False, 0.0, False),
    },
    "N02-D1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 76.0, False),
        "baseline": (False, 16.0, True),
        "label_copy": (False, 16.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C04-D1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 92.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C02-D1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 92.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C01-D1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 92.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C03-D1": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 75.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
    "C03-D2": {
        "reference": (True, 100.0, False),
        "alternative": (True, 100.0, False),
        "partial": (False, 92.0, False),
        "baseline": (False, 0.0, True),
        "label_copy": (False, 0.0, True),
        "poison_json": (False, 0.0, True),
    },
}


def wsl_path(path: Path, distro: str) -> str:
    result = subprocess.run(["wsl.exe", "-d", distro, "-u", "root", "--",
                             "wslpath", "-a", path.as_posix()],
                            capture_output=True, text=True, timeout=30)
    if result.returncode or not result.stdout.strip().startswith("/"):
        raise RuntimeError("cannot resolve protected grader in WSL")
    return result.stdout.strip()


def run(distro: str, task_ids: list[str], variants: list[str] | None = None) -> dict:
    path = wsl_path(GRADER, distro)
    rows = []
    for task_id in task_ids:
        count_before = len(rows)
        for variant, expected in EXPECTED[task_id].items():
            if variants is not None and variant not in variants:
                continue
            command = ["wsl.exe", "-d", distro, "-u", "root", "--", "python3",
                       path, "--task-id", task_id, "--variant", variant]
            result = subprocess.run(command, capture_output=True, text=True, timeout=120)
            if result.returncode:
                raise RuntimeError(
                    f"protected grader stopped on {task_id}/{variant}: "
                    f"{result.stderr[-400:]}")
            try:
                value = json.loads(result.stdout)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"protected grader gave no JSON for {task_id}/{variant}") from exc
            observed = (value.get("accepted"), value.get("quality"),
                        value.get("false_success"))
            if (observed != expected or value.get("task_id") != task_id
                    or value.get("oracle_read_denied") is not True
                    or value.get("provider_calls") != 0
                    or (variant == "poison_json"
                        and value.get("public_check_passed") is not True)):
                raise RuntimeError(f"X3 control {task_id}/{variant} failed: {observed}")
            rows.append({"task_id": task_id, "variant": variant,
                         "accepted": observed[0], "quality": observed[1],
                         "false_success": observed[2], "oracle_read_denied": True,
                         "public_check_passed": value["public_check_passed"],
                         "oracle_sha256": value["oracle_sha256"],
                         "actor_manifest_sha256": value["actor_manifest_sha256"]})
        print(f"X3 {task_id}: {len(rows) - count_before} controls passed",
              file=sys.stderr, flush=True)
    return {"schema_version": 1, "mode": "controller-x3-wsl-vertical-probe",
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "result": "PASS", "provider_calls": 0,
            "task_count": len(task_ids), "controls": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--distro", default="kali-linux")
    parser.add_argument("--task-id", choices=sorted(EXPECTED), action="append")
    parser.add_argument("--variant", choices=sorted(next(iter(EXPECTED.values()))),
                        action="append")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    value = run(args.distro, args.task_id or sorted(EXPECTED), args.variant)
    encoded = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8", newline="\n")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
