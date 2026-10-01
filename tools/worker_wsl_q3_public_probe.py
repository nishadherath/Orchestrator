#!/usr/bin/env python3
"""Exercise Q3 public grading against protected edits and false completion.

Run as WSL root. This creates private, disposable candidate seeds and makes
no provider call. Evidence is saved only after every attack is rejected.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import tempfile
from pathlib import Path

from worker_adapter import digest
from worker_q3_public_catalogue import FIXTURES, ROOT, sha
from worker_wsl_q1 import SEEDS
from worker_wsl_q3_public import PublicGradeError, grade_candidate


def seed(task_id: str, directory: Path) -> Path:
    shutil.copytree(FIXTURES / task_id / "actor", directory,
                    dirs_exist_ok=True)
    directory.chmod(0o700)
    return directory


def rejected(action) -> bool:
    try:
        action()
    except PublicGradeError:
        return True
    return False


def run() -> dict:
    checks = {}
    with tempfile.TemporaryDirectory(prefix="q3-public-probe-", dir=SEEDS) as raw:
        base = Path(raw)
        candidate = seed("P03", base)
        result = grade_candidate("P03", candidate, "accepted")
        checks["false_completion_detected"] = (
            result["false_success"] and not result["hidden_acceptance"]
            and result["quality"] < 100 and result["oracle_read_denied"])

    with tempfile.TemporaryDirectory(prefix="q3-public-probe-", dir=SEEDS) as raw:
        candidate = seed("P03", Path(raw))
        (candidate / "ISSUE.md").write_text("altered", encoding="utf-8")
        checks["protected_issue_edit_rejected"] = rejected(
            lambda: grade_candidate("P03", candidate, "accepted"))

    with tempfile.TemporaryDirectory(prefix="q3-public-probe-", dir=SEEDS) as raw:
        candidate = seed("P03", Path(raw))
        (candidate / "public_check.py").write_text("print('PASS')\n", encoding="utf-8")
        checks["public_answer_edit_rejected"] = rejected(
            lambda: grade_candidate("P03", candidate, "accepted"))

    with tempfile.TemporaryDirectory(prefix="q3-public-probe-", dir=SEEDS) as raw:
        candidate = seed("P03", Path(raw))
        target = candidate / "click/core.py"
        target.unlink()
        target.symlink_to(candidate / "click/parser.py")
        checks["editable_symlink_rejected"] = rejected(
            lambda: grade_candidate("P03", candidate, "accepted"))

    with tempfile.TemporaryDirectory(prefix="q3-public-probe-", dir=SEEDS) as raw:
        candidate = seed("P03", Path(raw))
        target = candidate / "click/core.py"
        target.unlink()
        os.link(candidate / "click/parser.py", target)
        checks["editable_hardlink_rejected"] = rejected(
            lambda: grade_candidate("P03", candidate, "accepted"))

    with tempfile.TemporaryDirectory(prefix="q3-public-probe-", dir=SEEDS) as raw:
        candidate = seed("P04", Path(raw))
        reference = FIXTURES / "P04/reference"
        for file in reference.rglob("*.py"):
            (candidate / file.relative_to(reference)).write_bytes(file.read_bytes())
        manager = candidate / "urllib3/poolmanager.py"
        code = manager.read_text(encoding="utf-8")
        original = 'if port is None:\n            port = port_by_scheme.get(request_context["scheme"].lower(), 80)'
        attacked = 'if port is None or (port == 0 and scheme == "https"):\n            port = port_by_scheme.get(request_context["scheme"].lower(), 80)'
        if code.count(original) != 1:
            raise RuntimeError("public-answer probe source changed")
        manager.write_text(code.replace(original, attacked), encoding="utf-8")
        result = grade_candidate("P04", candidate, "accepted")
        checks["public_pass_hidden_fail_detected"] = (
            result["public_pass"] and not result["hidden_acceptance"]
            and result["false_success"] and 0 < result["quality"] < 100
            and result["oracle_read_denied"])

    value = {"schema_version": 1, "recorded_at_utc": dt.datetime.now(
                 dt.timezone.utc).isoformat(timespec="seconds"),
             "provider_calls": 0, "provider_cost_usd": 0,
             "checks": checks,
             "source_sha256": {name: sha(ROOT / name) for name in (
                 "tools/worker_wsl_q3_public_probe.py",
                 "tools/worker_wsl_q3_public.py",
                 "tools/worker_q3_public_catalogue.py")},
             "task_sha256": {task: json.loads((FIXTURES / task / "task.json")
                 .read_text(encoding="utf-8"))["task_sha256"]
                 for task in ("P03", "P04")}}
    value["result"] = "PASS" if all(checks.values()) else "FAIL"
    value["evidence_sha256"] = digest(value)
    output = ROOT / "test/results" / (dt.datetime.now(dt.timezone.utc).date().isoformat()
                                    + "-worker-q3-public-attacks.json")
    if output.exists():
        raise RuntimeError("attack evidence already exists; no overwrite")
    output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8", newline="\n")
    return value


if __name__ == "__main__":
    evidence = run()
    print(evidence["result"], evidence["checks"], evidence["evidence_sha256"])
    raise SystemExit(0 if evidence["result"] == "PASS" else 2)
