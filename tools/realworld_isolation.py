#!/usr/bin/env python3
"""Prove an actor/evaluator file boundary inside the host's WSL2 VM."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = ROOT / "test" / "results" / "2026-09-17-realworld-isolation.json"

def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def run_probe() -> dict:
    if os.name != "nt":
        raise RuntimeError("this probe requires a Windows host with WSL2")
    base = f"/tmp/orchestrator-isolation-{uuid.uuid4().hex}"

    def call(user: str, *command: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["wsl.exe", "-u", user, "--", *command],
            capture_output=True,
            timeout=20,
        )

    setup = (
        "from pathlib import Path; import os; "
        f"base=Path({base!r}); actor=base/'actor'; evaluator=base/'evaluator'; "
        "actor.mkdir(parents=True); evaluator.mkdir(); "
        "(actor/'input.txt').write_text('actor-input\\n'); "
        "(evaluator/'oracle.txt').write_text('hidden-oracle\\n'); "
        "os.chmod(base,0o755); os.chmod(evaluator,0o700); "
        "os.chown(actor,65534,65534); os.chown(actor/'input.txt',65534,65534)"
    )
    try:
        created = call("root", "python3", "-c", setup)
        if created.returncode != 0:
            raise RuntimeError(created.stderr.decode("utf-8", errors="replace")[-600:])
        denied = call("root", "runuser", "-u", "nobody", "--", "cat", f"{base}/evaluator/oracle.txt")
        actor = call(
            "root", "runuser", "-u", "nobody", "--", "python3", "-c",
            f"from pathlib import Path; p=Path({base!r})/'actor'; "
            "assert (p/'input.txt').read_text() == 'actor-input\\n'; "
            "(p/'output.txt').write_text('actor-output\\n')",
        )
        if actor.returncode != 0:
            raise RuntimeError(actor.stderr.decode("utf-8", errors="replace")[-600:])
        root_value = call("root", "cat", f"{base}/actor/output.txt")
        mode = call("root", "stat", "-c", "%a", f"{base}/evaluator")
        checks = {
            "actor_oracle_read": "denied" if denied.returncode != 0 else "allowed",
            "actor_workspace": "read_write",
            "evaluator_actor_read": root_value.stdout.decode("utf-8", errors="replace").strip(),
            "evaluator_mode": mode.stdout.decode("utf-8", errors="replace").strip(),
        }
    finally:
        call("root", "rm", "-rf", base)
    passed = checks == {
        "actor_oracle_read": "denied",
        "actor_workspace": "read_write",
        "evaluator_actor_read": "actor-output",
        "evaluator_mode": "700",
    }
    evidence = {
        "schema_version": 1,
        "recorded_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "host": platform.node(),
        "boundary": "WSL2 Linux user and mode separation",
        "actor_identity": "nobody",
        "evaluator_identity": "root",
        "checks": checks,
        "result": "PASS" if passed else "FAIL",
        "limits": [
            "This proves the local filesystem boundary mechanism, not model transport or full episode execution.",
            "Every campaign host must run a fresh probe before paid execution.",
        ],
    }
    evidence["evidence_sha256"] = hashlib.sha256(canonical(evidence)).hexdigest()
    return evidence


def validate(path: Path) -> tuple[bool, str]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"cannot read isolation evidence: {exc}"
    digest = value.pop("evidence_sha256", None)
    expected = hashlib.sha256(canonical(value)).hexdigest()
    checks = value.get("checks") or {}
    ok = (
        digest == expected
        and value.get("result") == "PASS"
        and checks.get("actor_oracle_read") == "denied"
        and checks.get("actor_workspace") == "read_write"
        and checks.get("evaluator_actor_read") == "actor-output"
        and checks.get("evaluator_mode") == "700"
    )
    return ok, f"boundary={value.get('boundary')}; digest={'valid' if digest == expected else 'invalid'}"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if args.check:
        ok, detail = validate(output)
        print(f"{'PASS' if ok else 'FAIL'}: {detail}")
        return 0 if ok else 1
    try:
        evidence = run_probe()
    except RuntimeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"{evidence['result']}: wrote {output.relative_to(ROOT)}")
    return 0 if evidence["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
