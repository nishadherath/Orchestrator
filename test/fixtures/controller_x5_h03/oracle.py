#!/usr/bin/env python3
"""Private provider-free H03 acceptance; never copy this into the actor."""
from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path


def inspect_case(actor: Path, frames: list[list[dict]], *, external: bool = True,
                 critique_override: list[dict] | None = None) -> dict:
    sys.path.insert(0, str(actor / "tools"))
    import controller_integrity as integrity  # noqa: E402
    import system_controller as controller  # noqa: E402

    contract = {"version": 1, "kind": "rubric", "criteria": ["fix the duplicate"],
                "constraints": [], "required_outputs": ["result.txt"],
                "protected_paths": [], "command": [], "rubric": ["inspect the result"],
                "timeout_s": 30.0}
    acceptance = {"contract": contract, "contract_digest": integrity.digest(contract)} if external else None
    scripted = controller._happy_path_script()
    scripted[("frame", "framer")] = frames
    if critique_override is not None:
        scripted[("critique", "critic")] = [critique_override]
    fake = controller.FakeRoleRunner(scripted)
    with tempfile.TemporaryDirectory(prefix="controller-x5-h03-oracle-") as folder:
        result = controller.run_quick(
            "Duplicate accounts from whitespace; legacy_ids.py is frozen.",
            Path(folder), 5.0, 30, lambda _remaining: fake, run_id="oracle",
            acceptance=acceptance,
        )
        ledger = [json.loads(line) for line in
                  (result.run_dir / "ledger.jsonl").read_text(encoding="utf-8").splitlines()]
    return {"outcome": result.outcome,
            "framer_calls": fake.calls.count(("frame", "framer")),
            "frames": [row["acceptance_criteria"] for row in ledger if row["type"] == "FrameRecord"],
            "framer_records": sum(row["type"] in {"FrameRecord", "PremiseRecord", "CandidateRecord"}
                                  for row in ledger),
            "framer_record_versions": [row["ledger_version"] for row in ledger
                                       if row["type"] in {"FrameRecord", "PremiseRecord", "CandidateRecord"}],
            "unmet_criteria": result.record.get("unmet_criteria", [])}


def changed(batch: list[dict]) -> list[dict]:
    records = copy.deepcopy(batch)
    for record in records:
        if record["type"] == "FrameRecord":
            record["acceptance_criteria"] = ["fix the duplicate", "unapproved extra condition"]
    return records


def grade(actor: Path) -> dict:
    sys.path.insert(0, str(actor / "tools"))
    import system_controller as controller  # noqa: E402
    canned = controller._canned()
    initial = inspect_case(actor, [changed(canned["frame_v1"]), canned["frame_v1"], canned["frame_v2"]])
    reframe = inspect_case(actor, [canned["frame_v1"], changed(canned["frame_v2"]), canned["frame_v2"]])
    persistent_initial = inspect_case(actor, [changed(canned["frame_v1"]), changed(canned["frame_v1"])])
    persistent_reframe = inspect_case(actor, [canned["frame_v1"], changed(canned["frame_v2"]),
                                      changed(canned["frame_v2"])])
    frame_v3 = copy.deepcopy(canned["frame_v2"])
    frame_v3[0].update(text="The Critic's premise was corrected", source="critique",
                       supersedes="prem-001", ledger_version=3, references=["prem-001"])
    frame_v3[1].update(ledger_version=3, references=["frame-002", "prem-004", "cand-001"])
    critique = copy.deepcopy(canned["critique"])
    critique[1]["falsified_premise_claims"] = [{"premise_id": "prem-001", "reason": "false"}]
    persistent_critique = inspect_case(
        actor, [canned["frame_v1"], canned["frame_v2"], changed(frame_v3), changed(frame_v3)],
        critique_override=critique)
    ordinary = inspect_case(actor, [canned["frame_v1"], canned["frame_v2"]], external=False)
    criteria = ["fix the duplicate"]
    checks = {
        "initial_correction": initial["outcome"] == "solution" and initial["frames"] == [criteria, criteria],
        "reframe_correction": reframe["outcome"] == "solution" and reframe["frames"] == [criteria, criteria],
        "persistent_initial_atomic": (persistent_initial["outcome"] == "gap"
                                      and persistent_initial["frames"] == []
                                      and persistent_initial["framer_records"] == 0
                                      and persistent_initial["unmet_criteria"] == criteria),
        "persistent_reframe_atomic": (persistent_reframe["outcome"] == "gap"
                                      and persistent_reframe["frames"] == [criteria]
                                      and persistent_reframe["unmet_criteria"] == criteria),
        "persistent_critique_atomic": (persistent_critique["outcome"] == "gap"
                                       and persistent_critique["frames"] == [criteria, criteria]
                                       and 3 not in persistent_critique["framer_record_versions"]
                                       and persistent_critique["unmet_criteria"] == criteria),
        "ordinary_run": ordinary["outcome"] == "solution",
    }
    weights = {"initial_correction": 15, "reframe_correction": 15,
               "persistent_initial_atomic": 20, "persistent_reframe_atomic": 20,
               "persistent_critique_atomic": 20, "ordinary_run": 10}
    return {"schema_version": 2, "checks": checks,
            "score": sum(weights[name] for name, passed in checks.items() if passed),
            "critical_error": any(not checks[name] for name in
                                  ("persistent_initial_atomic", "persistent_reframe_atomic",
                                   "persistent_critique_atomic"))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--actor", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(grade(args.actor.resolve()), sort_keys=True))


if __name__ == "__main__":
    main()
