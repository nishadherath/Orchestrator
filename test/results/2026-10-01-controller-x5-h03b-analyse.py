"""Record the stopped H03b producer's evidence without any provider call."""
import difflib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_h03_pilot as pilot

row = pilot.manifest()
result = pilot.load(pilot.RUN_DIR / "producer-result.json")
if result["eligible"] or result["budget"]["unresolved"]:
    raise RuntimeError("Producer must be stopped and settled before private analysis")
state = pilot.entry(row, "B0").status(pilot.root_id(row, "B0"))
if len(state["attempts"]) != 1:
    raise RuntimeError("Expected exactly one stopped producer attempt")
attempt = state["attempts"][0]
receipt = attempt.get("receipt") or {}
if not receipt.get("terminal") or not receipt.get("writer_stopped"):
    raise RuntimeError("Producer writer has not stopped")
actor = pilot.actor_path(row, "B0")
grade = None
grade_error = None
try:
    grade = pilot.grade_actor(row, "B0")
except pilot.PilotStop as exc:
    grade_error = str(exc)
protected_stable = all(
    not (actor / name).is_symlink()
    and pilot.sha((actor / name).read_bytes()) == digest
    for name, digest in row["actor_files"].items()
    if name != pilot.EDITABLE
)
analysis = {
    "manifest_sha256": row["manifest_sha256"],
    "root_id": pilot.root_id(row, "B0"),
    "state": state["state"],
    "attempt_count": len(state["attempts"]),
    "protected_stable": protected_stable,
    "verification": attempt.get("verification"),
    "receipt": receipt,
    "grade": grade,
    "grade_error": grade_error,
    "spent_usd": state["budget"]["spent_usd"],
    "provider_calls_in_analysis": 0,
}
pilot.exclusive(pilot.RUN_DIR / "B0-analysis.json", analysis)
before = (pilot.SOURCE / pilot.EDITABLE).read_text().splitlines(keepends=True)
after = (actor / pilot.EDITABLE).read_text().splitlines(keepends=True)
with (pilot.RUN_DIR / "B0.patch").open("x", encoding="utf-8", newline="\n") as stream:
    stream.writelines(difflib.unified_diff(before, after, "before/system_controller.py",
                                         "after/system_controller.py"))
print(json.dumps({key: value for key, value in analysis.items() if key != "receipt"},
                 sort_keys=True))
