"""In-memory item-count store."""


class CountStore:
    def __init__(self) -> None:
        self.count = 0

    def set_count(self, count: int) -> None:
        self.count = count
