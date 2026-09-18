#!/usr/bin/env python3
"""Durable, provider-free Controller routing controls.

This module owns only operator intent.  It never imports a model adapter or
dispatcher and therefore setting, clearing, or resolving a control cannot
launch paid work.  A caller resolves once at a safe dispatch boundary and
retains the returned immutable decision for that in-flight operation; later
updates apply only when the next boundary is resolved.

Precedence, highest first: explicit CLI/request, task, session, project,
shipped default.  ``auto`` is a real value at every scope, so a narrower
``auto`` deliberately defeats a wider ``on`` or ``off``.
"""
from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime as dt
import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Iterator


SCHEMA_VERSION = 1
SHIPPED_DEFAULT = "auto"
MODES = ("auto", "on", "off")
SCOPES = ("project", "session", "task")
STATE_RELATIVE = Path(".claude/controller-control.json")
_SAFE_ID = re.compile(r"^[^\x00-\x1f\x7f]{1,256}$")


class ControlError(RuntimeError):
    """Base class for deterministic control-plane failures."""


class StaleControlError(ControlError):
    """Raised when an optimistic update uses an old state revision."""


class ControlLockTimeout(ControlError):
    """Raised when another process holds the state lock too long."""


@dataclasses.dataclass(frozen=True)
class ControlDecision:
    """Immutable result to retain for one in-flight dispatch operation."""

    mode: str
    source: str
    state_revision: int
    task_revision: str | None
    session_id: str | None

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


def state_path(project: Path) -> Path:
    """Return the control state path for a consumer project."""
    return project.resolve() / STATE_RELATIVE


def _empty_state() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "revision": 0,
        "project": None,
        "sessions": {},
        "tasks": {},
    }


def _identifier(value: str | None, label: str) -> str:
    if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
        raise ControlError(f"{label} must be 1-256 printable characters")
    return value


def _validate_record(record: object, label: str) -> dict:
    if not isinstance(record, dict):
        raise ControlError(f"{label} must be an object")
    if record.get("mode") not in MODES:
        raise ControlError(f"{label}.mode must be one of {MODES}")
    if not isinstance(record.get("revision"), int) or record["revision"] < 1:
        raise ControlError(f"{label}.revision must be a positive integer")
    if not isinstance(record.get("updated_at"), str) or not record["updated_at"]:
        raise ControlError(f"{label}.updated_at must be a timestamp")
    source = record.get("source")
    if (not isinstance(source, dict) or set(source) != {"kind", "reference"}
            or source.get("kind") not in ("operator-cli", "operator-api")
            or not isinstance(source.get("reference"), str) or not source["reference"]
            or len(source["reference"]) > 300):
        raise ControlError(f"{label}.source must identify the operator CLI/API action")
    return record


def validate_state(value: object) -> dict:
    """Validate persisted state strictly; corrupted intent must not be guessed."""
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise ControlError("unsupported or invalid controller control state")
    revision = value.get("revision")
    if not isinstance(revision, int) or revision < 0:
        raise ControlError("control state revision must be a non-negative integer")
    project_record = value.get("project")
    if project_record is not None:
        _validate_record(project_record, "project")
    for collection in ("sessions", "tasks"):
        records = value.get(collection)
        if not isinstance(records, dict):
            raise ControlError(f"{collection} must be an object")
        for key, record in records.items():
            _identifier(key, f"{collection} key")
            _validate_record(record, f"{collection}.{key}")
    return value


def load_state(project: Path) -> dict:
    path = state_path(project)
    if not path.exists():
        return _empty_state()
    try:
        return validate_state(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ControlError(f"cannot read {path}: {exc}") from exc


@contextlib.contextmanager
def state_lock(path: Path, timeout_s: float = 10.0) -> Iterator[None]:
    """Hold an OS-level sibling lock for a complete read-modify-write."""
    if timeout_s < 0:
        raise ValueError("lock timeout must be non-negative")
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    handle = lock_path.open("a+b")
    handle.seek(0, os.SEEK_END)
    if handle.tell() == 0:
        handle.write(b"\0")
        handle.flush()
    deadline = time.monotonic() + timeout_s
    acquired = False
    try:
        while not acquired:
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except (OSError, BlockingIOError):
                if time.monotonic() >= deadline:
                    raise ControlLockTimeout(f"timed out locking {lock_path}")
                time.sleep(0.01)
        yield
    finally:
        if acquired:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False,
                          allow_nan=False) + "\n").encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _check_expected(state: dict, expected_revision: int | None) -> None:
    if expected_revision is not None and state["revision"] != expected_revision:
        raise StaleControlError(
            f"stale control revision: expected {expected_revision}, current {state['revision']}"
        )


def _target(state: dict, scope: str, session_id: str | None,
            task_revision: str | None) -> tuple[dict, str | None]:
    if scope == "project":
        return state, "project"
    if scope == "session":
        return state["sessions"], _identifier(session_id, "session id")
    if scope == "task":
        return state["tasks"], _identifier(task_revision, "task revision")
    raise ControlError(f"scope must be one of {SCOPES}")


def set_mode(project: Path, scope: str, mode: str, *, session_id: str | None = None,
             task_revision: str | None = None, expected_revision: int | None = None,
             source_kind: str = "operator-api", source_reference: str = "direct-api") -> dict:
    """Persist one scoped value under lock and return the validated new state."""
    if mode not in MODES:
        raise ControlError(f"mode must be one of {MODES}")
    if source_kind not in ("operator-cli", "operator-api") or not isinstance(source_reference, str) \
            or not source_reference.strip() or len(source_reference) > 300:
        raise ControlError("source must identify an operator CLI/API action")
    path = state_path(project)
    with state_lock(path):
        state = load_state(project)
        _check_expected(state, expected_revision)
        state["revision"] += 1
        record = {
            "mode": mode,
            "revision": state["revision"],
            "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "source": {"kind": source_kind, "reference": source_reference},
        }
        target, key = _target(state, scope, session_id, task_revision)
        target[key] = record
        _atomic_write(path, validate_state(state))
        return state


def clear_mode(project: Path, scope: str, *, session_id: str | None = None,
               task_revision: str | None = None, expected_revision: int | None = None) -> dict:
    """Remove one scoped value.  Clearing an absent value is a no-op."""
    path = state_path(project)
    with state_lock(path):
        state = load_state(project)
        _check_expected(state, expected_revision)
        target, key = _target(state, scope, session_id, task_revision)
        if key not in target or target[key] is None:
            return state
        del target[key]
        state["revision"] += 1
        _atomic_write(path, validate_state(state))
        return state


def resolve(project: Path, *, explicit_mode: str | None = None,
            session_id: str | None = None,
            task_revision: str | None = None) -> ControlDecision:
    """Resolve precedence without mutating state or launching any work."""
    if explicit_mode is not None and explicit_mode not in MODES:
        raise ControlError(f"explicit mode must be one of {MODES}")
    state = load_state(project)
    if explicit_mode is not None:
        return ControlDecision(explicit_mode, "explicit", state["revision"], task_revision, session_id)
    if task_revision is not None:
        _identifier(task_revision, "task revision")
        record = state["tasks"].get(task_revision)
        if record is not None:
            return ControlDecision(record["mode"], "task", state["revision"], task_revision, session_id)
    if session_id is not None:
        _identifier(session_id, "session id")
        record = state["sessions"].get(session_id)
        if record is not None:
            return ControlDecision(record["mode"], "session", state["revision"], task_revision, session_id)
    if state["project"] is not None:
        return ControlDecision(state["project"]["mode"], "project", state["revision"], task_revision, session_id)
    return ControlDecision(SHIPPED_DEFAULT, "shipped-default", state["revision"], task_revision, session_id)


def _scope_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--scope", required=True, choices=SCOPES)
    parser.add_argument("--session-id")
    parser.add_argument("--task-revision")
    parser.add_argument("--expected-revision", type=int)


def _result(command: str, state: dict) -> dict:
    return {"schema_version": 1, "command": command, "state_revision": state["revision"],
            "paid_work_started": False, "state": state}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    set_parser = sub.add_parser("set", help="set a durable scoped mode")
    _scope_arguments(set_parser)
    set_parser.add_argument("--mode", required=True, choices=MODES)
    set_parser.add_argument("--source-ref", default="direct-cli",
                            help="operator message/action reference, never repository content")
    clear_parser = sub.add_parser("clear", help="remove a durable scoped mode")
    _scope_arguments(clear_parser)
    resolve_parser = sub.add_parser("resolve", help="show the effective mode at a dispatch boundary")
    resolve_parser.add_argument("--explicit", choices=MODES)
    resolve_parser.add_argument("--session-id")
    resolve_parser.add_argument("--task-revision")
    sub.add_parser("status", help="show durable state without mutation")
    args = parser.parse_args(argv)
    try:
        if args.command == "set":
            output = _result("set", set_mode(args.project, args.scope, args.mode,
                                             session_id=args.session_id,
                                             task_revision=args.task_revision,
                                             expected_revision=args.expected_revision,
                                             source_kind="operator-cli",
                                             source_reference=args.source_ref))
        elif args.command == "clear":
            output = _result("clear", clear_mode(args.project, args.scope,
                                                 session_id=args.session_id,
                                                 task_revision=args.task_revision,
                                                 expected_revision=args.expected_revision))
        elif args.command == "resolve":
            output = {"schema_version": 1, "command": "resolve", "paid_work_started": False,
                      "decision": resolve(args.project, explicit_mode=args.explicit,
                                          session_id=args.session_id,
                                          task_revision=args.task_revision).as_dict()}
        else:
            output = _result("status", load_state(args.project))
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0
    except ControlError as exc:
        print(json.dumps({"schema_version": 1, "result": "ERROR", "error": str(exc),
                          "paid_work_started": False}, indent=2), file=os.sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
