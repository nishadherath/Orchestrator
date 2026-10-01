#!/usr/bin/env python3
"""Provider-free evidence that the isolated WSL actor sees subscription auth.

No credential value, credential digest, email or account identifier is stored.
The private master may rotate after this check without invalidating the host
contract. A live worker still needs the normal manifest-bound spend gate.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import uuid
from pathlib import Path

import worker_wsl_attestation as host

ROOT = host.ROOT
OUTPUT = ROOT / "test" / "results" / "2026-09-25-worker-n5-subscription-host.json"
AUTH = str(host.RUNTIME / "worker_wsl_auth.py")
MATERIALIZE = str(host.RUNTIME / "worker_wsl_materialize.py")
LAUNCHER = str(host.RUNTIME / "bin" / "worker-wsl-namespace")
CLAUDE = str(host.RUNTIME / "bin" / "claude")
SETTINGS = ROOT / "tools" / "worker_wsl_restricted_settings.json"
SOURCE = ROOT / "tools" / "worker_wsl_subscription_attestation.py"
REQUIRED = {"host_current", "master_private", "isolated_claude_login",
            "subscription_reported", "auth_session_reconciled",
            "default_actor_master_denied", "restricted_file_tools",
            "credential_read_denied_by_settings"}


class SubscriptionAttestationError(RuntimeError):
    """Subscription delivery could not be qualified without a model call."""


def _host() -> dict:
    try:
        evidence = json.loads(host.OUTPUT.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SubscriptionAttestationError("N4 host evidence unavailable") from exc
    if not host.validate(evidence, check_host=True):
        raise SubscriptionAttestationError("N4 host evidence is stale")
    return evidence


def _inspect() -> None:
    host.checked("python3", AUTH, "inspect")


def validate(value: dict, *, check_host: bool) -> bool:
    if not isinstance(value, dict):
        return False
    body = {key: item for key, item in value.items() if key != "evidence_sha256"}
    if value.get("evidence_sha256") != hashlib.sha256(host.canonical(body)).hexdigest():
        return False
    if (value.get("schema_version") != 1 or value.get("result") != "PASS"
            or value.get("source_sha256") != host.sha(SOURCE)
            or set(value.get("checks", {})) != REQUIRED
            or not all(item is True for item in value["checks"].values())):
        return False
    if check_host:
        try:
            current = _host()
            _inspect()
        except (OSError, ValueError, host.AttestationError,
                SubscriptionAttestationError):
            return False
        if value.get("host_attestation_sha256") != current["evidence_sha256"]:
            return False
    return True


def run() -> dict:
    current = _host()
    _inspect()
    name = "inv-" + uuid.uuid4().hex
    with host.temporary_actor("worker-n5-subscription-") as source:
        (source / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (source / "public_check.py").write_text("assert True\n", encoding="utf-8")
        (source / "ISSUE.md").write_text("Check local login status.\n", encoding="utf-8")
        (source / "acceptance.json").write_text('{"schema_version":1}\n',
                                                 encoding="utf-8")
        linux_source = host.checked("wslpath", "-a", source.as_posix())
        staged = json.loads(host.checked("python3", MATERIALIZE, "--source",
                                         linux_source, "--name", name))
        actor = staged["actor_root"]
        if actor != host.ACTOR_BASE + name:
            raise SubscriptionAttestationError("materializer changed actor scope")
        process = host.wsl(LAUNCHER, "--subscription", actor, "--", CLAUDE,
                           "--restricted", "auth", "status", "--json", timeout=45)
        if process.returncode:
            raise SubscriptionAttestationError("isolated Claude auth status failed")
        try:
            status = json.loads(process.stdout)
        except (TypeError, ValueError) as exc:
            raise SubscriptionAttestationError("Claude auth status was not JSON") from exc
    _inspect()
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    denies = set(settings.get("permissions", {}).get("deny", []))
    checks = {
        "host_current": True,
        "master_private": True,
        "isolated_claude_login": status.get("loggedIn") is True
        and status.get("authMethod") == "claude.ai",
        "subscription_reported": status.get("subscriptionType") in
        {"pro", "max", "team", "enterprise"},
        "auth_session_reconciled": True,
        "default_actor_master_denied":
            current["checks"].get("auth_master_denied") is True,
        "restricted_file_tools":
            current["checks"].get("claude_only_expected_tools") is True
            and current["checks"].get("claude_no_execution_tools") is True,
        "credential_read_denied_by_settings":
            {"Read(//run/claude-auth/**)", "Edit(//run/claude-auth/**)"} <= denies,
    }
    evidence = {
        "schema_version": 1,
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "host_attestation_sha256": current["evidence_sha256"],
        "source_sha256": host.sha(SOURCE),
        "checks": checks,
        "result": "PASS" if all(checks.values()) else "FAIL",
        "limits": ["No model request or charged worker call was made.",
                   "Built-in Read denial needs a bounded live sentinel before N5 dispatch."],
    }
    evidence["evidence_sha256"] = hashlib.sha256(host.canonical(evidence)).hexdigest()
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            result = validate(json.loads(OUTPUT.read_text(encoding="utf-8")),
                              check_host=True)
            print("PASS: subscription host evidence current" if result else
                  "FAIL: subscription host evidence stale")
            return 0 if result else 1
        evidence = run()
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8", newline="\n")
        print(f"{evidence['result']}: {len(evidence['checks'])} subscription checks")
        return 0 if evidence["result"] == "PASS" else 1
    except (OSError, ValueError, KeyError, host.AttestationError,
            SubscriptionAttestationError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
