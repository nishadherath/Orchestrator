"""Run the existing offline checks affected by the local retrieval repair."""
import importlib.util
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("graft_repair_checks", root / "test/harness/check.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
report = module.Report()
for check in (module.check_prose, module.check_context_contract,
              module.check_dist, module.check_diagnostics):
    check(report)
(root / "test/results/2026-10-13-graft-offline-normal.json").write_text(
    json.dumps([vars(c) for c in report.checks], indent=2) + "\n", encoding="utf-8")
for result in report.checks:
    print(result.id, result.status, result.detail)
raise SystemExit(bool(report.failed))
