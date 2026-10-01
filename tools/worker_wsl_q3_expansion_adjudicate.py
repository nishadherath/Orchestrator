#!/usr/bin/env python3
"""Preserve and verify the actual Q3 public patches after writer stop."""
from __future__ import annotations

import datetime as dt
import difflib
import json
import os
from pathlib import Path

from worker_adapter import digest
from worker_q3_expansion import MANIFEST, ROOT
from worker_q3_public_catalogue import FIXTURES, sha
from worker_wsl_q1 import SEEDS

CAMPAIGN = ROOT / "test/results/2026-09-25-worker-q3-expansion-run/campaign.json"
OUTPUT = ROOT / "test/results/2026-09-25-worker-q3-expansion-adjudication.json"
PATCHES = ROOT / "test/results/2026-09-25-worker-q3-expansion-patches"


def run() -> dict:
    if os.geteuid() != 0 or OUTPUT.exists() or PATCHES.exists():
        raise RuntimeError("WSL root required; adjudication outputs must be new")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    campaign = json.loads(CAMPAIGN.read_text(encoding="utf-8"))
    if (campaign.get("state_sha256") != digest({
            key: value for key, value in campaign.items() if key != "state_sha256"})
            or campaign.get("status") != "complete"
            or campaign.get("manifest_sha256") != manifest["manifest_sha256"]
            or len(campaign.get("rows", [])) != 6):
        raise RuntimeError("Q3 campaign is incomplete or its checkpoint changed")
    PATCHES.mkdir()
    rows = []
    for planned, run_row in zip(manifest["rows"], campaign["rows"], strict=True):
        task_id = planned["task_id"]
        if run_row.get("task_id") != task_id or run_row.get("state") != "graded":
            raise RuntimeError(f"{task_id}: result order differs from manifest")
        episode = run_row["episode"]
        workspace = Path(episode["workspace"])
        if (workspace.is_symlink() or workspace.resolve().parent != SEEDS.resolve()
                or workspace.stat().st_uid != 0 or workspace.stat().st_mode & 0o077):
            raise RuntimeError(f"{task_id}: candidate workspace is unsafe")
        protected = {name: value for name, value in planned["actor_files"].items()
                     if name not in planned["editable_paths"]}
        if episode["protected_sha256"] != protected:
            raise RuntimeError(f"{task_id}: protected receipt differs from manifest")
        hidden = episode["hidden_grade"]
        if (hidden["grade_sha256"] != digest({
                key: value for key, value in hidden.items() if key != "grade_sha256"})
                or hidden["task_sha256"] != planned["task_sha256"]
                or not hidden["source_workspace_unchanged"]):
            raise RuntimeError(f"{task_id}: hidden grade is not bound")
        changed = []
        additions = removals = 0
        patch_lines = []
        for name, original in planned["actor_files"].items():
            path = workspace / name
            if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
                raise RuntimeError(f"{task_id}: candidate file is unsafe: {name}")
            actual = sha(path)
            if name in protected:
                if actual != original:
                    raise RuntimeError(f"{task_id}: protected file changed: {name}")
                continue
            if actual != hidden["candidate_edit_sha256"][name]:
                raise RuntimeError(f"{task_id}: hidden grader saw another revision: {name}")
            if actual == original:
                continue
            changed.append(name)
            before = (FIXTURES / task_id / "actor" / name).read_text(encoding="utf-8")
            after = path.read_text(encoding="utf-8")
            lines = list(difflib.unified_diff(before.splitlines(keepends=True),
                         after.splitlines(keepends=True),
                         fromfile=f"a/{name}", tofile=f"b/{name}"))
            patch_lines.extend(lines)
            additions += sum(line.startswith("+") and not line.startswith("+++")
                             for line in lines)
            removals += sum(line.startswith("-") and not line.startswith("---")
                            for line in lines)
        if sorted(changed) != sorted(episode["attempts"][-1]["changed_paths"]):
            raise RuntimeError(f"{task_id}: collected paths differ from final revision")
        patch_path = PATCHES / f"{task_id}.patch"
        patch_path.write_text("".join(patch_lines), encoding="utf-8", newline="\n")
        rows.append({"task_id": task_id, "changed_paths": changed,
                     "patch_sha256": sha(patch_path), "added_lines": additions,
                     "removed_lines": removals,
                     "root_state": episode["root_state"],
                     "hidden_quality": hidden["quality"],
                     "hidden_acceptance": hidden["hidden_acceptance"],
                     "false_success": hidden["false_success"],
                     "missed_milestones": [item["milestone"] for item in hidden["cases"]
                                           if not item["passed"]],
                     "attempts": len(episode["attempts"]),
                     "api_equivalent_cost_usd": episode["budget"]["spent_usd"],
                     "provider_wall_clock_s": sum(item["wall_clock_s"]
                                                  for item in episode["attempts"]),
                     "served_effort_observable": all(item["served_effort"] is not None
                                                      for item in episode["attempts"])})
    value = {"schema_version": 1, "recorded_at_utc": dt.datetime.now(
                 dt.timezone.utc).isoformat(timespec="seconds"),
             "manifest_sha256": manifest["manifest_sha256"],
             "campaign_state_sha256": campaign["state_sha256"],
             "provider_calls": 0, "provider_cost_usd": 0,
             "rows": rows,
             "total_api_equivalent_cost_usd": campaign["total_cost_usd"],
             "result": "PASS"}
    value["evidence_sha256"] = digest(value)
    OUTPUT.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8", newline="\n")
    return value


if __name__ == "__main__":
    value = run()
    print(value["result"], value["evidence_sha256"])
