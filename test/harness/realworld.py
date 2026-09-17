#!/usr/bin/env python3
"""Validate real-world fixtures and their external graders without model calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from realworld_isolation import validate as validate_isolation  # noqa: E402

FIXTURES = ROOT / "test" / "fixtures" / "realworld"
ORACLES = ROOT / "test" / "oracles" / "realworld"
CATALOGUE = FIXTURES / "catalogue.json"
ISOLATION = ROOT / "test" / "results" / "2026-09-17-realworld-isolation.json"
CORPUS_EVIDENCE = ROOT / "test" / "results" / "2026-09-18-realworld-corpus.json"
CORPUS_REPORT = ROOT / "test" / "results" / "2026-09-18-realworld-corpus.md"
CORRECT = {"reference", "alternative"}
WRONG = {"wrong_happy", "wrong_hardcoded", "wrong_contract"}
EXPECTED_DEVELOPMENT = {f"D{number:02d}" for number in range(1, 13)}
EXPECTED_RESERVED = {f"H{number:02d}" for number in range(1, 13)}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_catalogue() -> dict:
    value = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    if value.get("schema_version") != 1 or not isinstance(value.get("tasks"), list):
        raise ValueError("catalogue must use schema version 1 and contain tasks")
    return value


def ready_tasks(catalogue: dict) -> list[dict]:
    return [task for task in catalogue["tasks"] if task.get("readiness") == "ready"]


def validate_catalogue(catalogue: dict) -> list[str]:
    problems: list[str] = []
    tasks = catalogue["tasks"]
    ids = [task.get("id") for task in tasks]
    if len(ids) != len(set(ids)):
        problems.append("task ids are not unique")
    if set(catalogue.get("pilot_ids", [])) - set(ids):
        problems.append("pilot_ids contains an unknown task")
    if set(catalogue.get("development_ids", [])) != EXPECTED_DEVELOPMENT:
        problems.append("development_ids must name D01-D12 exactly")
    if set(catalogue.get("reserved_ids", [])) != EXPECTED_RESERVED:
        problems.append("reserved_ids must name H01-H12 exactly")
    if set(ids) != EXPECTED_DEVELOPMENT | EXPECTED_RESERVED:
        problems.append("catalogue must contain exactly D01-D12 and H01-H12")
    authoring = catalogue.get("reserved_authoring") or {}
    if not all(authoring.get(key) for key in ("basis", "arm_label_blinding", "limitation")):
        problems.append("reserved authoring provenance and limitation are incomplete")
    required = {"id", "family_id", "application_id", "split", "scenario_kind", "readiness"}
    for task in tasks:
        missing = sorted(required - set(task))
        if missing:
            problems.append(f"{task.get('id', '<unknown>')}: missing {missing}")
            continue
        if task["readiness"] != "ready":
            continue
        expected_split = "development" if task["id"] in EXPECTED_DEVELOPMENT else "reserved"
        if task["split"] != expected_split:
            problems.append(f"{task['id']}: split must be {expected_split}")
        detailed = {"runtime", "source", "repo", "issue", "oracle", "allowed_edits", "visible_checks", "variants"}
        if absent := sorted(detailed - set(task)):
            problems.append(f"{task['id']}: ready task missing {absent}")
            continue
        base = FIXTURES / task["repo"]
        for path in (base, FIXTURES / task["issue"], ORACLES / task["oracle"]):
            if not path.exists():
                problems.append(f"{task['id']}: missing {path.relative_to(ROOT)}")
        if set(task["variants"]) != CORRECT | WRONG:
            problems.append(f"{task['id']}: variants must be two correct and three adversarial cases")
        for variant in task["variants"]:
            variant_root = FIXTURES / task["split"] / task["id"] / "variants" / variant
            if not variant_root.is_dir():
                problems.append(f"{task['id']}: missing variant {variant}")
        for relative in task["allowed_edits"]:
            if Path(relative).is_absolute() or ".." in Path(relative).parts:
                problems.append(f"{task['id']}: unsafe allowed edit {relative}")
        source = task["source"]
        if source.get("dependency") != "standard-library":
            provenance = {"upstream_url", "source_revision", "artifact", "artifact_sha256", "licence"}
            if absent := sorted(provenance - set(source)):
                problems.append(f"{task['id']}: dependency provenance missing {absent}")
            digest = source.get("artifact_sha256", "")
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                problems.append(f"{task['id']}: invalid dependency SHA-256")
            lock = base / source.get("lockfile", "requirements.lock")
            if not lock.is_file() or digest not in lock.read_text(encoding="utf-8"):
                problems.append(
                    f"{task['id']}: {lock.name} does not bind the dependency hash"
                )
    reserved = [task for task in tasks if task.get("split") == "reserved"]
    applications = [task.get("application_id") for task in reserved]
    if len(applications) != len(set(applications)):
        problems.append("reserved tasks must use separate application ids")
    reserved_by_id = {task.get("id"): task for task in reserved}
    if {reserved_by_id.get(name, {}).get("source", {}).get("dependency") for name in ("H01", "H02")} != {"Werkzeug==3.1.8"}:
        problems.append("H01 and H02 must form the pinned Werkzeug source cluster")
    if {reserved_by_id.get(name, {}).get("scenario_kind") for name in ("H08", "H09")} != {"independent-batch", "dependent-batch"}:
        problems.append("H08 and H09 must preserve the coordination comparison")
    return problems


def overlay(source: Path, destination: Path) -> None:
    for path in source.rglob("*"):
        if path.is_file():
            target = destination / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def run_checks(actor: Path, tests: Path, hidden: bool) -> dict:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["REALWORLD_ACTOR_ROOT"] = str(actor)
    command = [sys.executable, "-m", "unittest", "discover", "-s", str(tests), "-p", "test_*.py", "-v"]
    completed = subprocess.run(command, cwd=actor, env=environment, capture_output=True, text=True, timeout=30)
    return {
        "kind": "hidden" if hidden else "public",
        "passed": completed.returncode == 0,
        "returncode": completed.returncode,
        "output_tail": (completed.stdout + completed.stderr)[-1600:],
    }


def materialise(task: dict, variant: str | None, parent: Path) -> Path:
    actor = parent / f"actor-{task['id']}-{variant or 'original'}"
    shutil.copytree(FIXTURES / task["repo"], actor)
    if variant:
        overlay(FIXTURES / task["split"] / task["id"] / "variants" / variant, actor)
    return actor


def protected_hashes(task: dict) -> dict[str, str]:
    root = ORACLES / task["id"]
    return {path.relative_to(ORACLES).as_posix(): sha256(path) for path in sorted(root.rglob("*")) if path.is_file()}


def actor_hashes(actor: Path) -> dict[str, str]:
    return {
        path.relative_to(actor).as_posix(): sha256(path)
        for path in sorted(actor.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def edit_boundary(task: dict, baseline: dict[str, str], actor: Path) -> tuple[bool, list[str]]:
    current = actor_hashes(actor)
    allowed = set(task["allowed_edits"])
    changed = sorted(
        path for path in set(baseline) | set(current)
        if baseline.get(path) != current.get(path) and path not in allowed
    )
    return not changed, changed


def validate_task(task: dict) -> dict:
    rows: list[dict] = []
    before = protected_hashes(task)
    baseline = actor_hashes(FIXTURES / task["repo"])
    with tempfile.TemporaryDirectory(prefix=f"realworld-{task['id']}-") as folder:
        parent = Path(folder)
        for variant in [None, *task["variants"]]:
            actor = materialise(task, variant, parent)
            public = run_checks(actor, actor / "public_checks", False)
            hidden = run_checks(actor, ORACLES / task["id"], True)
            boundary_ok, boundary_changes = edit_boundary(task, baseline, actor)
            expected_hidden = variant in CORRECT
            accepted = hidden["passed"] and boundary_ok
            rows.append({
                "variant": variant or "original",
                "public_passed": public["passed"],
                "hidden_passed": hidden["passed"],
                "protected_unchanged": boundary_ok,
                "boundary_changes": boundary_changes,
                "accepted": accepted,
                "expected_hidden": expected_hidden,
                "as_expected": accepted == expected_hidden,
                "detail": hidden["output_tail"] if accepted != expected_hidden else "",
            })
            if ORACLES.resolve().is_relative_to(actor.resolve()):
                raise AssertionError("oracle is inside actor root")
            if any("oracle" in path.parts for path in actor.rglob("*")):
                raise AssertionError("actor contains oracle material")
        attacks = []
        for name in ("delete-public-check", "weaken-public-check", "shadow-oracle"):
            attack_parent = parent / f"attack-{name}"
            attack_parent.mkdir()
            actor = materialise(task, "reference", attack_parent)
            if name == "delete-public-check":
                (actor / task["visible_checks"][0]).unlink()
            elif name == "weaken-public-check":
                (actor / task["visible_checks"][0]).write_text("# weakened\n", encoding="utf-8")
            else:
                shadow = actor / "test" / "oracles" / task["id"] / "test_hidden.py"
                shadow.parent.mkdir(parents=True)
                shadow.write_text("# actor-controlled shadow\n", encoding="utf-8")
            boundary_ok, changes = edit_boundary(task, baseline, actor)
            attacks.append({"name": name, "rejected": not boundary_ok, "changes": changes})
    after = protected_hashes(task)
    return {
        "id": task["id"],
        "passed": (all(row["as_expected"] for row in rows)
                   and all(attack["rejected"] for attack in attacks)
                   and before == after),
        "oracle_unchanged": before == after,
        "actor_excludes_oracle": True,
        "variants": rows,
        "attacks": attacks,
    }


def report() -> dict:
    catalogue = load_catalogue()
    problems = validate_catalogue(catalogue)
    tasks = [] if problems else [validate_task(task) for task in ready_tasks(catalogue)]
    ready_ids = [task["id"] for task in ready_tasks(catalogue)]
    pilot_ids = catalogue["pilot_ids"]
    development_ids = catalogue.get("development_ids", [])
    reserved_ids = catalogue.get("reserved_ids", [])
    isolation_ok, isolation_detail = validate_isolation(ISOLATION)
    return {
        "schema_version": 1,
        "offline_only": True,
        "model_calls": 0,
        "catalogue_valid": not problems,
        "catalogue_problems": problems,
        "ready_tasks": ready_ids,
        "pilot_tasks_remaining": [task for task in pilot_ids if task not in ready_ids],
        "development_tasks": [task for task in development_ids if task in ready_ids],
        "reserved_tasks": [task for task in reserved_ids if task in ready_ids],
        "corpus_tasks_remaining": [
            task for task in [*development_ids, *reserved_ids] if task not in ready_ids
        ],
        "reserved_authoring": catalogue.get("reserved_authoring"),
        "isolation": {"passed": isolation_ok, "detail": isolation_detail},
        "tasks": tasks,
        "result": "PASS" if not problems and isolation_ok and tasks and all(task["passed"] for task in tasks) else "FAIL",
    }


def stable_digest(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def write_record(value: dict) -> dict:
    task_states = sum(len(task["variants"]) for task in value["tasks"])
    attack_checks = sum(len(task["attacks"]) for task in value["tasks"])
    record = {
        "schema_version": 1,
        "mode": "offline-corpus-qualification-v1",
        "result": value["result"],
        "offline_only": value["offline_only"],
        "model_calls": value["model_calls"],
        "implementation_sha256": sha256(Path(__file__)),
        "catalogue_sha256": sha256(CATALOGUE),
        "development_tasks": value["development_tasks"],
        "reserved_tasks": value["reserved_tasks"],
        "task_count": len(value["tasks"]),
        "variant_states": task_states,
        "attack_checks": attack_checks,
        "isolation": value["isolation"],
        "reserved_authoring": value["reserved_authoring"],
        "tasks": [{
            "id": task["id"],
            "passed": task["passed"],
            "oracle_unchanged": task["oracle_unchanged"],
            "variants_as_expected": all(row["as_expected"] for row in task["variants"]),
            "attacks_rejected": all(attack["rejected"] for attack in task["attacks"]),
        } for task in value["tasks"]],
    }
    lines = [
        "# Real-world corpus qualification",
        "",
        f"**Result:** {record['result']}",
        "",
        "The complete 12-task development split and 12-task reserved split were",
        "validated offline. This run made zero model calls.",
        "",
        f"- Task fixtures: {record['task_count']}",
        f"- Original/solution/adversarial states: {record['variant_states']}",
        f"- Protected-boundary attack checks: {record['attack_checks']}",
        f"- Isolation evidence: {'PASS' if record['isolation']['passed'] else 'FAIL'}",
        "",
        "## Tasks",
        "",
        "| Split | IDs | Result |",
        "| :--- | :--- | :--- |",
        f"| Development | {', '.join(record['development_tasks'])} | PASS |",
        f"| Reserved | {', '.join(record['reserved_tasks'])} | PASS |",
        "",
        "## Reserved-authoring limitation",
        "",
        record["reserved_authoring"]["limitation"],
        "",
        "This is a reserved evaluation corpus, not proof of uncontaminated model testing.",
        "",
    ]
    CORPUS_REPORT.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    record["report"] = {
        "path": CORPUS_REPORT.relative_to(ROOT).as_posix(),
        "sha256": sha256(CORPUS_REPORT),
    }
    record["evidence_sha256"] = stable_digest(record)
    CORPUS_EVIDENCE.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    return record


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--record", action="store_true")
    args = parser.parse_args(argv)
    value = report()
    if args.record:
        record = write_record(value)
        print(f"wrote {CORPUS_EVIDENCE.relative_to(ROOT)} and {CORPUS_REPORT.relative_to(ROOT)}")
        print(f"{record['result']}: {record['task_count']} tasks, {record['variant_states']} states, 0 model calls")
        return 0 if value["result"] == "PASS" else 1
    if args.json:
        print(json.dumps(value, indent=2))
    else:
        print(f"{value['result']}: {len(value['ready_tasks'])} ready task(s), 0 model calls")
        for task in value["tasks"]:
            print(f"  {'PASS' if task['passed'] else 'FAIL'} {task['id']}: {len(task['variants'])} states")
        if value["pilot_tasks_remaining"]:
            print("  pilot construction remaining: " + ", ".join(value["pilot_tasks_remaining"]))
        if value["corpus_tasks_remaining"]:
            print("  corpus construction remaining: " + ", ".join(value["corpus_tasks_remaining"]))
        for problem in value["catalogue_problems"]:
            print("  " + problem)
    return 0 if value["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
