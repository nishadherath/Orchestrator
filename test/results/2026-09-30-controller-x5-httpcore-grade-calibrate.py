"""Calibrate H01 evaluator-owned scores and a protected-edit control."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_h01_grade as h01  # noqa: E402
import worker_wsl_q2_verify as q2  # noqa: E402


CASE = ROOT / "test/fixtures/controller_x5_authored_httpcore/development/H01"
RESULT = ROOT / "test/results/2026-09-30-controller-x5-httpcore-grade-calibration.json"
EXPECTED = {"baseline": 25, "partial": 50, "reference": 100, "alternative": 100}
POOLS = ("httpcore/_sync/connection_pool.py", "httpcore/_async/connection_pool.py")


def main() -> None:
    if os.name != "posix" or os.geteuid() != 0:
        raise RuntimeError("H01 grade calibration requires WSL root")
    rows = []
    with tempfile.TemporaryDirectory(prefix="x5-h01-grade-", dir=q2.SEEDS) as raw:
        temporary_root = Path(raw).resolve()
        if not temporary_root.is_relative_to(q2.SEEDS.resolve()):
            raise RuntimeError("H01 grade copy escaped seed root")
        for label, quality in EXPECTED.items():
            actor = temporary_root / label
            shutil.copytree(CASE / "actor", actor)
            if label != "baseline":
                for name in POOLS:
                    shutil.copyfile(CASE / "variants" / label / name, actor / name)
            result = h01.grade(actor)
            rows.append({"variant": label, "grade": result,
                         "matched_expected": result["quality"] == quality
                         and result["accepted"] == (quality == 100)
                         and result["critical"] is False})
        actor = temporary_root / "protected_edit"
        shutil.copytree(CASE / "actor", actor)
        for name in POOLS:
            shutil.copyfile(CASE / "variants/reference" / name, actor / name)
        issue = actor / "ISSUE.md"
        issue.write_bytes(issue.read_bytes() + b"\nchanged\n")
        tamper = h01.grade(actor)
        rows.append({"variant": "protected_edit", "grade": tamper,
                     "matched_expected": tamper["critical"] is True
                     and tamper["quality"] == 0 and not tamper["accepted"]})
        actor = temporary_root / "spoof"
        shutil.copytree(CASE / "actor", actor)
        source = actor / POOLS[0]
        source.write_bytes(source.read_bytes() + b"\nimport unittest\n"
                           b"unittest.TestCase.assertNotIn = lambda *args, **kwargs: None\n")
        spoof = h01.grade(actor)
        rows.append({"variant": "spoof", "grade": spoof,
                     "matched_expected": spoof["critical"] is True
                     and spoof["quality"] == 0 and not spoof["accepted"]
                     and bool(spoof.get("scope_violations"))})
    qualified = all(row["matched_expected"] for row in rows)
    RESULT.write_text(json.dumps({"schema_version": 1, "case": "H01",
                                  "qualified": qualified, "rows": rows},
                                 sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"qualified": qualified,
                      "rows": [{"variant": row["variant"],
                                "quality": row["grade"]["quality"],
                                "critical": row["grade"]["critical"]}
                               for row in rows]}, sort_keys=True))
    if not qualified:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
