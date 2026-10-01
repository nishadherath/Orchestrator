#!/usr/bin/env python3
"""Grade H02 with evaluator-owned tests in fresh Q4U WSL namespaces."""

from __future__ import annotations

import argparse
import ast
import base64
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid

import worker_wsl_q1 as q1
import worker_wsl_q2_verify as q2
import worker_wsl_q4u_adapter as q4u


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "test/fixtures/controller_x5_authored_pytest/development/H02"
ORACLE = ROOT / "test/oracles/controller_x5_authored_pytest/H02"
CATALOGUE = CASE / "catalogue-h02.json"
EDITABLE = "pytest_asyncio/plugin.py"
WEIGHTS = {"public": 20, "forward": 25, "reverse": 25,
           "no_hook": 10, "upstream": 20}
UNSAFE_NAMES = {"__import__", "eval", "exec", "compile", "globals", "locals",
                "vars", "open", "breakpoint"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inventory(actor: Path) -> dict[str, str]:
    if actor.is_symlink() or not actor.is_dir():
        raise ValueError("H02 actor root is missing or redirected")
    found = {}
    for path in actor.rglob("*"):
        relative = path.relative_to(actor).as_posix()
        if (path.is_symlink() or path.stat().st_nlink != 1 and path.is_file()
                or path.is_dir() and path.name == "__pycache__"):
            raise ValueError(f"H02 actor path is redirected or cached: {relative}")
        if path.is_file():
            found[relative] = sha(path.read_bytes())
    return found


def scope_violations(candidate: Path) -> list[str]:
    """Keep imports and module state fixed while allowing function repairs."""
    original = ast.parse((CASE / "actor" / EDITABLE).read_text(encoding="utf-8"))
    try:
        changed = ast.parse(candidate.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeError):
        return ["editable plugin does not parse"]
    def fixed(tree: ast.Module) -> list[str]:
        return [ast.dump(node, include_attributes=False) for node in tree.body
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if fixed(original) != fixed(changed):
        return ["imports, classes or module state changed"]
    original_functions: dict[str, set[str]] = {}
    for node in original.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            original_functions.setdefault(node.name, set()).add(
                ast.dump(node, include_attributes=False))
    original_counts = Counter(node.name for node in original.body
                              if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
    changed_counts = Counter(node.name for node in changed.body
                             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
    if (any(changed_counts[name] != count for name, count in original_counts.items())
            or any(count != 1 for name, count in changed_counts.items()
                   if name not in original_counts)):
        return ["original plugin function missing or duplicated"]
    violations = []
    for node in changed.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if ast.dump(node, include_attributes=False) in original_functions.get(node.name, set()):
            continue
        for child in ast.walk(node):
            if (isinstance(child, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal))
                    or isinstance(child, ast.Name) and child.id in UNSAFE_NAMES
                    or isinstance(child, ast.Attribute)
                    and isinstance(child.value, ast.Name)
                    and (child.value.id, child.attr) in {
                        ("sys", "modules"), ("sys", "exit"), ("os", "_exit"),
                        ("json", "dumps"), ("pytest", "main")
                    }):
                violations.append(f"evaluator-facing operation in {node.name}")
                break
    return violations


def hidden_program(phase: str, catalogue: dict) -> str:
    """Send sealed oracle bytes on stdin; never put them in actor inventory."""
    if phase == "upstream":
        names = ["upstream/conftest.py", "upstream/test_loop_factory_parametrization.py"]
    elif phase == "no_hook":
        names = ["no_hook/test_mre.py"]
    else:
        names = ["forward/conftest.py", "forward/lifecycle.py",
                 "forward/test_factory_scope.py"]
    files = {}
    for name in names:
        data = (ORACLE / name).read_bytes()
        if sha(data) != catalogue["oracle_files"][name]:
            raise RuntimeError(f"H02 evaluator oracle drifted: {name}")
        files[Path(name).name] = base64.b64encode(data).decode("ascii")
    options = ["-q", "-p", "no:cacheprovider"]
    if phase != "upstream":
        options += ["-p", "pytest_asyncio.plugin"]
    selector = "test_factory_scope.py"
    if phase == "reverse":
        targets = [selector + "::test_sync_using_async_fixture",
                   selector + "::test_async"]
    elif phase == "no_hook":
        targets = ["test_mre.py"]
    elif phase == "upstream":
        targets = ["test_loop_factory_parametrization.py"]
    else:
        targets = [selector]
    config = {"files": files, "options": options, "targets": targets,
              "expect_variants": phase in {"forward", "reverse"},
              "autoload": phase == "upstream"}
    return ("import base64,json,os,pathlib,sys,tempfile\n"
            "c=json.loads(" + repr(json.dumps(config, sort_keys=True)) + ")\n"
            "a=pathlib.Path.cwd()\n"
            "sys.path[:0]=[str(a/'deps'),str(a/'deps/pygments-runtime.zip'),str(a)]\n"
            "os.environ['PYTHONPATH']=os.pathsep.join(sys.path[:3])\n"
            "os.environ['PYTHONDONTWRITEBYTECODE']='1'\n"
            "if not c['autoload']: os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'\n"
            "if c['expect_variants']: os.environ['X5_EXPECT_SYNC_VARIANTS']='1'\n"
            "d=pathlib.Path(tempfile.mkdtemp(prefix='h02-oracle-'))\n"
            "for n,b in c['files'].items(): (d/n).write_bytes(base64.b64decode(b))\n"
            "import pytest\n"
            "sys.exit(pytest.main(c['options']+[str(d/t) for t in c['targets']]))\n")


def isolated(package: Path, spec: Path, manifest: dict,
             command: list[str], script: str | None = None) -> subprocess.CompletedProcess:
    name = "q1-" + uuid.uuid4().hex
    actor = q1.ACTORS / name
    staged = terminal = False
    try:
        q4u.stage(package, spec, name)
        staged = True
        result = subprocess.run([str(q4u.LAUNCHER), str(actor), "--", *command],
                                cwd="/", input=script, text=True, capture_output=True,
                                timeout=120, preexec_fn=q4u.cap_output, check=False)
        terminal = True
        for row in manifest["files"]:
            if sha((actor / row["path"]).read_bytes()) != row["sha256"]:
                raise RuntimeError(f"H02 isolated actor mutated: {row['path']}")
        if len(result.stdout) + len(result.stderr) > 65536:
            raise RuntimeError("H02 isolated output exceeded evaluator cap")
        return result
    finally:
        if staged and terminal:
            q2.dispose(actor, q1.ACTORS)
            q2.dispose(q1.OUTPUTS / name, q1.OUTPUTS)
            for suffix in (".json", ".start.json", ".stop.json"):
                (q1.MANIFESTS / f"{name}{suffix}").unlink(missing_ok=True)


def grade(actor: Path) -> dict:
    if os.name != "posix" or os.geteuid() != 0:
        raise RuntimeError("H02 protected grading requires WSL root")
    catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    body = {key: value for key, value in catalogue.items()
            if key != "catalogue_sha256"}
    if sha(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()) != catalogue.get("catalogue_sha256"):
        raise RuntimeError("H02 catalogue digest differs")
    if catalogue.get("editable_paths") != [EDITABLE] or catalogue.get("weights") != WEIGHTS:
        raise RuntimeError("H02 evaluator contract differs from catalogue")
    frozen = catalogue["actor_files"]
    before = inventory(actor)
    if set(before) != set(frozen):
        raise ValueError("H02 actor file inventory differs from frozen package")
    protected = [name for name in frozen if name != EDITABLE and before[name] != frozen[name]]
    if protected:
        return {"case": "H02", "quality": 0, "accepted": False,
                "critical": True, "protected_edits": sorted(protected)}
    scope = scope_violations(actor / EDITABLE)
    if scope:
        return {"case": "H02", "quality": 0, "accepted": False,
                "critical": True, "scope_violations": scope}
    task = {"actor_files": frozen, "editable_paths": [EDITABLE]}
    seed = Path(tempfile.mkdtemp(prefix="h02-grade-", dir=q1.SEEDS))
    package = spec = None
    uncertain = False
    try:
        shutil.copytree(actor, seed, dirs_exist_ok=True)
        seed.chmod(0o700)
        os.chown(seed, 0, 0)
        package, spec, manifest = q4u.public_source(seed, task)
        results = {"public": isolated(package, spec, manifest,
                                      ["/usr/bin/python3", "-B", "public_check.py"])}
        for phase in ("forward", "reverse", "no_hook", "upstream"):
            results[phase] = isolated(package, spec, manifest,
                                      ["/usr/bin/python3", "-B", "-"],
                                      hidden_program(phase, catalogue))
    except subprocess.TimeoutExpired:
        uncertain = True
        raise
    finally:
        if not uncertain:
            if package is not None:
                q2.dispose(package, q1.SEEDS)
            if spec is not None:
                spec.unlink(missing_ok=True)
            q2.dispose(seed, q1.SEEDS)
    if inventory(actor) != before:
        raise RuntimeError("H02 candidate changed during grading")
    if any(result.returncode not in {0, 1, 2, 3, 4, 5}
           for result in results.values()):
        raise RuntimeError("H02 check failed outside pytest outcome")
    checks = {name: result.returncode == 0 for name, result in results.items()}
    quality = sum(WEIGHTS[name] for name, passed in checks.items() if passed)
    return {"case": "H02", "quality": quality, "accepted": quality == 100,
            "critical": False, "checks": checks,
            "candidate_edit_sha256": before[EDITABLE],
            "catalogue_sha256": catalogue["catalogue_sha256"],
            "boundary": "Q4U isolated actor uid 65534; evaluator-owned stdin oracle"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actor", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(grade(args.actor), sort_keys=True))


if __name__ == "__main__":
    main()
