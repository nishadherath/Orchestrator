"""Observe the unchanged public reproducer before its temporary ledger closes."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "test/results/2026-10-01-controller-x5-h03b-pilot-run"
actor = Path(sys.argv[1]).resolve()
analysis = json.loads((RUN / "B0-analysis.json").read_text())
expected = analysis["verification"]["evidence"]["artefacts"]["files"][0]["sha256"]
if hashlib.sha256((actor / "tools/system_controller.py").read_bytes()).hexdigest() != expected:
    raise RuntimeError("Stopped producer source changed")
sys.path.insert(0, str(actor))
import public_check

original = public_check.controller.run_quick
observation = {"provider_calls": 0, "exception": None}

def observe(*args, **kwargs):
    project = args[1]
    fake = args[4](5.0)
    try:
        return original(*args, **kwargs)
    finally:
        observation["calls"] = fake.calls
        ledgers = list(project.rglob("ledger.jsonl"))
        if len(ledgers) != 1:
            raise RuntimeError("Expected one diagnostic ledger")
        records = [json.loads(line) for line in ledgers[0].read_text().splitlines()]
        observation["frames"] = [row for row in records if row["type"] == "FrameRecord"]
        observation["committed_record_count"] = len(records)

public_check.controller.run_quick = observe
output = io.StringIO()
try:
    with contextlib.redirect_stdout(output):
        public_check.main()
except Exception as exc:
    observation["exception"] = type(exc).__name__ + ": " + str(exc)
observation["public_stdout"] = output.getvalue()
observation["source_sha256"] = expected
with (RUN / "B0-public-diagnosis.json").open("x", encoding="utf-8") as stream:
    json.dump(observation, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(json.dumps(observation, sort_keys=True))
