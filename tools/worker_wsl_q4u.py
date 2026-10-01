#!/usr/bin/env python3
"""Versioned Q4U actor boundary: Q1 invariants with one editable file allowed.

Q1 remains byte-for-byte frozen. Only its manifest cardinality rule is widened
for Q4U tasks; all staging, stop-receipt, collection and ownership checks stay
in the attested Q1 implementation. New output paths remain forbidden.
"""
from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from pathlib import Path

import worker_wsl_q1 as q1


Q1_SHA256 = "33bd2985ac688680e90417db58c5b7e61e41748af284e3ce85b649e6b978b259"


def check_q1() -> None:
    if hashlib.sha256(Path(q1.__file__).read_bytes()).hexdigest() != Q1_SHA256:
        raise ValueError("Q4U base Q1 runtime differs from the attested snapshot")


def load_spec(path: Path) -> dict:
    """Validate the Q1 manifest, changing only the minimum editable count."""
    check_q1()
    if (path.is_symlink() or not path.is_file() or path.stat().st_uid != 0
            or path.stat().st_mode & 0o077 or path.stat().st_size > 100_000):
        raise ValueError("manifest must be a private root-owned regular file")
    value = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(value, dict) or set(value) != {"schema_version", "files"}
            or value["schema_version"] != 1):
        raise ValueError("unsupported manifest schema")
    rows = value["files"]
    if not isinstance(rows, list) or not 2 <= len(rows) <= q1.MAX_FILES:
        raise ValueError("manifest file count is invalid")
    paths: set[str] = set()
    editable = 0
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "sha256", "editable"}:
            raise ValueError("invalid manifest entry")
        q1.path_parts(row["path"])
        if (row["path"] in paths or not isinstance(row["sha256"], str)
                or not q1.SHA.fullmatch(row["sha256"])):
            raise ValueError("duplicate path or invalid digest")
        if type(row["editable"]) is not bool:
            raise ValueError("editable must be boolean")
        paths.add(row["path"])
        editable += row["editable"]
    if not 1 <= editable <= 8:
        raise ValueError("Q4U requires one to eight existing editable files")
    return value


@contextmanager
def q4u_spec():
    check_q1()
    original = q1.load_spec
    q1.load_spec = load_spec
    try:
        yield
    finally:
        q1.load_spec = original


def stage(source: Path, manifest: Path, name: str) -> dict:
    with q4u_spec():
        return q1.stage(source, manifest, name)


def main() -> int:
    with q4u_spec():
        return q1.main()


if __name__ == "__main__":
    raise SystemExit(main())
