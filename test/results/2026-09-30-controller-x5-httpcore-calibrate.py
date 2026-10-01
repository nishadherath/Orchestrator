"""Provider-free H01 baseline and overlay discrimination check."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "test/fixtures/controller_x5_authored_httpcore/development/H01"
ORACLE = ROOT / "test/oracles/controller_x5_authored_httpcore/H01_hidden.py"
RESULT = ROOT / "test/results/2026-09-30-controller-x5-httpcore-calibration.json"
POOLS = (Path("httpcore/_sync/connection_pool.py"),
         Path("httpcore/_async/connection_pool.py"))
EXPECTED = {"baseline": (False, False), "partial": (True, False),
            "reference": (True, True), "alternative": (True, True)}


def run(script: Path, actor: Path) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(actor)
    result = subprocess.run([sys.executable, "-B", str(script)], cwd=actor,
                            env=env, text=True, capture_output=True, timeout=20)
    return {"passed": result.returncode == 0,
            "exit_code": result.returncode,
            "output_tail": (result.stdout + result.stderr)[-1400:]}


def wsl_path(path: Path) -> str:
    resolved = path.resolve()
    if resolved.drive.upper() != ROOT.resolve().drive.upper():
        raise RuntimeError("WSL fixture is on another drive")
    return "/mnt/" + resolved.drive[0].lower() + resolved.as_posix()[2:]


def run_wsl(script: Path, actor: Path) -> dict:
    argv = ["wsl.exe", "-d", "kali-linux", "-u", "wsl", "--cd", wsl_path(actor),
            "--", "/usr/bin/env", "PYTHONPATH=" + wsl_path(actor),
            "python3", "-B", wsl_path(script)]
    result = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=30)
    return {"passed": result.returncode == 0,
            "exit_code": result.returncode,
            "output_tail": (result.stdout + result.stderr)[-1400:]}


def main() -> None:
    rows = []
    with tempfile.TemporaryDirectory(prefix="x5-h01-", dir=ROOT / "test/results") as temp:
        temporary_root = Path(temp).resolve()
        if not temporary_root.is_relative_to(ROOT.resolve()):
            raise RuntimeError("temporary actor escaped workspace")
        for label, expected in EXPECTED.items():
            actor = temporary_root / label
            shutil.copytree(CASE / "actor", actor)
            if label != "baseline":
                for pool in POOLS:
                    overlay = CASE / "variants" / label / pool
                    shutil.copyfile(overlay, actor / pool)
            public = run(actor / "public_check.py", actor)
            protected = run(ORACLE, actor)
            observed = (public["passed"], protected["passed"])
            wsl_public = run_wsl(actor / "public_check.py", actor)
            wsl_protected = run_wsl(ORACLE, actor)
            wsl_observed = (wsl_public["passed"], wsl_protected["passed"])
            rows.append({"variant": label,
                         "pool_sha256": {pool.as_posix(): hashlib.sha256((actor / pool).read_bytes()).hexdigest()
                                         for pool in POOLS},
                         "public": public, "protected": protected,
                         "wsl_public": wsl_public, "wsl_protected": wsl_protected,
                         "matched_expected": observed == expected and wsl_observed == expected})
    body = {"schema_version": 1, "case": "H01", "python": sys.version.split()[0],
            "results": rows, "qualified": all(row["matched_expected"] for row in rows)}
    RESULT.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"qualified": body["qualified"],
                      "rows": [{"variant": row["variant"],
                                "public": row["public"]["passed"],
                                "protected": row["protected"]["passed"],
                                "wsl_public": row["wsl_public"]["passed"],
                                "wsl_protected": row["wsl_protected"]["passed"]}
                               for row in rows]}, sort_keys=True))
    if not body["qualified"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
