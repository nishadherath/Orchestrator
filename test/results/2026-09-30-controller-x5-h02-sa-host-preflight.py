"""Provider-free Controller host check on the settled H02c candidate snapshot."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_dispatch  # noqa: E402
import controller_x5_h02c_producer as h02  # noqa: E402
from worker_wsl_q1 import SEEDS  # noqa: E402
from worker_wsl_q3_adapter import GRAFT, MCP, NODE  # noqa: E402


def main() -> None:
    row = h02.load(h02.MANIFEST_PATH)
    source = h02.actor_path(row)
    with tempfile.TemporaryDirectory(prefix="h02-controller-host-", dir=SEEDS) as raw:
        actor = Path(raw)
        for name in row["actor_files"]:
            target = actor / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((source / name).read_bytes())
        (actor / ".mcp.json").write_bytes(MCP.read_bytes())
        graph = subprocess.run([str(NODE), str(GRAFT), "build", str(actor)],
                               cwd=actor, capture_output=True, text=True,
                               timeout=120, check=False)
        if graph.returncode or not (actor / "graft").is_dir():
            raise RuntimeError("H02 Controller Graft build failed: " + graph.stderr[-300:])
        capability = controller_dispatch.ControllerRuntimeAdapter().capability(actor)
        print(json.dumps({"qualified": True, "provider_calls": 0,
                          "graft_enforcement_proven": capability.get(
                              "graft_enforcement_proven"),
                          "controller_host_graph": True,
                          "snapshot_plugin_sha256": h02.sha(
                              (actor / "pytest_asyncio/plugin.py").read_bytes())},
                         sort_keys=True))


if __name__ == "__main__":
    main()
