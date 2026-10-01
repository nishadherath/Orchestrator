#!/usr/bin/env python3
"""Provider-free H03 baseline/reference calibration in disposable checkouts."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "test" / "fixtures" / "controller_x5_h03"
ACTOR = FIXTURE / "actor"
REFERENCE = FIXTURE / "variants" / "reference" / "system_controller.py"
PARTIAL = FIXTURE / "variants" / "partial" / "system_controller.py"
ALTERNATIVE = FIXTURE / "variants" / "alternative" / "system_controller.py"
ORACLE = FIXTURE / "oracle.py"
RISK_CHECK = FIXTURE / "risk_check.py"
DEFAULT_RESULT = ROOT / "test" / "results" / "2026-09-30-controller-x5-h03-probe.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(variant: str, *, include_risk: bool) -> dict:
    with tempfile.TemporaryDirectory(prefix="controller-x5-h03-") as temp:
        checkout = Path(temp) / "actor"
        shutil.copytree(ACTOR, checkout)
        if variant in {"reference", "partial", "alternative"}:
            shutil.copy2({"reference": REFERENCE, "partial": PARTIAL,
                          "alternative": ALTERNATIVE}[variant],
                         checkout / "tools" / "system_controller.py")
        process = subprocess.run([sys.executable, "public_check.py"], cwd=checkout,
                                 capture_output=True, text=True, timeout=60, check=False)
        first = process.stdout.splitlines()[:1]
        observed = json.loads(first[0]) if first else None
        oracle = subprocess.run([sys.executable, str(ORACLE), "--actor", str(checkout)],
                                cwd=checkout, capture_output=True, text=True, timeout=60, check=False)
        result = {"returncode": process.returncode, "observed": observed,
                "stderr_tail": process.stderr.splitlines()[-2:],
                "oracle_returncode": oracle.returncode,
                "oracle": json.loads(oracle.stdout) if oracle.returncode == 0 else None,
                "oracle_stderr_tail": oracle.stderr.splitlines()[-2:]}
        if include_risk:
            risk = subprocess.run([sys.executable, str(RISK_CHECK), "--actor", str(checkout)],
                                  cwd=checkout, capture_output=True, text=True, timeout=60, check=False)
            result.update(risk_returncode=risk.returncode,
                          risk=json.loads(risk.stdout) if risk.stdout.strip() else None,
                          risk_stderr_tail=risk.stderr.splitlines()[-2:])
        return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--include-risk", action="store_true")
    args = parser.parse_args()
    baseline = run("baseline", include_risk=args.include_risk)
    partial = run("partial", include_risk=args.include_risk)
    alternative = run("alternative", include_risk=args.include_risk)
    reference = run("reference", include_risk=args.include_risk)
    assert baseline["returncode"] != 0 and baseline["observed"]["outcome"] == "gap", baseline
    assert partial["returncode"] == 0 and partial["observed"]["outcome"] == "solution", partial
    assert alternative["returncode"] == 0 and alternative["observed"]["outcome"] == "solution", alternative
    assert reference["returncode"] == 0 and reference["observed"]["outcome"] == "solution", reference
    assert all(row["oracle_returncode"] == 0 for row in (baseline, partial, alternative, reference))
    assert baseline["oracle"]["score"] < partial["oracle"]["score"] < reference["oracle"]["score"] == 100
    assert alternative["oracle"]["score"] == 100 and not alternative["oracle"]["critical_error"]
    if args.include_risk:
        assert baseline["risk_returncode"] != 0 and partial["risk_returncode"] != 0
        assert alternative["risk_returncode"] == reference["risk_returncode"] == 0
    files = [path for path in ACTOR.rglob("*") if path.is_file()]
    result = {"schema_version": 1, "provider_calls": 0,
              "platform": platform.platform(), "python": platform.python_version(),
              "actor_files": len(files), "actor_bytes": sum(p.stat().st_size for p in files),
              "baseline_source_sha256": digest(ACTOR / "tools" / "system_controller.py"),
              "partial_source_sha256": digest(PARTIAL),
              "alternative_source_sha256": digest(ALTERNATIVE),
              "reference_source_sha256": digest(REFERENCE),
              "baseline": baseline, "partial": partial,
              "alternative": alternative, "reference": reference}
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
