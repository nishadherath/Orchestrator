#!/usr/bin/env python3
"""Provider-free, versioned multi-file WSL actor staging and collection.

Only a root-owned source package under ``seed`` may be staged. Every source
file and every editable path is frozen in the caller's manifest. Collection
requires a stop receipt written by the root-owned namespace launcher and
returns a new private snapshot; it never mutates the source package.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from pathlib import Path

BASE = Path("/var/lib/orchestrator-worker-n4")
ACTORS = BASE / "actors"
SEEDS = BASE / "seed"
MANIFESTS = BASE / "qualification-manifests"
OUTPUTS = BASE / "qualification-collected"
NAME = re.compile(r"q1-[0-9a-f]{32}\Z")
PART = re.compile(r"[A-Za-z0-9_.-]+\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
MAX_FILES = 200
MAX_FILE_BYTES = 1_000_000
MAX_TOTAL_BYTES = 5_000_000
RESERVED = {".home", ".cache", ".scratch", "graft", ".gitignore"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def path_parts(value: str) -> tuple[str, ...]:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/"):
        raise ValueError("unsafe manifest path")
    parts = tuple(value.split("/"))
    if (len(parts) > 12 or any(part in {"", ".", ".."} or not PART.fullmatch(part)
                             for part in parts) or parts[0] in RESERVED):
        raise ValueError("unsafe manifest path")
    return parts


def safe_tree(root: Path, *, private: bool) -> dict[str, Path]:
    """Inventory all public files without following symlinks or special files."""
    if root.is_symlink() or not root.is_dir():
        raise ValueError("package root is not a real directory")
    if private and (root.stat().st_uid != 0 or root.stat().st_mode & 0o077):
        raise ValueError("source package must be root-owned and private")
    found: dict[str, Path] = {}
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            child = Path(parent) / name
            relative = child.relative_to(root).as_posix()
            path_parts(relative)
            info = child.lstat()
            if stat.S_ISLNK(info.st_mode) or not (
                    stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
                raise ValueError(f"unsafe package entry: {relative}")
            if stat.S_ISDIR(info.st_mode):
                if private and (info.st_uid != 0 or info.st_mode & 0o022):
                    raise ValueError(f"unsafe source directory: {relative}")
            else:
                if info.st_nlink != 1 or info.st_size > MAX_FILE_BYTES:
                    raise ValueError(f"unsafe package file: {relative}")
                found[relative] = child
    if len(found) > MAX_FILES:
        raise ValueError("too many package files")
    return found


def actor_tree(root: Path) -> dict[str, Path]:
    """Inventory staged public files, excluding only fixed private work areas."""
    found: dict[str, Path] = {}
    for parent, dirs, files in os.walk(root, followlinks=False):
        for directory in list(dirs):
            child = Path(parent) / directory
            relative = child.relative_to(root).as_posix()
            if child.parent == root and directory in RESERVED - {".gitignore"}:
                dirs.remove(directory)
                continue
            path_parts(relative)
            info = child.lstat()
            if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
                raise ValueError(f"unsafe actor directory: {relative}")
        for filename in files:
            child = Path(parent) / filename
            relative = child.relative_to(root).as_posix()
            if relative == ".gitignore":
                if (child.is_symlink() or child.read_text(encoding="utf-8") !=
                        "graft/\n.cache/\n.home/\n.scratch/\n"):
                    raise ValueError("actor Graft exclusion changed")
                continue
            path_parts(relative)
            info = child.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError(f"unsafe actor file: {relative}")
            found[relative] = child
    return found


def load_spec(path: Path) -> dict:
    if (path.is_symlink() or not path.is_file() or path.stat().st_uid != 0
            or path.stat().st_mode & 0o077 or path.stat().st_size > 100_000):
        raise ValueError("manifest must be a private root-owned regular file")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or set(value) != {"schema_version", "files"} or value["schema_version"] != 1:
        raise ValueError("unsupported manifest schema")
    rows = value["files"]
    if not isinstance(rows, list) or not 2 <= len(rows) <= MAX_FILES:
        raise ValueError("manifest file count is invalid")
    paths: set[str] = set()
    editable = 0
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "sha256", "editable"}:
            raise ValueError("invalid manifest entry")
        path_parts(row["path"])
        if row["path"] in paths or not isinstance(row["sha256"], str) or not SHA.fullmatch(row["sha256"]):
            raise ValueError("duplicate path or invalid digest")
        if type(row["editable"]) is not bool:
            raise ValueError("editable must be boolean")
        paths.add(row["path"])
        editable += row["editable"]
    if not 2 <= editable <= 8:
        raise ValueError("Q1 requires two to eight existing editable files")
    return value


def record_path(name: str) -> Path:
    if not NAME.fullmatch(name):
        raise ValueError("invalid Q1 actor name")
    return MANIFESTS / f"{name}.json"


def load_record(name: str) -> dict:
    path = record_path(name)
    if path.is_symlink() or path.stat().st_uid != 0 or path.stat().st_mode & 0o077:
        raise ValueError("Q1 record is not root-owned and private")
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("schema_version") != 1 or record.get("actor_root") != str(ACTORS / name):
        raise ValueError("Q1 record identity mismatch")
    if digest(canonical({k: v for k, v in record.items() if k != "record_sha256"})) != record.get("record_sha256"):
        raise ValueError("Q1 record digest mismatch")
    return record


def stage(source: Path, manifest: Path, name: str) -> dict:
    if os.geteuid() != 0:
        raise ValueError("WSL root required")
    record_path(name)
    if (source.is_symlink() or source.resolve().parent != SEEDS.resolve()
            or source.stat().st_uid != 0):
        raise ValueError("source must be a root-owned seed package")
    if ACTORS.is_symlink() or ACTORS.stat().st_uid != 0:
        raise ValueError("actor parent is unsafe")
    spec = load_spec(manifest)
    files = safe_tree(source, private=True)
    if set(files) != {row["path"] for row in spec["files"]}:
        raise ValueError("manifest must enumerate the whole source package")
    payload: dict[str, bytes] = {}
    for row in spec["files"]:
        data = files[row["path"]].read_bytes()
        if digest(data) != row["sha256"]:
            raise ValueError(f"source digest mismatch: {row['path']}")
        payload[row["path"]] = data
    if sum(map(len, payload.values())) > MAX_TOTAL_BYTES:
        raise ValueError("source package exceeds Q1 size limit")
    MANIFESTS.mkdir(mode=0o700, exist_ok=True)
    OUTPUTS.mkdir(mode=0o700, exist_ok=True)
    if any(root.is_symlink() or root.stat().st_uid != 0 or root.stat().st_mode & 0o077
           for root in (MANIFESTS, OUTPUTS)):
        raise ValueError("Q1 private root is unsafe")
    actor = ACTORS / name
    actor.mkdir(mode=0o755)
    try:
        for row in spec["files"]:
            target = actor.joinpath(*path_parts(row["path"]))
            target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(payload[row["path"]])
            target.chmod(0o644)
            if row["editable"]:
                os.chown(target, 65534, 65534)
        (actor / ".gitignore").write_text("graft/\n.cache/\n.home/\n.scratch/\n", encoding="utf-8")
        (actor / ".gitignore").chmod(0o644)
        for folder in (".home", ".cache", ".scratch", "graft"):
            directory = actor / folder
            directory.mkdir(mode=0o700)
            os.chown(directory, 65534, 65534)
        record = {"schema_version": 1, "actor_root": str(actor),
                  "source_root": str(source.resolve()), "spec": spec,
                  "spec_sha256": digest(canonical(spec))}
        record["record_sha256"] = digest(canonical(record))
        with record_path(name).open("x", encoding="utf-8") as stream:
            os.chmod(stream.fileno(), 0o600)
            json.dump(record, stream, sort_keys=True)
            stream.write("\n")
        return {"actor_root": str(actor), "spec_sha256": record["spec_sha256"],
                "record_sha256": record["record_sha256"]}
    except Exception:
        shutil.rmtree(actor)
        raise


def preflight(name: str, actor: Path) -> dict:
    record = load_record(name)
    if actor.is_symlink() or str(actor.resolve()) != record["actor_root"]:
        raise ValueError("actor path differs from Q1 record")
    if actor.stat().st_uid != 0 or actor.stat().st_mode & 0o022:
        raise ValueError("actor root is writable by non-root")
    expected = {row["path"] for row in record["spec"]["files"]}
    if set(actor_tree(actor)) != expected:
        raise ValueError("actor file inventory changed")
    for row in record["spec"]["files"]:
        path = actor.joinpath(*path_parts(row["path"]))
        if (path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1
                or path.stat().st_uid != (65534 if row["editable"] else 0)):
            raise ValueError(f"actor file identity changed: {row['path']}")
    return record


def launch_event(name: str, action: str, status: int | None = None) -> dict:
    if os.geteuid() != 0 or action not in {"start", "stop"}:
        raise ValueError("root and valid launch action required")
    record = preflight(name, ACTORS / name)
    path = MANIFESTS / f"{name}.{action}.json"
    if action == "stop" and (not (MANIFESTS / f"{name}.start.json").is_file()
                             or type(status) is not int or not 0 <= status <= 255):
        raise ValueError("stop requires a started actor and exit status")
    value = {"actor_root": record["actor_root"],
             "record_sha256": record["record_sha256"], "action": action}
    if action == "stop":
        value["exit_status"] = status
    with path.open("x", encoding="utf-8") as stream:
        os.chmod(stream.fileno(), 0o600)
        json.dump(value, stream, sort_keys=True)
        stream.write("\n")
    return value


def collect(name: str, source: Path) -> dict:
    if os.geteuid() != 0:
        raise ValueError("WSL root required")
    record = preflight(name, ACTORS / name)
    stop_path = MANIFESTS / f"{name}.stop.json"
    if stop_path.is_symlink() or stop_path.stat().st_uid != 0 or stop_path.stat().st_mode & 0o077:
        raise ValueError("root-owned writer stop receipt missing")
    stop = json.loads(stop_path.read_text(encoding="utf-8"))
    if (stop.get("record_sha256") != record["record_sha256"]
            or stop.get("actor_root") != record["actor_root"]
            or stop.get("action") != "stop"
            or type(stop.get("exit_status")) is not int):
        raise ValueError("writer stop receipt is for another actor")
    if source.is_symlink() or str(source.resolve()) != record["source_root"]:
        raise ValueError("source identity mismatch")
    source_files = safe_tree(source, private=True)
    actor = ACTORS / name
    actor_files = actor_tree(actor)
    expected = {row["path"] for row in record["spec"]["files"]}
    if set(source_files) != expected or set(actor_files) != expected:
        raise ValueError("source or actor file inventory drifted")
    after: dict[str, str] = {}
    payload: dict[str, bytes] = {}
    changed = []
    for row in record["spec"]["files"]:
        name_in_tree = row["path"]
        if digest(source_files[name_in_tree].read_bytes()) != row["sha256"]:
            raise ValueError(f"source changed during actor run: {name_in_tree}")
        target = actor_files[name_in_tree]
        if target.is_symlink() or not target.is_file() or target.stat().st_nlink != 1:
            raise ValueError(f"actor file identity changed: {name_in_tree}")
        data = target.read_bytes()
        if len(data) > MAX_FILE_BYTES:
            raise ValueError(f"actor file is too large: {name_in_tree}")
        after[name_in_tree] = digest(data)
        if not row["editable"] and after[name_in_tree] != row["sha256"]:
            raise ValueError(f"protected actor file changed: {name_in_tree}")
        if row["editable"] and after[name_in_tree] != row["sha256"]:
            changed.append(name_in_tree)
        payload[name_in_tree] = data
    if sum(map(len, payload.values())) > MAX_TOTAL_BYTES:
        raise ValueError("collected package exceeds Q1 size limit")
    if (OUTPUTS.is_symlink() or OUTPUTS.stat().st_uid != 0 or OUTPUTS.stat().st_mode & 0o077
            or (OUTPUTS / name).exists()):
        raise ValueError("private collection root is unsafe or already used")
    temporary = Path(tempfile.mkdtemp(prefix=f".{name}-", dir=OUTPUTS))
    try:
        for relative, data in payload.items():
            path = temporary.joinpath(*path_parts(relative))
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            path.write_bytes(data)
            path.chmod(0o600)
        temporary.rename(OUTPUTS / name)
    except Exception:
        shutil.rmtree(temporary)
        raise
    return {"output_root": str(OUTPUTS / name), "record_sha256": record["record_sha256"],
            "spec_sha256": record["spec_sha256"], "changed_paths": sorted(changed),
            "after_sha256": after, "writer_exit_status": stop["exit_status"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    staged = sub.add_parser("stage")
    staged.add_argument("--source", type=Path, required=True)
    staged.add_argument("--manifest", type=Path, required=True)
    staged.add_argument("--name", required=True)
    for command in ("preflight", "start", "stop"):
        child = sub.add_parser(command)
        child.add_argument("--name", required=True)
        if command == "stop":
            child.add_argument("--status", type=int, required=True)
    collected = sub.add_parser("collect")
    collected.add_argument("--source", type=Path, required=True)
    collected.add_argument("--name", required=True)
    args = parser.parse_args()
    try:
        if args.command == "stage":
            result = stage(args.source, args.manifest, args.name)
        elif args.command == "preflight":
            result = preflight(args.name, ACTORS / args.name)
        elif args.command in {"start", "stop"}:
            result = launch_event(args.name, args.command, getattr(args, "status", None))
        else:
            result = collect(args.name, args.source)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"Q1 boundary rejected: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
