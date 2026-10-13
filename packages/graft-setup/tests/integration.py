"""Real, provider-free Graft acceptance in isolated code and document layouts."""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
SCRIPTS = PACKAGE / "graft-setup/scripts"
sys.path.insert(0, str(SCRIPTS))
from graft_common import child_env, graph_summary, launcher


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--launcher-json")
    parser.add_argument("--parent", type=Path)
    parser.add_argument("--output", type=Path, default=PACKAGE / "integration-result.json")
    args = parser.parse_args()
    results = {"platform": platform.system(), "python": platform.python_version(),
               "provider_calls": 0, "steps": []}
    env = dict(os.environ, DO_NOT_TRACK="1", GRAFT_NO_REFRESH="1")
    if args.parent:
        args.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="graft portable & unicode Ω ", dir=args.parent) as temp:
            parent = Path(temp)
            # A requested --parent may be inside an ignored directory of an
            # outer Git checkout. Keep the non-Git fixture genuinely non-Git.
            env["GIT_CEILING_DIRECTORIES"] = str(parent.resolve())

            def execute(name: str, root: Path, *options: str):
                command = [sys.executable, str(SCRIPTS / name), "--repo", str(root), *options]
                if args.launcher_json:
                    command.extend(["--launcher-json", args.launcher_json])
                start = time.monotonic()
                result = subprocess.run(command, env=env, capture_output=True, text=True,
                                        encoding="utf-8", timeout=240)
                data = json.loads(result.stdout)
                step = {"script": name, "layout": root.name, "exit_code": result.returncode,
                        "ok": data.get("ok"), "elapsed_seconds": round(time.monotonic() - start, 3)}
                if "graph" in data:
                    step["graph"] = {k: data["graph"].get(k) for k in ("files", "nodes", "edges", "languages")}
                if "capabilities" in data:
                    step["graft_version"] = data["capabilities"]["version"]
                if "checks" in data:
                    step["checks"] = data["checks"]
                results["steps"].append(step)
                if result.returncode or not data.get("ok"):
                    raise RuntimeError(f"{name} failed in {root.name}: {data.get('error', 'acceptance failed')}")
                return data

            first = parent / "app project"
            (first / "app").mkdir(parents=True)
            (first / "fixtures").mkdir()
            (first / "app/main.py").write_text("def compute():\n    return 'distinctive_literal'\n\ndef caller():\n    return compute()\n", encoding="utf-8")
            (first / "fixtures/copy.py").write_text("def fixture_only():\n    return 'fixture_literal'\n", encoding="utf-8")
            if shutil.which("git"):
                subprocess.run(["git", "init", "--quiet", str(first)], check=True, capture_output=True)
                visible = subprocess.run(["git", "-C", str(first), "rev-parse", "--show-toplevel"],
                                         env=env, capture_output=True, text=True, encoding="utf-8", check=True)
                assert Path(visible.stdout.strip()).resolve() == first.resolve(), "Git root identity differs from the fixture"
            core = execute("refresh.py", first, "--only-dir", "app")
            assert core["graph"]["files"] == 1
            execute("diagnose.py", first, "--check")
            execute("probe_mcp.py", first, "--file", "app/main.py", "--symbol", "compute",
                    "--needle", "distinctive_literal", "--exercise-refresh", "app")
            execute("refresh.py", first, "--cache", ".graft/corpus", "--only-dir", "fixtures")
            execute("probe_mcp.py", first, "--cache", ".graft/corpus", "--file", "fixtures/copy.py",
                    "--symbol", "fixture_only", "--needle", "fixture_literal")
            after = execute("diagnose.py", first, "--check")
            assert after["graph"]["files"] == core["graph"]["files"]
            assert after["graph"]["fingerprints"][0]["only_dirs"] == ["app"]
            execute("refresh.py", first, "--cache", ".graft/manual", "--only-dir", "app")
            manual = first.resolve() / ".graft/manual"
            native_env = child_env(cache=manual)
            native_env["GIT_CEILING_DIRECTORIES"] = str(parent.resolve())
            direct = subprocess.run([*launcher(args.launcher_json), "--dir", str(manual), "build",
                "--no-gitignore", "--no-ignore", str(first.resolve())], env=native_env,
                capture_output=True, text=True, encoding="utf-8", timeout=180)
            widened = graph_summary(manual, first.resolve())
            assert direct.returncode == 0 and widened["files"] == 2
            assert widened["fingerprints"][0]["only_dirs"] == []
            results["steps"].append({"script": "native bare build", "layout": first.name,
                "ok": True, "scope_widened": True, "files_before": 1, "files_after": 2})
            second = parent / "non git build-source"
            (second / "build").mkdir(parents=True)
            (second / "build/main.py").write_text("def compute():\n    return 'distinctive_literal'\n", encoding="utf-8")
            if shutil.which("git"):
                outside = subprocess.run(["git", "-C", str(second), "rev-parse", "--show-toplevel"],
                                         env=env, capture_output=True)
                assert outside.returncode != 0, "Non-Git fixture inherited an ancestor Git repository"
            execute("refresh.py", second, "--cache", ".graft/core", "--only-dir", "build", "--include-dir", "build")
            execute("probe_mcp.py", second, "--cache", ".graft/core", "--file", "build/main.py",
                    "--symbol", "compute", "--needle", "distinctive_literal", "--exercise-refresh", "build")
            execute("refresh.py", second, "--cache", ".graft/core", "--only-dir", "build", "--include-dir", "build", "--clean")
            execute("diagnose.py", second, "--cache", ".graft/core", "--check")
            third = parent / "structured documents"
            (third / "docs").mkdir(parents=True)
            (third / "docs/overview.md").write_text("# Overview\n\nA distinctive_document_literal.\n", encoding="utf-8")
            documents = execute("refresh.py", third, "--cache", ".graft/docs", "--only-dir", "docs", "--structured")
            assert documents["graph"]["files"] == 1
            execute("diagnose.py", third, "--cache", ".graft/docs", "--check")
        results["ok"] = True
    except (OSError, RuntimeError, ValueError, AssertionError, subprocess.SubprocessError) as exc:
        results["ok"] = False
        results["error"] = str(exc) or type(exc).__name__
    args.output.write_bytes((json.dumps(results, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(results, indent=2))
    return 0 if results["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
