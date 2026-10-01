"""Versioned execution inventory for new Controller campaigns.

Archived R5 manifests keep their original bytes and remain audit evidence.
This inventory intentionally includes the entire first-party runtime and its
prompt/configuration tree, rather than trusting a static-import shortlist.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import sys
from pathlib import Path

import controller_evaluation
import evaluation_runner
import route

SOURCE_TREES = {
    "tools": frozenset({".py", ".ps1", ".sh", ".json"}),
    "src": frozenset({".py", ".json", ".md"}),
    "test/harness": frozenset({".py", ".md", ".sha256"}),
    "test/fixtures/controller-routing-v1": frozenset({".json", ".jsonl"}),
    "test/fixtures/controller_x3": frozenset({".py", ".json", ".md", ".h"}),
    "test/oracles/controller_x3": frozenset({".json"}),
}
MARKER = "runtime-package.json"


class CampaignManifestError(ValueError):
    """The runnable source or its frozen inventory has changed."""


def inventory(root: Path) -> dict[str, str]:
    """Reject unsupported inputs and hash every permitted first-party file."""
    root = root.resolve()
    found: dict[str, str] = {}
    for relative, suffixes in SOURCE_TREES.items():
        directory = root / relative
        if directory.is_symlink() or not directory.is_dir():
            raise CampaignManifestError(f"runtime tree missing or redirected: {relative}")
        for path in directory.rglob("*"):
            name = path.relative_to(root).as_posix()
            if "__pycache__" in path.parts:
                continue
            if path.is_symlink():
                raise CampaignManifestError(f"runtime path is redirected: {name}")
            if path.is_dir():
                continue
            if not path.is_file() or path.suffix not in suffixes:
                raise CampaignManifestError(f"unsupported runtime file: {name}")
            found[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    if not found or "tools/controller_campaign_manifest.py" not in found:
        raise CampaignManifestError("runtime inventory is incomplete")
    return dict(sorted(found.items()))


def package_record(root: Path) -> dict:
    files = inventory(root)
    return {"schema_version": 2, "files": files,
            "inventory_sha256": controller_evaluation.digest(files)}


def host_record() -> dict:
    """Record non-secret local runtime facts without claiming live eligibility."""
    executable = Path(sys.executable)
    return {"schema_version": 1, "platform": platform.platform(),
            "python_version": platform.python_version(),
            "python_executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
            "claude_code_version": None, "claude_launcher_sha256": None,
            "effort_override_present": bool(os.environ.get("CLAUDE_CODE_EFFORT_LEVEL")),
            "forced_model_present": bool(os.environ.get("CLAUDE_CODE_SUBAGENT_MODEL_FORCE")),
            "live_eligibility": "unqualified-host-attestation"}


def verify_host(expected: dict, *, require_live: bool) -> None:
    if not isinstance(expected, dict) or expected != host_record():
        raise CampaignManifestError("host version or relevant settings changed")
    if require_live:
        raise CampaignManifestError(
            "X1 has no qualified Claude Code host attestation; live dispatch is closed")


def materialise(source: Path, destination: Path) -> dict:
    """Copy a complete package into a new directory and seal its inventory."""
    source, destination = source.resolve(), destination.resolve()
    if (destination == source or destination.is_relative_to(source)
            or source.is_relative_to(destination) or destination.exists()):
        raise CampaignManifestError("runtime package needs a fresh separate directory")
    record = package_record(source)
    destination.mkdir(parents=True)
    for relative in record["files"]:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / relative, target)
    (destination / MARKER).write_text(json.dumps(record, indent=2, sort_keys=True)
                                      + "\n", encoding="utf-8", newline="\n")
    verify_package(destination, record, require_materialised=True)
    return record


def verify_package(root: Path, expected: dict, *, require_materialised: bool) -> None:
    """Compare the exact file set, every byte and the package marker."""
    if (not isinstance(expected, dict) or expected.get("schema_version") != 2
            or not isinstance(expected.get("files"), dict)
            or expected.get("inventory_sha256") != controller_evaluation.digest(
                expected.get("files"))):
        raise CampaignManifestError("runtime package record is invalid")
    actual = inventory(root)
    if actual != expected["files"]:
        raise CampaignManifestError("runtime package file inventory or content changed")
    if require_materialised:
        marker = root / MARKER
        if marker.is_symlink() or not marker.is_file():
            raise CampaignManifestError("materialised runtime marker is absent")
        try:
            recorded = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise CampaignManifestError("materialised runtime marker is unreadable") from exc
        if recorded != expected:
            raise CampaignManifestError("materialised runtime marker differs")
        allowed = set(expected["files"]) | {MARKER}
        for path in root.rglob("*"):
            if "__pycache__" in path.parts:
                raise CampaignManifestError("materialised runtime contains bytecode cache")
            if path.is_symlink():
                raise CampaignManifestError("materialised runtime has a redirected path")
            if path.is_dir():
                continue
            if path.relative_to(root).as_posix() not in allowed:
                raise CampaignManifestError("materialised runtime has an extra or redirected file")


def upgrade(legacy: dict, root: Path) -> dict:
    """Create a fresh v2 candidate from a schedule, never alter an R5 file."""
    value = dict(legacy)
    value["schema_version"] = 2
    value["runtime_package"] = package_record(root)
    value["host_record"] = host_record()
    value["bound_files"] = value["runtime_package"]["files"]
    value["manifest_sha256"] = controller_evaluation.digest(
        {key: item for key, item in value.items() if key != "manifest_sha256"})
    return value


def _episode_identity(row: dict, kind: str) -> str:
    if kind == "matrix":
        return f"matrix-{row['sequence']:03d}-{row['cell']}-{row['kind']}"
    return f"pilot-{row['sequence']:03d}-{row['task_id'].lower()}-{row['arm'].lower()}"


def _schedule_digest(rows: list[dict], maximum_usd: float) -> str:
    return controller_evaluation.digest({"episodes": rows,
                                         "maximum_authorised_usd": maximum_usd})


def prepare_continuation(predecessor_manifest_path: Path, predecessor_run_root: Path,
                         successor_root: Path, episodes: list[dict], maximum_usd: float,
                         approval: dict, *, kind: str) -> tuple[Path, Path]:
    """Commit one named continuation grant, then write a linked new schedule.

    An approval binds the exact proposed rows and allowance before the grant
    is recorded. The predecessor journal retains the grant, so another caller
    cannot take the same remaining allowance under a different manifest.
    """
    if kind not in {"matrix", "pilot"} or not episodes or type(maximum_usd) not in (int, float):
        raise CampaignManifestError("continuation needs a campaign kind, rows and USD cap")
    predecessor_manifest_path = predecessor_manifest_path.resolve()
    predecessor_run_root = predecessor_run_root.resolve()
    successor_root = successor_root.resolve()
    if (successor_root == predecessor_run_root
            or successor_root.is_relative_to(predecessor_run_root)):
        raise CampaignManifestError("continuation needs a separate output root")
    original = json.loads(predecessor_manifest_path.read_text(encoding="utf-8"))
    if (original.get("schema_version") != 2
            or original.get("stage") != ("matrix-calibration" if kind == "matrix"
                                              else "instrumented-pilot")
            or original.get("manifest_sha256") != controller_evaluation.digest(
                {k: v for k, v in original.items() if k != "manifest_sha256"})):
        raise CampaignManifestError("predecessor manifest is not a sealed v2 campaign")
    from controller_campaign_state import load, reconcile  # local to keep state ownership clear
    predecessor = reconcile(predecessor_run_root, original["manifest_sha256"], kind=kind)
    if (predecessor["status"] not in {"stopped", "cancelled"}
            or predecessor["current"] is not None
            or predecessor["accounting"]["unresolved"]
            or predecessor["accounting"]["reserved_usd"] != 0):
        raise CampaignManifestError("predecessor has an active writer or unresolved charge")
    remaining = {row["sequence"]: row for row in original["episodes"]
                 if _episode_identity(row, kind) not in predecessor["episodes"]}
    if ([row.get("sequence") for row in episodes] != sorted({row.get("sequence") for row in episodes})
            or any(row.get("sequence") not in remaining
                   or {k: v for k, v in row.items() if k != "maximum_usd"}
                   != {k: v for k, v in remaining[row["sequence"]].items()
                       if k != "maximum_usd"}
                   or type(row.get("maximum_usd")) not in (int, float)
                   or not 0 < row["maximum_usd"] <= remaining[row["sequence"]]["maximum_usd"]
                   for row in episodes)):
        raise CampaignManifestError("continuation changes or replays a predecessor row")
    inherited = original.get("continuation", {}).get("inherited_spend_usd", 0.0)
    consumed = round(inherited + predecessor["known_spend_usd"], 9)
    root_limit = original.get("continuation", {}).get(
        "root_limit_usd", original["maximum_authorised_usd"])
    if (maximum_usd <= 0 or maximum_usd > root_limit - consumed + 1e-9
            or sum(row["maximum_usd"] for row in episodes) > maximum_usd + 1e-9):
        raise CampaignManifestError("continuation exceeds the inherited root allowance")
    schedule = _schedule_digest(episodes, maximum_usd)
    if (not isinstance(approval, dict) or approval.get("decision") != "approved"
            or approval.get("schedule_sha256") != schedule
            or approval.get("maximum_authorised_usd") != maximum_usd
            or not all(isinstance(approval.get(key), str) and approval[key].strip()
                       for key in ("authority_id", "approved_by", "approved_at"))):
        raise CampaignManifestError("exact continuation authority is absent")
    authority_digest = controller_evaluation.digest(approval)
    grant = {"authority_id": approval["authority_id"],
             "authority_sha256": authority_digest, "schedule_sha256": schedule,
             "successor_run_root": str(successor_root / "run")}
    path = predecessor_run_root / "state.json"
    with route.ledger_lock(path):
        current = load(path)
        if current["state_sha256"] != predecessor["state_sha256"]:
            raise CampaignManifestError("predecessor changed during continuation approval")
        grants = current.setdefault("continuations", [])
        if grants and grants != [grant]:
            raise CampaignManifestError("predecessor allowance is already assigned")
        if not grants:
            if successor_root.exists():
                raise CampaignManifestError("ungranted successor output root already exists")
            grants.append(grant)
            # save obtains the same OS lock, so write directly while holding it.
            current["state_sha256"] = controller_evaluation.digest(
                {k: v for k, v in current.items() if k != "state_sha256"})
            evaluation_runner.atomic_json(path, current)
    fresh = dict(original)
    fresh["episodes"] = episodes
    fresh["maximum_authorised_usd"] = maximum_usd
    fresh["continuation"] = {
        "predecessor_manifest_path": str(predecessor_manifest_path),
        "predecessor_manifest_sha256": original["manifest_sha256"],
        "predecessor_run_root": str(predecessor_run_root),
        "predecessor_state_sha256": current["state_sha256"],
        "successor_run_root": str(successor_root / "run"),
        "authority_id": approval["authority_id"],
        "authority_sha256": authority_digest,
        "schedule_sha256": schedule,
        "root_limit_usd": root_limit,
        "inherited_spend_usd": consumed,
    }
    fresh["manifest_sha256"] = controller_evaluation.digest(
        {k: v for k, v in fresh.items() if k != "manifest_sha256"})
    authorisation = {"schema_version": 1, "decision": "approved",
                     "manifest_sha256": fresh["manifest_sha256"],
                     "maximum_authorised_usd": maximum_usd,
                     "approved_at": approval["approved_at"],
                     "approved_by": approval["approved_by"],
                     "authority_id": approval["authority_id"],
                     "authority_sha256": authority_digest}
    manifest_path, auth_path = successor_root / "manifest.json", successor_root / "authorisation.json"
    # A crash after the predecessor grant can leave zero, one or both files.
    # Retry only that same grant and never overwrite a differing file or a
    # started run. This preserves the single allowance without erasing evidence.
    if successor_root.exists():
        if (successor_root.is_symlink() or not successor_root.is_dir()
                or {p.name for p in successor_root.iterdir()}
                - {manifest_path.name, auth_path.name}):
            raise CampaignManifestError("successor contains unrecognised or started work")
        for target, expected in ((manifest_path, fresh), (auth_path, authorisation)):
            if target.exists():
                if target.is_symlink() or json.loads(target.read_text(encoding="utf-8")) != expected:
                    raise CampaignManifestError("existing successor file differs from grant")
    else:
        successor_root.mkdir(parents=True)
    evaluation_runner.atomic_json(manifest_path, fresh)
    evaluation_runner.atomic_json(auth_path, authorisation)
    return manifest_path, auth_path


def verify_continuation(value: dict, run_root: Path | None = None) -> None:
    """Recheck the predecessor grant and shared money before each admission."""
    link = value.get("continuation")
    if link is None:
        return
    if (not isinstance(link, dict)
            or run_root is not None
            and Path(link.get("successor_run_root", "")).resolve() != run_root.resolve()
            or link.get("schedule_sha256") != _schedule_digest(
                value["episodes"], value["maximum_authorised_usd"])):
        raise CampaignManifestError("continuation schedule or output root changed")
    original_path = Path(link["predecessor_manifest_path"])
    predecessor_root = Path(link["predecessor_run_root"])
    if original_path.is_symlink() or predecessor_root.is_symlink():
        raise CampaignManifestError("continuation predecessor path is redirected")
    original = json.loads(original_path.read_text(encoding="utf-8"))
    if (original.get("manifest_sha256") != link.get("predecessor_manifest_sha256")
            or original.get("manifest_sha256") != controller_evaluation.digest(
                {k: v for k, v in original.items() if k != "manifest_sha256"})):
        raise CampaignManifestError("continuation predecessor manifest changed")
    from controller_campaign_state import reconcile
    kind = "matrix" if value["stage"] == "matrix-calibration" else "pilot"
    state = reconcile(predecessor_root, original["manifest_sha256"], kind=kind)
    grant = {"authority_id": link["authority_id"],
             "authority_sha256": link["authority_sha256"],
             "schedule_sha256": link["schedule_sha256"],
             "successor_run_root": link["successor_run_root"]}
    if (state["state_sha256"] != link.get("predecessor_state_sha256")
            or state.get("continuations") != [grant]
            or state["current"] is not None or state["accounting"]["unresolved"]
            or state["accounting"]["reserved_usd"] != 0):
        raise CampaignManifestError("continuation predecessor is unsettled or grant changed")
    consumed = round(original.get("continuation", {}).get("inherited_spend_usd", 0.0)
                     + state["known_spend_usd"], 9)
    root_limit = original.get("continuation", {}).get(
        "root_limit_usd", original["maximum_authorised_usd"])
    if (link.get("inherited_spend_usd") != consumed
            or link.get("root_limit_usd") != root_limit
            or value["maximum_authorised_usd"] > root_limit - consumed + 1e-9):
        raise CampaignManifestError("continuation exceeds the shared root allowance")
    remaining = {row["sequence"]: row for row in original["episodes"]
                 if _episode_identity(row, kind) not in state["episodes"]}
    for row in value["episodes"]:
        prior = remaining.get(row["sequence"])
        if (prior is None
                or {k: v for k, v in row.items() if k != "maximum_usd"}
                != {k: v for k, v in prior.items() if k != "maximum_usd"}
                or row["maximum_usd"] > prior["maximum_usd"]):
            raise CampaignManifestError("continuation replays or changes a predecessor row")
