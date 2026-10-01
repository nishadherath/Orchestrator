#!/usr/bin/env python3
"""Report local Python imports omitted by the historical Q4U canary seal.

This is a read-only review aid. It does not amend a manifest after outcomes
exist, and static imports are a lower bound on the full runtime dependency set.
"""
from __future__ import annotations

import ast
import argparse
import json
from collections import deque
from pathlib import Path

from worker_q4u_canary_manifest import ROOT, SOURCES


def imported_local_modules(path: Path, tools_root: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            candidates = (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            candidates = (node.module or "",)
        else:
            continue
        for candidate in candidates:
            name = candidate.split(".", 1)[0]
            if name and (tools_root / f"{name}.py").is_file():
                names.add(f"tools/{name}.py")
    return names


def audit() -> dict:
    tools_root = ROOT / "tools"
    bound = set(SOURCES)
    direct = set().union(*(imported_local_modules(ROOT / path, tools_root)
                           for path in SOURCES if path.endswith(".py")))
    visited: set[str] = set()
    queue = deque(path for path in SOURCES if path.endswith(".py"))
    while queue:
        relative = queue.popleft()
        if relative in visited:
            continue
        visited.add(relative)
        for imported in imported_local_modules(ROOT / relative, tools_root):
            if imported not in visited:
                queue.append(imported)
    missing = sorted(visited - bound)
    return {"schema_version": 1, "bound_python_files": len(
        [path for path in SOURCES if path.endswith(".py")]),
            "reachable_local_python_files": len(visited),
            "direct_unbound_static_imports": sorted(direct - bound),
            "unbound_static_local_imports": missing,
            "static_local_imports_bound": not missing,
            "scope_limit": "static tools/*.py imports only; config, dynamic imports and runtime binaries need separate review"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    arguments = parser.parse_args()
    result = audit()
    body = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if arguments.out is not None:
        with arguments.out.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(body)
    print(body, end="")
