"""Prompt-assembly helpers shared by `role_probe.py` and `system_controller.py`
(docs/PLAN.md Stages 9 and 10): pulling a role's brief out of `ROLES.md`, a
technique family's brief out of `TECHNIQUES.md`, and a compact schema summary
out of `src/System/schemas/`.

Responsible for: turning the prose in `src/System/` into the text a role's
`claude -p` prompt is built from, without either file duplicating the other's
extraction logic. `role_probe.py` had this logic first (Stage 9.7); it moved
here when `system_controller.py` needed the same thing (Stage 10), matching
the reasoning behind `tools/claudep.py` (task 10.1): one place, not a second
hand-copied version.

Deliberately does not: build a full prompt. Each caller assembles its own
prompt from these pieces plus its own input slice and instruction, because
the input slice (a toy problem's fixed records for role_probe.py, a live
ledger for system_controller.py) is caller-specific.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SYSTEM = REPO_ROOT / "src" / "System"

OUTPUT_RULE = (
    "\n\nReply with the records only: one JSON object per line, no prose before or after, no code fence. "
    "Every record carries `type`, `id` (a lower-case prefix, a hyphen, three or more digits), "
    "`ledger_version` and `references`. Field names and caps are as the schemas in the brief state; "
    "when in doubt, fewer fields and shorter text."
)


def role_section(role_heading: str) -> str:
    """The role's own section of ROLES.md plus the rules that bind every role."""
    text = (SYSTEM / "ROLES.md").read_text(encoding="utf-8")
    rules = re.search(r"## Rules that bind every role\n(.*?)\n## ", text, re.S)
    section = re.search(rf"\n## {re.escape(role_heading)}\n(.*?)(?=\n## |\Z)", text, re.S)
    assert rules and section, f"ROLES.md lacks the section for {role_heading!r}"
    return "Rules that bind every role:\n" + rules.group(1).strip() + f"\n\nYour role: {role_heading}\n" + section.group(1).strip()


def technique_brief(family: str) -> str:
    """One family's full brief from TECHNIQUES.md, matched on its heading
    ('subtract', 're-represent' or 'abduce', case-insensitive)."""
    text = (SYSTEM / "TECHNIQUES.md").read_text(encoding="utf-8")
    m = re.search(rf"\n## Family \d+: {re.escape(family)}.*?(?=\n---)", text, re.S | re.I)
    assert m, f"TECHNIQUES.md lacks a family named {family!r}"
    return m.group(0).strip()


def schema_summary(*types: str) -> str:
    """The properties and required list of each named schema, compactly:
    enough for a role to write a valid record without seeing the full JSON
    Schema document."""
    out = []
    for t in types:
        s = json.loads((SYSTEM / "schemas" / f"{t}.schema.json").read_text(encoding="utf-8"))
        fields = []
        for k, v in s["properties"].items():
            if k == "type":
                continue
            kind = v.get("enum") or v.get("type") or "object"
            cap = v.get("maxLength")
            fields.append(f"{k}: {kind if not isinstance(kind, list) else '/'.join(map(str, kind))}"
                          + (f" (<= {cap} chars)" if cap else ""))
        out.append(f"{t}, required {s['required']}:\n  " + "\n  ".join(fields))
    return "Output schemas:\n" + "\n".join(out)


def as_jsonl(records: list[dict]) -> str:
    return "\n".join(json.dumps(r, ensure_ascii=False) for r in records)
