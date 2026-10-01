"""Evaluator-only cases for IDNA joiner errors."""
import json
import sys
from unittest import mock

import idna


def run(case):
    if case in {"zwj-type", "zwnj-type"}:
        joiner = "\u200d" if case == "zwj-type" else "\u200c"
        try:
            idna.check_label("a" + joiner + "a")
        except idna.InvalidCodepointContext as error:
            return "position 2" in str(error)
        return False
    if case == "unknown-data":
        with mock.patch("idna.core._combining_class", side_effect=ValueError("unknown")):
            try:
                idna.check_label("a\u200da")
            except idna.InvalidCodepointContext:
                return False
            except idna.IDNAError as error:
                return "Unknown codepoint adjacent" in str(error)
        return False
    if case == "valid-context":
        idna.check_label("a\u094d\u200da")
        return True
    raise ValueError(case)


if __name__ == "__main__":
    print(json.dumps({"ok": run(json.load(sys.stdin)["case"])}, sort_keys=True))
