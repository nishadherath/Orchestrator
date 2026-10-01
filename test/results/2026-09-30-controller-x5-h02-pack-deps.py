"""Pack H02's vendored Pygments modules without changing their source bytes."""

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACTOR = ROOT / "test/fixtures/controller_x5_authored_pytest/development/H02/actor"
SOURCE = ACTOR / "deps/pygments"
ARCHIVE = ACTOR / "deps/pygments-runtime.zip"
INVENTORY = ACTOR / "SOURCE.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    if (not SOURCE.resolve().is_relative_to(ROOT.resolve())
            or SOURCE.resolve() != (ACTOR / "deps/pygments").resolve()
            or SOURCE.is_symlink() or not SOURCE.is_dir()
            or ARCHIVE.exists()):
        raise ValueError("Pygments source or archive target is unsafe")
    record = json.loads(INVENTORY.read_text(encoding="utf-8"))
    files = record["files"]
    selected = {name: expected for name, expected in files.items()
                if name.startswith("deps/pygments/")}
    if len(selected) < 100:
        raise ValueError("Pygments inventory is incomplete")
    for name, expected in selected.items():
        if sha((ACTOR / name).read_bytes()) != expected:
            raise ValueError(f"Pygments source drifted: {name}")
    temporary = ARCHIVE.with_suffix(".zip.tmp")
    if temporary.exists():
        raise ValueError("temporary archive already exists")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=9) as archive:
            for name in sorted(selected):
                member = name.removeprefix("deps/")
                info = zipfile.ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, (ACTOR / name).read_bytes())
        with zipfile.ZipFile(temporary) as archive:
            if set(archive.namelist()) != {name.removeprefix("deps/")
                                           for name in selected}:
                raise ValueError("archive member inventory differs")
            for name, expected in selected.items():
                if sha(archive.read(name.removeprefix("deps/"))) != expected:
                    raise ValueError(f"archive member differs: {name}")
        temporary.replace(ARCHIVE)
        shutil.rmtree(SOURCE)
        for name in selected:
            del files[name]
        files["deps/pygments-runtime.zip"] = sha(ARCHIVE.read_bytes())
        INVENTORY.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")
        actor_files = sum(path.is_file() for path in ACTOR.rglob("*"))
        if actor_files > 200:
            raise ValueError(f"actor still exceeds Q1 file ceiling: {actor_files}")
        print(json.dumps({"archived_members": len(selected),
                          "actor_files": actor_files,
                          "archive_sha256": files["deps/pygments-runtime.zip"]}))
    finally:
        if temporary.exists():
            temporary.unlink()


if __name__ == "__main__":
    main()
