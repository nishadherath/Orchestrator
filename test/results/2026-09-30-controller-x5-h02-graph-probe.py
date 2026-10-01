"""Reproduce H02's provider-free Graft graph step on a fresh staged actor."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_h02_producer as h02  # noqa: E402
import worker_wsl_q1 as q1  # noqa: E402
import worker_wsl_q2_verify as q2  # noqa: E402
import worker_wsl_q3_adapter as q3  # noqa: E402
import worker_wsl_q4u_adapter as q4u  # noqa: E402


def main() -> None:
    if os.name != "posix" or os.geteuid() != 0:
        raise RuntimeError("H02 graph probe requires WSL root")
    row = h02.case()
    seed = Path(tempfile.mkdtemp(prefix="h02-graph-seed-", dir=q1.SEEDS))
    package = spec = None
    name = "q1-" + uuid.uuid4().hex
    actor = q1.ACTORS / name
    staged = False
    try:
        shutil.copytree(h02.SOURCE, seed, dirs_exist_ok=True)
        seed.chmod(0o700)
        os.chown(seed, 0, 0)
        package, spec, _ = q4u.public_source(seed, h02.task(row))
        q4u.stage(package, spec, name)
        staged = True
        q3.build_actor_graph(actor)
        graph = actor / "graft"
        result = {"graph_ok": graph.is_dir(),
                  "largest_graph_file_bytes": max(
                      (path.stat().st_size for path in graph.rglob("*")
                       if path.is_file()), default=0)}
        launched = subprocess.run(
            [str(q4u.LAUNCHER), str(actor), "--", "/usr/bin/python3",
             "-B", "-c", "from pathlib import Path; print(Path('graft').is_dir())"],
            cwd="/", capture_output=True, text=True, timeout=60,
            preexec_fn=q3.cap_output)
        result["credential_free_launcher_ok"] = (
            launched.returncode == 0 and launched.stdout.strip() == "True")
        result["launcher_exit_code"] = launched.returncode
        result["launcher_stderr_tail"] = launched.stderr[-250:]
        print(json.dumps(result, sort_keys=True))
    finally:
        if staged:
            q2.dispose(actor, q1.ACTORS)
            q2.dispose(q1.OUTPUTS / name, q1.OUTPUTS)
            for suffix in (".json", ".start.json", ".stop.json"):
                (q1.MANIFESTS / f"{name}{suffix}").unlink(missing_ok=True)
        if package is not None:
            q2.dispose(package, q1.SEEDS)
        if spec is not None:
            spec.unlink(missing_ok=True)
        q2.dispose(seed, q1.SEEDS)


if __name__ == "__main__":
    main()
