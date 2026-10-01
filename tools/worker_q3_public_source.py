#!/usr/bin/env python3
"""Materialise pinned, unmodified upstream sources for a Q3 public fixture.

This deliberately stops before writing an issue or oracle. Those are authored
and reviewed separately so a source snapshot cannot silently become a task.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = {
    "P03": ("click", "click", "src/click", "19fd4d6e18bc9fce451f92f422696b11169faa57", "831c8f0948af519e45b90801d7430ff25451f972", "BSD-3-Clause", "LICENSE.txt", ("__init__.py", "core.py", "exceptions.py", "parser.py")),
    "P04": ("urllib3", "urllib3", "src/urllib3", "f4e4bc31f40f8c94c6a1f1685df28f97ff48c305", "f5cf122346141b187cca0db6e6445297d336b610", "MIT", "LICENSE.txt", ("connectionpool.py", "poolmanager.py", "util/url.py")),
    "P05": ("tenacity", "tenacity", "tenacity", "a09999688c8d3bb3d4ca1716748009954cc7c4d0", "389aab8b2688f7a1df41c2dd7797eeb18c8baff9", "Apache-2.0", "LICENSE", ("__init__.py", "asyncio/__init__.py", "wait.py")),
    "P06": ("pyjwt", "jwt", "jwt", "ea7267519f2be5ff031efabd692af7a4461f3d5e", "384c945065ad1f1d7e5a0331c7377c7f278532f5", "MIT", "LICENSE", ("api_jwk.py", "jwk_set_cache.py", "jwks_client.py")),
    "P07": ("packaging", "packaging", "src/packaging", "823b44ed1f904084a77ae3adf0ef130af6365f84", "48a8a069805291186522de3eff73ea80a8ca96ad", "Apache-2.0 OR BSD-2-Clause", "LICENSE", ("_parser.py", "markers.py", "requirements.py")),
    "P08": ("platformdirs", "platformdirs", "src/platformdirs", "5118d32ca567aba27f0af81b7b5931e162e1b86b", "7d5c85d14e760688a2210c56148b4052e2355ba6", "MIT", "LICENSE", ("_xdg.py", "api.py", "macos.py", "unix.py")),
}
URLS = {
    "click": "https://github.com/pallets/click",
    "urllib3": "https://github.com/urllib3/urllib3",
    "tenacity": "https://github.com/jd/tenacity",
    "pyjwt": "https://github.com/jpadilla/pyjwt",
    "packaging": "https://github.com/pypa/packaging",
    "platformdirs": "https://github.com/tox-dev/platformdirs",
}


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-c", "safe.directory=*", "-C", str(repo), *args])


def verify(task_id: str) -> dict:
    """Prove actor source and reference overlay match exact Git objects."""
    repo_name, package, upstream, parent, fix, licence, licence_file, files = CONFIG[task_id]
    source_repo = ROOT / "pilot-runs/q3-sources" / repo_name
    target = ROOT / "test/fixtures/worker_q3_public" / task_id
    provenance = json.loads((target / "provenance.json").read_text(encoding="utf-8"))
    if (provenance["source_commit"] != parent or provenance["fix_commit"] != fix
            or provenance["licence"] != licence
            or provenance["editable_paths"] != [f"{package}/{name}" for name in files]):
        raise RuntimeError(f"{task_id}: provenance differs from selected upstream commit")
    tracked = git(source_repo, "ls-tree", "-r", "--name-only", parent, upstream).decode().splitlines()
    expected = {f"{package}/{name.removeprefix(upstream + '/')}": name for name in tracked}
    actual = {path.relative_to(target / "actor").as_posix(): path
              for path in (target / "actor" / package).rglob("*") if path.is_file()}
    generated = set(provenance.get("generated_files", []))
    if set(actual) != set(expected) | generated or generated & set(expected):
        raise RuntimeError(f"{task_id}: package inventory differs from upstream plus generated files")
    for relative, upstream_path in expected.items():
        if actual[relative].read_bytes() != git(source_repo, "show", f"{parent}:{upstream_path}"):
            raise RuntimeError(f"{task_id}: actor source differs at {relative}")
    if (target / "actor" / licence_file).read_bytes() != git(source_repo, "show", f"{parent}:{licence_file}"):
        raise RuntimeError(f"{task_id}: licence differs from upstream")
    for name in files:
        relative = f"{package}/{name}"
        if (target / "reference" / relative).read_bytes() != git(source_repo, "show", f"{fix}:{upstream}/{name}"):
            raise RuntimeError(f"{task_id}: reference differs from upstream at {relative}")
    return {"task_id": task_id, "source_files": len(expected),
            "generated_files": sorted(generated), "source_commit": parent,
            "fix_commit": fix, "source_url": URLS[repo_name]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id", choices=CONFIG)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        print(json.dumps(verify(args.task_id), sort_keys=True))
        return
    repo_name, package, upstream, parent, fix, licence, licence_file, files = CONFIG[args.task_id]
    source_repo = ROOT / "pilot-runs/q3-sources" / repo_name
    parent_tree = ROOT / "pilot-runs/q3-parents" / repo_name
    target = ROOT / "test/fixtures/worker_q3_public" / args.task_id
    if target.exists():
        raise SystemExit(f"refusing to overwrite {target}")
    if git(source_repo, "rev-parse", f"{fix}^").decode().strip() != parent:
        raise SystemExit("selected source is not the fix's exact parent")
    if git(source_repo, "rev-parse", f"{parent}^{{tree}}").decode().strip() != git(parent_tree, "rev-parse", "HEAD^{tree}").decode().strip():
        raise SystemExit("parent worktree is not the pinned starting tree")
    actor = target / "actor"
    actor.mkdir(parents=True)
    shutil.copytree(parent_tree / upstream, actor / package)
    shutil.copy2(parent_tree / licence_file, actor / licence_file)
    editable = []
    for name in files:
        relative = f"{package}/{name}"
        parent_bytes = (actor / relative).read_bytes()
        if parent_bytes != git(source_repo, "show", f"{parent}:{upstream}/{name}"):
            raise SystemExit(f"source mismatch: {relative}")
        fixed = git(source_repo, "show", f"{fix}:{upstream}/{name}")
        reference = target / "reference" / relative
        reference.parent.mkdir(parents=True, exist_ok=True)
        reference.write_bytes(fixed)
        editable.append(relative)
    provenance = {
        "schema_version": 1, "id": args.task_id, "name": "TO AUTHOR",
        "source_url": URLS[repo_name],
        "source_commit": parent, "fix_commit": fix, "issue_origin": "upstream-fix",
        "licence": licence, "licence_file": licence_file,
        "licence_sha256": hashlib.sha256((actor / licence_file).read_bytes()).hexdigest(),
        "package_path": package, "editable_paths": editable,
        "oracle_file": f"{args.task_id}.json", "case_file": f"{args.task_id}_case.py",
    }
    (target / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    (actor / "acceptance.json").write_text(json.dumps({"schema_version": 1, "public_command": ["python3", "-B", "public_check.py"], "editable_paths": editable}, indent=2) + "\n", encoding="utf-8")
    print(f"{args.task_id}: pinned parent {parent}, fix {fix}, files {editable}")


if __name__ == "__main__":
    main()
