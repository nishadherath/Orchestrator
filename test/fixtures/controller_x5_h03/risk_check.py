#!/usr/bin/env python3
"""Predeclared public follow-up for H03 accepted producer bytes.

This is not the protected oracle. It exercises one corrected critique re-entry
and reports the result for both review arms before any private grade.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--actor", type=Path, required=True)
    args = parser.parse_args()
    actor = args.actor.resolve()
    sys.path.insert(0, str(actor / "tools"))
    import controller_integrity as integrity  # noqa: E402
    import system_controller as controller  # noqa: E402

    canned = controller._canned()
    frame_v3 = copy.deepcopy(canned["frame_v2"])
    frame_v3[0].update(text="The Critic's premise was corrected", source="critique",
                       supersedes="prem-001", ledger_version=3, references=["prem-001"])
    frame_v3[1].update(ledger_version=3, references=["frame-002", "prem-004", "cand-001"])
    changed = copy.deepcopy(frame_v3)
    changed[1]["acceptance_criteria"] = ["fix the duplicate", "an unapproved extra condition"]

    candidate_v3 = copy.deepcopy(canned["candidate"])
    candidate_v3[0].update(ledger_version=3, references=["prem-004"])
    first_critique = copy.deepcopy(canned["critique"])
    first_critique[1]["falsified_premise_claims"] = [{"premise_id": "prem-001", "reason": "false"}]
    second_critique = copy.deepcopy(canned["critique"])
    for record in second_critique:
        record["ledger_version"] = 3
    second_critique[0]["candidate_id"] = "cand-003"
    second_critique[0]["references"] = ["cand-003"]
    selection = copy.deepcopy(canned["selection"])
    selection[0]["ledger_version"] = 3
    selection[0]["shortlist"][0]["candidate_id"] = "cand-003"
    selection[0]["references"] = ["cand-001", "cand-003"]
    scripted = controller._happy_path_script()
    scripted[("frame", "framer")] = [canned["frame_v1"], canned["frame_v2"], changed, frame_v3]
    scripted[("generate", "generator")] = [canned["candidate"], [], [], candidate_v3, [], []]
    scripted[("critique", "critic")] = [first_critique, second_critique]
    scripted[("select", "selector")] = [selection]
    fake = controller.FakeRoleRunner(scripted)
    contract = {"version": 1, "kind": "rubric", "criteria": ["fix the duplicate"],
                "constraints": [], "required_outputs": ["result.txt"],
                "protected_paths": [], "command": [], "rubric": ["inspect the result"],
                "timeout_s": 30.0}
    acceptance = {"contract": contract, "contract_digest": integrity.digest(contract)}
    with tempfile.TemporaryDirectory(prefix="controller-x5-h03-risk-") as folder:
        result = controller.run_quick(
            "Duplicate accounts from whitespace; legacy_ids.py is frozen.",
            Path(folder), 5.0, 30, lambda _remaining: fake, run_id="risk",
            acceptance=acceptance,
        )
        ledger = [json.loads(line) for line in
                  (result.run_dir / "ledger.jsonl").read_text(encoding="utf-8").splitlines()]
    frames = [row["acceptance_criteria"] for row in ledger if row["type"] == "FrameRecord"]
    passed = result.outcome == "solution" and frames == [["fix the duplicate"]] * 3
    print(json.dumps({"schema_version": 1, "passed": passed, "outcome": result.outcome,
                      "frames": frames, "framer_calls": fake.calls.count(("frame", "framer"))},
                     sort_keys=True))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
