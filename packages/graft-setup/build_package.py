"""Build/check the deterministic, allowlisted skill archive and integrity manifest."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL = ROOT / "graft-setup"
FILES = ("SKILL.md", "VERSION", "LICENSE", "agents/openai.yaml",
         "scripts/graft_common.py", "scripts/diagnose.py", "scripts/refresh.py", "scripts/probe_mcp.py", "scripts/fs_probe.py", "scripts/trace.py",
         "references/version-0211.md", "references/repair.md", "references/deep.md",
         "references/hosts.md", "references/installation.md")


def release_bytes() -> tuple[bytes, bytes, str]:
    version = (SKILL / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("VERSION must be a numeric semantic version")
    body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    if not re.match(r"\A---\nname: graft-setup\ndescription: .+\nlicense: Apache-2.0\n---\n", body):
        raise ValueError("Skill frontmatter is missing or invalid")
    actual = {p.relative_to(SKILL).as_posix() for p in SKILL.rglob("*") if p.is_file()
              and "__pycache__" not in p.parts and p.suffix != ".pyc"}
    if actual != set(FILES):
        raise ValueError(f"Release file allowlist differs: {sorted(actual ^ set(FILES))}")
    contents = {}
    for relative in FILES:
        path = SKILL / relative
        if path.is_symlink() or not path.resolve().is_relative_to(SKILL.resolve()):
            raise ValueError("Release source must not contain links or escaped paths")
        raw = path.read_bytes()
        if b"\r" in raw or not raw.endswith(b"\n"):
            raise ValueError(f"Release text must be UTF-8/LF with a final newline: {relative}")
        text = raw.decode("utf-8")
        if path.suffix == ".md":
            for link in re.findall(r"\]\(([^)]+)\)", text):
                if "://" in link or link.startswith("#"):
                    continue
                target = (path.parent / link.split("#")[0]).resolve()
                if not target.is_relative_to(SKILL.resolve()) or not target.is_file():
                    raise ValueError(f"Broken or escaped skill reference: {relative}: {link}")
        contents[f"graft-setup/{relative}"] = raw
    buffer = io.BytesIO()
    # STORE avoids zlib-version variation; this small text package is portable.
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, raw in sorted(contents.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    data = buffer.getvalue()
    filename = f"graft-setup-{version}.zip"
    manifest = {"package": "graft-setup", "version": version, "tested_graft": "0.21.1",
                "archive": filename, "archive_sha256": hashlib.sha256(data).hexdigest(),
                "archive_bytes": len(data), "files": {k: hashlib.sha256(v).hexdigest() for k, v in sorted(contents.items())}}
    return data, (json.dumps(manifest, indent=2) + "\n").encode("utf-8"), filename


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        data, manifest, filename = release_bytes()
        release = ROOT / "releases"
        paths = [(release / filename, data), (release / filename.replace(".zip", ".manifest.json"), manifest)]
        if args.check:
            if any(not p.is_file() or p.read_bytes() != expected for p, expected in paths):
                raise ValueError("Release archive/manifest is stale; rebuild after changing source")
        else:
            release.mkdir(exist_ok=True)
            for path, expected in paths:
                path.write_bytes(expected)
        print(("Verified " if args.check else "Built ") + filename)
        return 0
    except (OSError, ValueError) as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
