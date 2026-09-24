#!/usr/bin/env python3
"""Stage only the four public N4 files into a locked-down WSL actor root.

Run as WSL root outside the actor namespace. The evaluator and executor state
are never copied. N4 permits edits to an existing app.py only; expansion of
this file contract requires a new versioned host attestation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path

BASE = Path("/var/lib/orchestrator-worker-n4")
ACTORS = BASE / "actors"
MANIFESTS = BASE / "manifests"
PUBLIC = ("app.py", "public_check.py", "ISSUE.md", "acceptance.json")
NAME = re.compile(r"(?:probe-[A-Za-z0-9_-]{8}|inv-[0-9a-f]{32})\Z")
MAX_INPUT_BYTES = 1_000_000


def stage(source: Path, name: str) -> dict:
    if os.geteuid() != 0 or not NAME.fullmatch(name):
        raise ValueError("root identity and opaque probe/invocation name required")
    if source.is_symlink() or not source.is_dir():
        raise ValueError("source must be a real directory")
    if ACTORS.is_symlink() or not ACTORS.is_dir() or ACTORS.stat().st_uid != 0:
        raise ValueError("root-owned actor parent is unavailable")
    MANIFESTS.mkdir(mode=0o700, exist_ok=True)
    if MANIFESTS.is_symlink() or MANIFESTS.stat().st_uid != 0:
        raise ValueError("root-owned manifest parent is unavailable")
    payload = {}
    for filename in PUBLIC:
        path = source / filename
        if path.is_symlink() or not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
            raise ValueError(f"public source file invalid: {filename}")
        if path.stat().st_size > MAX_INPUT_BYTES:
            raise ValueError(f"public source file too large: {filename}")
        payload[filename] = path.read_bytes()
    target = ACTORS / name
    target.mkdir(mode=0o755)  # Atomic refusal if an invocation name was used.
    for filename, data in payload.items():
        path = target / filename
        with path.open("xb") as stream:
            stream.write(data)
        path.chmod(0o644)
        if filename == "app.py":
            os.chown(path, 65534, 65534)
    (target / ".gitignore").write_text("graft/\n.cache/\n.home/\n.scratch/\n",
                                       encoding="utf-8")
    (target / ".gitignore").chmod(0o644)
    for folder in (".home", ".cache", ".scratch", "graft"):
        directory = target / folder
        directory.mkdir(mode=0o700)
        os.chown(directory, 65534, 65534)
    target.chmod(0o755)
    record = {"actor_root": str(target), "source_root": str(source.resolve()),
              "public_sha256": {name: hashlib.sha256(data).hexdigest()
                                for name, data in payload.items()}}
    manifest = MANIFESTS / f"{name}.json"
    descriptor = os.open(manifest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(record, stream, sort_keys=True)
        stream.write("\n")
    return {"actor_root": record["actor_root"],
            "public_sha256": record["public_sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(stage(args.source, args.name), sort_keys=True))
        return 0
    except (OSError, ValueError) as exc:
        print(f"materialization rejected: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
