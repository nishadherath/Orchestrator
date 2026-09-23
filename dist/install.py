#!/usr/bin/env python3
"""Plan, install, inspect, uninstall or roll back an orchestrator bundle.

The installer is intentionally standard-library only. It treats the bundle
manifest as an ownership contract, merges only declared configuration values
and records enough pre-install state to reverse one operation safely.

Usage from a bundle directory:
    python3 install.py plan --target /path/to/project
    python3 install.py apply --target /path/to/project
    python3 install.py status --target /path/to/project
    python3 install.py uninstall --target /path/to/project
    python3 install.py rollback --target /path/to/project [--backup ID]

Pass --graft-command and repeated --graft-arg values on plan/apply when the
installer should own the consumer project's mcpServers.graft entry. Omitting
them leaves .mcp.json untouched because an executable path cannot be inferred
portably.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = 1
MANIFEST_NAME = "bundle-manifest.json"
STATE_REL = PurePosixPath(".claude/orchestrator-install/state.json")
BACKUP_ROOT_REL = PurePosixPath(".claude/orchestrator-install/backups")
CLAUDE_BEGIN = "<!-- orchestrator:begin -->"
CLAUDE_END = "<!-- orchestrator:end -->"
ABSENT = {"exists": False}


class InstallError(RuntimeError):
    """A bundle, target or rollback state is unsafe to mutate."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def safe_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise InstallError(f"unsafe manifest path {value!r}")
    return path


def target_path(root: Path, relative: PurePosixPath) -> Path:
    return root.joinpath(*relative.parts)


def atomic_write(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    except BaseException:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def load_json(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InstallError(f"{label} is malformed JSON at line {exc.lineno}, column {exc.colno}: {path}") from exc
    except OSError as exc:
        raise InstallError(f"cannot read {label} at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise InstallError(f"{label} must be a JSON object: {path}")
    return value


def bundle_default() -> Path:
    here = Path(__file__).resolve().parent
    if (here / MANIFEST_NAME).is_file():
        return here
    candidate = here.parent / "dist"
    return candidate if (candidate / MANIFEST_NAME).is_file() else here


def load_manifest(bundle: Path) -> dict:
    path = bundle / MANIFEST_NAME
    value = load_json(path, "bundle manifest")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise InstallError(f"unsupported bundle manifest schema {value.get('schema_version')!r}")
    if not isinstance(value.get("bundle_version"), str) or not value["bundle_version"]:
        raise InstallError("bundle manifest has no bundle_version")
    files = value.get("files")
    if not isinstance(files, dict) or not files:
        raise InstallError("bundle manifest has no owned files")
    normalised: dict[str, str] = {}
    for name, digest in files.items():
        relative = safe_relative(name)
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise InstallError(f"bundle manifest has invalid hash for {name!r}")
        source = target_path(bundle, relative)
        if not source.is_file():
            raise InstallError(f"bundle payload is missing {name}")
        actual = sha256_bytes(source.read_bytes())
        if actual != digest:
            raise InstallError(f"bundle payload hash mismatch for {name}: expected {digest}, found {actual}")
        normalised[relative.as_posix()] = digest
    value["files"] = normalised
    for asset in ("settings.fragment.json", "CLAUDE.template.md"):
        if not (bundle / asset).is_file():
            raise InstallError(f"bundle support asset is missing {asset}")
    return value


def read_optional_json(path: Path, label: str) -> dict:
    return load_json(path, label) if path.exists() else {}


def get_path(value: dict, path: tuple[str, ...]) -> tuple[bool, Any]:
    cursor: Any = value
    for key in path:
        if not isinstance(cursor, dict) or key not in cursor:
            return False, None
        cursor = cursor[key]
    return True, cursor


def set_path(value: dict, path: tuple[str, ...], item: Any) -> None:
    cursor = value
    for key in path[:-1]:
        child = cursor.get(key)
        if child is None:
            child = {}
            cursor[key] = child
        if not isinstance(child, dict):
            raise InstallError(f"configuration path {'.'.join(path)} crosses a non-object value")
        cursor = child
    cursor[path[-1]] = copy.deepcopy(item)


def delete_path(value: dict, path: tuple[str, ...]) -> None:
    parents: list[tuple[dict, str]] = []
    cursor = value
    for key in path[:-1]:
        child = cursor.get(key)
        if not isinstance(child, dict):
            return
        parents.append((cursor, key))
        cursor = child
    cursor.pop(path[-1], None)
    for parent, key in reversed(parents):
        child = parent.get(key)
        if isinstance(child, dict) and not child:
            del parent[key]
        else:
            break


def setting_spec(fragment: dict) -> dict:
    values = {}
    for key, value in fragment.items():
        if key not in ("_comment", "permissions", "hooks"):
            values[key] = copy.deepcopy(value)
    permissions = fragment.get("permissions", {}).get("allow", [])
    hooks = fragment.get("hooks", {}).get("SessionStart", [])
    if not isinstance(permissions, list) or not isinstance(hooks, list):
        raise InstallError("settings.fragment.json permissions.allow and hooks.SessionStart must be arrays")
    return {"values": values, "permissions_allow": copy.deepcopy(permissions),
            "session_start_hooks": copy.deepcopy(hooks)}


def graft_spec(command: str | None, args: list[str]) -> dict | None:
    if command is None:
        if args:
            raise InstallError("--graft-arg requires --graft-command")
        return None
    return {"type": "stdio", "command": command, "args": args}


def snapshot(value: Any, exists: bool = True) -> dict:
    return {"exists": exists, "value": copy.deepcopy(value)} if exists else copy.deepcopy(ABSENT)


@dataclass
class Transaction:
    action: str
    target: Path
    bundle: Path | None
    bundle_version: str | None
    backup_id: str
    changes: list[dict] = field(default_factory=list)
    conflicts: list[dict] = field(default_factory=list)
    raw_writes: dict[PurePosixPath, bytes | None] = field(default_factory=dict)
    raw_ops: list[dict] = field(default_factory=list)
    json_writes: dict[PurePosixPath, dict] = field(default_factory=dict)
    json_ops: dict[str, list[dict]] = field(default_factory=dict)
    claude_write: bytes | None | object = field(default_factory=lambda: _NO_WRITE)
    claude_op: dict | None = None
    state_after: dict | None = None
    state_before: bytes | None = None

    @property
    def backup_rel(self) -> PurePosixPath:
        return BACKUP_ROOT_REL / self.backup_id

    def public(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "action": self.action,
            "result": "CONFLICT" if self.conflicts else ("NO_CHANGES" if not self.changes else "READY"),
            "target": str(self.target),
            "bundle": str(self.bundle) if self.bundle else None,
            "bundle_version": self.bundle_version,
            "backup_location": str(target_path(self.target, self.backup_rel)),
            "changes": self.changes,
            "conflicts": self.conflicts,
        }


_NO_WRITE = object()


def assign_backup_id(tx: Transaction) -> None:
    """Choose a deterministic unused backup name for this exact plan.

    A separate `plan` followed by `apply` therefore names the same location.
    Existing backups receive a numeric suffix, which also permits an earlier
    operation to be rolled back and the same transition applied again.
    """
    identity = json.dumps({"action": tx.action, "version": tx.bundle_version,
                           "changes": tx.changes}, sort_keys=True).encode("utf-8")
    version = re.sub(r"[^A-Za-z0-9._-]+", "-", tx.bundle_version or "none")
    base = f"{tx.action}-{version}-{sha256_bytes(identity)[:10]}"
    root = target_path(tx.target, BACKUP_ROOT_REL)
    candidate, suffix = base, 1
    while (root / candidate).exists():
        suffix += 1
        candidate = f"{base}-{suffix}"
    tx.backup_id = candidate


def load_state(target: Path) -> tuple[dict | None, bytes | None]:
    path = target_path(target, STATE_REL)
    if not path.exists():
        return None, None
    raw = path.read_bytes()
    value = load_json(path, "installer state")
    if value.get("schema_version") != SCHEMA_VERSION or not isinstance(value.get("files"), dict):
        raise InstallError(f"unsupported or incomplete installer state: {path}")
    return value, raw


def add_conflict(tx: Transaction, kind: str, path: str, detail: str) -> None:
    tx.conflicts.append({"kind": kind, "path": path, "detail": detail})


def add_change(tx: Transaction, kind: str, path: str, status: str, detail: str) -> None:
    tx.changes.append({"kind": kind, "path": path, "status": status, "detail": detail})


def plan_payload(tx: Transaction, manifest: dict, previous: dict | None, remove: bool = False) -> None:
    current_owned = (previous or {}).get("files", {})
    desired = {} if remove else manifest["files"]
    names = sorted(set(current_owned) | set(desired))
    for name in names:
        relative = safe_relative(name)
        path = target_path(tx.target, relative)
        exists = path.is_file()
        current_hash = sha256_bytes(path.read_bytes()) if exists else None
        old_hash = current_owned.get(name)
        new_hash = desired.get(name)
        if old_hash is None and exists:
            add_conflict(tx, "file", name, "path already exists but is not owned by an earlier installer state")
            continue
        if old_hash is not None and (not exists or current_hash != old_hash):
            found = "missing" if not exists else current_hash
            add_conflict(tx, "file", name, f"owned file changed since install; expected {old_hash}, found {found}")
            continue
        if new_hash == current_hash:
            continue
        before = path.read_bytes() if exists else None
        after = None if new_hash is None else target_path(tx.bundle, relative).read_bytes()
        tx.raw_writes[relative] = after
        tx.raw_ops.append({"path": name, "before_exists": exists,
                           "before_sha256": current_hash, "after_sha256": new_hash})
        status = "remove" if after is None else ("update" if exists else "add")
        add_change(tx, "file", name, status, f"{status} bundle-owned file")
        if before is not None:
            # The bytes are written into the backup when the transaction commits.
            pass


def plan_owned_json(tx: Transaction, relative: PurePosixPath, desired: dict,
                    previous: dict | None, label: str) -> None:
    path = target_path(tx.target, relative)
    try:
        current = read_optional_json(path, label)
    except InstallError as exc:
        add_conflict(tx, "configuration", relative.as_posix(), str(exc))
        return
    updated = copy.deepcopy(current)
    ops: list[dict] = []
    old_values = (previous or {}).get("values", {})
    new_values = desired.get("values", {})
    for key in sorted(set(old_values) | set(new_values)):
        json_path = (key,)
        exists, actual = get_path(current, json_path)
        if key in old_values:
            if not exists or actual != old_values[key]:
                add_conflict(tx, "configuration", f"{relative.as_posix()}:{key}",
                             "owned value changed after installation")
                continue
        elif exists:
            add_conflict(tx, "configuration", f"{relative.as_posix()}:{key}",
                         "same-name value already exists and is not bundle-owned")
            continue
        before = snapshot(actual, exists)
        if key in new_values:
            after = snapshot(new_values[key])
            set_path(updated, json_path, new_values[key])
        else:
            after = snapshot(None, False)
            delete_path(updated, json_path)
        if before != after:
            ops.append({"kind": "value", "path": list(json_path), "before": before, "after": after})

    for spec_key, json_path in (("permissions_allow", ("permissions", "allow")),
                                ("session_start_hooks", ("hooks", "SessionStart"))):
        old_items = (previous or {}).get(spec_key, [])
        new_items = desired.get(spec_key, [])
        exists, actual = get_path(current, json_path)
        if exists and not isinstance(actual, list):
            add_conflict(tx, "configuration", f"{relative.as_posix()}:{'.'.join(json_path)}",
                         "expected an array and found another JSON type")
            continue
        actual_items = copy.deepcopy(actual) if exists else []
        identity = ".".join(json_path)
        if previous is None:
            desired.setdefault("array_preexisting", {})[identity] = exists
        else:
            desired.setdefault("array_preexisting", {})[identity] = (
                previous.get("array_preexisting", {}).get(identity, True))
        missing_old = [item for item in old_items if item not in actual_items]
        if missing_old:
            add_conflict(tx, "configuration", f"{relative.as_posix()}:{'.'.join(json_path)}",
                         "one or more owned array entries changed or were removed")
            continue
        unowned_collisions = [item for item in new_items if item in actual_items and item not in old_items]
        if unowned_collisions:
            add_conflict(tx, "configuration", f"{relative.as_posix()}:{'.'.join(json_path)}",
                         "an identical entry exists but ownership is not established")
            continue
        removed = [item for item in old_items if item not in new_items]
        added = [item for item in new_items if item not in old_items]
        next_items = [item for item in actual_items if item not in removed] + copy.deepcopy(added)
        if removed or added:
            keep_empty = desired["array_preexisting"][identity]
            after_exists = bool(next_items) or keep_empty
            if after_exists:
                set_path(updated, json_path, next_items)
            else:
                delete_path(updated, json_path)
            ops.append({"kind": "list", "path": list(json_path),
                        "removed": copy.deepcopy(removed), "added": copy.deepcopy(added),
                        "before_exists": exists, "after_exists": after_exists})

    if ops:
        tx.json_writes[relative] = updated
        tx.json_ops[relative.as_posix()] = ops
        add_change(tx, "configuration", relative.as_posix(), "merge",
                   f"merge {len(ops)} owned value group(s); preserve unrelated values")


def template_block(bundle: Path) -> str:
    text = (bundle / "CLAUDE.template.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    if text.startswith("# CLAUDE.md\n"):
        text = text[len("# CLAUDE.md\n"):].lstrip("\n")
    return f"{CLAUDE_BEGIN}\n{text.rstrip()}\n{CLAUDE_END}"


def find_block(text: str) -> tuple[int, int, str] | None:
    starts = [m.start() for m in re.finditer(re.escape(CLAUDE_BEGIN), text)]
    ends = [m.end() for m in re.finditer(re.escape(CLAUDE_END), text)]
    if not starts and not ends:
        return None
    if len(starts) != 1 or len(ends) != 1 or ends[0] <= starts[0]:
        raise InstallError("CLAUDE.md has incomplete or duplicate orchestrator ownership markers")
    return starts[0], ends[0], text[starts[0]:ends[0]]


def plan_claude(tx: Transaction, desired: str | None, previous: str | None) -> None:
    relative = PurePosixPath("CLAUDE.md")
    path = target_path(tx.target, relative)
    existed = path.exists()
    try:
        current = path.read_text(encoding="utf-8").replace("\r\n", "\n") if existed else ""
        found = find_block(current)
    except (OSError, UnicodeDecodeError, InstallError) as exc:
        add_conflict(tx, "instructions", relative.as_posix(), str(exc))
        return
    if previous is None:
        if found is not None:
            add_conflict(tx, "instructions", relative.as_posix(),
                         "an orchestrator block exists but no installer state owns it")
            return
        before_block = None
    else:
        if found is None or found[2] != previous:
            add_conflict(tx, "instructions", relative.as_posix(),
                         "the bundle-owned block changed after installation")
            return
        before_block = previous
    if desired == before_block:
        return
    if found is None:
        prefix = current.rstrip()
        if not prefix:
            prefix = "# CLAUDE.md"
        updated = prefix + "\n\n" + (desired or "") + "\n"
    else:
        start, end, _ = found
        replacement = desired or ""
        updated = (current[:start] + replacement + current[end:])
        updated = re.sub(r"\n{3,}", "\n\n", updated).rstrip() + "\n"
    if not desired and not existed and updated.strip() == "# CLAUDE.md":
        updated_bytes: bytes | None = None
    elif not desired and current[:found[0]].strip() == "# CLAUDE.md" and not current[found[1]:].strip():
        updated_bytes = None if tx.action == "uninstall" else b"# CLAUDE.md\n"
    else:
        updated_bytes = updated.encode("utf-8")
    tx.claude_write = updated_bytes
    tx.claude_op = {"path": relative.as_posix(), "before_block": before_block,
                    "after_block": desired, "file_existed_before": existed}
    status = "remove" if desired is None else ("update" if previous else "add")
    add_change(tx, "instructions", relative.as_posix(), status,
               f"{status} the marked bundle instruction block")


def new_state(manifest: dict, settings: dict, graft: dict | None, block: str,
              backup_id: str, previous: dict | None) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "bundle_version": manifest["bundle_version"],
        "installed_at": utc_now(),
        "previous_bundle_version": (previous or {}).get("bundle_version"),
        "last_backup": backup_id,
        "files": manifest["files"],
        "settings": settings,
        "graft_server": graft,
        "claude_block": block,
    }


def plan_apply(bundle: Path, target: Path, command: str | None, args: list[str]) -> Transaction:
    bundle, target = bundle.resolve(), target.resolve()
    manifest = load_manifest(bundle)
    previous, state_raw = load_state(target)
    action = "upgrade" if previous else "install"
    tx = Transaction(action, target, bundle, manifest["bundle_version"], "pending",
                     state_before=state_raw)
    plan_payload(tx, manifest, previous)
    fragment = load_json(bundle / "settings.fragment.json", "settings fragment")
    settings = setting_spec(fragment)
    plan_owned_json(tx, PurePosixPath(".claude/settings.json"), settings,
                    (previous or {}).get("settings"), "Claude settings")
    old_graft = (previous or {}).get("graft_server")
    graft = graft_spec(command, args)
    if command is None and previous is not None:
        graft = copy.deepcopy(old_graft)
    if graft is not None or old_graft is not None:
        desired = {"values": {"mcpServers": {"graft": graft}}} if graft is not None else {"values": {}}
        old = {"values": {"mcpServers": {"graft": old_graft}}} if old_graft is not None else None
        # Merge the server itself rather than owning the whole mcpServers object.
        path = target / ".mcp.json"
        try:
            current = read_optional_json(path, "MCP configuration")
        except InstallError as exc:
            add_conflict(tx, "configuration", ".mcp.json", str(exc))
        else:
            updated = copy.deepcopy(current)
            exists, actual = get_path(current, ("mcpServers", "graft"))
            if old_graft is not None and (not exists or actual != old_graft):
                add_conflict(tx, "configuration", ".mcp.json:mcpServers.graft",
                             "owned Graft server entry changed after installation")
            elif old_graft is None and exists:
                add_conflict(tx, "configuration", ".mcp.json:mcpServers.graft",
                             "same-name Graft server entry already exists and is not bundle-owned")
            else:
                before = snapshot(actual, exists)
                after = snapshot(graft, graft is not None)
                if before != after:
                    if graft is None:
                        delete_path(updated, ("mcpServers", "graft"))
                    else:
                        set_path(updated, ("mcpServers", "graft"), graft)
                    rel = PurePosixPath(".mcp.json")
                    tx.json_writes[rel] = updated
                    tx.json_ops[rel.as_posix()] = [{"kind": "value", "path": ["mcpServers", "graft"],
                                                    "before": before, "after": after}]
                    add_change(tx, "configuration", rel.as_posix(), "merge",
                               "merge bundle-owned mcpServers.graft; preserve other servers")
    block = template_block(bundle)
    plan_claude(tx, block, (previous or {}).get("claude_block"))
    assign_backup_id(tx)
    desired_identity = {"bundle_version": manifest["bundle_version"], "files": manifest["files"],
                        "settings": settings, "graft_server": graft, "claude_block": block}
    same_identity = previous is not None and all(previous.get(key) == value
                                                 for key, value in desired_identity.items())
    tx.state_after = previous if same_identity and not tx.changes else new_state(
        manifest, settings, graft, block, tx.backup_id, previous)
    state_after_raw = json_bytes(tx.state_after)
    if state_raw != state_after_raw:
        add_change(tx, "metadata", STATE_REL.as_posix(), "write", "record bundle ownership and rollback state")
    return tx


def plan_uninstall(target: Path) -> Transaction:
    target = target.resolve()
    previous, state_raw = load_state(target)
    tx = Transaction("uninstall", target, None, (previous or {}).get("bundle_version"),
                     "pending", state_before=state_raw)
    if previous is None:
        add_conflict(tx, "metadata", STATE_REL.as_posix(), "no installer state exists; ownership is unknown")
        return tx
    manifest = {"files": {}}
    plan_payload(tx, manifest, previous, remove=True)
    plan_owned_json(tx, PurePosixPath(".claude/settings.json"),
                    {"values": {}, "permissions_allow": [], "session_start_hooks": []},
                    previous.get("settings"), "Claude settings")
    old_graft = previous.get("graft_server")
    if old_graft is not None:
        path = target / ".mcp.json"
        try:
            current = read_optional_json(path, "MCP configuration")
        except InstallError as exc:
            add_conflict(tx, "configuration", ".mcp.json", str(exc))
        else:
            exists, actual = get_path(current, ("mcpServers", "graft"))
            if not exists or actual != old_graft:
                add_conflict(tx, "configuration", ".mcp.json:mcpServers.graft",
                             "owned Graft server entry changed after installation")
            else:
                updated = copy.deepcopy(current)
                delete_path(updated, ("mcpServers", "graft"))
                rel = PurePosixPath(".mcp.json")
                tx.json_writes[rel] = updated
                tx.json_ops[rel.as_posix()] = [{"kind": "value", "path": ["mcpServers", "graft"],
                                                "before": snapshot(old_graft), "after": snapshot(None, False)}]
                add_change(tx, "configuration", rel.as_posix(), "merge", "remove the owned Graft server entry")
    plan_claude(tx, None, previous.get("claude_block"))
    assign_backup_id(tx)
    tx.state_after = None
    add_change(tx, "metadata", STATE_REL.as_posix(), "remove", "remove current ownership state; keep backups")
    return tx


def backup_preimages(tx: Transaction) -> dict:
    backup = target_path(tx.target, tx.backup_rel)
    if backup.exists():
        raise InstallError(f"backup path already exists: {backup}")
    backup_root = target_path(tx.target, BACKUP_ROOT_REL)
    ignore = backup_root / ".gitignore"
    ignore_content = b"*\n!.gitignore\n"
    if ignore.exists() and ignore.read_bytes() != ignore_content:
        raise InstallError(f"backup ignore file has an unexpected value: {ignore}")
    if not ignore.exists():
        atomic_write(ignore, ignore_content)
    files_dir = backup / "files"
    preimages: dict[str, dict] = {}
    touched = set(tx.raw_writes) | set(tx.json_writes)
    if tx.claude_write is not _NO_WRITE:
        touched.add(PurePosixPath("CLAUDE.md"))
    touched.add(STATE_REL)
    for relative in sorted(touched, key=lambda p: p.as_posix()):
        source = target_path(tx.target, relative)
        exists = source.is_file()
        raw = source.read_bytes() if exists else None
        preimages[relative.as_posix()] = {"existed": exists, "sha256": sha256_bytes(raw) if raw is not None else None}
        if raw is not None:
            saved = target_path(files_dir, relative)
            saved.parent.mkdir(parents=True, exist_ok=True)
            saved.write_bytes(raw)
    return {"schema_version": SCHEMA_VERSION, "backup_id": tx.backup_id, "created_at": utc_now(),
            "action": tx.action, "target": str(tx.target), "bundle_version": tx.bundle_version,
            "preimages": preimages, "raw_ops": tx.raw_ops, "json_ops": tx.json_ops,
            "claude_op": tx.claude_op,
            "state_before_existed": tx.state_before is not None,
            "state_after_sha256": sha256_bytes(json_bytes(tx.state_after)) if tx.state_after is not None else None}


def commit(tx: Transaction) -> dict:
    if tx.conflicts:
        raise InstallError("refusing to mutate a plan with conflicts")
    if not tx.changes:
        result = tx.public()
        result["result"] = "NO_CHANGES"
        return result
    metadata = backup_preimages(tx)
    backup = target_path(tx.target, tx.backup_rel)
    atomic_write(backup / "metadata.json", json_bytes(metadata))
    for relative, value in tx.raw_writes.items():
        path = target_path(tx.target, relative)
        if value is None:
            path.unlink(missing_ok=True)
        else:
            atomic_write(path, value)
    for relative, value in tx.json_writes.items():
        atomic_write(target_path(tx.target, relative), json_bytes(value))
    if tx.claude_write is not _NO_WRITE:
        path = tx.target / "CLAUDE.md"
        if tx.claude_write is None:
            path.unlink(missing_ok=True)
        else:
            atomic_write(path, tx.claude_write)
    state_path = target_path(tx.target, STATE_REL)
    if tx.state_after is None:
        state_path.unlink(missing_ok=True)
    else:
        atomic_write(state_path, json_bytes(tx.state_after))
    result = tx.public()
    result["result"] = "APPLIED"
    return result


def status(target: Path) -> dict:
    target = target.resolve()
    try:
        state, _ = load_state(target)
    except InstallError as exc:
        return {"schema_version": SCHEMA_VERSION, "result": "INVALID", "target": str(target),
                "installed": False, "bundle_version": None, "drift": [{"path": STATE_REL.as_posix(), "detail": str(exc)}]}
    if state is None:
        return {"schema_version": SCHEMA_VERSION, "result": "NOT_INSTALLED", "target": str(target),
                "installed": False, "bundle_version": None, "drift": []}
    drift = []
    for name, expected in sorted(state["files"].items()):
        path = target_path(target, safe_relative(name))
        actual = sha256_bytes(path.read_bytes()) if path.is_file() else None
        if actual != expected:
            drift.append({"path": name, "detail": f"expected {expected}, found {actual or 'missing'}"})
    settings_path = target / ".claude" / "settings.json"
    try:
        settings = read_optional_json(settings_path, "Claude settings")
        spec = state.get("settings") or {}
        for key, expected in spec.get("values", {}).items():
            exists, actual = get_path(settings, (key,))
            if not exists or actual != expected:
                drift.append({"path": f".claude/settings.json:{key}", "detail": "owned value differs"})
        for spec_key, json_path in (("permissions_allow", ("permissions", "allow")),
                                    ("session_start_hooks", ("hooks", "SessionStart"))):
            exists, actual = get_path(settings, json_path)
            missing = [item for item in spec.get(spec_key, []) if not exists or not isinstance(actual, list) or item not in actual]
            if missing:
                drift.append({"path": f".claude/settings.json:{'.'.join(json_path)}",
                              "detail": f"{len(missing)} owned entries missing or changed"})
    except InstallError as exc:
        drift.append({"path": ".claude/settings.json", "detail": str(exc)})
    try:
        text = (target / "CLAUDE.md").read_text(encoding="utf-8").replace("\r\n", "\n")
        found = find_block(text)
        if found is None or found[2] != state.get("claude_block"):
            drift.append({"path": "CLAUDE.md", "detail": "owned instruction block differs"})
    except (OSError, UnicodeDecodeError, InstallError) as exc:
        drift.append({"path": "CLAUDE.md", "detail": str(exc)})
    graft = state.get("graft_server")
    if graft is not None:
        try:
            mcp = read_optional_json(target / ".mcp.json", "MCP configuration")
            exists, actual = get_path(mcp, ("mcpServers", "graft"))
            if not exists or actual != graft:
                drift.append({"path": ".mcp.json:mcpServers.graft", "detail": "owned server entry differs"})
        except InstallError as exc:
            drift.append({"path": ".mcp.json", "detail": str(exc)})
    return {"schema_version": SCHEMA_VERSION, "result": "DRIFT" if drift else "INSTALLED",
            "target": str(target), "installed": True, "bundle_version": state.get("bundle_version"),
            "last_backup": state.get("last_backup"), "drift": drift}


def load_backup(target: Path, backup_id: str | None) -> tuple[Path, dict]:
    root = target_path(target, BACKUP_ROOT_REL)
    if backup_id is None:
        state, _ = load_state(target)
        backup_id = (state or {}).get("last_backup")
        if not backup_id:
            raise InstallError("no current installer state names a backup; pass --backup ID")
    if Path(backup_id).name != backup_id:
        raise InstallError("backup ID must be a directory name, not a path")
    backup = root / backup_id
    value = load_json(backup / "metadata.json", "backup metadata")
    if value.get("schema_version") != SCHEMA_VERSION or value.get("backup_id") != backup_id:
        raise InstallError(f"unsupported or mismatched backup metadata: {backup}")
    return backup, value


def rollback_plan(target: Path, backup_id: str | None) -> tuple[dict, Path, dict, dict[PurePosixPath, bytes | None]]:
    target = target.resolve()
    backup, metadata = load_backup(target, backup_id)
    conflicts = []
    restores: dict[PurePosixPath, bytes | None] = {}
    raw_paths = {safe_relative(op["path"]) for op in metadata.get("raw_ops", [])}
    for relative in raw_paths:
        op = next(item for item in metadata["raw_ops"] if item["path"] == relative.as_posix())
        path = target_path(target, relative)
        actual = sha256_bytes(path.read_bytes()) if path.is_file() else None
        if actual != op.get("after_sha256"):
            conflicts.append({"kind": "file", "path": relative.as_posix(),
                              "detail": f"owned value changed after operation; expected {op.get('after_sha256')}, found {actual}"})
        pre = metadata["preimages"][relative.as_posix()]
        restores[relative] = ((backup / "files" / Path(*relative.parts)).read_bytes()
                              if pre["existed"] else None)

    json_results: dict[PurePosixPath, dict] = {}
    for name, ops in metadata.get("json_ops", {}).items():
        relative = safe_relative(name)
        path = target_path(target, relative)
        try:
            value = read_optional_json(path, name)
        except InstallError as exc:
            conflicts.append({"kind": "configuration", "path": name, "detail": str(exc)})
            continue
        updated = copy.deepcopy(value)
        for op in reversed(ops):
            json_path = tuple(op["path"])
            if op["kind"] == "value":
                exists, actual = get_path(updated, json_path)
                expected = op["after"]
                if exists != expected["exists"] or (exists and actual != expected["value"]):
                    conflicts.append({"kind": "configuration", "path": f"{name}:{'.'.join(json_path)}",
                                      "detail": "owned value changed after operation"})
                    continue
                before = op["before"]
                if before["exists"]:
                    set_path(updated, json_path, before["value"])
                else:
                    delete_path(updated, json_path)
            elif op["kind"] == "list":
                exists, actual = get_path(updated, json_path)
                after_exists = op.get("after_exists", True)
                if exists != after_exists or (exists and not isinstance(actual, list)):
                    conflicts.append({"kind": "configuration", "path": f"{name}:{'.'.join(json_path)}",
                                      "detail": "owned array changed after operation"})
                    continue
                actual_items = actual if exists else []
                missing_added = [item for item in op["added"] if item not in actual_items]
                present_removed = [item for item in op["removed"] if item in actual_items]
                if missing_added or present_removed:
                    conflicts.append({"kind": "configuration", "path": f"{name}:{'.'.join(json_path)}",
                                      "detail": "owned array entries changed after operation"})
                    continue
                restored = [item for item in actual_items if item not in op["added"]] + copy.deepcopy(op["removed"])
                if restored or op.get("before_exists", True):
                    set_path(updated, json_path, restored)
                else:
                    delete_path(updated, json_path)
        json_results[relative] = updated

    claude_op = metadata.get("claude_op")
    claude_result: bytes | None | object = _NO_WRITE
    if claude_op:
        path = target / "CLAUDE.md"
        try:
            text = path.read_text(encoding="utf-8").replace("\r\n", "\n") if path.exists() else ""
            found = find_block(text)
        except (OSError, UnicodeDecodeError, InstallError) as exc:
            conflicts.append({"kind": "instructions", "path": "CLAUDE.md", "detail": str(exc)})
        else:
            after = claude_op.get("after_block")
            if after is None:
                if found is not None:
                    conflicts.append({"kind": "instructions", "path": "CLAUDE.md",
                                      "detail": "owned block was expected to be absent after operation"})
                else:
                    before = claude_op.get("before_block")
                    pre = metadata["preimages"].get("CLAUDE.md", {"existed": False})
                    if before and not path.exists() and pre["existed"]:
                        claude_result = (backup / "files" / "CLAUDE.md").read_bytes()
                    elif before:
                        base = text.rstrip()
                        claude_result = (base + ("\n\n" if base else "") + before + "\n").encode("utf-8")
                    else:
                        claude_result = path.read_bytes() if path.exists() else None
            elif found is None or found[2] != after:
                conflicts.append({"kind": "instructions", "path": "CLAUDE.md",
                                  "detail": "owned block changed after operation"})
            else:
                start, end, _ = found
                before = claude_op.get("before_block") or ""
                restored = re.sub(r"\n{3,}", "\n\n", (text[:start] + before + text[end:])).rstrip() + "\n"
                if not claude_op.get("file_existed_before") and restored.strip() == "# CLAUDE.md":
                    claude_result = None
                else:
                    claude_result = restored.encode("utf-8")

    state_path = target_path(target, STATE_REL)
    actual_state = sha256_bytes(state_path.read_bytes()) if state_path.is_file() else None
    if actual_state != metadata.get("state_after_sha256"):
        conflicts.append({"kind": "metadata", "path": STATE_REL.as_posix(),
                          "detail": "installer state changed after operation"})
    pre_state = metadata["preimages"].get(STATE_REL.as_posix(), {"existed": False})
    state_restore = ((backup / "files" / Path(*STATE_REL.parts)).read_bytes() if pre_state["existed"] else None)
    public = {"schema_version": SCHEMA_VERSION, "action": "rollback",
              "result": "CONFLICT" if conflicts else "READY", "target": str(target),
              "backup_location": str(backup), "changes": [], "conflicts": conflicts}
    payload = {"raw": restores, "json": json_results, "claude": claude_result, "state": state_restore}
    return public, backup, metadata, payload


def commit_rollback(public: dict, target: Path, payload: dict) -> dict:
    if public["conflicts"]:
        raise InstallError("refusing to roll back with conflicts")
    for relative, value in payload["raw"].items():
        path = target_path(target, relative)
        if value is None:
            path.unlink(missing_ok=True)
        else:
            atomic_write(path, value)
    for relative, value in payload["json"].items():
        atomic_write(target_path(target, relative), json_bytes(value))
    if payload["claude"] is not _NO_WRITE:
        path = target / "CLAUDE.md"
        if payload["claude"] is None:
            path.unlink(missing_ok=True)
        else:
            atomic_write(path, payload["claude"])
    state_path = target_path(target, STATE_REL)
    if payload["state"] is None:
        state_path.unlink(missing_ok=True)
    else:
        atomic_write(state_path, payload["state"])
    result = copy.deepcopy(public)
    result["result"] = "ROLLED_BACK"
    return result


def print_result(value: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(value, indent=2, sort_keys=True))
        return
    print(f"{value['result']}: {value.get('action', 'status')} {value['target']}")
    if value.get("bundle_version"):
        print(f"Bundle: {value['bundle_version']}")
    if value.get("backup_location"):
        print(f"Backup: {value['backup_location']}")
    for item in value.get("changes", []):
        print(f"  {item['status']:8} {item['path']}: {item['detail']}")
    for item in value.get("conflicts", value.get("drift", [])):
        print(f"  CONFLICT {item['path']}: {item['detail']}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=("plan", "apply", "status", "uninstall", "rollback"))
    parser.add_argument("--target", type=Path, required=True, help="consumer project root")
    parser.add_argument("--bundle", type=Path, default=bundle_default(), help="bundle directory")
    parser.add_argument("--graft-command", help="portable command or absolute executable for mcpServers.graft")
    parser.add_argument("--graft-arg", action="append", default=[], help="one Graft command argument; repeat as needed")
    parser.add_argument("--backup", help="backup ID for rollback; defaults to current state's last backup")
    parser.add_argument("--json", action="store_true", help="stable machine-readable output")
    args = parser.parse_args(argv)
    try:
        if args.action == "status":
            result = status(args.target)
        elif args.action in ("plan", "apply"):
            tx = plan_apply(args.bundle, args.target, args.graft_command, args.graft_arg)
            result = tx.public() if args.action == "plan" or tx.conflicts else commit(tx)
        elif args.action == "uninstall":
            tx = plan_uninstall(args.target)
            result = tx.public() if tx.conflicts else commit(tx)
        else:
            result, _, _, payload = rollback_plan(args.target.resolve(), args.backup)
            if not result["conflicts"]:
                result = commit_rollback(result, args.target.resolve(), payload)
        print_result(result, args.json)
        return 1 if result["result"] in ("CONFLICT", "INVALID") else 0
    except InstallError as exc:
        result = {"schema_version": SCHEMA_VERSION, "action": args.action, "result": "ERROR",
                  "target": str(args.target.resolve()), "changes": [], "conflicts": [{"path": "", "detail": str(exc)}]}
        print_result(result, args.json)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
