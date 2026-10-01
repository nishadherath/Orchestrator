#!/usr/bin/env python3
"""Decode safe Windows-to-WSL argv and exec one tool-free Claude assessment.

Windows wsl.exe rewrites JSON quotation marks and braces in argv. The Windows
adapter passes only URL-safe base64 for the schema and fixed system prompt;
the public packet itself remains on stdin. This helper must run inside WSL.
"""
from __future__ import annotations

import base64
import json
import math
import os
import re
import sys
from pathlib import PurePosixPath


def _decode(value: str, *, maximum: int) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]+={0,2}", value) or len(value) > maximum * 2:
        raise ValueError("encoded argument is invalid or too large")
    raw = base64.b64decode(value, altchars=b"-_", validate=True)
    if len(raw) > maximum:
        raise ValueError("decoded argument is too large")
    return raw.decode("utf-8")


def command(argv: list[str]) -> list[str]:
    """Validate the six fixed transport values before calling Claude Code."""
    if len(argv) != 6:
        raise ValueError("launcher expects six fixed arguments")
    binary, model, effort, cap_text, schema_arg, prompt_arg = argv
    path = PurePosixPath(binary)
    if not path.is_absolute() or path.name != "claude" or ".." in path.parts:
        raise ValueError("Claude binary path is invalid")
    if not re.fullmatch(r"claude-[a-z0-9.-]+", model):
        raise ValueError("Claude model is invalid")
    if effort not in {"low", "medium", "high", "xhigh", "max"}:
        raise ValueError("Claude effort is invalid")
    try:
        cap = float(cap_text)
    except ValueError as exc:
        raise ValueError("Claude allowance is invalid") from exc
    if not math.isfinite(cap) or not 0 < cap <= 100:
        raise ValueError("Claude allowance is outside launcher bounds")
    schema = _decode(schema_arg, maximum=65536)
    if not isinstance(json.loads(schema), dict):
        raise ValueError("assessment schema is not a JSON object")
    prompt = _decode(prompt_arg, maximum=16384)
    if not prompt.strip():
        raise ValueError("assessment prompt is empty")
    return [binary, "-p", "--output-format=stream-json", "--verbose",
            "--model", model, "--effort", effort,
            "--json-schema", schema, "--max-budget-usd", cap_text,
            "--restricted", "--safe-mode", "--strict-mcp-config",
            "--no-session-persistence", "--permission-mode=dontAsk",
            "--permission-prompts=none", "--tools", "",
            "--system-prompt", prompt]


if __name__ == "__main__":
    try:
        args = command(sys.argv[1:])
    except (UnicodeError, ValueError) as exc:
        print(f"Controller WSL launcher: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    os.execv(args[0], args)
