#!/usr/bin/env python3
"""Provider-free Q4U namespace check for H03's frozen risk variants."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_h03_pilot as pilot  # noqa: E402


def main() -> None:
    row = pilot.case()
    results = {}
    for variant in ("baseline", "partial", "reference"):
        with tempfile.TemporaryDirectory(prefix="h03-risk-smoke-", dir=pilot.SEEDS) as raw:
            actor = Path(raw)
            for name in row["actor_files"]:
                target = actor / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(pilot.SOURCE / name, target)
            if variant != "baseline":
                overlay = pilot.FIXTURE / "variants" / variant / "system_controller.py"
                shutil.copyfile(overlay, actor / pilot.EDITABLE)
            result = pilot.public_risk(row, actor)
            results[variant] = {key: result[key] for key in (
                "passed", "qualified_failure", "returncode", "observed")}
    assert results["baseline"]["qualified_failure"] is True
    assert results["partial"]["qualified_failure"] is True
    assert results["reference"]["passed"] is True
    print(json.dumps({"schema_version": 1, "provider_calls": 0,
                      "variants": results}, sort_keys=True))


if __name__ == "__main__":
    main()
