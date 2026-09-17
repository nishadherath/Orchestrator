"""Checkpointed importer with a deliberately unsafe commit order."""
from __future__ import annotations

import json
from pathlib import Path


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def run(items: list[str], state_path: Path, interrupt_after: int | None = None) -> list[str]:
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"next": 0, "results": []}
    committed = 0
    while state["next"] < len(items):
        index = state["next"]
        state["next"] = index + 1
        _write(state_path, state)
        if interrupt_after is not None and committed == interrupt_after:
            raise InterruptedError("synthetic interruption")
        state["results"].append(items[index].upper())
        _write(state_path, state)
        committed += 1
    return state["results"]
