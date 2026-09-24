#!/usr/bin/env python3
"""Freeze and inspect the N5 worker-cell screen; never dispatch a paid call.

The screen has one identity call and three distinct microtasks for each of the
fifteen registry cells. This module freezes its inputs and validates an exact
spend authorisation. Live dispatch is deliberately absent until credential
delivery, durable accounting and the final launch path are qualified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import model_registry
import worker_evaluation
import worker_wsl_attestation
from worker_adapter import digest

ROOT = Path(__file__).resolve().parent.parent
SCREEN = ROOT / "test" / "fixtures" / "worker_n5_screen"
CORPUS = ROOT / "test" / "fixtures" / "worker_n4"
PUBLIC = {"app.py", "public_check.py", "ISSUE.md", "acceptance.json"}
MICROTASKS = ("S01", "S02", "S03")
IDENTITY = "I00"
SCREEN_CEILING_USD = 48.75
HEX_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class ScreenError(RuntimeError):
    """A screen input, manifest or approval does not meet the frozen contract."""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_fixtures(screen: Path = SCREEN) -> dict[str, str]:
    """Validate public actor packages and evaluator-only oracle inventory."""
    if screen.is_symlink() or not screen.is_dir():
        raise ScreenError("screen fixture root must be a real directory")
    files = worker_evaluation._files(screen)
    try:
        catalogue = json.loads((screen / "catalogue.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScreenError("screen catalogue is missing or invalid") from exc
    if catalogue != {"schema_version": 1, "identity": IDENTITY,
                     "microtasks": list(MICROTASKS), "allowed_edits": ["app.py"]}:
        raise ScreenError("screen catalogue differs from the fixed N5 inventory")
    if any((screen / name).stat().st_size > 1_000_000 for name in files):
        raise ScreenError("screen file exceeds the WSL materializer or grader limit")
    required = {"catalogue.json"}
    for ident in (IDENTITY, *MICROTASKS):
        required.update(f"{ident}/{name}" for name in PUBLIC)
        actor = screen / ident
        if actor.is_symlink() or not actor.is_dir():
            raise ScreenError(f"public actor package is missing: {ident}")
        acceptance = json.loads((actor / "acceptance.json").read_text(encoding="utf-8"))
        if (acceptance.get("version") != 1 or acceptance.get("kind") != "command"
                or acceptance.get("command") != ["python3", "public_check.py"]
                or acceptance.get("required_outputs") != ["app.py"]
                or set(acceptance.get("protected_paths", [])) !=
                {"public_check.py", "ISSUE.md", "acceptance.json"}):
            raise ScreenError(f"acceptance contract is invalid: {ident}")
        issue = (actor / "ISSUE.md").read_text(encoding="utf-8").lower()
        if any(word in issue for word in ("oracle", "hidden grader", "reference patch")):
            raise ScreenError(f"actor issue discloses evaluator details: {ident}")
        if ident == IDENTITY and "do not edit" not in issue:
            raise ScreenError("identity issue must prohibit edits")
    for ident in MICROTASKS:
        required.add(f"oracles/{ident}.json")
        oracle = json.loads((screen / "oracles" / f"{ident}.json").read_text(
            encoding="utf-8"))
        if (oracle.get("schema_version") != 1 or not isinstance(oracle.get("cases"), list)
                or not oracle["cases"]):
            raise ScreenError(f"oracle contract is invalid: {ident}")
        if (set(oracle) - {"schema_version", "cases", "no_edit_baseline_sha256"}
                or any(not isinstance(case, dict) or
                       set(case) != {"input", "expected", "weight", "milestone", "critical"}
                       or type(case["weight"]) is not int or case["weight"] <= 0
                       or type(case["critical"]) is not bool
                       or not isinstance(case["milestone"], str) or not case["milestone"]
                       for case in oracle["cases"])):
            raise ScreenError(f"oracle case contract is invalid: {ident}")
        if ident != "S03" and "no_edit_baseline_sha256" in oracle:
            raise ScreenError(f"unexpected no-edit baseline: {ident}")
    if set(files) != required:
        raise ScreenError("screen files differ from the fixed public/oracle inventory")
    baseline = json.loads((screen / "oracles" / "S03.json").read_text(
        encoding="utf-8")).get("no_edit_baseline_sha256")
    if baseline != sha(screen / "S03" / "app.py"):
        raise ScreenError("S03 no-edit baseline does not match app.py")
    return files


def build_manifest(*, credential_method: str = "unconfigured",
                   host_attestation_sha256: str,
                   spend_notice_sha256: str | None = None,
                   screen: Path = SCREEN) -> dict:
    """Build a deterministic manifest; its default cannot authorise spending."""
    if credential_method not in {"unconfigured", "api_key", "subscription"}:
        raise ScreenError("credential method is not a recognised N5 option")
    if not HEX_DIGEST.fullmatch(host_attestation_sha256):
        raise ScreenError("a current host-attestation digest is required")
    if spend_notice_sha256 is not None and not HEX_DIGEST.fullmatch(spend_notice_sha256):
        raise ScreenError("spend notice digest must be SHA-256")
    files = validate_fixtures(screen)
    registry = model_registry.load()
    cells = [f"worker-{model}-{effort}" for model in registry["model_order"]
             for effort in registry["effort_order"]]
    if len(cells) != 15 or set(cells) != set(registry["cells"]):
        raise ScreenError("registry does not contain the fixed fifteen-cell screen")
    rows = []
    for cell in cells:
        for kind, task, cap in (("identity", IDENTITY, 0.25),
                                *(("microtask", ident, 1.0) for ident in MICROTASKS)):
            rows.append({"sequence": len(rows) + 1, "cell": cell, "kind": kind,
                         "task": task, "maximum_usd": cap,
                         "timeout_seconds": 300 if kind == "identity" else 900})
    value = {"schema_version": 1, "profile": "worker-n5-cell-screen",
             "credential_method": credential_method,
             "spend_notice_sha256": spend_notice_sha256,
             "host_attestation_sha256": host_attestation_sha256,
             "n4_manifest_sha256": worker_evaluation.freeze(CORPUS)["manifest_sha256"],
             "registry_id": registry["registry_id"],
             "screen_files": files,
             "screen_source_sha256": sha(ROOT / "tools" / "worker_n5_screen.py"),
             "runner_source_sha256": sha(ROOT / "tools" / "worker_n5_live_screen.py"),
             "rows": rows,
             "cost": {"currency": "USD", "identity_calls": 15,
                      "microtask_calls": 45, "maximum_usd": SCREEN_CEILING_USD,
                      "basis": "15 x USD 0.25 plus 45 x USD 1 local allocations"},
             "retry_policy": "no-automatic-provider-replay",
             "reserved_tasks_allowed": False,
             "authorisation": "separate-exact-approval-required"}
    if round(sum(row["maximum_usd"] for row in rows), 2) != SCREEN_CEILING_USD:
        raise ScreenError("screen rows exceed the declared ceiling")
    return {**value, "manifest_sha256": digest(value)}


def validate_manifest(manifest: dict, *, screen: Path = SCREEN,
                      check_host: bool = False) -> None:
    """Re-derive all frozen inputs and optionally check the actual WSL host."""
    if not isinstance(manifest, dict):
        raise ScreenError("screen manifest must be an object")
    expected = build_manifest(
        credential_method=manifest.get("credential_method", ""),
        host_attestation_sha256=manifest.get("host_attestation_sha256", ""),
        spend_notice_sha256=manifest.get("spend_notice_sha256"), screen=screen)
    if manifest != expected:
        raise ScreenError("screen manifest or frozen inputs changed")
    if check_host:
        evidence = json.loads(worker_wsl_attestation.OUTPUT.read_text(encoding="utf-8"))
        if (not worker_wsl_attestation.validate(evidence, check_host=True)
                or evidence["evidence_sha256"] != manifest["host_attestation_sha256"]):
            raise ScreenError("WSL host attestation is stale or differs from the screen")


def validate_authorisation(manifest: dict, approval: dict, *,
                           screen: Path = SCREEN, check_host: bool = True) -> None:
    """Require an exact approval for this host, notice, credential and cap."""
    validate_manifest(manifest, screen=screen, check_host=check_host)
    if manifest["credential_method"] == "unconfigured" or (
            not manifest["spend_notice_sha256"]):
        raise ScreenError("credential method and spend notice must be frozen first")
    if (not isinstance(approval, dict) or set(approval) != {
            "schema_version", "decision", "manifest_sha256", "maximum_authorised_usd",
            "credential_method", "spend_notice_sha256", "approved_by", "approved_at"}
            or approval["schema_version"] != 1 or approval["decision"] != "approved"
            or approval["manifest_sha256"] != manifest["manifest_sha256"]
            or type(approval["maximum_authorised_usd"]) not in (int, float)
            or approval["maximum_authorised_usd"] != SCREEN_CEILING_USD
            or approval["credential_method"] != manifest["credential_method"]
            or approval["spend_notice_sha256"] != manifest["spend_notice_sha256"]
            or not isinstance(approval["approved_by"], str)
            or not approval["approved_by"].strip()
            or not isinstance(approval["approved_at"], str)
            or not approval["approved_at"].strip()):
        raise ScreenError("approval must exactly match the screen manifest and USD ceiling")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--credential-method", choices=("unconfigured", "api_key",
                                                       "subscription"), default="unconfigured")
    parser.add_argument("--spend-notice", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    evidence = json.loads(worker_wsl_attestation.OUTPUT.read_text(encoding="utf-8"))
    if not worker_wsl_attestation.validate(evidence, check_host=True):
        raise ScreenError("current WSL host attestation is required before screen planning")
    notice = sha(args.spend_notice) if args.spend_notice else None
    manifest = build_manifest(credential_method=args.credential_method,
                              host_attestation_sha256=evidence["evidence_sha256"],
                              spend_notice_sha256=notice)
    if args.json:
        print(json.dumps(manifest, indent=2, sort_keys=True))
    else:
        print(f"N5 screen: {len(manifest['rows'])} fixed calls, "
              f"USD {SCREEN_CEILING_USD:.2f} local allocation ceiling; "
              f"manifest {manifest['manifest_sha256'][:12]}; paid launch disabled")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
