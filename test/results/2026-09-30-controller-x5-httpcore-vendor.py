"""Copy pinned installed sources into the authored H01 development actor once."""

from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "test/fixtures/controller_x5_authored_httpcore/development/H01/actor"
PACKAGES = {"httpcore": "1.0.9", "h11": "0.16.0", "certifi": "2026.7.22"}
LICENCES = {"httpcore": "LICENSE.md", "h11": "LICENSE.txt", "certifi": "LICENSE"}
SOURCE_POOL_SHA256 = "6be4fc2d3b14c5ceebd16c356ad7c7483a163e34347c0f1497b4b7f85d0c8fbd"
HTTPCORE_RELEASE_COMMIT = "98209758cc14e1a5f966fe1dfdc1064b94055d8c"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if TARGET.exists() or not TARGET.resolve().is_relative_to(ROOT.resolve()):
        raise RuntimeError("actor target exists or is outside repository")
    sources = {}
    for name, version in PACKAGES.items():
        package = importlib.import_module(name)
        distribution = importlib.metadata.distribution(name)
        if distribution.version != version:
            raise RuntimeError(f"{name} version drift: {distribution.version}")
        source = Path(package.__file__).resolve().parent
        licence = next((distribution.locate_file(item) for item in distribution.files
                        if Path(str(item)).name == LICENCES[name]
                        and "licenses" in Path(str(item)).parts), None)
        if licence is None:
            raise RuntimeError(f"{name} licence unavailable")
        sources[name] = (source, Path(licence))
    if sha(sources["httpcore"][0] / "_sync/connection_pool.py") != SOURCE_POOL_SHA256:
        raise RuntimeError("httpcore connection_pool.py source drift")
    TARGET.mkdir(parents=True)
    hashes = {}
    for name, (source, licence) in sources.items():
        for path in sorted(source.rglob("*")):
            if not path.is_file() or (path.suffix != ".py" and path.name != "cacert.pem"):
                continue
            relative = path.relative_to(source)
            destination = TARGET / name / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(path.read_bytes())
            hashes[destination.relative_to(TARGET).as_posix()] = sha(destination)
        destination = TARGET / "licenses" / name / licence.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(licence.read_bytes())
        hashes[destination.relative_to(TARGET).as_posix()] = sha(destination)
    (TARGET / "SOURCE.json").write_text(json.dumps({"httpcore_release_commit": HTTPCORE_RELEASE_COMMIT,
                                                     "package_versions": PACKAGES,
                                                     "source_sha256": hashes},
                                                    indent=2, sort_keys=True) + "\n",
                                        encoding="utf-8")
    print(json.dumps({"files": len(hashes), "pool_sha256": SOURCE_POOL_SHA256}))


if __name__ == "__main__":
    main()
