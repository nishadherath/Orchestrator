#!/usr/bin/env python3
"""Provider-free audit of the exact H02 S/A source payload."""

import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from worker_wsl_q1 import SEEDS  # noqa: E402
import controller_evaluation  # noqa: E402
import controller_x5_h02_pair as pair  # noqa: E402
import task_executor  # noqa: E402


def sha(data):
    return hashlib.sha256(data).hexdigest()


manifest = json.loads((ROOT / "test/results/2026-09-30-controller-x5-h02-sa-manifest.json").read_text())
assert pair.manifest() == manifest
catalogue = json.loads((ROOT / "test/fixtures/controller_x5_authored_pytest/development/H02/catalogue-h02.json").read_text())
expected = manifest["snapshot"]["actor_files"]
assert set(expected) == set(catalogue["actor_files"])
source = json.loads((ROOT / "test/fixtures/controller_x5_authored_pytest/development/H02/actor/SOURCE.json").read_text())
assert source["origin"] == "authored development adaptation of pytest-asyncio issue 1501"
patterns = [re.compile(pattern, re.IGNORECASE) for pattern in (
    rb"sk-ant-[A-Za-z0-9_-]{15,}", rb"sk-proj-[A-Za-z0-9_-]{15,}",
    rb"gh[pousr]_[A-Za-z0-9]{20,}", rb"AKIA[0-9A-Z]{16}",
    rb"-----BEGIN [A-Z ]*PRIVATE KEY-----", rb"xox[baprs]-[A-Za-z0-9-]{20,}")]
rows = []
for arm in ("S", "A"):
    actor = SEEDS / f"x5-h02-sa-{manifest['manifest_sha256'][:16]}-{arm.lower()}"
    count = 0
    size = 0
    for name, digest in expected.items():
        path = actor / name
        assert path.is_file() and not path.is_symlink() and path.stat().st_nlink == 1, name
        data = path.read_bytes()
        assert sha(data) == digest, name
        assert not any(pattern.search(data) for pattern in patterns), name
        count += 1
        size += len(data)
    root_id = controller_evaluation.digest(
        {"manifest": manifest["manifest_sha256"], "case": "H02", "arm": arm})[:24]
    state = task_executor.TaskExecutor(actor, None).status(root_id)
    assert state["state"] == "ready" and not state["attempts"]
    assert state["budget"]["spent_usd"] == 0 and not state["budget"]["unresolved"]
    rows.append({"arm": arm, "actor_root": str(actor), "files": count,
                 "bytes": size, "secret_pattern_hits": 0,
                 "root_state": state["state"], "spent_usd": 0,
                 "source_origin": source["origin"],
                 "only_manifest_files_packaged": True})
assert rows[0]["bytes"] == rows[1]["bytes"]
notice = json.loads((ROOT / "test/results/2026-09-30-controller-x5-h02-sa-cost-notice.json").read_text())
assert notice["approved"] is True
assert "159 authored pytest-asyncio fixture files" in notice["approval_source"]
assert "Claude.ai destination" in notice["approval_source"]
pair.gate(manifest, notice)
print(json.dumps({"result": "PASS", "manifest_sha256": manifest["manifest_sha256"],
                  "destination": "Claude.ai subscription via Q4U launcher",
                  "paid_gate_active": True,
                  "payload": rows}, sort_keys=True))
