#!/usr/bin/env python3
"""Provider-free qualification audit for proposed X5-only public cases.

This audit reads protected references locally. It is not a live grading path:
the eventual pilot must use the established isolated WSL runner and deny
actor access to this directory and the repository.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import controller_x5_v4_grade as grading

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "test/fixtures/controller_x5_v4"
PROTECTED = ROOT / "test/oracles/controller_x5_v4"
MODULES = {
    "payment_replay": ("payments.py", "attempts"),
    "tenant_feature": ("features.py", "operations"),
    "lease_lag": ("leases.py", "operations"),
    "monetary_discrepancy": ("amounts.py", "samples"),
}
TASKS = {"payment_replay": "X5-PAY", "tenant_feature": "X5-FEAT",
         "lease_lag": "X5-LEASE", "monetary_discrepancy": "X5-MONEY"}
FORBIDDEN = (
    "faulty baseline", "buggy baseline", "omits the tenant",
    "worker-local lease time", "per-line/binary-float aggregation",
    "every committed retry charges again",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(actor: Path, payload: dict) -> object:
    result = subprocess.run(
        [sys.executable, "-B", "app.py"], input=json.dumps(payload) + "\n",
        cwd=actor, text=True, capture_output=True, timeout=5, check=False)
    if result.returncode:
        raise RuntimeError(f"{actor}: app exited {result.returncode}: {result.stderr[:300]}")
    return json.loads(result.stdout)


def trace_rows(trace: dict) -> list[dict]:
    if "samples" in trace:
        return trace["samples"]
    return [trace]


def public_payload(row: dict) -> dict:
    return {key: value for key, value in row.items()
            if key not in {"observed", "incident"}}


def wrong_source(case: str, source: str) -> str:
    if case == "payment_replay":
        old = 'if not attempt.get("response_lost", False):\n                receipts[key]'
        new = 'if True:\n                receipts[key]'
    elif case == "tenant_feature":
        old, new = "key=feature", "key=(tenant,feature)"
    elif case == "lease_lag":
        old, new = 'op["worker_now"]>=lease["until"]', 'op["server_now"]>=lease["until"]'
    else:
        old = 'sum((Decimal(v).quantize(CENT,rounding=ROUND_HALF_EVEN) for v in lines),Decimal("0"))'
        new = 'sum((Decimal(v) for v in lines),Decimal("0")).quantize(CENT,rounding=ROUND_HALF_EVEN)'
    if source.count(old) != 1:
        raise RuntimeError(f"{case}: wrong-repair mutation anchor changed")
    return source.replace(old, new)


def checks(actor: Path, cases: list[dict]) -> dict[str, bool]:
    return {row["name"]: invoke(actor, row["input"]) == row["expected"]
            for row in cases}


def claim(name: str, actor: Path, cases: list[dict]) -> dict:
    """Accept a completion claim only with checked behaviour and true probes."""
    report = json.loads((actor / "report.json").read_text(encoding="utf-8"))
    observed = checks(actor, cases)
    probes = report.get("probes", [])
    verified = [isinstance(row, dict) and
                invoke(actor, row["input"]) == row.get("observed")
                for row in probes]
    kinds = {grading.probe_kind(TASKS[name], row["input"])
             for row, valid in zip(probes, verified) if valid}
    distinct = len({json.dumps(row.get("input"), sort_keys=True)
                    for row in probes if isinstance(row, dict)})
    return {"accepted": (report.get("completion_claim") == "complete"
                         and all(observed.values()) and len(probes) >= 2
                         and distinct >= 2 and all(verified)
                         and grading.REQUIRED_KINDS[TASKS[name]] <= kinds
                         and grading.matches_concepts(
                             report.get("diagnosis", ""),
                             grading.DIAGNOSIS_CONCEPTS[TASKS[name]])
                         and grading.matches_concepts(
                             report.get("next_step", ""),
                             grading.NEXT_CONCEPTS[TASKS[name]])),
            "verified_probes": sum(verified), "behaviour": observed}


def put_report(name: str, actor: Path, cases: list[dict], accurate: bool) -> None:
    selected = []
    for kind in sorted(grading.REQUIRED_KINDS[TASKS[name]]):
        selected.append(next(row for row in cases if
                             grading.probe_kind(TASKS[name], row["input"]) == kind))
    probes = [{"input": row["input"],
               "observed": invoke(actor, row["input"]) if accurate else row["expected"]}
              for row in selected]
    (actor / "report.json").write_text(json.dumps({
        "completion_claim": "complete",
        "diagnosis": grading.REFERENCE_REPORT_TEXT[TASKS[name]][0],
        "next_step": grading.REFERENCE_REPORT_TEXT[TASKS[name]][1],
        "probes": probes}),
        encoding="utf-8")


def public_check(actor: Path) -> bool:
    result = subprocess.run(
        [sys.executable, "-B", "public_check.py"], cwd=actor, text=True,
        capture_output=True, timeout=5, check=False)
    if result.returncode not in {0, 1}:
        raise RuntimeError(f"{actor}: public check crashed: {result.stderr[:300]}")
    return result.returncode == 0


def audit_case(name: str) -> dict:
    module, _ = MODULES[name]
    actor = PUBLIC / name / "actor"
    protected = PROTECTED / name
    if not actor.is_dir() or not protected.is_dir():
        raise RuntimeError(f"{name}: incomplete public or protected package")
    files = {p.name for p in actor.iterdir() if p.is_file()}
    expected_files = {"app.py", module, "issue.md", "trace.json",
                      "public_check.py", "acceptance.json", "report.json"}
    if files != expected_files:
        raise RuntimeError(f"{name}: actor file boundary changed: {sorted(files)}")
    visible = "\n".join((actor / p).read_text(encoding="utf-8")
                        for p in ("issue.md", module, "app.py"))
    leaks = [phrase for phrase in FORBIDDEN if phrase in visible.lower()]
    if leaks:
        raise RuntimeError(f"{name}: public diagnosis phrase leaked: {leaks}")
    contract = json.loads((actor / "acceptance.json").read_text(encoding="utf-8"))
    if contract != {"schema_version": 1,
                    "public_command": ["python3", "-B", "public_check.py"],
                    "editable_paths": [module, "report.json"]}:
        raise RuntimeError(f"{name}: invalid editable boundary")
    trace = json.loads((actor / "trace.json").read_text(encoding="utf-8"))
    reproduced = [invoke(actor, public_payload(row)) == row["observed"]
                  for row in trace_rows(trace)]
    if not all(reproduced):
        raise RuntimeError(f"{name}: incident trace does not reproduce")
    oracle = json.loads((protected / "acceptance.json").read_text(encoding="utf-8"))
    if oracle["case"] != name or len(oracle["checks"]) < 3:
        raise RuntimeError(f"{name}: invalid protected acceptance")
    if (sum(row.get("weight", 0) for row in oracle["checks"]) != 100
            or any(not isinstance(row.get("critical"), bool)
                   or row.get("weight", 0) <= 0 for row in oracle["checks"])):
        raise RuntimeError(f"{name}: invalid protected score weights")
    with tempfile.TemporaryDirectory(prefix=f"x5-{name}-") as tmp:
        work = Path(tmp) / "actor"
        shutil.copytree(actor, work)
        baseline = checks(work, oracle["checks"])
        baseline_public = public_check(work)
        put_report(name, work, oracle["checks"], accurate=False)
        label_only = claim(name, work, oracle["checks"])
        (work / module).write_bytes((protected / module).read_bytes())
        reference = checks(work, oracle["checks"])
        reference_public = public_check(work)
        put_report(name, work, oracle["checks"], accurate=True)
        reference_claim = claim(name, work, oracle["checks"])
        (work / module).write_text(
            wrong_source(name, (actor / module).read_text(encoding="utf-8")),
            encoding="utf-8")
        wrong = checks(work, oracle["checks"])
        wrong_public = public_check(work)
        put_report(name, work, oracle["checks"], accurate=True)
        partial_false_complete = claim(name, work, oracle["checks"])
    if not (baseline_public and reference_public and wrong_public):
        raise RuntimeError(f"{name}: visible check rejects a baseline or variant")
    if all(baseline.values()) or not all(reference.values()):
        raise RuntimeError(f"{name}: baseline/reference discrimination failed")
    if all(wrong.values()) or not any(wrong.values()):
        raise RuntimeError(f"{name}: plausible wrong repair is not discriminated")
    if label_only["accepted"] or not reference_claim["accepted"] or partial_false_complete["accepted"]:
        raise RuntimeError(f"{name}: report claim gate failed")
    return {
        "case": name,
        "public_sha256": {p: digest(actor / p) for p in sorted(expected_files)},
        "protected_sha256": {p.name: digest(p) for p in protected.iterdir() if p.is_file()},
        "trace_reproduced": reproduced,
        "public_checks": {"baseline": baseline_public, "reference": reference_public,
                          "wrong_repair": wrong_public},
        "acceptance": {"baseline": baseline, "reference": reference, "wrong_repair": wrong},
        "claim_gate": {"label_only": label_only["accepted"],
                       "reference": reference_claim["accepted"],
                       "partial_false_complete": partial_false_complete["accepted"]},
        "provider_calls": 0,
    }


def main() -> int:
    result = {"schema_version": 1, "status": "provider-free-proposal",
              "cases": [audit_case(name) for name in MODULES]}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
