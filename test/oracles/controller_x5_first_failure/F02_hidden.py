"""Protected behavioural checks for the Click F02 development case."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys


actor = Path(os.environ["X5_F02_ACTOR_ROOT"])
if actor.is_symlink() or not actor.is_dir():
    raise RuntimeError("candidate actor is unavailable")
sys.path.insert(0, str(actor))
from click.formatting import HelpFormatter, wrap_text  # noqa: E402


RED = "\x1b[31mred\x1b[0m"
GREEN = "\x1b[32m>\x1b[0m "


def styled_word() -> None:
    assert wrap_text(f"{RED} blue green", width=8) == f"{RED} blue\ngreen"


def styled_indent() -> None:
    expected = f"{GREEN}alpha\n{GREEN}beta\n{GREEN}gamma"
    assert wrap_text("alpha beta gamma", width=10,
                     initial_indent=GREEN, subsequent_indent=GREEN) == expected


def subsequent_styled_indent() -> None:
    assert wrap_text("alpha beta gamma", width=10,
                     subsequent_indent=GREEN) == f"alpha beta\n{GREEN}gamma"


def paragraph_boundary() -> None:
    expected = (f"{GREEN}first\n{GREEN}second\n\n"
                f"{GREEN}third\n{GREEN}fourth")
    assert wrap_text("first second\n\nthird fourth", width=12,
                     initial_indent=GREEN, subsequent_indent=GREEN,
                     preserve_paragraphs=True) == expected


def styled_usage() -> None:
    formatter = HelpFormatter(width=35)
    formatter.write_usage("\x1b[35mtool\x1b[0m", "[OPTIONS] FILE [EXTRA]")
    assert formatter.getvalue() == "Usage: \x1b[35mtool\x1b[0m [OPTIONS] FILE [EXTRA]\n"


def unstyled_wrap() -> None:
    assert wrap_text("alpha beta gamma", width=10) == "alpha beta\ngamma"


def unstyled_usage() -> None:
    formatter = HelpFormatter(width=35)
    formatter.write_usage("plain", "[OPTIONS] FILE [EXTRA]")
    assert formatter.getvalue() == "Usage: plain [OPTIONS] FILE [EXTRA]\n"


CASES = (
    ("styled_word", styled_word, False),
    ("styled_indent", styled_indent, True),
    ("subsequent_styled_indent", subsequent_styled_indent, True),
    ("paragraph_boundary", paragraph_boundary, True),
    ("styled_usage", styled_usage, True),
    ("unstyled_wrap", unstyled_wrap, False),
    ("unstyled_usage", unstyled_usage, False),
)


def main() -> None:
    results = []
    for name, check, critical in CASES:
        try:
            check()
            passed = True
        except Exception:
            passed = False
        results.append({"name": name, "passed": passed,
                        "critical": critical, "weight": 1})
    print(json.dumps({"schema_version": 1, "cases": results}, sort_keys=True))
    if not all(row["passed"] for row in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
