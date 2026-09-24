#!/usr/bin/env python3
"""Grade one stopped WSL actor without exposing evaluator cases to its code.

The root-owned evaluator reads the oracle outside the actor namespace. Each
case runs from a fresh copy of the four public files, so candidate state from
an earlier case cannot influence a later case. This script makes no provider
call and never grants the candidate access to the oracle path or expected data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from worker_wsl_materialize import ACTORS, NAME, stage

EVALUATOR = Path("/var/lib/orchestrator-worker-n4/evaluator")
LAUNCHER = "/opt/orchestrator-worker-runtime/bin/worker-wsl-namespace"
MAX_ORACLE_BYTES = 1_000_000
MAX_OUTPUT_BYTES = 65_536
CASE_TIMEOUT_SECONDS = 10


class GradeError(RuntimeError):
    """An evaluator input or isolated candidate run was unsafe or incomplete."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _cap_output() -> None:
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_OUTPUT_BYTES, MAX_OUTPUT_BYTES))


def _candidate(actor: Path, case_input: object) -> object:
    """Execute one case in a fresh actor namespace; return its JSON value."""
    copy = stage(actor, "inv-" + uuid.uuid4().hex)
    case_actor = Path(copy["actor_root"])
    before = sha((case_actor / "app.py").read_bytes())

    # Regular files and RLIMIT_FSIZE bound output in the kernel while the
    # candidate runs. communicate(capture_output=True) would grow without a
    # bound until the timeout, even when the result is later rejected.
    with (tempfile.TemporaryFile(dir=EVALUATOR) as stdout,
          tempfile.TemporaryFile(dir=EVALUATOR) as stderr):
        try:
            result = subprocess.run(
                [LAUNCHER, str(case_actor), "--", "/usr/bin/python3", "app.py"],
                input=json.dumps(case_input, separators=(",", ":")) + "\n",
                stdout=stdout, stderr=stderr, text=True, encoding="utf-8",
                timeout=CASE_TIMEOUT_SECONDS, preexec_fn=_cap_output,
            )
        except subprocess.TimeoutExpired as exc:
            raise GradeError("candidate case timed out; writer termination needs review") from exc
        if stdout.tell() >= MAX_OUTPUT_BYTES or stderr.tell() >= MAX_OUTPUT_BYTES:
            raise GradeError("candidate case exceeded the output limit")
        stdout.seek(0)
        output = stdout.read().decode("utf-8", errors="replace")
    if sha((case_actor / "app.py").read_bytes()) != before:
        raise GradeError("candidate changed its implementation during grading")
    if result.returncode:
        return object()
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return object()


def grade(actor_name: str, oracle_source: Path, expected_sha256: str,
          root_state: str) -> dict:
    """Return the N4 scoring fields from isolated black-box case outcomes."""
    if os.geteuid() != 0 or not NAME.fullmatch(actor_name):
        raise GradeError("root identity and an opaque actor name are required")
    if ACTORS.is_symlink() or not ACTORS.is_dir() or ACTORS.stat().st_uid != 0:
        raise GradeError("root-owned actor parent is unavailable")
    actor = ACTORS / actor_name
    if actor.is_symlink() or not actor.is_dir() or actor.stat().st_uid != 0:
        raise GradeError("root-owned actor directory is unavailable")
    app = actor / "app.py"
    if app.is_symlink() or not app.is_file():
        raise GradeError("candidate app.py is missing or redirected")
    if (oracle_source.is_symlink() or not oracle_source.is_file()
            or oracle_source.stat().st_size > MAX_ORACLE_BYTES):
        raise GradeError("oracle source is missing, redirected or too large")
    oracle_path = oracle_source.resolve()
    if not any(oracle_path.is_relative_to(root) for root in (
            EVALUATOR, Path("/mnt/c"), Path("/mnt/d"))):
        raise GradeError("oracle source must be in the hidden evaluator or Windows mount")
    if (EVALUATOR.is_symlink() or not EVALUATOR.is_dir()
            or EVALUATOR.stat().st_uid != 0
            or EVALUATOR.stat().st_mode & 0o077):
        raise GradeError("root-owned evaluator directory is unavailable")
    oracle_bytes = oracle_source.read_bytes()
    if sha(oracle_bytes) != expected_sha256:
        raise GradeError("oracle source does not match the frozen digest")
    try:
        oracle = json.loads(oracle_bytes)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise GradeError("oracle is not valid JSON") from exc
    if (not isinstance(oracle, dict) or oracle.get("schema_version") != 1
            or set(oracle) - {"schema_version", "cases", "no_edit_baseline_sha256"}
            or not isinstance(oracle.get("cases"), list) or not oracle["cases"]):
        raise GradeError("oracle needs schema version 1 and nonempty cases")
    baseline = oracle.get("no_edit_baseline_sha256")
    if baseline is not None and (not isinstance(baseline, str) or len(baseline) != 64):
        raise GradeError("no-edit baseline digest is invalid")
    before_app = sha(app.read_bytes())
    earned = total = 0
    milestones = []
    critical = False
    for case in oracle["cases"]:
        if (not isinstance(case, dict) or set(case) != {"input", "expected", "weight",
                                                        "milestone", "critical"}
                or type(case["weight"]) is not int or case["weight"] <= 0
                or type(case["critical"]) is not bool
                or not isinstance(case["milestone"], str) or not case["milestone"]):
            raise GradeError("oracle case has an invalid contract")
        total += case["weight"]
        passed = _candidate(actor, case["input"]) == case["expected"]
        if passed:
            earned += case["weight"]
            milestones.append(case["milestone"])
        elif case["critical"]:
            critical = True
    if sha(app.read_bytes()) != before_app or sha(oracle_source.read_bytes()) != expected_sha256:
        raise GradeError("actor or oracle changed while grading")
    edited_when_prohibited = baseline is not None and before_app != baseline
    acceptance = earned == total and not edited_when_prohibited
    return {"acceptance": acceptance,
            "quality": 0 if edited_when_prohibited else round(100 * earned / total, 2),
            "critical_error": critical or edited_when_prohibited,
            "false_success": root_state == "accepted" and not acceptance,
            "milestones": milestones,
            "oracle_sha256": expected_sha256, "actor_app_sha256": before_app,
            "case_count": len(oracle["cases"])}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actor-name", required=True)
    parser.add_argument("--oracle-source", type=Path, required=True)
    parser.add_argument("--oracle-sha256", required=True)
    parser.add_argument("--root-state", choices=("accepted", "partial", "failed"),
                        required=True)
    args = parser.parse_args()
    try:
        result = grade(args.actor_name, args.oracle_source, args.oracle_sha256,
                       args.root_state)
    except (OSError, ValueError, GradeError) as exc:
        print(f"isolated grading rejected: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
