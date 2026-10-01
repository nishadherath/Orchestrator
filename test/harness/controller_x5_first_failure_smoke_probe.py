"""Provider-free P02 smoke admission checks; run inside attested WSL root."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import acceptance  # noqa: E402
import controller_public_assessment  # noqa: E402
import controller_x5_first_failure as checkpoint  # noqa: E402
import controller_x5_first_failure_smoke as smoke  # noqa: E402
from worker_wsl_q2_verify import verify  # noqa: E402


def main() -> None:
    if sys.platform != "linux":
        raise RuntimeError("this probe requires the WSL root runtime")
    row = smoke.task()
    source = smoke.SOURCE
    files = checkpoint.actor_files(source, set(row["actor_files"]))
    assert {name: smoke.sha(data) for name, data in files.items()} == row["actor_files"]
    public = subprocess.run([sys.executable, "-B", "public_check.py"], cwd=source,
                            capture_output=True, text=True, timeout=15, check=False)
    assert public.returncode == 1 and "AssertionError" in public.stderr
    manifest = smoke.freeze()
    smoke.validate(manifest)
    notice = {"approved": False, "manifest_sha256": manifest["manifest_sha256"],
              "maximum_usd": smoke.MAXIMUM_USD, "scope": smoke.SCOPE,
              "date": dt.date.today().isoformat(), "approval_source": "probe"}
    try:
        smoke.gate(manifest, notice)
    except smoke.SmokeStop:
        pass
    else:
        raise AssertionError("unapproved notice passed the paid gate")
    notice["approved"] = True
    smoke.gate(manifest, notice)
    notice["manifest_sha256"] = "0" * 64
    try:
        smoke.gate(manifest, notice)
    except smoke.SmokeStop:
        pass
    else:
        raise AssertionError("changed manifest passed the paid gate")
    inputs = smoke.assessment_inputs(source)
    protected = sorted(set(row["actor_files"]) - set(row["editable_paths"]))
    revision = {"git": acceptance.revision(source), "input_paths": protected,
                "content": acceptance.snapshot(source, protected)}
    packet = controller_public_assessment.collect(
        source, issue=inputs["issue"], source_paths=inputs["source_paths"],
        quote_requests=inputs["quote_requests"], input_revision=revision)
    assert len(packet["citations"]) == 3 and len(packet["sources"]) == 5
    oracle = ROOT / "test/oracles/worker_q2_public/P02.json"
    baseline = verify("P02", source, None, oracle, "failed", "baseline")
    reference = verify("P02", source, source.parent / "reference", oracle,
                       "accepted", "reference")
    assert baseline["public_pass"] is False
    assert baseline["hidden_acceptance"] is False
    assert reference["public_pass"] is True
    assert reference["hidden_acceptance"] is True
    print({"case": "P02", "manifest_sha256": manifest["manifest_sha256"],
           "public_exit_code": public.returncode,
           "packet_sha256": packet["packet_sha256"],
           "baseline_quality": baseline["quality"],
           "reference_quality": reference["quality"],
           "provider_calls": 0})


if __name__ == "__main__":
    main()
