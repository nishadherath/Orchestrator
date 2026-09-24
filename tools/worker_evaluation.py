#!/usr/bin/env python3
"""Frozen worker-only campaign preparation and provider-free rehearsal (N4).

The campaign owns episode order and independent grading, not task execution.
TaskExecutor remains the only root scheduler and budget owner. This module
deliberately has no live-launch entry point until actor isolation is attested
and the paid N5 manifest and authorisation are frozen.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import model_registry
import route
import worker_selector
from task_executor import TaskExecutor
from worker_adapter import digest

ROOT = Path(__file__).resolve().parent.parent
BOUND_SOURCE = (
    "tools/worker_evaluation.py", "tools/worker_corpus.py",
    "tools/worker_oracles.py", "tools/worker_statistics.py",
    "tools/task_executor.py",
    "tools/worker_selector.py", "tools/worker_adapter.py",
    "tools/managed_delegation.py", "tools/dispatch_budget.py",
    "tools/acceptance.py", "tools/route.py", "tools/model_registry.py",
    "src/model_registry.json", "src/cost_table.json",
    "src/ORCHESTRATOR_CORE.md", "src/ROUTING.md", "src/LIFECYCLE.md",
    "dist/bundle-manifest.json", ".mcp.json", ".claude/settings.json",
    "AGENTS.md", "CLAUDE.md", "docs/WORKER-EXECUTION-CONTRACT-v2.md",
)
FAMILIES = {"configuration", "resilience", "integrity", "concurrency",
            "protocol", "diagnosis"}


class CampaignError(RuntimeError):
    """A campaign cannot proceed without frozen inputs or safe recovery."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _inside(root: Path, name: str, *, file: bool = False) -> Path:
    if not isinstance(name, str) or not name or Path(name).is_absolute() or "\\" in name:
        raise CampaignError("catalogue paths must be non-empty relative POSIX paths")
    path = root / name
    if ".." in Path(name).parts or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise CampaignError(f"unsafe catalogue path: {name}")
    if file and not path.is_file():
        raise CampaignError(f"missing catalogue file: {name}")
    return path


def _files(root: Path) -> dict[str, str]:
    if not root.is_dir() or root.is_symlink():
        raise CampaignError(f"corpus root is missing or a symlink: {root}")
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise CampaignError(f"symlink is forbidden in a corpus: {path}")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = sha256(path)
    return result


def load_catalogue(corpus: Path, *, miniature: bool = False) -> dict:
    path = corpus / "catalogue.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CampaignError(f"invalid corpus catalogue: {exc}") from exc
    if not isinstance(value, dict) or set(value) != {"schema_version", "tasks"} or value["schema_version"] != 1:
        raise CampaignError("corpus catalogue needs schema_version 1 and tasks")
    tasks = value["tasks"]
    if not isinstance(tasks, list) or len(tasks) != (2 if miniature else 24):
        raise CampaignError("corpus must contain exactly 24 tasks, or two in a miniature")
    seen: set[str] = set()
    counts: dict[tuple[str, str], int] = {}
    for task in tasks:
        keys = {"id", "family", "split", "actor", "issue", "acceptance",
                "oracle", "allowed_edits", "assessment"}
        if not isinstance(task, dict) or set(task) != keys:
            raise CampaignError("task fields must match the catalogue schema")
        ident = task["id"]
        if not isinstance(ident, str) or not ident.isidentifier() or ident in seen:
            raise CampaignError("task ids must be unique safe identifiers")
        seen.add(ident)
        family, split = task["family"], task["split"]
        if family not in FAMILIES or split not in {"development", "reserved"}:
            raise CampaignError("invalid task family or split")
        counts[(family, split)] = counts.get((family, split), 0) + 1
        actor = _inside(corpus, task["actor"])
        if not actor.is_dir():
            raise CampaignError(f"actor package missing: {ident}")
        _files(actor)
        for key in ("issue", "acceptance", "oracle"):
            _inside(corpus, task[key], file=True)
        if not isinstance(task["allowed_edits"], list) or not task["allowed_edits"]:
            raise CampaignError("each task needs a bounded edit scope")
        for name in task["allowed_edits"]:
            if not _inside(actor, name).parent.is_relative_to(actor):
                raise CampaignError("edit scope escapes actor")
        worker_selector.assess(task["assessment"])
        # The issue cannot disclose its holdout status, label or evaluator path.
        issue = _inside(corpus, task["issue"]).read_text(encoding="utf-8")
        if any(token in issue.lower() for token in
               ("reserved", "hidden grader", "reference patch", "corpus family")):
            raise CampaignError(f"issue leaks evaluator labels: {ident}")
    if not miniature and (set(counts) != {(family, split) for family in FAMILIES
                                       for split in ("development", "reserved")}
                          or any(count != 2 for count in counts.values())):
        raise CampaignError("need two tasks per family and split")
    return value


def freeze(corpus: Path, *, miniature: bool = False,
           episode_budget_usd: float = 3.0) -> dict:
    """Bind the actor/evaluator inventory and all worker execution dependencies."""
    if (type(episode_budget_usd) not in (int, float) or
            not math.isfinite(episode_budget_usd) or episode_budget_usd <= 0):
        raise CampaignError("episode budget must be finite and positive")
    catalogue = load_catalogue(corpus, miniature=miniature)
    bound = {name: sha256(ROOT / name) for name in BOUND_SOURCE}
    corpus_files = _files(corpus)
    value = {"schema_version": 1, "profile": "offline-miniature" if miniature else "worker-n4",
             "policy": "B0+worker-shadow-v1", "controller_allowed": False,
             "tasks": [{"id": row["id"], "family": row["family"], "split": row["split"]}
                       for row in catalogue["tasks"]],
             "corpus_files": corpus_files, "bound_source": bound,
             "python_version": sys.version.split()[0],
             "model_registry_id": model_registry.load()["registry_id"],
             "episode_budget_usd": episode_budget_usd,
             "maximum_usd": round(len(catalogue["tasks"]) * episode_budget_usd, 9),
             "host_isolation": "unproved-live; fake-transport-only",
             "authorisation": "not-authorised-for-paid-calls",
             "retry_policy": "no-automatic-provider-replay"}
    return {**value, "manifest_sha256": digest(value)}


def validate_manifest(corpus: Path, manifest: dict) -> None:
    if not isinstance(manifest, dict) or manifest.get("manifest_sha256") != digest(
            {key: val for key, val in manifest.items() if key != "manifest_sha256"}):
        raise CampaignError("manifest digest is invalid")
    current = freeze(corpus, miniature=manifest.get("profile") == "offline-miniature",
                     episode_budget_usd=manifest["episode_budget_usd"])
    if manifest != current:
        raise CampaignError("campaign inputs changed since manifest freeze")


def _atomic(path: Path, value: dict) -> None:
    route._atomic_write_bytes(path, (json.dumps(value, indent=2, sort_keys=True,
                                               allow_nan=False) + "\n").encode())


def _grade(oracle: Path, actor: Path, root_state: str) -> dict:
    """Compare black-box JSON I/O with evaluator-only, data-only oracle cases.

    Candidate code runs in its own process with a stripped environment. The
    evaluator never imports candidate code, so a malicious module cannot
    execute inside the grader's privileged process. Live evaluation still
    requires a proven OS boundary around this child process.
    """
    try:
        value = json.loads(oracle.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CampaignError(f"invalid oracle: {oracle}") from exc
    if (not isinstance(value, dict) or not {"schema_version", "cases"} <= set(value)
            or set(value) - {"schema_version", "cases", "no_edit_baseline_sha256"}
            or value["schema_version"] != 1 or not isinstance(value["cases"], list)
            or not value["cases"]):
        raise CampaignError("oracle needs schema version 1 and cases")
    earned = total = 0
    passed = []
    critical = False
    for case in value["cases"]:
        if not isinstance(case, dict) or set(case) != {"input", "expected", "weight",
                                                     "milestone", "critical"}:
            raise CampaignError("invalid oracle case")
        weight = case["weight"]
        if (type(weight) is not int or weight <= 0 or type(case["critical"]) is not bool
                or not isinstance(case["milestone"], str) or not case["milestone"]):
            raise CampaignError("oracle weight, milestone or critical flag is invalid")
        total += weight
        env = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT", "WINDIR", "TMP", "TEMP")
               if key in os.environ}
        env["PYTHONNOUSERSITE"] = "1"
        try:
            result = subprocess.run([sys.executable, "app.py"], cwd=actor,
                                    input=json.dumps(case["input"]) + "\n", env=env,
                                    text=True, capture_output=True, timeout=10)
            observed = json.loads(result.stdout) if result.returncode == 0 else object()
            ok = observed == case["expected"]
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            ok = False
        passed.append(ok)
        if ok:
            earned += weight
        elif case["critical"]:
            critical = True
    no_edit = value.get("no_edit_baseline_sha256")
    edited_when_prohibited = False
    if no_edit is not None:
        if not isinstance(no_edit, str) or len(no_edit) != 64:
            raise CampaignError("invalid no-edit baseline digest")
        try:
            source = (actor / "app.py").read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            edited_when_prohibited = True
        else:
            edited_when_prohibited = hashlib.sha256(source.encode("utf-8")).hexdigest() != no_edit
    accepted = all(passed) and not edited_when_prohibited
    return {"acceptance": accepted,
            "quality": (0 if edited_when_prohibited else round(100 * earned / total, 2)),
            "critical_error": critical or edited_when_prohibited,
            "false_success": root_state == "accepted" and not accepted,
            "milestones": [case["milestone"] for case, ok in zip(value["cases"], passed) if ok]}


class OfflineCampaign:
    """Run a frozen corpus using an injected fake adapter, never a CLI call."""

    def __init__(self, corpus: Path, manifest: dict, output: Path, adapter_factory):
        if manifest.get("profile") not in {"offline-miniature", "worker-n4"}:
            raise CampaignError("N4 runner is not authorised for paid campaigns")
        validate_manifest(corpus, manifest)
        self.corpus = corpus.resolve()
        self.manifest = manifest
        self.output = output.resolve()
        self.adapter_factory = adapter_factory
        self.catalogue = load_catalogue(
            self.corpus, miniature=manifest["profile"] == "offline-miniature")["tasks"]
        if self.output.is_relative_to(self.corpus) or self.corpus.is_relative_to(self.output):
            raise CampaignError("campaign output and evaluator corpus must be disjoint")

    def run(self) -> dict:
        state_path = self.output / "campaign.json"
        with route.ledger_lock(state_path):
            if state_path.is_file():
                state = json.loads(state_path.read_text(encoding="utf-8"))
                if state.get("manifest_sha256") != self.manifest["manifest_sha256"]:
                    raise CampaignError("campaign checkpoint belongs to another manifest")
                if state["status"] in {"blocked", "complete"}:
                    return state
            else:
                state = {"schema_version": 1, "manifest_sha256": self.manifest["manifest_sha256"],
                         "status": "running", "next_index": 0, "results": []}
                _atomic(state_path, state)
            while state["next_index"] < len(self.catalogue):
                index = state["next_index"]
                task = self.catalogue[index]
                # Opaque directory names keep task IDs and split out of the
                # actor's path. A restart reuses this directory and executor.
                token = digest({"manifest": self.manifest["manifest_sha256"],
                                "index": index})[:20]
                actor = self.output / "actors" / token
                if actor.is_symlink() or not actor.resolve().is_relative_to(self.output):
                    raise CampaignError("actor root escapes campaign output")
                if not actor.exists():
                    shutil.copytree(_inside(self.corpus, task["actor"]), actor)
                    shutil.copyfile(_inside(self.corpus, task["issue"], file=True),
                                    actor / "ISSUE.md")
                    shutil.copyfile(_inside(self.corpus, task["acceptance"], file=True),
                                    actor / "acceptance.json")
                _files(actor)  # Reject actor symlinks before running or grading.
                # The adapter receives only its materialised actor root. The
                # catalogue row carries protected family/split/oracle fields.
                adapter = self.adapter_factory(actor)
                if not getattr(adapter, "offline_fake", False):
                    raise CampaignError("offline campaign requires an explicit fake adapter")
                executor = TaskExecutor(actor, adapter)
                root_id = f"episode_{token}"
                if not executor._path(root_id).exists():
                    executor.admit(goal=(actor / "ISSUE.md").read_text(encoding="utf-8"),
                                   scope=task["allowed_edits"], permissions=["read", "edit"],
                                   acceptance_path=actor / "acceptance.json",
                                   budget_usd=self.manifest["episode_budget_usd"],
                                   authority_id=f"grant_{token}", actor="offline-campaign",
                                   root_id=root_id)
                    executor.shadow_select(root_id, worker_selector.assess(task["assessment"]))
                result = executor.run(root_id)
                if result["state"] in {"blocked", "uncertain", "cancelled", "awaiting_review"}:
                    state["status"] = "blocked"
                    state["block"] = {"index": index, "root_state": result["state"],
                                      "reason": result.get("block")}
                    _atomic(state_path, state)
                    return state
                _files(actor)
                before = sha256(_inside(self.corpus, task["oracle"], file=True))
                grade = _grade(_inside(self.corpus, task["oracle"], file=True), actor,
                               result["state"])
                if sha256(_inside(self.corpus, task["oracle"], file=True)) != before:
                    raise CampaignError("protected oracle changed during grading")
                state["results"].append({"task_id": task["id"], "root_state": result["state"],
                                         "grade": grade, "spent_usd": result["budget"]["spent_usd"],
                                         "root_record_digest": digest({key: val for key, val in result.items()
                                                                       if key != "budget"})})
                state["next_index"] += 1
                _atomic(state_path, state)
            state["status"] = "complete"
            _atomic(state_path, state)
            return state
