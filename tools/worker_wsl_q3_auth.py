#!/usr/bin/env python3
"""Use the audited N4 credential store for Q1-named paid actors only.

The store's identity regex is intentionally narrow for the frozen N5 path.
This root-only wrapper changes that regex in its own process, leaving the N5
runtime and credential implementation untouched.
"""
from __future__ import annotations

import re
import sys

import worker_wsl_auth


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in {"begin", "finish"}:
        print("Q3 credential wrapper accepts begin/finish and one actor name", file=sys.stderr)
        return 64
    if not re.fullmatch(r"q1-[0-9a-f]{32}", sys.argv[2]):
        print("Q3 credential wrapper rejected actor identity", file=sys.stderr)
        return 64
    worker_wsl_auth.NAME = re.compile(r"q1-[0-9a-f]{32}\Z")
    return worker_wsl_auth.main()


if __name__ == "__main__":
    raise SystemExit(main())
