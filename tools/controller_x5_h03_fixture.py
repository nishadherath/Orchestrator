#!/usr/bin/env python3
"""Build an isolated development actor for the observed Controller frame defect.

This is retrospective engineering calibration, not a reserved or blind case.
No provider call is made. The generator and reference source stay outside the
actor shown to a worker.
"""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
ACTOR = ROOT / "test" / "fixtures" / "controller_x5_h03" / "actor"
REFERENCE = ROOT / "test" / "fixtures" / "controller_x5_h03" / "variants" / "reference"
PARTIAL = ROOT / "test" / "fixtures" / "controller_x5_h03" / "variants" / "partial"
ALTERNATIVE = ROOT / "test" / "fixtures" / "controller_x5_h03" / "variants" / "alternative"

OLD_WRITE = '''    def write_with_retry(phase: str, role: str, records: list[dict], expected_types: set[str],
                          retry_prompt: Callable[[list[ScribeRejection]], str] | None) -> list[dict]:
        accepted, rejected = scribe.write(records, writer_role=role, expected_types=expected_types)
        if rejected and retry_prompt is not None:
            for _ in range(MAX_RECORD_RETRIES):
                if not rejected:
                    break
                fixed = call(phase, role, retry_prompt(rejected))
                more_accepted, rejected = scribe.write(fixed, writer_role=role, expected_types=expected_types)
                accepted += more_accepted
        return accepted

'''

ALTERNATIVE_WRITE = '''    def write_with_retry(phase: str, role: str, records: list[dict], expected_types: set[str],
                          retry_prompt: Callable[[list[ScribeRejection]], str] | None) -> list[dict]:
        def guarded_write(batch: list[dict]) -> tuple[list[dict], list[ScribeRejection]]:
            if role == "framer" and acceptance_state is not None and any(
                    record.get("type") == "FrameRecord"
                    and record.get("acceptance_criteria") != acceptance_state["criteria"]
                    for record in batch):
                rejected = [ScribeRejection(record, [
                    "The FrameRecord must preserve the externally frozen acceptance criteria exactly; "
                    "the complete batch was rejected before commit"])
                    for record in batch]
                scribe._log_rejections(rejected, role)
                return [], rejected
            return scribe.write(batch, writer_role=role, expected_types=expected_types)

        accepted, rejected = guarded_write(records)
        if rejected and retry_prompt is not None:
            for _ in range(MAX_RECORD_RETRIES):
                if not rejected:
                    break
                fixed = call(phase, role, retry_prompt(rejected))
                more_accepted, rejected = guarded_write(fixed)
                accepted += more_accepted
        return accepted

'''

ISSUE = '''# Controller closes before checking a supplied acceptance contract

An external caller supplies one immutable acceptance criterion for a quick
Controller run. A reproduced run closes with a gap before the later
verification and candidate stages, although the scripted roles include a
corrective reply within the configured call ceiling. Run
`python public_check.py` to reproduce the observed behaviour.

Make the Controller recover when the role output is correctable. Preserve
the caller's criterion exactly, keep the existing retry ceiling, and retain
a useful gap when the role cannot be corrected.
Edit only `tools/system_controller.py`. The check runs without provider calls.
'''

PUBLIC_CHECK = '''#!/usr/bin/env python3
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
    assert frames and all(row == ["fix the duplicate"] for row in frames), \\
        "the external criterion changed in the committed ledger"


if __name__ == "__main__":
    main()
'''


def old_source(source: str) -> str:
    start = source.index("    def write_with_retry(")
    end = source.index("    def phases() -> RunResult:", start)
    source = source[:start] + OLD_WRITE + source[end:]
    prompt_start = source.index('        if problem.get("acceptance_criteria"):',
                                source.index("def build_frame_prompt("))
    prompt_end = source.index('        body.append("Produce ledger version 1.', prompt_start)
    source = source[:prompt_start] + source[prompt_end:]
    source, count = re.subn(r",\n\s+framer_prompt=frame_prompt\)", ")", source)
    if count != 3:
        raise RuntimeError(f"expected three Framer call sites; found {count}")
    newer = '''                frame_prompt = build_frame_prompt(problem, [], prior_ledger, falsified)
                recs = call("frame", "framer", frame_prompt)
                accepted = write_with_retry("frame", "framer", recs, {"PremiseRecord", "FrameRecord"},
                                             lambda rej: _retry_prompt(frame_prompt, rej))'''
    older = '''                recs = call("frame", "framer", build_frame_prompt(problem, [], prior_ledger, falsified))
                accepted = write_with_retry("frame", "framer", recs, {"PremiseRecord", "FrameRecord"},
                                             lambda rej: _retry_prompt(build_frame_prompt(problem, [], prior_ledger, falsified), rej))'''
    if source.count(newer) != 1:
        raise RuntimeError("critique reframe call site changed")
    source = source.replace(newer, older)
    return source


def generate() -> None:
    if ACTOR.exists() or REFERENCE.exists():
        raise FileExistsError("H03 output already exists; do not overwrite a frozen actor")
    ACTOR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(DIST / "tools", ACTOR / "tools")
    shutil.copytree(DIST / "src", ACTOR / "src")
    shutil.copy2(DIST / "LICENSE", ACTOR / "LICENSE")
    source = (DIST / "tools" / "system_controller.py").read_text(encoding="utf-8")
    (ACTOR / "tools" / "system_controller.py").write_text(old_source(source), encoding="utf-8", newline="\n")
    (ACTOR / "ISSUE.md").write_text(ISSUE, encoding="utf-8", newline="\n")
    (ACTOR / "public_check.py").write_text(PUBLIC_CHECK, encoding="utf-8", newline="\n")
    REFERENCE.mkdir(parents=True)
    (REFERENCE / "system_controller.py").write_text(source, encoding="utf-8", newline="\n")


def make_partial() -> None:
    """A plausible initial-frame-only repair that misses re-entry safety."""
    if PARTIAL.exists():
        raise FileExistsError("H03 partial control already exists")
    source = (REFERENCE / "system_controller.py").read_text(encoding="utf-8")
    old = ('lambda rej: _retry_prompt(frame_prompt, rej),\n'
           '                                         framer_prompt=frame_prompt)')
    new = 'lambda rej: _retry_prompt(frame_prompt, rej))'
    if source.count(old) != 1:
        raise RuntimeError("reframe call site changed")
    PARTIAL.mkdir(parents=True)
    (PARTIAL / "system_controller.py").write_text(source.replace(old, new),
                                                    encoding="utf-8", newline="\n")


def make_alternative() -> None:
    """Use the existing Scribe rejection retry as the correction mechanism."""
    if ALTERNATIVE.exists():
        raise FileExistsError("H03 alternative control already exists")
    source = (ACTOR / "tools" / "system_controller.py").read_text(encoding="utf-8")
    if source.count(OLD_WRITE) != 1:
        raise RuntimeError("baseline retry implementation changed")
    ALTERNATIVE.mkdir(parents=True)
    (ALTERNATIVE / "system_controller.py").write_text(
        source.replace(OLD_WRITE, ALTERNATIVE_WRITE), encoding="utf-8", newline="\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--generate", action="store_true")
    action.add_argument("--partial", action="store_true")
    action.add_argument("--alternative", action="store_true")
    args = parser.parse_args()
    if args.generate:
        generate()
        print(ACTOR)
    elif args.partial:
        make_partial()
        print(PARTIAL)
    else:
        make_alternative()
        print(ALTERNATIVE)


if __name__ == "__main__":
    main()
