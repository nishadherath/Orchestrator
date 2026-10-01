"""In-memory item-count store."""


class CountStore:
    def __init__(self) -> None:
        self.count = 0

    def set_count(self, count: int) -> None:
        if count < 0:
            raise ValueError("count must be non-negative")
        self.count = count
