"""Compare byte-identical helper tests with source and fixtures on native storage."""
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-package", type=Path, required=True)
    parser.add_argument("--native-parent", type=Path, default=Path(tempfile.gettempdir()))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    package = args.source_package.resolve(strict=True)
    spec = importlib.util.spec_from_file_location("control_builder", package / "build_package.py")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    names = ["graft-setup/" + name for name in builder.FILES] + ["build_package.py", "tests/test_helpers.py", "tests/fake_graft.py", "tests/integration.py", "tests/timed_unittest.py"]
    report = {"source_package": str(package), "files": {}, "acceptance_deadlines_changed": False, "started_unix": time.time()}
    with tempfile.TemporaryDirectory(prefix="graft-native-control-", dir=args.native_parent) as temporary:
        root = Path(temporary)
        for name in names:
            data = (package / name).read_bytes()
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()
            assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
            report["files"][name] = digest
        fixtures = root / "fixtures"
        fixtures.mkdir()
        env = dict(os.environ, GRAFT_TEST_PARENT=str(fixtures), GRAFT_API_KEY="", OPENROUTER_API_KEY="", DO_NOT_TRACK="1")
        started = time.monotonic()
        result = subprocess.run([sys.executable, str(root / "tests/timed_unittest.py")], env=env, cwd=root, capture_output=True, timeout=300)
        report.update(exit_code=result.returncode, elapsed_seconds=round(time.monotonic() - started, 3), source_hashes_verified=True)
        args.output.with_suffix(".log").write_bytes(result.stdout + result.stderr)
        sys.path.insert(0, str(root / "graft-setup/scripts"))
        from graft_common import filesystem_info
        report["filesystem"] = filesystem_info(root.resolve())
    report["ok"] = report["exit_code"] == 0
    args.output.write_bytes((json.dumps(report, indent=2) + "\n").encode())
    print(json.dumps({key: report[key] for key in ("ok", "elapsed_seconds", "filesystem")}))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
