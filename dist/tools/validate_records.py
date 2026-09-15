#!/usr/bin/env python3
"""Validate a JSONL ledger against src/System/schemas/, standard library only.

    python3 tools/validate_records.py ledger.jsonl [more.jsonl ...]
    python3 tools/validate_records.py --strict ledger.jsonl

Each line is one record; its `type` field selects the schema. Exit 0 when
every record validates and every reference resolves, 1 otherwise, with one
line per problem on stderr.

This is not a JSON Schema implementation. It implements exactly the subset
the schemas use (type, const, enum, properties, required,
additionalProperties, items, minItems, minLength, maxLength, pattern,
minimum, maximum) and raises on any other validating keyword, so a schema
edit that reaches for something this file does not check fails loudly
instead of passing silently. `docs/PLAN.md` task 9.3 allowed a hand-written
validator over the record types; this is one, written against the schema
files rather than beside them so the two cannot drift.

Cross-record checks, after per-record validation: ids are unique within
the input; every id in `references` (and in the id-valued fields listed in
REF_FIELDS) resolves to a record in the input. `--strict` additionally
requires every CandidateRecord's ledger_version to equal the highest
FrameRecord version present, which is the Scribe's stale-ledger rejection.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO_ROOT / "src" / "System" / "schemas"

# Keywords this validator understands. Anything else that is not
# annotation is refused, see validate_node.
ANNOTATION = {"$schema", "$id", "title", "description"}
SUPPORTED = {"type", "const", "enum", "properties", "required", "additionalProperties",
             "items", "minItems", "minLength", "maxLength", "pattern", "minimum", "maximum"}

# Id-valued fields beyond `references` that must resolve within the input.
REF_FIELDS = {
    "PremiseRecord": ["supersedes"],
    "FrameRecord": ["b0_candidate_id"],
    "MeasurementRecord": ["premise_id"],
    "CandidateRecord": ["refines"],
    "CritiqueRecord": ["candidate_id"],
    "SelectionRecord": ["baseline_id"],
    "EvaluationRecord": ["candidate_id"],
    "SolutionRecord": ["candidate_id"],
    "GapReport": ["best_candidate_id"],
}

JSON_TYPES = {
    "object": dict, "array": list, "string": str, "boolean": bool,
    "integer": int, "number": (int, float), "null": type(None),
}


def load_schemas(schema_dir: Path = SCHEMA_DIR) -> dict[str, dict]:
    schemas = {}
    for path in sorted(schema_dir.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        schemas[schema["title"]] = schema
    if not schemas:
        raise SystemExit(f"no schemas found under {schema_dir}")
    return schemas


def _is_type(value, name: str) -> bool:
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name == "boolean":
        return isinstance(value, bool)
    return isinstance(value, JSON_TYPES[name])


def validate_node(value, schema: dict, path: str, errors: list[str]) -> None:
    unknown = set(schema) - SUPPORTED - ANNOTATION
    if unknown:
        raise ValueError(f"schema at {path or '$'} uses unsupported keyword(s) {sorted(unknown)}; extend validate_records.py before relying on them")

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected the constant {schema['const']!r}, got {value!r}")
        return
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} is not one of {schema['enum']}")
        return
    if "type" in schema:
        allowed = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_is_type(value, t) for t in allowed):
            errors.append(f"{path}: expected type {'/'.join(allowed)}, got {type(value).__name__}")
            return
        if value is None:
            return  # a nullable field holding null has nothing further to check

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: shorter than {schema['minLength']} character(s)")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append(f"{path}: {len(value)} characters, cap is {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: {value!r} does not match {schema['pattern']}")
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: {value} is below the minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: {value} is above the maximum {schema['maximum']}")
    elif isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: {len(value)} item(s), at least {schema['minItems']} required")
        if "items" in schema:
            for i, item in enumerate(value):
                validate_node(item, schema["items"], f"{path}[{i}]", errors)
    elif isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path or '$'}: missing required field {key!r}")
        if schema.get("additionalProperties", True) is False:
            for key in value:
                if key not in props:
                    errors.append(f"{path or '$'}: field {key!r} is not in the schema")
        for key, sub in props.items():
            if key in value:
                validate_node(value[key], sub, f"{path}.{key}" if path else key, errors)


def validate_record(record, schemas: dict[str, dict]) -> list[str]:
    if not isinstance(record, dict):
        return ["record is not a JSON object"]
    rtype = record.get("type")
    if rtype not in schemas:
        return [f"type {rtype!r} has no schema (known: {', '.join(sorted(schemas))})"]
    errors: list[str] = []
    validate_node(record, schemas[rtype], "", errors)
    return errors


def validate_ledger(records: list[tuple[str, dict]], schemas: dict[str, dict], strict: bool = False) -> list[str]:
    """records: (label, record) pairs, label being 'file:line' for messages."""
    problems: list[str] = []
    ids: dict[str, str] = {}
    for label, rec in records:
        for err in validate_record(rec, schemas):
            problems.append(f"{label}: {err}")
        rid = rec.get("id") if isinstance(rec, dict) else None
        if isinstance(rid, str):
            if rid in ids:
                problems.append(f"{label}: id {rid!r} already used at {ids[rid]}")
            else:
                ids[rid] = label

    for label, rec in records:
        if not isinstance(rec, dict):
            continue
        targets = list(rec.get("references", []) if isinstance(rec.get("references"), list) else [])
        for field in REF_FIELDS.get(rec.get("type", ""), []):
            if isinstance(rec.get(field), str):
                targets.append(rec[field])
        for target in targets:
            if isinstance(target, str) and target not in ids:
                problems.append(f"{label}: reference {target!r} does not resolve to a record in the input")

    if strict:
        frame_versions = [r["ledger_version"] for _, r in records
                          if isinstance(r, dict) and r.get("type") == "FrameRecord" and isinstance(r.get("ledger_version"), int)]
        if frame_versions:
            frozen = max(frame_versions)
            for label, rec in records:
                if isinstance(rec, dict) and rec.get("type") == "CandidateRecord" and rec.get("technique") != "b0" \
                        and rec.get("ledger_version") != frozen:
                    problems.append(f"{label}: candidate cites ledger version {rec.get('ledger_version')}, frozen version is {frozen}")
    return problems


def read_jsonl(paths: list[Path]) -> tuple[list[tuple[str, dict]], list[str]]:
    records: list[tuple[str, dict]] = []
    problems: list[str] = []
    for path in paths:
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            label = f"{path}:{n}"
            try:
                records.append((label, json.loads(line)))
            except json.JSONDecodeError as exc:
                problems.append(f"{label}: not JSON ({exc.msg})")
    return records, problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--strict", action="store_true", help="also reject candidates citing a stale ledger version")
    ap.add_argument("--quiet", action="store_true", help="print only the count")
    args = ap.parse_args(argv)

    schemas = load_schemas()
    records, problems = read_jsonl(args.files)
    problems += validate_ledger(records, schemas, strict=args.strict)
    if problems and not args.quiet:
        for p in problems:
            print(p, file=sys.stderr)
    print(f"{len(records)} record(s), {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
