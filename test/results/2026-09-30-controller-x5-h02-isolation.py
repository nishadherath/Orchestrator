"""Provider-free H02 public check and oracle denial in the Q4U boundary."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import worker_wsl_q2_verify as q2  # noqa: E402
import worker_wsl_q1 as q1  # noqa: E402
import worker_wsl_q4u_adapter as q4u  # noqa: E402

CASE = ROOT / "test/fixtures/controller_x5_authored_pytest/development/H02"
ORACLE = ROOT / "test/oracles/controller_x5_authored_pytest/H02/forward/conftest.py"
RESULT = ROOT / "test/results/2026-09-30-controller-x5-h02-isolation.json"
EXPECTED = {"baseline": False, "narrow_control": True,
            "proposal": True, "alternative": True}


def probe(label: str) -> dict:
    actor = CASE / "actor"
    inventory = json.loads((actor / "SOURCE.json").read_text(encoding="utf-8"))
    for name, expected in inventory["files"].items():
        if hashlib.sha256((actor / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"H02 source inventory differs: {name}")
    files = {path.relative_to(actor).as_posix(): q1.digest(path.read_bytes())
             for path in actor.rglob("*") if path.is_file()}
    if len(files) > q1.MAX_FILES:
        raise ValueError("H02 actor exceeds attested file ceiling")
    task = {"actor_files": files, "editable_paths": ["pytest_asyncio/plugin.py"]}
    seed = Path(tempfile.mkdtemp(prefix="h02-seed-", dir=q1.SEEDS))
    package = manifest_path = None
    uncertain = False
    try:
        shutil.copytree(actor, seed, dirs_exist_ok=True)
        seed.chmod(0o700)
        os.chown(seed, 0, 0)
        if label != "baseline":
            overlay = CASE / "variants" / label / "pytest_asyncio"
            if q1.digest((overlay / "__init__.py").read_bytes()) != files["pytest_asyncio/__init__.py"]:
                raise ValueError("H02 variant changed the package facade")
            shutil.copyfile(overlay / "plugin.py", seed / "pytest_asyncio/plugin.py")
        package, manifest_path, manifest = q4u.public_source(seed, task)
        denial = run_isolated(
            package, manifest_path, manifest,
            ["/usr/bin/python3", "-B", "-c",
             "from pathlib import Path;import sys;"
             "\ntry: Path(sys.argv[1]).read_bytes()"
             "\nexcept OSError: print('DENIED')"
             "\nelse: print('EXPOSED')", str(ORACLE)],
        )
        public = run_isolated(
            package, manifest_path, manifest,
            ["/usr/bin/python3", "-B", "public_check.py"],
        )
        return {"variant": label,
                "oracle_read_denied": denial.returncode == 0
                and denial.stdout.strip() == "DENIED",
                "public_passed": public.returncode == 0,
                "public_exit_code": public.returncode,
                "public_tail": (public.stdout + public.stderr)[-600:]}
    except subprocess.TimeoutExpired:
        uncertain = True
        raise
    finally:
        if not uncertain:
            if package is not None:
                q2.dispose(package, q1.SEEDS)
            if manifest_path is not None:
                manifest_path.unlink(missing_ok=True)
            q2.dispose(seed, q1.SEEDS)


def run_isolated(package: Path, spec: Path, manifest: dict,
                 command: list[str]) -> subprocess.CompletedProcess:
    name = "q1-" + uuid.uuid4().hex
    actor = q1.ACTORS / name
    staged = False
    terminal = False
    try:
        q4u.stage(package, spec, name)
        staged = True
        result = subprocess.run(
            [str(q4u.LAUNCHER), str(actor), "--", *command], cwd="/",
            text=True, capture_output=True, timeout=60, preexec_fn=q4u.cap_output,
            check=False)
        terminal = True
        for row in manifest["files"]:
            if q1.digest((actor / row["path"]).read_bytes()) != row["sha256"]:
                raise ValueError(f"H02 isolated actor changed: {row['path']}")
        return result
    finally:
        if staged and terminal:
            q2.dispose(actor, q1.ACTORS)
            q2.dispose(q1.OUTPUTS / name, q1.OUTPUTS)
            for suffix in (".json", ".start.json", ".stop.json"):
                (q1.MANIFESTS / f"{name}{suffix}").unlink(missing_ok=True)


def main() -> None:
    if os.name != "posix" or os.geteuid() != 0:
        raise RuntimeError("H02 isolation probe requires WSL root")
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=[*EXPECTED, "all"], default="all")
    args = parser.parse_args()
    labels = list(EXPECTED) if args.variant == "all" else [args.variant]
    rows = [probe(label) for label in labels]
    qualified = all(row["oracle_read_denied"] and
                    row["public_passed"] == EXPECTED[row["variant"]]
                    for row in rows)
    record = {"schema_version": 1, "case": "H02", "qualified": qualified,
              "boundary": "Q4U isolated actor uid 65534; evaluator-owned oracle",
              "rows": rows}
    if args.variant == "all":
        RESULT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8")
    print(json.dumps({"qualified": qualified, "rows": [
        {"variant": row["variant"], "oracle_read_denied": row["oracle_read_denied"],
         "public_passed": row["public_passed"]} for row in rows]}))
    if not qualified:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
