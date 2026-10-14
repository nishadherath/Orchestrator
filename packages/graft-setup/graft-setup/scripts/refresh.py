"""Build an explicit structural scope, verify it, then publish with a preserved backup."""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
import uuid
from pathlib import Path

from graft_common import GraftError, arguments, capabilities, check, graph_summary, launcher, local_path, no_links, repo_path, report, run


def ensure_ignored(root: Path, relative: str) -> None:
    path = local_path(root, ".gitignore")
    if path.is_symlink():
        raise GraftError("Inspect the symlinked .gitignore before changing cache ignore rules.")
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    line = f"/{relative}/"
    if line in text.splitlines():
        return
    tmp = root / (".graft-ignore-" + uuid.uuid4().hex)
    try:
        tmp.write_bytes((text.rstrip() + "\n\n# Local Graft cache and repair state.\n" + line + "\n").encode("utf-8"))
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def main() -> int:
    parser = arguments(__doc__)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--only-dir", action="append", help="Explicit relative source prefix; repeat as needed")
    scope.add_argument("--whole-repo", action="store_true", help="Explicitly index the whole project")
    parser.add_argument("--include-dir", action="append", default=[], help="Re-admit a built-in skipped directory name")
    parser.add_argument("--structured", action="store_true", help="Opt in to Markdown/JSON/YAML/TOML/INI indexing")
    parser.add_argument("--clean", action="store_true", help="Build without reusing the old cache or semantic tier")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the plan without changing project files")
    args = parser.parse_args()
    stage = lock = backup = cache = None
    owns_lock = False
    try:
        if args.timeout <= 0:
            raise GraftError("Timeout must be positive.")
        root = repo_path(args.repo)
        cache = local_path(root, args.cache)
        state = local_path(root, ".graft")
        if state.is_symlink() or state.is_junction():
            raise GraftError("Repair state must not be a symlink or junction.")
        if cache == state or cache.is_relative_to(state / "backups"):
            raise GraftError("Select a cache outside .graft itself and its backup directory.")
        # Existing arbitrary source directories must never be moved as caches.
        if cache.exists() and any(cache.iterdir()) and not (cache / ".graph/wiring.json").is_file():
            raise GraftError("Selected non-empty directory is not a Graft cache; refusing to replace it.")
        no_links(cache)
        if (cache / ".cache/.sync.lock").exists():
            raise GraftError("A Graft refresh lock exists. Stop automatic client refresh and inspect its owner before retrying.")
        if args.whole_repo and cache.exists() and not cache.relative_to(root).parts[0].startswith("."):
            if not (root / ".git").exists() or shutil.which("git") is None:
                raise GraftError("Whole-repo replacement needs Git visibility or a hidden cache; use --cache .graft/core or explicit source scopes.")
        prefixes = []
        for value in args.only_dir or []:
            path = local_path(root, value)
            if not path.exists() or path == cache or path.is_relative_to(cache) or cache.is_relative_to(path) or path.is_relative_to(state):
                raise GraftError("Source scope must exist and must not select a cache or repair state.")
            prefixes.append(path.relative_to(root).as_posix())
        for name in args.include_dir:
            if not name or name.startswith(".") or any(x in name for x in ("/", "\\", ":")):
                raise GraftError("--include-dir takes a bare non-dot directory name.")
        command = launcher(args.launcher_json)
        info = capabilities(command, root, args.timeout)
        if args.structured and not info["supports_structured"]:
            raise GraftError("This launcher does not support --structured.")
        value = {"ok": True, "repo": str(root), "cache": str(cache), "scope": prefixes,
                 "whole_repo": args.whole_repo, "clean": args.clean, "capabilities": info,
                 "provider_calls": 0, "dry_run": args.dry_run}
        if args.dry_run:
            report(value, args.output)
            return 0
        state.mkdir(exist_ok=True)
        ensure_ignored(root, ".graft")
        ensure_ignored(root, cache.relative_to(root).as_posix())
        lock = state / "skill-refresh.lock"
        try:
            with lock.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps({"pid": os.getpid(), "cache": str(cache)}))
            owns_lock = True
        except FileExistsError as exc:
            raise GraftError("Another skill refresh holds .graft/skill-refresh.lock. Check its PID before removing a stale lock.") from exc
        stage = state / ("staging-" + uuid.uuid4().hex)
        if cache.exists() and not args.clean:
            shutil.copytree(cache, stage, symlinks=True)
        else:
            stage.mkdir()
            # This stamp records host choices, not semantic content. Retain it
            # during a clean build so MCP boot does not revert to global defaults.
            stamp = cache / ".cache/wiring-stamp.json"
            if stamp.is_file():
                (stage / ".cache").mkdir()
                shutil.copy2(stamp, stage / ".cache/wiring-stamp.json")
        # Old extractor identities can carry a different scope. The staged
        # build must produce its own fingerprint, not silently reuse another.
        for old_print in (stage / ".cache").glob("fingerprint.*.json"):
            old_print.unlink()
        build = [*command, "--dir", str(stage), "build", "--no-gitignore", "--no-ignore"]
        for prefix in prefixes:
            build.extend(["--only-dir", prefix])
        for name in args.include_dir:
            build.extend(["--include-dir", name])
        if args.structured:
            build.append("--structured")
        start = time.monotonic()
        result = run([*build, str(root)], root, args.timeout)
        if result.returncode:
            raise GraftError("Build failed; active cache is unchanged. Check runtime/parser and cache-write permissions.")
        value["graph"] = graph_summary(stage, root)
        if not value["graph"].get("files"):
            raise GraftError("Build produced no indexed files. Check source scope, parsers and Git ignore rules.")
        built = json.loads((stage / ".graph/wiring.json").read_text(encoding="utf-8"))
        if prefixes and any(not any(n["path"] == p or n["path"].startswith(p + "/")
                                    for p in prefixes) for n in built["nodes"]):
            raise GraftError("Build returned source outside the requested prefixes; active cache is unchanged.")
        if any(local_path(root, n["path"]).is_relative_to(cache) for n in built["nodes"]):
            raise GraftError("Build indexed the old cache as source. Use explicit source prefixes or a hidden cache.")
        if not value["graph"]["fingerprints"] or any(p["only_dirs"] != prefixes for p in value["graph"]["fingerprints"]):
            raise GraftError("Build fingerprint disagrees with the explicit scope; active cache is unchanged.")
        value["freshness"] = check(command, root, stage, args.timeout, info["identity"])
        if not value["freshness"]["structural_fresh"]:
            raise GraftError("Staged structure is stale; active cache is unchanged. Resolve source drift before retrying.")
        backup = None
        if (cache / ".cache/.sync.lock").exists():
            raise GraftError("Graft started a concurrent refresh; staged build will not replace its active cache.")
        if cache.exists():
            backups = local_path(root, ".graft/backups")
            if backups.is_symlink() or backups.is_junction():
                raise GraftError("Backup directory must not be a symlink or junction.")
            backups.mkdir(exist_ok=True)
            backup = backups / (cache.name + "-" + time.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8])
            cache.rename(backup)
        try:
            cache.parent.mkdir(parents=True, exist_ok=True)
            stage.rename(cache)
            stage = None
        except OSError:
            if backup is not None:
                backup.rename(cache)
            raise
        value["backup"] = str(backup) if backup else None
        value["elapsed_seconds"] = round(time.monotonic() - start, 3)
        report(value, args.output)
        return 0
    except (GraftError, OSError) as exc:
        # Filesystem failures are separate from MCP protocol timeouts. Never
        # weaken freshness or delete the old cache to make a build appear green.
        message = exc if isinstance(exc, GraftError) else GraftError(
            "Filesystem operation failed. Active cache/backup is preserved; inspect permissions and use a normal host shell if atomic renames are blocked.")
        report({"ok": False, "error": str(message), "cache": str(cache) if cache else None,
                "backup": str(backup) if backup else None,
                "staging": str(stage) if stage else None}, args.output)
        return 1
    finally:
        if stage is not None and stage.exists():
            # Only this run's UUID staging directory is removed; never a user cache.
            try:
                if stage.resolve().is_relative_to(root) and stage.parent == root / ".graft" and stage.name.startswith("staging-"):
                    shutil.rmtree(stage)
                else:
                    print("Staging cleanup refused: resolved path no longer belongs to this project.", file=sys.stderr)
            except OSError:
                # Preserve failed staging for inspection when the host blocks cleanup.
                pass
        if owns_lock and lock is not None:
            try:
                lock.unlink(missing_ok=True)
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
