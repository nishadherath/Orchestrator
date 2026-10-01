#!/usr/bin/env python3
"""Freeze and validate two pinned public Q2 tasks; optionally run WSL probes."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import worker_wsl_q1_attestation as q1_host

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "test/fixtures/worker_q2_public"
ORACLES = ROOT / "test/oracles/worker_q2_public"
CATALOGUE = FIXTURES / "catalogue.json"
RESULT = ROOT / "test/results/2026-09-25-worker-q2-public.json"
TASKS = {
    "P01": {"upstream_url": "https://github.com/tkem/cachetools",
            "upstream_commit": "3c082c654c2804b9354e4b62dbd2994f1aac464d",
            "upstream_source": "src/cachetools", "licence": "MIT",
            "licence_file": "LICENSE", "package": "cachetools",
            "stratum": "concurrent cold-key computation and typed-key invariant"},
    "P02": {"upstream_url": "https://github.com/pallets/itsdangerous",
            "upstream_commit": "672971d66a2ef9f85151e53283113f33d642dabd",
            "upstream_source": "src/itsdangerous", "licence": "BSD-3-Clause",
            "licence_file": "LICENSE.txt", "package": "itsdangerous",
            "stratum": "signed-token protocol and clock boundary"},
}
RUNTIME = {
    "tools/worker_wsl_q2_case.py": "/opt/orchestrator-worker-runtime/worker_wsl_q2_case.py",
    "tools/worker_wsl_q2_verify.py": "/opt/orchestrator-worker-runtime/worker_wsl_q2_verify.py",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(value: dict) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8"))


def files(root: Path) -> dict[str, bytes]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"task directory is missing: {root}")
    result = {}
    for item in sorted(root.rglob("*")):
        if item.is_symlink():
            raise ValueError(f"task contains a symlink: {item}")
        if item.is_file():
            result[item.relative_to(root).as_posix()] = item.read_bytes()
    return result


def build_catalogue() -> dict:
    tasks = []
    for task_id, metadata in TASKS.items():
        fixture = FIXTURES / task_id
        actor = files(fixture / "actor")
        reference = files(fixture / "reference")
        partial = files(fixture / "variants/partial")
        contract = json.loads(actor["acceptance.json"])
        editable = contract.get("editable_paths")
        if (contract.get("schema_version") != 1 or not isinstance(editable, list)
                or not 2 <= len(editable) <= 8 or set(editable) != set(reference)
                or set(editable) != set(partial)
                or contract.get("public_command") != ["python3", "-B", "public_check.py"]):
            raise ValueError(f"{task_id}: invalid editable/public contract")
        if (not {"ISSUE.md", "acceptance.json", "public_check.py",
                 metadata["licence_file"]} <= set(actor)
                or len(actor) > 200 or sum(map(len, actor.values())) > 5_000_000
                or any(len(value) > 1_000_000 for value in actor.values())):
            raise ValueError(f"{task_id}: Q1 package limit or protected file missing")
        package = metadata["package"] + "/"
        upstream = {name.removeprefix(package): sha(reference.get(name, value))
                    for name, value in actor.items() if name.startswith(package)}
        if {name for name in reference if actor[name] != reference[name]} != set(editable):
            raise ValueError(f"{task_id}: both authored regressions must differ from upstream")
        if not any(partial[name] == actor[name] for name in editable) or not any(
                partial[name] == reference[name] for name in editable):
            raise ValueError(f"{task_id}: partial variant must fix exactly part of the task")
        source_lines = sum(len(reference.get(name, value).splitlines()) for name, value in actor.items()
                           if name.startswith(package) and name.endswith(".py"))
        if not 1_000 <= source_lines <= 20_000:
            raise ValueError(f"{task_id}: source size outside target stratum")
        oracle = json.loads((ORACLES / f"{task_id}.json").read_text(encoding="utf-8"))
        cases = oracle.get("cases")
        if (oracle.get("schema_version") != 1 or not isinstance(cases, list)
                or sum(case["weight"] for case in cases) != 100
                or len({case["milestone"] for case in cases}) != len(cases)):
            raise ValueError(f"{task_id}: oracle cases are invalid")
        tasks.append({"id": task_id, **metadata,
                      "issue_origin": "authored regression on pinned upstream source; not an upstream issue",
                      "dependency_lock": "Python 3.10+ standard library only",
                      "source_lines": source_lines, "source_files": len(upstream),
                      "actor_files": {name: sha(data) for name, data in actor.items()},
                      "actor_total_bytes": sum(map(len, actor.values())),
                      "clean_upstream_source_sha256": upstream,
                      "editable_paths": sorted(editable),
                      "reference_files": {name: sha(data) for name, data in reference.items()},
                      "partial_files": {name: sha(data) for name, data in partial.items()},
                      "oracle_sha256": sha((ORACLES / f"{task_id}.json").read_bytes()),
                      "oracle_cases": len(cases)})
    return {"schema_version": 1, "date": "2026-09-25",
            "purpose": "public Q2 pilot calibration only; excluded from reserved inference",
            "selection_visibility": "issue and actor package only; never oracle, variant or family label",
            "tasks": tasks}


def check_catalogue() -> dict:
    stored = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    if stored != build_catalogue():
        raise ValueError("Q2 public catalogue differs from current fixture bytes")
    return stored


def wsl(*args: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(["wsl.exe", "-u", "root", "--", *args],
                          capture_output=True, text=True, timeout=timeout)


def linux_path(path: Path) -> str:
    result = wsl("wslpath", "-a", path.resolve().as_posix(), timeout=30)
    if result.returncode:
        raise RuntimeError("WSL path translation failed")
    return result.stdout.strip()


def runtime_hashes() -> dict[str, str]:
    result = wsl("sha256sum", *RUNTIME.values(), timeout=90)
    if result.returncode:
        raise RuntimeError("Q2 runtime hashes unavailable")
    rows = [line.split() for line in result.stdout.splitlines()]
    if len(rows) != len(RUNTIME) or any(len(row) != 2 for row in rows):
        raise RuntimeError("Q2 runtime hash inventory incomplete")
    return {source: row[0] for source, row in zip(RUNTIME, rows, strict=True)}


def run() -> dict:
    catalogue = check_catalogue()
    q1 = json.loads(q1_host.OUTPUT.read_text(encoding="utf-8"))
    if not q1_host.validate(q1, check_host=True):
        raise RuntimeError("Q1 WSL host attestation is stale")
    expected_runtime = {name: sha((ROOT / name).read_bytes()) for name in RUNTIME}
    if runtime_hashes() != expected_runtime:
        raise RuntimeError("Q2 installed runtime differs from source; run worker_wsl_q2_install.sh")
    outcomes = []
    for task in catalogue["tasks"]:
        task_id = task["id"]
        fixture = FIXTURES / task_id
        before = {name: sha(data) for name, data in files(fixture / "actor").items()}
        for variant in ("baseline", "partial", "reference"):
            args = ["python3", "/opt/orchestrator-worker-runtime/worker_wsl_q2_verify.py",
                    "--task-id", task_id, "--source", linux_path(fixture / "actor"),
                    "--oracle", linux_path(ORACLES / f"{task_id}.json"),
                    "--variant", variant, "--root-state",
                    "accepted" if variant == "reference" else variant if variant == "partial" else "failed"]
            if variant != "baseline":
                overlay = fixture / ("reference" if variant == "reference" else "variants/partial")
                args += ["--overlay", linux_path(overlay)]
            process = wsl(*args)
            if process.returncode:
                raise RuntimeError(f"{task_id}/{variant} WSL verification failed: "
                                   + (process.stderr + process.stdout)[-500:])
            value = json.loads(process.stdout)
            if (value.get("task_id") != task_id or value.get("variant") != variant
                    or value.get("provider_calls") != 0 or value.get("provider_cost_usd") != 0
                    or value.get("oracle_sha256") != task["oracle_sha256"]):
                raise RuntimeError(f"{task_id}/{variant} returned unbound evidence")
            outcomes.append(value)
        if before != {name: sha(data) for name, data in files(fixture / "actor").items()}:
            raise RuntimeError(f"{task_id} public source changed during verification")
    for task_id in TASKS:
        rows = [row for row in outcomes if row["task_id"] == task_id]
        baseline, partial, reference = rows
        if (baseline["hidden_acceptance"] or partial["hidden_acceptance"]
                or not reference["hidden_acceptance"] or baseline["public_pass"]
                or partial["public_pass"] or not reference["public_pass"]
                or not baseline["quality"] < partial["quality"] < reference["quality"]
                or any(row["provider_calls"] != 0 for row in rows)):
            raise RuntimeError(f"{task_id} calibration variants did not separate")
    record = {"schema_version": 1, "date_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "result": "PASS", "catalogue_sha256": digest(catalogue),
              "q1_host_evidence_sha256": q1["evidence_sha256"],
              "runtime_sha256": expected_runtime,
              "outcomes": outcomes, "provider_calls": 0, "provider_cost_usd": 0,
              "claim": "two public task mechanisms only; no routing or population effect"}
    record["evidence_sha256"] = digest(record)
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def check_evidence() -> dict:
    catalogue = check_catalogue()
    record = json.loads(RESULT.read_text(encoding="utf-8"))
    body = {key: value for key, value in record.items() if key != "evidence_sha256"}
    if (record.get("result") != "PASS" or record.get("evidence_sha256") != digest(body)
            or record.get("catalogue_sha256") != digest(catalogue)
            or record.get("runtime_sha256") !=
            {name: sha((ROOT / name).read_bytes()) for name in RUNTIME}
            or record.get("provider_calls") != 0
            or record.get("provider_cost_usd") != 0):
        raise ValueError("Q2 saved result digest, source or cost evidence differs")
    outcomes = record.get("outcomes")
    if (not isinstance(outcomes, list) or len(outcomes) != len(TASKS) * 3
            or {(row["task_id"], row["variant"]) for row in outcomes} !=
            {(task_id, variant) for task_id in TASKS
             for variant in ("baseline", "partial", "reference")}):
        raise ValueError("Q2 saved outcome inventory is incomplete")
    for task in catalogue["tasks"]:
        task_id = task["id"]
        oracle = json.loads((ORACLES / f"{task_id}.json").read_text(encoding="utf-8"))
        rows = {row["variant"]: row for row in outcomes if row["task_id"] == task_id}
        for row in rows.values():
            if (row.get("oracle_sha256") != task["oracle_sha256"]
                    or row.get("oracle_direct_read_denied") is not True
                    or row.get("provider_calls") != 0 or row.get("provider_cost_usd") != 0
                    or len(row.get("cases", [])) != len(oracle["cases"])):
                raise ValueError(f"{task_id}: saved isolation or case evidence differs")
            earned = sum(case["weight"] for case in row["cases"] if case["passed"])
            critical = any(not case["passed"] and frozen["critical"]
                           for case, frozen in zip(row["cases"], oracle["cases"], strict=True))
            if (row["quality"] != earned or any(
                    case["weight"] != frozen["weight"]
                    or case["milestone"] != frozen["milestone"]
                    for case, frozen in zip(row["cases"], oracle["cases"], strict=True))
                    or row["critical_error"] is not critical
                    or row["hidden_acceptance"] is not (earned == 100 and row["public_pass"])
                    or row["false_success"] is not False):
                raise ValueError(f"{task_id}: saved score differs from case outcomes")
        if (not rows["baseline"]["quality"] < rows["partial"]["quality"] < 100
                or rows["baseline"]["hidden_acceptance"]
                or rows["partial"]["hidden_acceptance"]
                or not rows["reference"]["hidden_acceptance"]
                or rows["reference"]["quality"] != 100):
            raise ValueError(f"{task_id}: saved variants do not separate")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--check-evidence", action="store_true")
    args = parser.parse_args()
    try:
        if args.write:
            CATALOGUE.write_text(json.dumps(build_catalogue(), indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
            print("Wrote Q2 public catalogue")
        elif args.check:
            value = check_catalogue()
            print(f"PASS: {len(value['tasks'])} public Q2 task packages match their catalogue")
        elif args.check_evidence:
            value = check_evidence()
            print(f"PASS: {len(value['outcomes'])} saved Q2 grades match frozen source and oracle")
        else:
            record = run()
            print(f"PASS: {len(record['outcomes'])} isolated public/hidden grades; "
                  f"evidence {record['evidence_sha256']}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError,
            subprocess.TimeoutExpired) as exc:
        print(f"Q2 public corpus rejected: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
