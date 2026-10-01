"""Private Controller mount view with evaluation material hidden."""

from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from worker_wsl_q1 import SEEDS


HIDDEN = ("test", "docs", "handoffs", ".git")


class IsolationStop(RuntimeError):
    """The Controller mount view could not be proved private."""


def command(*parts: str) -> None:
    result = subprocess.run(parts, capture_output=True, text=True,
                            timeout=20, check=False)
    if result.returncode:
        raise IsolationStop(f"mount operation failed: {parts[0]} {parts[1]}")


@contextmanager
def hidden_evaluation_tree(root: Path):
    """Hide evaluation files in this process and all Controller children."""
    if os.name != "posix" or os.geteuid() != 0 or not hasattr(os, "unshare"):
        raise IsolationStop("private mount namespace requires WSL root")
    root = root.resolve()
    targets = [root / name for name in HIDDEN]
    if any(path.is_symlink() or not path.is_dir() for path in targets):
        raise IsolationStop("evaluation hide target is missing or redirected")
    os.unshare(os.CLONE_NEWNS)
    command("/usr/bin/mount", "--make-rprivate", "/")
    empty = Path(tempfile.mkdtemp(prefix="x5-recovery-hidden-", dir=SEEDS))
    mounted = []
    try:
        for target in targets:
            command("/usr/bin/mount", "--bind", str(empty), str(target))
            mounted.append(target)
        if any(list(target.iterdir()) for target in targets):
            raise IsolationStop("Controller evaluation trees remain visible")
        yield
    finally:
        failed = False
        for target in reversed(mounted):
            try:
                command("/usr/bin/umount", str(target))
            except IsolationStop:
                failed = True
        if not failed:
            if empty.resolve().parent != SEEDS.resolve():
                raise IsolationStop("hidden mount cleanup path escaped seed root")
            shutil.rmtree(empty)
        else:
            raise IsolationStop("private evaluation mounts need reconciliation")
