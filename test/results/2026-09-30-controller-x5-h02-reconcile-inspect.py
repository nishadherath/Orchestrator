"""Read the stopped H02 worker and Q4U receipts without replaying it."""

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_h02_producer as h02  # noqa: E402
import worker_wsl_q1 as q1  # noqa: E402


def main() -> None:
    row = h02.manifest()
    status = h02.entry(row).status(h02.root_id(row))
    attempt = status["attempts"][-1]
    invocation = attempt["invocation_id"]
    name = "q1-" + invocation
    paths = {"actor": q1.ACTORS / name,
             "output": q1.OUTPUTS / name,
             "manifest": q1.MANIFESTS / f"{name}.json",
             "start": q1.MANIFESTS / f"{name}.start.json",
             "stop": q1.MANIFESTS / f"{name}.stop.json"}
    boundary = {}
    for label, path in paths.items():
        value = {"exists": path.exists(), "path": str(path)}
        if path.is_file() and label in {"manifest", "start", "stop"}:
            data = json.loads(path.read_text(encoding="utf-8"))
            value["keys"] = sorted(data)
            value["status"] = data.get("status")
            value["phase"] = data.get("phase")
            value["exit_code"] = data.get("exit_code")
        boundary[label] = value
    print(json.dumps({"state": status["state"], "block": status.get("block"),
                      "events_tail": status.get("events", [])[-8:],
                      "attempt": attempt, "budget": status["budget"],
                      "boundary": boundary}, indent=2, sort_keys=True,
                     default=str))


if __name__ == "__main__":
    main()
