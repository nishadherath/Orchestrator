"""Copy the pinned E01 pytest runtime into an unfrozen H02 development actor."""

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACTOR = ROOT / "test/fixtures/controller_x5_authored_pytest/development/H02/actor"
PLUGIN_SHA256 = "ba47c25a4a22b117891e9214940729c41af936d3dafbb18b4284de8a88ed3375"
SOURCE_COMMIT = "6e14cd2af9292dca1fa2b027a06bbc40b0e0e425"
PACKAGES = ("_pytest", "pytest", "pluggy", "iniconfig", "packaging", "pygments")
INFO = (
    "pytest-9.1.1.dist-info",
    "pytest_asyncio-1.4.0.dist-info",
    "pluggy-1.6.0.dist-info",
    "iniconfig-2.3.0.dist-info",
    "packaging-26.3.dist-info",
    "pygments-2.21.0.dist-info",
    "typing_extensions-4.16.0.dist-info",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_file(source: Path, relative: Path, inventory: dict[str, str]) -> None:
    if source.is_symlink() or not source.is_file():
        raise ValueError(f"unsafe source file: {source}")
    target = ACTOR / relative
    if not target.resolve().is_relative_to(ACTOR.resolve()):
        raise ValueError(f"unsafe target: {relative}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.is_symlink() or digest(target) != digest(source):
            raise ValueError(f"existing actor source differs: {relative}")
    else:
        shutil.copyfile(source, target)
    inventory[relative.as_posix()] = digest(target)


def copy_tree(source: Path, relative: Path, inventory: dict[str, str]) -> None:
    if source.is_symlink() or not source.is_dir():
        raise ValueError(f"unsafe source directory: {source}")
    for item in sorted(source.rglob("*")):
        if item.is_symlink():
            raise ValueError(f"symlink in package: {item}")
        if not item.is_file() or "__pycache__" in item.parts:
            continue
        if item.suffix not in {".py", ".pyi"} and item.name != "py.typed":
            continue
        copy_file(item, relative / item.relative_to(source), inventory)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: vendor.py <pinned-source-checkout> <local-package-cache>")
    source, cache = (Path(arg).resolve() for arg in sys.argv[1:])
    if digest(source / "pytest_asyncio/plugin.py") != PLUGIN_SHA256:
        raise ValueError("source plugin SHA-256 does not match E01 qualification")
    if (ACTOR / "deps/pygments-runtime.zip").exists():
        raise ValueError("packed H02 actor exists; vendor into a fresh actor")
    if not ACTOR.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("actor target is outside repository")
    inventory: dict[str, str] = {}
    copy_tree(source / "pytest_asyncio", Path("pytest_asyncio"), inventory)
    copy_file(source / "LICENSE", Path("licenses/pytest_asyncio/LICENSE"), inventory)
    for package in PACKAGES:
        copy_tree(cache / package, Path("deps") / package, inventory)
    for filename in ("typing_extensions.py", "py.py"):
        copy_file(cache / filename, Path("deps") / filename, inventory)
    for info in INFO:
        directory = cache / info
        if not directory.is_dir():
            raise ValueError(f"missing package metadata: {info}")
        for item in sorted(directory.rglob("*")):
            if item.is_symlink():
                raise ValueError(f"symlink in package metadata: {item}")
            if item.is_file() and (item.name in {"METADATA", "WHEEL", "entry_points.txt"}
                                   or "licenses" in item.parts):
                copy_file(item, Path("deps") / info / item.relative_to(directory), inventory)
    for filename in ("conftest.py", "test_mre.py"):
        original = ROOT / "test/fixtures/controller_x5_external/development/E01/repro" / filename
        copy_file(original, Path("case") / filename, inventory)
    record = {
        "schema_version": 1,
        "origin": "authored development adaptation of pytest-asyncio issue 1501",
        "source_commit": SOURCE_COMMIT,
        "source_plugin_sha256": PLUGIN_SHA256,
        "runtime": "pytest 9.1.1 from existing E01 local package cache",
        "files": inventory,
    }
    (ACTOR / "SOURCE.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"actor": str(ACTOR), "copied_files": len(inventory)}))


if __name__ == "__main__":
    main()
