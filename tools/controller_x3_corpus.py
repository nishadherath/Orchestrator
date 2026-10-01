#!/usr/bin/env python3
"""Inventory the X3 corpus against its frozen 48-task mechanism contract.

This provider-free check intentionally reports incomplete work. An ID becomes
ready only after a public actor package, protected oracle and independent
controls exist with safe paths and exact editable overlays. It does not grade
quality or convert the historical R5 label fixture into executable evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import controller_evaluation  # noqa: E402

ACTORS = ROOT / "test" / "fixtures" / "controller_x3"
ORACLES = ROOT / "test" / "oracles" / "controller_x3"
CONTROLS = {"reference", "alternative", "partial", "label_copy", "poison_json"}
MAX_FILE_BYTES = 100_000


class CorpusError(ValueError):
    """A present task violates the X3 actor/oracle separation contract."""


def _files(root: Path) -> dict[str, str]:
    if root.is_symlink() or not root.is_dir():
        raise CorpusError(f"unsafe directory: {root}")
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or (not path.is_file() and not path.is_dir()):
            raise CorpusError(f"unsafe fixture path: {path}")
        if path.is_file():
            if path.stat().st_size > MAX_FILE_BYTES:
                raise CorpusError(f"oversized fixture file: {path}")
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def _ready(row: dict) -> dict | None:
    task_id = row["task_id"]
    root = ACTORS / row["split"] / task_id
    actor = root / "actor"
    oracle = ORACLES / f"{task_id}.json"
    if not root.exists() and not oracle.exists():
        return None
    if not actor.is_dir() or not oracle.is_file() or oracle.is_symlink():
        raise CorpusError(f"incomplete task package: {task_id}")
    public_files = _files(actor)
    if not {"acceptance.json", "issue.md", "app.py", "public_check.py"} <= set(public_files):
        raise CorpusError(f"required public files missing: {task_id}")
    forbidden = {"oracle.json", "family.json", "reference.py", "expected.json"}
    if set(public_files) & forbidden:
        raise CorpusError(f"protected metadata leaked into actor: {task_id}")
    public_text = (actor / "issue.md").read_text(encoding="utf-8")
    if task_id in public_text or row["family_id"] in public_text:
        raise CorpusError(f"benchmark identity leaked in public issue: {task_id}")
    contract = json.loads((actor / "acceptance.json").read_text(encoding="utf-8"))
    editable = contract.get("editable_paths")
    if (contract.get("schema_version") != 1
            or contract.get("public_command") != ["python3", "-B", "public_check.py"]
            or not isinstance(editable, list) or not 2 <= len(editable) <= 8
            or len(set(editable)) != len(editable)
            or any(not isinstance(name, str) or name.startswith("/")
                   or ".." in Path(name).parts or name not in public_files
                   or name in {"app.py", "public_check.py", "acceptance.json", "issue.md"}
                   for name in editable)):
        raise CorpusError(f"invalid editable boundary: {task_id}")
    oracle_value = json.loads(oracle.read_text(encoding="utf-8"))
    if (oracle_value.get("schema_version") != 1
            or oracle_value.get("task_id") != task_id
            or not isinstance(oracle_value.get("cases"), list)
            or not oracle_value["cases"]):
        raise CorpusError(f"invalid protected oracle: {task_id}")
    variants = {}
    for name in CONTROLS:
        files = _files(root / "variants" / name)
        if set(files) != set(editable):
            raise CorpusError(f"{task_id} {name} overlay differs from editable boundary")
        variants[name] = files
    return {"actor_files": public_files,
            "oracle_sha256": hashlib.sha256(oracle.read_bytes()).hexdigest(),
            "variant_files": variants}


def inventory() -> dict:
    contract = controller_evaluation.load_contract()
    blueprints = controller_evaluation.task_blueprints(contract)
    if len(blueprints) != 48:
        raise CorpusError("frozen contract no longer has 48 task blueprints")
    rows = []
    for blueprint in blueprints:
        item = {"task_id": blueprint["task_id"],
                "family_id": blueprint["family_id"],
                "split": blueprint["split"],
                "mechanism": blueprint["mechanism"]}
        package = _ready(item)
        rows.append({**item, "status": "ready" if package else "pending",
                     "package": package})
    known_ids = {row["task_id"] for row in rows}
    unexpected = sorted(path.name for split in ("development", "reserved")
                        for path in (ACTORS / split).glob("*")
                        if path.is_dir() and path.name not in known_ids)
    if unexpected:
        raise CorpusError(f"uncontracted X3 task directories: {unexpected}")
    body = {"schema_version": 1, "mode": "controller-x3-inventory",
            "contract_sha256": hashlib.sha256(controller_evaluation.CONTRACT_PATH.read_bytes()).hexdigest(),
            "required_tasks": len(rows),
            "ready_tasks": sum(row["status"] == "ready" for row in rows),
            "pending_tasks": sum(row["status"] == "pending" for row in rows),
            "tasks": rows}
    body["inventory_sha256"] = controller_evaluation.digest(body)
    return body


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = inventory()
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8", newline="\n")
    print(json.dumps({key: result[key] for key in (
        "required_tasks", "ready_tasks", "pending_tasks", "inventory_sha256")},
        sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
