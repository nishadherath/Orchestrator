"""Provider-free Q3 Graft build outside the Controller mount view."""

from pathlib import Path
import os
import shutil
import sys
import tempfile

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "tools"))

from worker_wsl_q1 import ACTORS
from worker_wsl_q3_adapter import build_actor_graph
from controller_x5_recovery_isolation import hidden_evaluation_tree


source = root / "test/fixtures/controller_x5_public_risk/development/K01/actor"
with tempfile.TemporaryDirectory(prefix="x5-review-graph-preflight-", dir=ACTORS) as raw:
    actor = Path(raw)
    if actor.resolve().parent != ACTORS.resolve():
        raise RuntimeError("preflight path escaped actor root")
    actor.chmod(0o755)
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        destination = actor / relative
        if path.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
    graph = actor / "graft"
    graph.mkdir()
    os.chown(graph, 65534, 65534)
    graph.chmod(0o700)
    if "--after-hidden" in sys.argv:
        with hidden_evaluation_tree(root):
            pass
        os.chdir("/")
    build_actor_graph(actor)
    print({"graft_built": (actor / "graft").is_dir(),
           "after_hidden_view": "--after-hidden" in sys.argv,
           "provider_calls": 0})
