from pathlib import Path


def run(items: list[str], state_path: Path, interrupt_after: int | None = None) -> list[str]:
    return [item.upper() for item in items]
