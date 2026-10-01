"""Keep H02's full Pygments snapshot while packing a Q4U-sized runtime subset."""

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACTOR = ROOT / "test/fixtures/controller_x5_authored_pytest/development/H02/actor"
ARCHIVE = ACTOR / "deps/pygments-runtime.zip"
FULL = ROOT / "test/results/2026-09-30-controller-x5-h02-pygments-full.zip"
RECEIPT = ROOT / "test/results/2026-09-30-controller-x5-h02-pygments-subset.json"
INVENTORY = ACTOR / "SOURCE.json"
LEXERS = {"__init__.py", "_mapping.py", "python.py", "special.py", "diff.py",
          "text.py", "configs.py", "markup.py", "shell.py", "data.py"}
CEILING = 1_000_000


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def retain(member: str) -> bool:
    return (not member.startswith("pygments/lexers/")
            or member.removeprefix("pygments/lexers/") in LEXERS)


def main() -> None:
    if (not ARCHIVE.resolve().is_relative_to(ROOT.resolve())
            or not FULL.resolve().is_relative_to(ROOT.resolve())
            or FULL.exists() or RECEIPT.exists()):
        raise ValueError("archive source or preservation target is unsafe")
    record = json.loads(INVENTORY.read_text(encoding="utf-8"))
    old = sha(ARCHIVE.read_bytes())
    if record["files"].get("deps/pygments-runtime.zip") != old:
        raise ValueError("actor archive differs from source inventory")
    shutil.copyfile(ARCHIVE, FULL)
    temporary = ARCHIVE.with_suffix(".min.tmp")
    if temporary.exists():
        raise ValueError("temporary archive already exists")
    kept: dict[str, str] = {}
    excluded: dict[str, str] = {}
    try:
        with zipfile.ZipFile(FULL) as source, zipfile.ZipFile(
            temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as target:
            for name in sorted(source.namelist()):
                data = source.read(name)
                if retain(name):
                    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    target.writestr(info, data)
                    kept[name] = sha(data)
                else:
                    excluded[name] = sha(data)
        if temporary.stat().st_size >= CEILING:
            raise ValueError("minimal archive still exceeds Q4U per-file ceiling")
        with zipfile.ZipFile(temporary) as target:
            if set(target.namelist()) != set(kept):
                raise ValueError("minimal archive inventory differs")
            for name, expected in kept.items():
                if sha(target.read(name)) != expected:
                    raise ValueError(f"minimal archive member differs: {name}")
        temporary.replace(ARCHIVE)
        record["files"]["deps/pygments-runtime.zip"] = sha(ARCHIVE.read_bytes())
        INVENTORY.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")
        receipt = {"schema_version": 1, "full_sha256": old,
                   "full_path": str(FULL.relative_to(ROOT)).replace("\\", "/"),
                   "runtime_sha256": record["files"]["deps/pygments-runtime.zip"],
                   "runtime_bytes": ARCHIVE.stat().st_size,
                   "kept": kept, "excluded": excluded}
        RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
        print(json.dumps({"runtime_bytes": receipt["runtime_bytes"],
                          "kept_members": len(kept),
                          "excluded_optional_lexers": len(excluded)}))
    finally:
        if temporary.exists():
            temporary.unlink()


if __name__ == "__main__":
    main()
