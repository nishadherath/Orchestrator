#!/usr/bin/env python3
"""Measure static instruction surfaces without making a model call.

The estimate is deliberately simple and labelled: Unicode characters divided
by four, rounded up. It is useful for before/after comparison, not provider
billing. Hashes make the measured baseline reversible.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def measure(text: str) -> dict:
    return {
        "bytes_utf8": len(text.encode("utf-8")),
        "characters": len(text),
        "estimated_tokens_chars_div_4": math.ceil(len(text) / 4),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
    )
    if not match:
        raise ValueError(f"missing section {heading!r}")
    return match.group(1).strip()


def inventory(root: Path) -> dict:
    bundle = root / "dist" if (root / "dist" / "ORCHESTRATOR.md").is_file() else root
    template = bundle / "CLAUDE.template.md"
    if not template.is_file():
        template = bundle / "CLAUDE.md"

    surfaces: dict[str, dict] = {}

    def add(name: str, paths: list[Path]) -> None:
        parts = [read(path) for path in paths if path.is_file()]
        value = measure("".join(parts))
        value["files"] = [path.relative_to(root).as_posix() for path in paths if path.is_file()]
        surfaces[name] = value

    add("repository_development_standing", [root / "AGENTS.md", root / "CLAUDE.md"])
    add("consumer_orchestrator_standing", [template, bundle / "ORCHESTRATOR.md"])

    workers = sorted((bundle / ".claude" / "agents").glob("WORKER_*.md"))
    worker_values = {path.name: measure(read(path)) for path in workers}
    worker_tokens = [value["estimated_tokens_chars_div_4"] for value in worker_values.values()]

    roles_text = read(bundle / "src" / "System" / "ROLES.md")
    role_names = [
        "Framer",
        "Verifier",
        "Generator (template; the technique family is the parameter)",
        "Critic",
        "Selector",
        "Librarian",
    ]
    shared = section(roles_text, "Rules that bind every role")
    role_values = {
        name: measure(shared + "\n" + section(roles_text, name)) for name in role_names
    }

    techniques_text = read(bundle / "src" / "System" / "TECHNIQUES.md")
    technique_values = {}
    for name in ("Subtract", "Re-represent", "Abduce"):
        match = re.search(
            rf"^## Family \d+: {re.escape(name)}.*?\n(.*?)(?=^---$|\Z)",
            techniques_text,
            re.MULTILINE | re.DOTALL | re.IGNORECASE,
        )
        if not match:
            raise ValueError(f"missing technique family {name!r}")
        technique_values[name.lower()] = measure(match.group(1).strip())

    return {
        "version": 1,
        "method": "UTF-8 bytes and Unicode characters measured exactly; token estimate is ceil(characters / 4).",
        "root": str(root.resolve()),
        "bundle_root": str(bundle.resolve()),
        "surfaces": surfaces,
        "selected_worker": {
            "count": len(worker_values),
            "minimum_estimated_tokens": min(worker_tokens) if worker_tokens else None,
            "maximum_estimated_tokens": max(worker_tokens) if worker_tokens else None,
            "mean_estimated_tokens": round(sum(worker_tokens) / len(worker_tokens), 1) if worker_tokens else None,
            "files": worker_values,
        },
        "controller_role_static_briefs": role_values,
        "controller_generator_technique_briefs": technique_values,
        "limits": [
            "Character estimates are not tokenizer counts or billed usage.",
            "Task input, tool schemas, ledger records and retrieved source are dynamic and excluded.",
            "Controller role totals exclude dynamic records and generated schema summaries.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(inventory(args.root.resolve()), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
