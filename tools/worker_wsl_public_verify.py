#!/usr/bin/env python3
"""Run a stopped actor's public check in a fresh, credential-free WSL copy.

Only four public files enter this namespace. The candidate executes as UID
65534, without Windows mounts, sibling actors, the hidden evaluator or the
Claude subscription credential. The original actor is never executed here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import resource
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from worker_wsl_materialize import ACTORS, NAME, PUBLIC, stage

EVALUATOR = Path("/var/lib/orchestrator-worker-n4/evaluator")
LAUNCHER = "/opt/orchestrator-worker-runtime/bin/worker-wsl-namespace"
MAX_OUTPUT_BYTES = 65_536
MAX_TIMEOUT_SECONDS = 120
HEX = re.compile(r"[0-9a-f]{64}\Z")


class PublicVerifyError(RuntimeError):
    """The public check could not be run inside its required boundary."""


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cap_output() -> None:
    resource.setrlimit(resource.RLIMIT_FSIZE,
                       (MAX_OUTPUT_BYTES, MAX_OUTPUT_BYTES))


def verify(actor_name: str, expected: dict[str, str], timeout_s: int) -> dict:
    if os.geteuid() != 0 or not NAME.fullmatch(actor_name):
        raise PublicVerifyError("root identity and opaque actor name required")
    if (type(timeout_s) is not int or not 1 <= timeout_s <= MAX_TIMEOUT_SECONDS
            or not isinstance(expected, dict) or set(expected) != set(PUBLIC)
            or any(not isinstance(value, str) or not HEX.fullmatch(value)
                   for value in expected.values())):
        raise PublicVerifyError("public file hashes or timeout are invalid")
    if (ACTORS.is_symlink() or not ACTORS.is_dir() or ACTORS.stat().st_uid != 0
            or EVALUATOR.is_symlink() or not EVALUATOR.is_dir()
            or EVALUATOR.stat().st_uid != 0 or EVALUATOR.stat().st_mode & 0o077):
        raise PublicVerifyError("root-owned actor or evaluator boundary unavailable")
    actor = ACTORS / actor_name
    if actor.is_symlink() or not actor.is_dir() or actor.stat().st_uid != 0:
        raise PublicVerifyError("actor directory is missing or redirected")
    if any((actor / name).is_symlink() or not (actor / name).is_file()
           or _hash(actor / name) != expected[name] for name in PUBLIC):
        raise PublicVerifyError("actor public files differ from stopped writer")

    copy = stage(actor, "inv-" + uuid.uuid4().hex)
    fresh = Path(copy["actor_root"])
    if copy["public_sha256"] != expected:
        raise PublicVerifyError("fresh verifier copy differs from stopped actor")
    with (tempfile.TemporaryFile(dir=EVALUATOR) as stdout,
          tempfile.TemporaryFile(dir=EVALUATOR) as stderr):
        try:
            process = subprocess.run(
                [LAUNCHER, str(fresh), "--", "/usr/bin/python3", "public_check.py"],
                stdout=stdout, stderr=stderr, timeout=timeout_s,
                preexec_fn=_cap_output,
            )
        except subprocess.TimeoutExpired as exc:
            raise PublicVerifyError("public check timed out; writer stop needs review") from exc
        if stdout.tell() >= MAX_OUTPUT_BYTES or stderr.tell() >= MAX_OUTPUT_BYTES:
            raise PublicVerifyError("public check exceeded output limit")
        stdout.seek(0)
        stderr.seek(0)
        output = stdout.read().decode("utf-8", errors="replace")
        errors = stderr.read().decode("utf-8", errors="replace")
    if (any(_hash(fresh / name) != expected[name] for name in PUBLIC)
            or any(_hash(actor / name) != expected[name] for name in PUBLIC)):
        raise PublicVerifyError("public check changed its fresh copy or source")
    return {"schema_version": 1, "exit_code": process.returncode,
            "stdout": output, "stderr": errors,
            "actor_app_sha256": expected["app.py"],
            "public_sha256": expected,
            "boundary": "fresh WSL mount+PID namespace, uid 65534, no credentials"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actor-name", required=True)
    parser.add_argument("--public-hashes-json", required=True)
    parser.add_argument("--timeout-s", type=int, required=True)
    args = parser.parse_args()
    try:
        expected = json.loads(args.public_hashes_json)
        result = verify(args.actor_name, expected, args.timeout_s)
    except (OSError, ValueError, PublicVerifyError) as exc:
        print(f"public verifier blocked: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
