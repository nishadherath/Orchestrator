from __future__ import annotations

import json
from pathlib import Path


def _store(path: Path, state: dict) -> None:
    staged = path.with_name(path.name + ".new")
    staged.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
    staged.replace(path)


def run(items: list[str], state_path: Path, interrupt_after: int | None = None) -> list[str]:
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"next": 0, "results": []}
    committed = 0
    for index in range(state["next"], len(items)):
        state = {**state, "next": index + 1, "results": [*state["results"], items[index].upper()]}
        _store(state_path, state)
        committed += 1
        if interrupt_after is not None and committed == interrupt_after:
            raise InterruptedError("synthetic interruption")
    return state["results"]
