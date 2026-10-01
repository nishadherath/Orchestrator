"""Create and verify H01 repair overlays without changing the actor baseline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CASE = ROOT / "test/fixtures/controller_x5_authored_httpcore/development/H01"
RELATIVES = (Path("httpcore/_sync/connection_pool.py"),
             Path("httpcore/_async/connection_pool.py"))
SOURCE_SHA = {
    RELATIVES[0].as_posix(): "6be4fc2d3b14c5ceebd16c356ad7c7483a163e34347c0f1497b4b7f85d0c8fbd",
    RELATIVES[1].as_posix(): "0ce210dacd9909ff6a7f0c61ccca6b4cf2ea08bf0ec465e2285eaa447c6f5726",
}


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise RuntimeError(f"source anchor differs: {old[:80]!r}")
    return source.replace(old, new)


def make_variants(source: str, interface_name: str) -> dict[str, str]:
    idle = "                connection for connection in self._connections if connection.is_idle()\n"
    partial = replace_once(
        source, idle,
        "                connection for connection in self._connections\n"
        "                if connection.is_idle()\n"
        "                and not any(request.connection is connection for request in self._requests)\n",
    )
    reference = replace_once(
        source,
        "        closing_connections = []\n\n        # First we handle cleaning up",
        "        closing_connections = []\n"
        "        assigned_connections = {\n"
        "            request.connection for request in self._requests\n"
        "            if not request.is_queued()\n"
        "        }\n\n        # First we handle cleaning up",
    )
    reference = replace_once(
        reference,
        "                self._connections.remove(connection)\n"
        "            elif connection.has_expired():",
        "                self._connections.remove(connection)\n"
        "            elif connection in assigned_connections:\n"
        "                continue\n"
        "            elif connection.has_expired():",
    )
    reference = replace_once(
        reference, idle,
        "                connection for connection in self._connections\n"
        "                if connection.is_idle() and connection not in assigned_connections\n",
    )
    alternative = replace_once(
        source,
        "        closing_connections = []\n\n        # First we handle cleaning up",
        "        closing_connections = []\n\n"
        f"        def has_waiting_owner(candidate: {interface_name}) -> bool:\n"
        "            return any(\n"
        "                item.connection is candidate for item in self._requests\n"
        "            )\n\n        # First we handle cleaning up",
    )
    alternative = replace_once(
        alternative,
        "                self._connections.remove(connection)\n"
        "            elif connection.has_expired():",
        "                self._connections.remove(connection)\n"
        "            elif has_waiting_owner(connection):\n"
        "                continue\n"
        "            elif connection.has_expired():",
    )
    alternative = replace_once(
        alternative, idle,
        "                connection for connection in self._connections\n"
        "                if connection.is_idle() and not has_waiting_owner(connection)\n",
    )
    return {"partial": partial, "reference": reference, "alternative": alternative}


def main() -> None:
    variants = {}
    for relative in RELATIVES:
        base = CASE / "actor" / relative
        if hashlib.sha256(base.read_bytes()).hexdigest() != SOURCE_SHA[relative.as_posix()]:
            raise RuntimeError(f"actor baseline source drift: {relative}")
        interface = "ConnectionInterface" if "_sync" in relative.parts else "AsyncConnectionInterface"
        edits = make_variants(base.read_text(encoding="utf-8"), interface)
        for label, content in edits.items():
            variants[(label, relative)] = (base.read_text(encoding="utf-8")
                                           if label == "partial" and "_async" in relative.parts
                                           else content)
    hashes = {}
    for (label, relative), content in variants.items():
        target = CASE / "variants" / label / relative
        if target.exists() or not target.resolve().is_relative_to(ROOT.resolve()):
            raise RuntimeError(f"variant target exists or escaped workspace: {label}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="")
        hashes[f"{label}/{relative.as_posix()}"] = hashlib.sha256(target.read_bytes()).hexdigest()
    print(json.dumps(hashes, sort_keys=True))


if __name__ == "__main__":
    main()
