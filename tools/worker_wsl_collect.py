#!/usr/bin/env python3
"""Collect one stopped N4 actor's allowed app.py edit, rejecting any drift.

The caller must first observe the WSL namespace launcher terminate normally.
Timeouts and ambiguous writer state must never invoke this collector.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path

from worker_wsl_materialize import ACTORS, MANIFESTS, MAX_INPUT_BYTES, NAME, PUBLIC


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect(name: str, source: Path) -> dict:
    if os.geteuid() != 0 or not NAME.fullmatch(name):
        raise ValueError("root identity and opaque actor name required")
    manifest_path = MANIFESTS / f"{name}.json"
    if manifest_path.is_symlink() or manifest_path.stat().st_uid != 0:
        raise ValueError("root-owned materialization manifest missing")
    record = json.loads(manifest_path.read_text(encoding="utf-8"))
    actor = ACTORS / name
    if actor.is_symlink() or not actor.is_dir() or record["actor_root"] != str(actor):
        raise ValueError("actor identity mismatch")
    if source.is_symlink() or not source.is_dir() or str(source.resolve()) != record["source_root"]:
        raise ValueError("source identity mismatch")
    baseline = record["public_sha256"]
    if set(baseline) != set(PUBLIC):
        raise ValueError("public inventory mismatch")
    for filename in PUBLIC:
        target = actor / filename
        original = source / filename
        if (target.is_symlink() or original.is_symlink() or not target.is_file()
                or not original.is_file() or not stat.S_ISREG(target.stat().st_mode)
                or not stat.S_ISREG(original.stat().st_mode)):
            raise ValueError(f"public file identity changed: {filename}")
        if sha(original) != baseline[filename]:
            raise ValueError(f"source changed while worker ran: {filename}")
        if filename != "app.py" and sha(target) != baseline[filename]:
            raise ValueError(f"protected actor file changed: {filename}")
    updated = actor / "app.py"
    if updated.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("edited app.py is too large")
    before, after = baseline["app.py"], sha(updated)
    if after != before:
        temp = source / f".worker-n5-{name}.tmp"
        try:
            with temp.open("xb") as stream:
                stream.write(updated.read_bytes())
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, source / "app.py")
        finally:
            if temp.exists():
                temp.unlink()
    return {"actor_root": str(actor), "changed": after != before,
            "app_sha256_before": before, "app_sha256_after": after}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(collect(args.name, args.source), sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"collection rejected: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
