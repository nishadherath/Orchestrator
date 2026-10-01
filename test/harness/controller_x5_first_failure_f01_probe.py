"""Provider-free F01 live-driver admission checks in the WSL root runtime."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import acceptance  # noqa: E402
import controller_public_assessment  # noqa: E402
import controller_x5_first_failure as checkpoint  # noqa: E402
import controller_x5_first_failure_f01 as live  # noqa: E402


def check_public(actor: Path, expected: int) -> subprocess.CompletedProcess:
    result = subprocess.run([sys.executable, "-B", "public_check.py"], cwd=actor,
                            capture_output=True, text=True, timeout=20, check=False)
    assert result.returncode == expected, result.stderr[-600:]
    return result


def main() -> None:
    if sys.platform != "linux":
        raise RuntimeError("this probe requires the WSL root runtime")
    row = live.task()
    files = checkpoint.actor_files(live.SOURCE, set(row["actor_files"]))
    assert {name: live.sha(data) for name, data in files.items()} == row["actor_files"]
    first_failure = check_public(live.SOURCE, 1)
    manifest = live.freeze()
    live.validate(manifest)
    notice = {"approved": False, "manifest_sha256": manifest["manifest_sha256"],
              "maximum_usd": live.MAXIMUM_USD, "scope": live.SCOPE,
              "date": dt.date.today().isoformat(), "approval_source": "probe"}
    try:
        live.gate(manifest, notice)
    except live.SmokeStop:
        pass
    else:
        raise AssertionError("unapproved notice passed the paid gate")
    notice["approved"] = True
    live.gate(manifest, notice)
    notice["manifest_sha256"] = "0" * 64
    try:
        live.gate(manifest, notice)
    except live.SmokeStop:
        pass
    else:
        raise AssertionError("changed manifest passed the paid gate")
    inputs = live.assessment_inputs(live.SOURCE)
    protected = sorted(set(row["actor_files"]) - set(row["editable_paths"]))
    with tempfile.TemporaryDirectory(prefix="x5-f01-packet-", dir=live.SEEDS) as raw:
        packet_actor = Path(raw) / "actor"
        shutil.copytree(live.SOURCE, packet_actor)
        (packet_actor / "public_failure.txt").write_text(
            first_failure.stdout + first_failure.stderr, encoding="utf-8")
        revision = {"git": acceptance.revision(packet_actor), "input_paths": protected,
                    "content": acceptance.snapshot(packet_actor, protected)}
        packet = controller_public_assessment.collect(
            packet_actor, issue=inputs["issue"], source_paths=inputs["source_paths"],
            quote_requests=inputs["quote_requests"], input_revision=revision)
    assert len(packet["citations"]) == 3 and len(packet["sources"]) == 4
    state = {"state": "ready", "budget": {"unresolved": []},
             "attempts": [{"sequence": 1}]}
    baseline = live.protected_grade(live.SOURCE, state)
    assert baseline["quality"] == round(100 * 2 / 6, 3)
    with tempfile.TemporaryDirectory(prefix="x5-f01-probe-", dir=live.SEEDS) as raw:
        actor = Path(raw) / "actor"
        shutil.copytree(live.SOURCE, actor)
        reference = live.SOURCE.parent / "variants/reference"
        for name in row["editable_paths"]:
            shutil.copy2(reference / name, actor / name)
        check_public(actor, 0)
        graded = live.protected_grade(actor, {**state, "state": "accepted"})
    assert graded["quality"] == 100 and graded["critical_errors"] == 0
    print({"case": "F01", "manifest_sha256": manifest["manifest_sha256"],
           "packet_sha256": packet["packet_sha256"],
           "baseline_quality": baseline["quality"],
           "reference_quality": graded["quality"], "provider_calls": 0})


if __name__ == "__main__":
    main()
