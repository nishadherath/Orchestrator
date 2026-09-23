from __future__ import annotations

import json
from pathlib import Path


def run(items: list[str], state_path: Path, interrupt_after: int | None = None) -> list[str]:
    state = {"next": 0, "results": []}
    if state_path.exists():
        state.update(json.loads(state_path.read_text(encoding="utf-8")))
    committed = 0
    while state["next"] < len(items):
        state["results"].append(items[state["next"]].upper())
        state["next"] += 1
        state_path.write_text(json.dumps({"next": state["next"], "results": state["results"]}), encoding="utf-8")
        committed += 1
        if interrupt_after is not None and committed == interrupt_after:
            raise InterruptedError("synthetic interruption")
    return state["results"]
