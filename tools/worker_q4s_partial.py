#!/usr/bin/env python3
"""Regenerate the deliberately incomplete Q4S overlays from pinned bytes."""
from __future__ import annotations

import argparse
from pathlib import Path

from worker_q4s_public_source import FIXTURES, SOURCES


def expected(task_id: str) -> dict[str, bytes]:
    _, _, _, _, package, _, _, editable = SOURCES[task_id]
    task = FIXTURES / task_id
    baseline = {f"{package}/{name}": (task / "actor" / package / name).read_bytes()
                for name in editable}
    fixed = {name: (task / "reference" / name).read_bytes() for name in baseline}
    if task_id == "S01":
        result = dict(fixed)
        original = b'''                gen.close()\n                msg = "Generator on_setattr hook yielded more than once."\n                raise RuntimeError(msg)'''
        assert result["attr/_make.py"].count(original) == 1
        result["attr/_make.py"] = result["attr/_make.py"].replace(original, b"                return")
        return result
    if task_id == "S02":
        return {**baseline, "pluggy/_hooks.py": fixed["pluggy/_hooks.py"]}
    if task_id == "S03":
        return {**baseline, "h11/_writers.py": fixed["h11/_writers.py"]}
    if task_id == "S04":
        return {**baseline, "sortedcontainers/sortedlist.py": fixed["sortedcontainers/sortedlist.py"]}
    if task_id == "S05":
        result = dict(fixed)
        name = "more_itertools/more.py"
        old = b"return self._source.peek(default)"
        assert result[name].count(old) == 1
        result[name] = result[name].replace(old, b"return self._source.peek()")
        return result
    if task_id == "S06":
        result = dict(fixed)
        name = "idna/core.py"
        old = b"            if not contextj_ok:\n"
        replacement = (b"            if cp_value == 0x200C and not contextj_ok:\n"
                       b"                raise IDNAError('Invalid non-joiner context')\n"
                       b"            if not contextj_ok:\n")
        assert result[name].count(old) == 1
        result[name] = result[name].replace(old, replacement)
        return result
    raise ValueError(task_id)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    for task_id in SOURCES:
        for name, contents in expected(task_id).items():
            path = FIXTURES / task_id / "partial" / name
            if args.prepare:
                path.write_bytes(contents)
            elif path.read_bytes() != contents:
                raise RuntimeError(f"partial bytes changed: {task_id}/{name}")
        print(f"PASS: {task_id} partial overlay")


if __name__ == "__main__":
    main()
