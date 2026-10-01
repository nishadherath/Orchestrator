#!/usr/bin/env python3
"""Public H03 reproducer. No provider or hidden oracle is invoked."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
import controller_integrity as integrity  # noqa: E402
import system_controller as controller  # noqa: E402


def acceptance() -> dict:
    contract = {"version": 1, "kind": "rubric", "criteria": ["fix the duplicate"],
                "constraints": [], "required_outputs": ["result.txt"],
                "protected_paths": [], "command": [], "rubric": ["inspect the result"],
                "timeout_s": 30.0}
    return {"contract": contract, "contract_digest": integrity.digest(contract)}


def main() -> None:
    canned = controller._canned()
    changed = copy.deepcopy(canned["frame_v1"])
    for record in changed:
        if record["type"] == "FrameRecord":
            record["acceptance_criteria"] = ["fix the duplicate", "check every related path"]
    scripted = controller._happy_path_script()
    scripted[("frame", "framer")] = [changed, canned["frame_v1"], canned["frame_v2"]]
    fake = controller.FakeRoleRunner(scripted)
    with tempfile.TemporaryDirectory(prefix="x5-h03-public-") as folder:
        result = controller.run_quick(
            "Duplicate accounts from whitespace; legacy_ids.py is frozen.",
            Path(folder), 5.0, 30, lambda _remaining: fake, run_id="public",
            acceptance=acceptance(),
        )
        ledger = [json.loads(line) for line in
                  (result.run_dir / "ledger.jsonl").read_text(encoding="utf-8").splitlines()]
    frames = [row["acceptance_criteria"] for row in ledger if row["type"] == "FrameRecord"]
    observed = {"outcome": result.outcome, "frames": frames,
                "framer_calls": fake.calls.count(("frame", "framer"))}
    print(json.dumps(observed, sort_keys=True))
    assert result.outcome == "solution", "Controller did not finish after a correctable reply"
    assert frames and all(row == ["fix the duplicate"] for row in frames), \
        "the external criterion changed in the committed ledger"


if __name__ == "__main__":
    main()
