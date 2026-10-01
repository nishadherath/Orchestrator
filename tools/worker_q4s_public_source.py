#!/usr/bin/env python3
"""Materialise and audit the six pinned Q4S upstream source snapshots.

The Git clones are staging inputs only. Frozen fixture bytes and their hashes
are the campaign inputs; this command never fetches, selects or replaces tasks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "test/fixtures/worker_q4s_public"
SOURCES = {
    "S01": ("attrs", "python-attrs/attrs", "4b5b295bb8", ("src/attr", "src/attrs"), "attr", "LICENSE", "MIT", ("_compat.py", "_make.py", "_next_gen.py", "setters.py")),
    "S02": ("pluggy", "pytest-dev/pluggy", "a031c1c91f", ("src/pluggy",), "pluggy", "LICENSE", "MIT", ("_hooks.py", "_manager.py", "_callers.py")),
    "S03": ("h11", "python-hyper/h11", "ce515c5a9a", ("h11",), "h11", "LICENSE.txt", "MIT", ("_connection.py", "_headers.py", "_writers.py")),
    "S04": ("sortedcontainers", "grantjenks/python-sortedcontainers", "b5395b553d", ("sortedcontainers",), "sortedcontainers", "LICENSE", "Apache-2.0", ("sorteddict.py", "sortedlist.py", "sortedset.py")),
    "S05": ("more-itertools", "more-itertools/more-itertools", "3eb4053", ("more_itertools",), "more_itertools", "LICENSE", "MIT", ("more.py", "recipes.py")),
    "S06": ("idna", "kjd/idna", "9067b80", ("idna",), "idna", "LICENSE.md", "BSD-3-Clause", ("core.py", "codec.py")),
}
RATIONALES = {
    "S01": "Authored regression from the pinned upstream generator-hook fix; exercises class and field hooks across assignment boundaries.",
    "S02": "Authored regression from the pinned upstream hookspec-default fix; exercises registration and call forms.",
    "S03": "Authored regression from the pinned upstream header-casing fix; exercises storage, framing and wire output.",
    "S04": "Authored regression from the pinned upstream reducer fix; exercises constructor-based pickle contracts across collection types.",
    "S05": "Authored regression from the pinned upstream zero-cache lookahead fix; exercises bounded retention on repeated peeks.",
    "S06": "Authored regression from the pinned upstream joiner-exception fix; exercises specific and generic error boundaries.",
}


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-c", "safe.directory=*", "-C", str(repo), *args])


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_files(repo: Path, commit: str, roots: tuple[str, ...]) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for root in roots:
        for upstream in git(repo, "ls-tree", "-r", "--name-only", commit, root).decode().splitlines():
            # Some old upstream releases store tests inside the importable
            # package. Their pre-fix expectations conflict with the authored
            # public issue, so the actor receives source modules only.
            if upstream.startswith(root + "/") and "/tests/" not in upstream:
                result[upstream.removeprefix("src/")] = git(repo, "show", f"{commit}:{upstream}")
    return result


def audit(task_id: str, repo_base: Path, *, prepare: bool) -> dict:
    name, slug, fix_abbrev, roots, package, licence, licence_id, editable = SOURCES[task_id]
    repo = repo_base / name
    fix = git(repo, "rev-parse", fix_abbrev).decode().strip()
    parent = git(repo, "rev-parse", f"{fix}^").decode().strip()
    files = source_files(repo, parent, roots)
    target = FIXTURES / task_id
    actor = target / "actor"
    expected = {**files, licence: git(repo, "show", f"{parent}:{licence}")}
    if prepare:
        if target.exists():
            raise RuntimeError(f"refusing to overwrite {target}")
        actor.mkdir(parents=True)
        for relative, contents in expected.items():
            path = actor / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
        (target / "reference").mkdir()
        (target / "partial").mkdir()
        for filename in editable:
            relative = f"{package}/{filename}"
            upstream = f"{roots[0]}/{filename}"
            for overlay, contents in (("reference", git(repo, "show", f"{fix}:{upstream}")),
                                      ("partial", expected[relative])):
                path = target / overlay / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(contents)
        provenance = {
            "schema_version": 1, "id": task_id, "name": "TO AUTHOR",
            "source_url": f"https://github.com/{slug}", "source_commit": parent,
            "fix_commit": fix, "issue_origin": "authored-regression",
            "authored_rationale": RATIONALES[task_id],
            "upstream_change_url": f"https://github.com/{slug}/commit/{fix}",
            "licence": licence_id, "licence_file": licence,
            "licence_sha256": sha(expected[licence]), "package_path": package,
            "editable_paths": [f"{package}/{f}" for f in editable],
            "oracle_file": f"{task_id}.json", "case_file": f"{task_id}_case.py",
        }
        (target / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
        (actor / "acceptance.json").write_text(json.dumps({
            "schema_version": 1, "public_command": ["python3", "-B", "public_check.py"],
            "editable_paths": provenance["editable_paths"],
        }, indent=2) + "\n", encoding="utf-8")
    provenance = json.loads((target / "provenance.json").read_text(encoding="utf-8"))
    if (provenance["source_commit"] != parent or provenance["fix_commit"] != fix
            or provenance["source_url"] != f"https://github.com/{slug}"
            or provenance["issue_origin"] != "authored-regression"
            or provenance["authored_rationale"] != RATIONALES[task_id]
            or provenance["upstream_change_url"] != f"https://github.com/{slug}/commit/{fix}"
            or provenance["licence"] != licence_id
            or provenance["editable_paths"] != [f"{package}/{f}" for f in editable]):
        raise RuntimeError(f"{task_id}: provenance differs from pinned Git objects")
    actual_source = {p.relative_to(actor).as_posix() for p in actor.rglob("*") if p.is_file()
                     and p.relative_to(actor).as_posix() not in {"ISSUE.md", "public_check.py", "acceptance.json"}}
    if actual_source != set(expected):
        raise RuntimeError(f"{task_id}: upstream actor inventory differs")
    for relative, contents in expected.items():
        if (actor / relative).read_bytes() != contents:
            raise RuntimeError(f"{task_id}: altered upstream byte {relative}")
    for filename in editable:
        relative = f"{package}/{filename}"
        fixed = git(repo, "show", f"{fix}:{roots[0]}/{filename}")
        if (target / "reference" / relative).read_bytes() != fixed:
            raise RuntimeError(f"{task_id}: reference differs from upstream {relative}")
    return {"id": task_id, "source_commit": parent, "fix_commit": fix,
            "actor_source_files": len(files), "licence_sha256": sha(expected[licence])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-base", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    print(json.dumps([audit(task_id, args.repo_base, prepare=args.prepare)
                      for task_id in SOURCES], indent=2))


if __name__ == "__main__":
    main()
