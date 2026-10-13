"""Verify six Graft tools through a fresh process; optionally exercise source refresh."""
from __future__ import annotations

import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from graft_common import GraftError, TOOLS, arguments, capabilities, child_env, graph_summary, launcher, local_path, no_links, repo_path, report, startup_review_needed


class Client:
    """Bounded JSON-RPC requests with concurrent stderr draining."""

    def __init__(self, command: list[str], root: Path, cache: Path, refresh: bool):
        self.process = subprocess.Popen(command, cwd=root,
            env=child_env(refresh=refresh, cache=cache), stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", errors="replace", bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        self.events: queue.Queue = queue.Queue()
        self.ident = 0
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=self._drain, daemon=True).start()

    def _drain(self) -> None:
        while self.process.stderr.read(4096):
            pass

    def _read(self) -> None:
        while True:
            line = self.process.stdout.readline(5_000_001)
            if not line:
                self.events.put(None)
                return
            try:
                if len(line) > 5_000_000 or not line.endswith("\n"):
                    raise ValueError("oversized reply")
                self.events.put(json.loads(line))
            except (ValueError, TypeError):
                self.events.put({"invalid": True})
                return

    def send(self, message: dict) -> None:
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def call(self, method: str, params: dict, timeout: float) -> dict:
        self.ident += 1
        self.send({"jsonrpc": "2.0", "id": self.ident, "method": method, "params": params})
        end = time.monotonic() + timeout
        while True:
            remaining = end - time.monotonic()
            if remaining <= 0:
                raise GraftError("MCP request timed out. Inspect startup versus freshness latency separately.")
            try:
                response = self.events.get(timeout=remaining)
            except queue.Empty as exc:
                raise GraftError("MCP request timed out. Inspect startup versus freshness latency separately.") from exc
            if not isinstance(response, dict) or response.get("invalid"):
                raise GraftError("MCP process closed or emitted invalid JSON. Check the launcher and stdout protocol.")
            if response.get("id") == self.ident:
                if "error" in response or not isinstance(response.get("result"), dict):
                    raise GraftError("MCP returned a protocol error; check arguments and installed tool schemas.")
                return response["result"]

    def close(self) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            stream.close()


def structural_fresh(text: str) -> bool:
    if "graph check:" not in text:
        return False
    graph = text.split("graph check:", 1)[1]
    return graph.lstrip().startswith(("OK", "STALE")) and not re.search(r"^(?:changed|added|removed) \(", graph, re.MULTILINE)


def main() -> int:
    parser = arguments(__doc__)
    parser.add_argument("--file", required=True, help="Representative indexed source file")
    parser.add_argument("--symbol", required=True, help="Definition name in that file")
    parser.add_argument("--needle", required=True, help="Literal occurring in the selected definition")
    parser.add_argument("--exercise-refresh", metavar="DIR", help="Create/delete one temporary Python file in this indexed directory")
    parser.add_argument("--allow-startup-upkeep", action="store_true", help="Acknowledge reviewed Graft-managed wiring changes at MCP startup")
    args = parser.parse_args()
    client = created = None
    checks = []
    try:
        if args.timeout <= 0 or not args.needle or not args.symbol:
            raise GraftError("Timeout, needle and symbol must be non-empty/positive.")
        root = repo_path(args.repo)
        cache = local_path(root, args.cache)
        no_links(cache)
        command = launcher(args.launcher_json)
        info = capabilities(command, root, args.timeout)
        if startup_review_needed(root, cache, info["version"]) and not args.allow_startup_upkeep:
            raise GraftError("MCP startup may replay existing host wiring, including global entries. Review it first; --allow-startup-upkeep acknowledges that review.")
        source = local_path(root, args.file)
        if not source.is_file() or args.needle not in source.read_text(encoding="utf-8"):
            raise GraftError("Select an existing UTF-8 source file and a literal it contains.")
        before = graph_summary(cache, root)
        if not before["present"]:
            raise GraftError("No structural index. Run an explicitly scoped refresh first.")
        exercise = None
        if args.exercise_refresh:
            exercise = local_path(root, args.exercise_refresh)
            if not exercise.is_dir() or exercise == cache or exercise.is_relative_to(cache):
                raise GraftError("Refresh test needs an existing indexed source directory outside the cache.")
            rel = exercise.relative_to(root).as_posix()
            scopes = before["fingerprints"]
            if not scopes or any(p["only_dirs"] and not any(
                    rel == s or rel.startswith(s + "/") for s in p["only_dirs"]) for p in scopes):
                raise GraftError("Refresh-test directory is outside the fingerprint scope.")
        client = Client([*command, "--dir", str(cache), "mcp", str(root)],
                        root, cache, exercise is not None)

        def request(label, method, params, expected):
            start = time.monotonic()
            result = client.call(method, params, args.timeout)
            text = "\n".join(c.get("text", "") for c in result.get("content", []) if isinstance(c, dict))
            ok = not result.get("isError") and expected(result, text)
            checks.append({"name": label, "ok": bool(ok), "elapsed_seconds": round(time.monotonic() - start, 3)})
            if not ok:
                raise GraftError(f"MCP acceptance failed: {label}. Inspect scope, source spans and freshness.")
            return result, text

        def tool(label, name, params, expected):
            return request(label, "tools/call", {"name": name, "arguments": params}, expected)

        initialized, _ = request("initialize", "initialize", {"protocolVersion": "2024-11-05",
            "capabilities": {}, "clientInfo": {"name": "graft-setup-probe", "version": "1.0.0"}},
            lambda r, t: r.get("serverInfo", {}).get("name") == "graft")
        client.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        request("tools", "tools/list", {}, lambda r, t: TOOLS <= {x["name"] for x in r.get("tools", [])})
        tool("freshness", "graft_check_freshness", {}, lambda r, t: structural_fresh(t))
        relative = source.relative_to(root).as_posix()
        tool("source", "graft_find_code", {"query": args.needle, "in": relative, "limit": 1, "full": True},
             lambda r, t: relative in t and args.needle in t)
        _, api = tool("api", "graft_file_api", {"file": relative}, lambda r, t: args.symbol in t)
        line_count = len(source.read_text(encoding="utf-8").splitlines())
        spans = re.findall(r"L(\d+)-L(\d+)", api)
        if not spans or not all(1 <= int(a) <= int(b) <= line_count for a, b in spans):
            raise GraftError("File API returned an invalid source line span.")
        tool("literal", "graft_find_all", {"pattern": args.needle, "fixed": True, "in": relative},
             lambda r, t: relative in t and args.needle in t)
        tool("callers", "graft_trace_calls", {"symbol": args.symbol, "in": relative}, lambda r, t: args.symbol in t)
        tool("map", "graft_repo_map", {"max_dirs": 8}, lambda r, t: "repo map" in t)
        if exercise:
            marker = "graft_skill_probe_" + uuid.uuid4().hex
            created = exercise / (marker + ".py")
            with created.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(f"def {marker}():\n    return 'graft skill fresh source'\n")
            try:
                tool("detect_addition", "graft_check_freshness", {}, lambda r, t: created.name in t and not structural_fresh(t))
                tool("automatic_addition", "graft_find_code", {"query": marker, "in": created.relative_to(root).as_posix(), "full": True},
                     lambda r, t: "return 'graft skill fresh source'" in t)
            finally:
                created.unlink(missing_ok=True)
                tool("automatic_removal", "graft_find_code", {"query": marker, "in": exercise.relative_to(root).as_posix()},
                     lambda r, t: not r.get("isError"))
            after = graph_summary(cache, root)
            graph = json.loads((cache / ".graph/wiring.json").read_text(encoding="utf-8"))
            if any(n["path"] == created.relative_to(root).as_posix() for n in graph["nodes"]):
                raise GraftError("Temporary source is removed but its graph entry remains; refresh cleanup is incomplete.")
            if [p["only_dirs"] for p in before["fingerprints"]] != [p["only_dirs"] for p in after["fingerprints"]]:
                raise GraftError("Automatic refresh widened the recorded scope.")
            tool("final_freshness", "graft_check_freshness", {}, lambda r, t: structural_fresh(t))
        report({"ok": True, "server": initialized["serverInfo"], "checks": checks,
                "graph": graph_summary(cache, root), "provider_calls": 0,
                "automatic_refresh_exercised": exercise is not None}, args.output)
        return 0
    except (GraftError, OSError, ValueError, KeyError, TypeError) as exc:
        report({"ok": False, "checks": checks, "error": str(exc), "provider_calls": 0,
                "temporary_source": str(created) if created is not None else None}, args.output)
        return 1
    finally:
        if created is not None:
            try:
                created.unlink(missing_ok=True)
            except OSError:
                print("Cleanup failed for owned source file; see temporary_source in the report.", file=sys.stderr)
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
