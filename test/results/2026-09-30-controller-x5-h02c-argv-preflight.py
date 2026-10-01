"""Check the exact H02c worker argv against the installed Q4U launch contract."""

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_h02c_producer as h02  # noqa: E402
from worker_adapter import WorkerRequest  # noqa: E402
from worker_wsl_transport import _linux_command  # noqa: E402
import worker_wsl_q4u_adapter as q4u  # noqa: E402


def main() -> None:
    row = h02.manifest()
    actor = h02.actor_path(row)
    request = WorkerRequest(
        actor_root=actor,
        issue=(actor / "ISSUE.md").read_text(encoding="utf-8"),
        allowed_edits=(h02.task(row)["editable_paths"][0],),
        requested_cell="worker-sonnet-low",
        allowance_usd=h02.MAXIMUM_USD,
        policy="fixed_floor",
        admission_token="a" * 48,
        invocation_id="b" * 32,
        revision_id="c" * 64,
        decision_digest="d" * 64,
        intent_digest="e" * 64)
    adapter = q4u.Q4UWslAdapter(h02.task(row))
    command = adapter.command(request)
    if len(command) != 20 or command[-1] != q4u.schema_argument():
        raise RuntimeError("H02c adapter command differs from Q4U contract")
    linux = [*_linux_command(command[:-1]), command[-1]]
    installed = q4u.LAUNCHER.read_bytes()
    source = (ROOT / "tools/worker_wsl_namespace_q4u.sh").read_bytes()
    if hashlib.sha256(installed).digest() != hashlib.sha256(source).digest():
        raise RuntimeError("Q4U installed launcher differs from source")
    if (len(linux) != 21 or linux[1] != "-p"
            or linux[9] != "--max-budget-usd" or linux[10] != "4.0"
            or linux[14] != f"--settings={q4u.RUNTIME / 'actor-settings.json'}"
            or linux[15] != "--no-session-persistence"
            or linux[20] != q4u.schema_argument()
            or b"0 < x <= 4" not in installed):
        raise RuntimeError("H02c translated argv violates installed Q4U launcher")
    print(json.dumps({"qualified": True, "provider_calls": 0,
                      "adapter_argv_count": len(command),
                      "launcher_argv_count": len(linux),
                      "allowance_usd": h02.MAXIMUM_USD,
                      "launcher_sha256": hashlib.sha256(installed).hexdigest(),
                      "manifest_sha256": row["manifest_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
