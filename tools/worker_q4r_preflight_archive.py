#!/usr/bin/env python3
"""Preserve Q4R's stopped authentication preflight before a clean campaign.

This one-time reconciliation requires a verified blocked checkpoint and the
absence of the episode workspace, which precedes every provider invocation.
It never invokes Claude Code or deletes campaign evidence.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path

import worker_q4r_screen as plan
import worker_q4r_screen_live as live
from worker_adapter import digest
from worker_wsl_auth import CredentialStore
from worker_wsl_q1 import SEEDS

ARCHIVE = live.RUN.with_name(live.RUN.name + "-preflight-blocked")
EVIDENCE = plan.ROOT / "test/results/2026-09-25-worker-q4r-r1-preflight-reconciliation.json"


def within_repo(path: Path) -> bool:
    return path.resolve().is_relative_to(plan.ROOT.resolve())


def main() -> int:
    if sys.platform != "linux" or os.geteuid() != 0:
        raise RuntimeError("reconciliation requires WSL root")
    manifest = json.loads(plan.MANIFEST.read_text(encoding="utf-8"))
    approval = json.loads(plan.APPROVAL.read_text(encoding="utf-8"))
    plan.validate_approval(manifest, approval)
    campaign_path = live.RUN / "campaign.json"
    campaign = json.loads(campaign_path.read_text(encoding="utf-8"))
    body = {key: value for key, value in campaign.items()
            if key != "state_sha256"}
    workspace = SEEDS / ("q4r-" + manifest["manifest_sha256"][:12] + "-01")
    if (campaign.get("state_sha256") != digest(body)
            or campaign.get("manifest_sha256") != manifest["manifest_sha256"]
            or campaign.get("status") != "blocked"
            or campaign.get("stop_reason") != "uncertain episode"
            or campaign.get("next_sequence") != 1
            or campaign.get("total_provider_calls") != 0
            or campaign.get("total_cost_usd") != 0
            or len(campaign.get("rows", [])) != 1
            or campaign["rows"][0].get("sequence") != 1
            or campaign["rows"][0].get("state") != "uncertain"
            or workspace.exists() or workspace.is_symlink()
            or live.RUN.is_symlink() or ARCHIVE.exists()
            or ARCHIVE.is_symlink() or EVIDENCE.exists()
            or not within_repo(live.RUN) or not within_repo(ARCHIVE)
            or not within_repo(EVIDENCE)):
        raise RuntimeError("Q4R is not the exact pre-dispatch blocked campaign")
    CredentialStore().inspect()
    evidence = {
        "schema_version": 1,
        "recorded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(
            timespec="seconds"),
        "manifest_sha256": manifest["manifest_sha256"],
        "blocked_campaign_sha256": hashlib.sha256(
            campaign_path.read_bytes()).hexdigest(),
        "blocked_state_sha256": campaign["state_sha256"],
        "source_runner_sha256": hashlib.sha256(
            Path(live.__file__).read_bytes()).hexdigest(),
        "first_episode_workspace": str(workspace),
        "first_episode_workspace_exists": False,
        "recorded_provider_calls": 0,
        "recorded_cost_usd": 0,
        "renewed_credential_inspection": "PASS",
        "conclusion": "No actor workspace or provider invocation was created",
        "qualification": "Recorded zero cost does not prove zero external charge",
        "archived_run": str(ARCHIVE.relative_to(plan.ROOT)),
    }
    evidence["evidence_sha256"] = digest(evidence)
    live.RUN.rename(ARCHIVE)
    with EVIDENCE.open("x", encoding="utf-8") as handle:
        json.dump(evidence, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"result": "PASS", "evidence_sha256":
                      evidence["evidence_sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        print(json.dumps({"result": "BLOCKED", "error_type":
                          type(exc).__name__, "detail": str(exc)[:240]}))
        raise SystemExit(2) from None
