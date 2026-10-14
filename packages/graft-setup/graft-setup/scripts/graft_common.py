"""Shared local-only Graft helpers. Apache-2.0; see the packaged LICENSE."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import time
from pathlib import Path, PurePosixPath

TESTED_VERSION = "0.21.1"
TOOLS = {"graft_check_freshness", "graft_find_code", "graft_find_all",
         "graft_file_api", "graft_trace_calls", "graft_repo_map"}


class GraftError(RuntimeError):
    """An actionable failure without raw provider or process output."""


def repo_path(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    if not root.is_dir() or root == Path(root.anchor) or root == Path.home().resolve():
        raise GraftError("Select a project directory, not a filesystem root or home directory.")
    return root


def local_path(root: Path, value: str) -> Path:
    posix = PurePosixPath(value.replace("\\", "/"))
    if posix.is_absolute() or not posix.parts or any(p in {"..", "."} or ":" in p for p in posix.parts):
        raise GraftError("Paths must be non-empty, relative to the project, with no parent traversal.")
    path = root.joinpath(*posix.parts)
    resolved = path.resolve()
    if not resolved.is_relative_to(root) or resolved == root:
        raise GraftError("The selected path escapes the project or selects its root.")
    return path


def no_links(path: Path) -> None:
    candidates = [path, *path.rglob("*")] if path.exists() else [path]
    if any(p.is_symlink() or p.is_junction() for p in candidates):
        raise GraftError("Cache contains a symlink or junction; inspect it before replacing the cache.")


def launcher(value: str | None = None) -> list[str]:
    if value:
        try:
            command = json.loads(value)
        except json.JSONDecodeError as exc:
            raise GraftError("--launcher-json must be a JSON array of executable and arguments.") from exc
        if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
            raise GraftError("--launcher-json must contain non-empty strings.")
        if any(x.startswith(("--api-key", "--deep")) for x in command):
            raise GraftError("Pass only a Graft launcher, without provider or build options.")
    else:
        found = shutil.which("graft.cmd" if os.name == "nt" else "graft")
        if not found:
            raise GraftError("Graft was not found. Install @nanonets/graft or supply --launcher-json.")
        command = [found]
    # Execute npm's JavaScript entry directly on Windows. Avoid cmd.exe quoting
    # and the batch-file fallback that can interpret metacharacters in paths.
    if Path(command[0]).suffix.lower() in {".cmd", ".bat"}:
        shim = Path(command[0]).resolve()
        cli = shim.parent / "node_modules/@nanonets/graft/dist/cli.js"
        node = shim.parent / "node.exe"
        node_name = str(node) if node.is_file() else shutil.which("node")
        if not cli.is_file() or not node_name:
            raise GraftError("Cannot resolve npm shim. Supply --launcher-json '[\"node\",\"/path/to/graft/dist/cli.js\"]'.")
        command = [node_name, str(cli), *command[1:]]
    return command


def child_env(*, refresh: bool = False, cache: Path | None = None) -> dict[str, str]:
    env = dict(os.environ)
    for key in ("GRAFT_API_KEY", "OPENROUTER_API_KEY", "GRAFT_DIR", "GRAFT_NO_REFRESH"):
        env.pop(key, None)
    env["DO_NOT_TRACK"] = "1"
    # Existing empty values also keep dotenv from restoring these overrides.
    env["GRAFT_API_KEY"] = ""
    env["OPENROUTER_API_KEY"] = ""
    env["GRAFT_DIR"] = str(cache) if cache else ""
    env["GRAFT_NO_REFRESH"] = "0" if refresh else "1"
    return env


def run(command: list[str], root: Path, timeout: float) -> subprocess.CompletedProcess[str]:
    try:
        cache = Path(command[command.index("--dir") + 1]) if "--dir" in command else None
        return subprocess.run(command, cwd=root, env=child_env(cache=cache), capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=timeout,
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    except subprocess.TimeoutExpired as exc:
        raise GraftError("Command timed out. Measure scope and choose an explicit larger timeout if justified.") from exc
    except OSError as exc:
        raise GraftError("Launcher failed to start. Check the executable, runtime and host permissions.") from exc


def capabilities(command: list[str], root: Path, timeout: float) -> dict:
    version = run([*command, "--version"], root, timeout)
    help_result = run([*command, "build", "--help"], root, timeout)
    if version.returncode or help_result.returncode:
        raise GraftError("Graft version/help failed. Check the selected launcher before changing the index.")
    required = ("--only-dir", "--no-gitignore", "--no-ignore")
    if any(flag not in help_result.stdout for flag in required):
        raise GraftError("Installed Graft lacks required scope/ignore flags. Read its help; do not apply this repair blindly.")
    identity = launcher_identity(command)
    if identity["available"] and len(command) == 2 and Path(command[0]).name.lower() in {"node", "node.exe"}:
        probe = run([command[0], str(Path(__file__).with_name("runtime_probe.mjs")), identity["cli_path"]], root, timeout)
        try:
            identity["runtime_features"] = json.loads(probe.stdout) if probe.returncode == 0 else {"available": False}
        except ValueError:
            identity["runtime_features"] = {"available": False}
    return {"version": version.stdout.strip(), "tested_version": TESTED_VERSION,
            "version_matches": version.stdout.strip() == TESTED_VERSION,
            "supports_structured": "--structured" in help_result.stdout,
            "supports_documents": "--documents" in help_result.stdout,
            "supports_deep_documents": "--deep-documents" in help_result.stdout,
            "identity": identity}


def launcher_identity(command: list[str]) -> dict:
    """Record local entry-point bytes, without inferring release provenance."""
    # Do not traverse arbitrary wrapper/runtime arguments. A mounted path can
    # be slow to resolve, and only an actual Graft entry can establish identity.
    candidates = [Path(value) for value in command[1:] if Path(value).name == "cli.js"]
    if Path(command[0]).name in {"graft", "graft.js", "cli.js"}:
        candidates.append(Path(shutil.which(command[0]) or command[0]))
    for candidate in candidates:
        try:
            entry = candidate.resolve()
            if entry.name != "cli.js" or entry.parent.name != "dist" or not entry.is_file():
                continue
            package = entry.parent.parent / "package.json"
            raw = package.read_bytes()
            metadata = json.loads(raw)
            if not isinstance(metadata, dict) or metadata.get("name") != "@nanonets/graft":
                continue
            return {"available": True, "package_root": str(package.parent),
                    "package_version": metadata.get("version"), "cli_path": str(entry),
                    "cli_sha256": hashlib.sha256(entry.read_bytes()).hexdigest(),
                    "package_json_sha256": hashlib.sha256(raw).hexdigest()}
        except (OSError, ValueError):
            continue
    # Wrappers are valid launchers, but do not reveal their eventual package.
    return {"available": False,
            "reason": "Package entry is not directly resolvable; use an explicit Node/CLI launcher to record identity."}


def filesystem_info(root: Path, mount_table: Path = Path("/proc/self/mountinfo")) -> dict:
    """Observe Linux mount transport without invoking tools or changing it."""
    try:
        lines = mount_table.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {"available": False, "reason": "Linux mount information is unavailable on this host."}
    selected = None
    for line in lines:
        before, separator, after = line.partition(" - ")
        fields, filesystem = before.split(), after.split()
        if not separator or len(fields) < 6 or len(filesystem) < 2:
            continue
        decode = lambda value: re.sub(r"\\([0-7]{3})", lambda match: chr(int(match[1], 8)), value)
        target = Path(decode(fields[4]))
        if root.is_relative_to(target) and (selected is None or len(target.parts) > len(selected[0].parts)):
            selected = (target, filesystem[0], decode(filesystem[1]))
    if selected is None:
        return {"available": False, "reason": "No mount contains the selected project."}
    target, kind, source = selected
    return {"available": True, "mount_point": str(target), "filesystem_type": kind,
            "source": source, "host_shared": kind in {"9p", "virtiofs", "drvfs"}}


def startup_review_needed(root: Path, cache: Path, version: str) -> bool:
    """0.21.1 MCP boot may replay wiring, including prior global writes."""
    if version != TESTED_VERSION:
        return True
    stamp = cache / ".cache/wiring-stamp.json"
    if stamp.exists():
        try:
            if stamp.is_symlink() or not stamp.resolve().is_relative_to(cache.resolve()):
                return True
            return json.loads(stamp.read_text(encoding="utf-8")).get("version") != version
        except (OSError, ValueError, AttributeError):
            return True
    owned = (".claude/helpers/graft-hooks.cjs", ".adal/skills/graft/SKILL.md",
             ".cursor/rules/graft.mdc", ".grok/skills/graft/SKILL.md",
             ".kiro/steering/graft.md", ".windsurf/rules/graft.md")
    if any((root / value).exists() for value in owned):
        return True
    for value in ("AGENTS.md", "GEMINI.md", ".github/copilot-instructions.md"):
        path = root / value
        if path.is_file():
            if not path.resolve().is_relative_to(root):
                return True
            if "<!-- graft:start -->" in path.read_text(encoding="utf-8"):
                return True
    return False


def graph_summary(cache: Path, root: Path) -> dict:
    no_links(cache)
    wiring = cache / ".graph/wiring.json"
    if not wiring.is_file():
        return {"present": False, "semantic_manifest": (cache / "manifest.json").is_file()}
    try:
        graph = json.loads(wiring.read_text(encoding="utf-8"))
        nodes, edges = graph["nodes"], graph["edges"]
        if not isinstance(nodes, list) or not isinstance(edges, list):
            raise ValueError("invalid graph lists")
        files = {n["path"] for n in nodes if n["kind"] == "file"}
        validated = set()
        for node in nodes:
            if not isinstance(node.get("path"), str):
                raise ValueError("invalid node path")
            # Symbols share file paths. Resolve each distinct path once per
            # snapshot, preserving all escape checks without repeated host I/O.
            if node["path"] not in validated:
                local_path(root, node["path"])
                validated.add(node["path"])
        groups: dict[str, int] = {}
        states: dict[str, int] = {}
        for value in files:
            group = "/".join(value.split("/")[:2])
            groups[group] = groups.get(group, 0) + 1
        for node in nodes:
            state = node.get("summary_state", "unknown")
            states[state] = states.get(state, 0) + 1
        prints = []
        for path in sorted((cache / ".cache").glob("fingerprint.*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            prints.append({"name": path.name, "extractor": data.get("extractor"),
                           "only_dirs": data.get("onlyDirs", []), "files": len(data["files"])})
        return {"present": True, "files": len(files), "nodes": len(nodes), "edges": len(edges),
                "languages": graph.get("meta", {}).get("languages", []),
                "file_groups": groups, "summary_states": states, "fingerprints": prints,
                "semantic_manifest": (cache / "manifest.json").is_file()}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise GraftError("Graph or fingerprint is malformed. Preserve the cache and inspect before a clean rebuild.") from exc


def check(command: list[str], root: Path, cache: Path, timeout: float, identity: dict | None = None) -> dict:
    # A cache built by another extractor can lose its saved whitelist in old
    # Graft builds. Refuse that widening before launching an expensive check.
    features = (identity or {}).get("runtime_features", {})
    stamp = features.get("extractor_stamp")
    prints = list((cache / ".cache").glob("fingerprint.*.json"))
    if stamp and prints and not (cache / ".cache" / f"fingerprint.{stamp}.json").is_file() and not features.get("preserves_foreign_scope"):
        raise GraftError("Cache extractor differs from this launcher. This Graft build can discard saved scope. Refresh with the same explicit source prefixes and launcher, or apply the documented source repair; do not widen the check or increase its timeout.")
    start = time.monotonic()
    result = run([*command, "--dir", str(cache), "check", "--json", str(root)], root, timeout)
    try:
        data = json.loads(result.stdout)
        graph = data.get("graph")
        if not isinstance(graph, dict):
            raise ValueError("missing graph")
        if result.returncode not in (0, 1):
            raise ValueError("unexpected check exit")
        structural = not graph.get("missing") and all(
            isinstance(graph.get(k), list) and not graph[k] for k in ("added", "removed", "changed"))
        context = data.get("context", {})
        semantic = "absent" if context.get("missing") else ("fresh" if context.get("ok") else "stale")
        if result.returncode == 1 and structural and semantic != "stale" and not graph.get("stale"):
            raise ValueError("failed check without reported drift")
        return {"structural_fresh": structural, "semantic": semantic,
                "files_reused": graph.get("filesReused"), "files_parsed": graph.get("filesParsed"),
                "stale_summaries": len(graph.get("stale", [])), "pending_summaries": graph.get("pending"),
                "exit_code": result.returncode, "elapsed_seconds": round(time.monotonic() - start, 3)}
    except (ValueError, TypeError, AttributeError) as exc:
        raise GraftError("Freshness check returned no usable structural result. Check scope, launcher and cache.") from exc


def arguments(description: str) -> argparse.ArgumentParser:
    def positive_timeout(value: str) -> float:
        number = float(value)
        if not math.isfinite(number) or number <= 0:
            raise argparse.ArgumentTypeError("timeout must be finite and positive")
        return number
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--repo", required=True, help="Explicit project root")
    parser.add_argument("--cache", default="graft", help="Repository-relative cache path")
    parser.add_argument("--launcher-json", help="JSON executable/argument array; never a shell string")
    parser.add_argument("--timeout", type=positive_timeout, default=180, help="Per-command/request timeout in seconds")
    parser.add_argument("--output", type=Path, help="Optional JSON report destination")
    return parser


def report(value: dict, destination: Path | None) -> None:
    data = json.dumps(value, indent=2, ensure_ascii=True) + "\n"
    if destination:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data.encode("utf-8"))
    print(data, end="")


def failure(exc: Exception, destination: Path | None) -> int:
    report({"ok": False, "error": str(exc)}, destination)
    return 1
