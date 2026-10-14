"""Check, or explicitly apply, the bundled Graft source repair. Never edit installed dist."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
import uuid
from pathlib import Path

from graft_common import GraftError, failure, local_path, repo_path, report


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Explicit Graft source checkout root")
    parser.add_argument("--apply", action="store_true", help="Back up affected files and apply after all checks")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    backup = None
    try:
        root = repo_path(args.source)
        assets = Path(__file__).resolve().parent.parent / "assets"
        plan = json.loads((assets / "graft-scoped-walk.json").read_text(encoding="utf-8"))
        patch = assets / "graft-scoped-walk.patch"
        if hashlib.sha256(patch.read_bytes()).hexdigest() != plan["patch_sha256"]:
            raise GraftError("Bundled patch digest differs from its manifest.")
        package = json.loads((root / "package.json").read_text(encoding="utf-8"))
        if package.get("name") != "@nanonets/graft":
            raise GraftError("Select the Graft source checkout, not the indexed application.")
        git_root = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True, text=True, timeout=20, check=True)
        if Path(git_root.stdout.strip()).resolve() != root:
            raise GraftError("The source must be its own Git checkout, not a directory inside another repository.")
        for name, expected in plan["before"].items():
            path = local_path(root, name)
            if path.is_symlink() or path.is_junction() or (expected is None and path.exists()) or (expected is not None and (not path.is_file() or digest(path) != expected)):
                raise GraftError("Source differs from this patch's verified base. Inspect or port the source change; do not force it onto another build.")
        # Zero-context hunks avoid whitespace-only context lines in this tracked
        # patch asset. Exact source hashes above prevent ambiguous application.
        subprocess.run(["git", "apply", "--unidiff-zero", "--check", str(patch)], cwd=root, capture_output=True, timeout=20, check=True)
        if args.apply:
            backup = local_path(root, ".graft-skill-patch-backups")
            if backup.is_symlink() or backup.is_junction():
                raise GraftError("Patch backup directory must not be a link.")
            backup = backup / (time.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex)
            backup.mkdir(parents=True)
            for name, expected in plan["before"].items():
                if expected is not None:
                    dest = backup / name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(local_path(root, name), dest)
            (backup / "manifest.json").write_bytes((json.dumps(plan, indent=2) + "\n").encode())
            subprocess.run(["git", "apply", "--unidiff-zero", str(patch)], cwd=root, capture_output=True, timeout=20, check=True)
        report({"ok": True, "applied": args.apply, "backup": str(backup) if backup else None,
                "source": str(root), "files": list(plan["before"]), "installed_runtime_changed": False,
                "next": "Run the source project's build/test gate, then its reviewed runtime synchronisation workflow."}, args.output)
        return 0
    except (GraftError, OSError, ValueError, subprocess.SubprocessError) as exc:
        return failure(GraftError(str(exc) if isinstance(exc, GraftError) else "Source patch check/apply failed. Preserve the checkout and inspect Git/runtime permissions; no installed runtime was changed."), args.output)


if __name__ == "__main__":
    raise SystemExit(main())
