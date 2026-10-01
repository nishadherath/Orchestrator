"""Regrade the settled H02c candidate after repairing the overload AST check."""

import hashlib
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import controller_x5_h02c_producer as producer  # noqa: E402
import controller_x5_h02_grade as grader  # noqa: E402
import worker_wsl_q1 as q1  # noqa: E402


OUT = ROOT / "test/results/2026-09-30-controller-x5-h02c-regrade.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    row = producer.load(producer.MANIFEST_PATH)
    actor = producer.actor_path(row)
    before = {name: sha(actor / name) for name in row["actor_files"]}
    with tempfile.TemporaryDirectory(prefix="h02c-regrade-", dir=q1.SEEDS) as raw:
        candidate = Path(raw)
        for name in row["actor_files"]:
            target = candidate / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((actor / name).read_bytes())
        grade = grader.grade(candidate)
    if before != {name: sha(actor / name) for name in row["actor_files"]}:
        raise RuntimeError("H02c actor changed during regrade")
    body = {"schema_version": 1, "case": "H02c",
            "original_manifest_sha256": row["manifest_sha256"],
            "original_producer_result_sha256": sha(producer.RUN_DIR / "producer-result.json"),
            "corrected_grader_sha256": sha(Path(grader.__file__)),
            "candidate_plugin_sha256": before[grader.EDITABLE],
            "provider_calls": 0, "grade": grade}
    with OUT.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(body, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"quality": grade["quality"], "accepted": grade["accepted"],
                      "critical": grade["critical"], "checks": grade.get("checks"),
                      "result": str(OUT)}, sort_keys=True))


if __name__ == "__main__":
    main()
