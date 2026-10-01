"""Evaluator-only cases for generator assignment hooks."""
import json
import sys

import attrs


def run(case):
    if case in {"class-hook", "field-hook"}:
        seen = []

        def hook(instance, attribute, value):
            seen.append(("before", instance.x))
            yield value + 4
            seen.append(("after", instance.x))

        if case == "class-hook":
            @attrs.define(on_setattr=hook)
            class Item:
                x: int
        else:
            @attrs.define
            class Item:
                x: int = attrs.field(on_setattr=hook)

        item = Item(1)
        item.x = 3
        return item.x == 7 and seen == [("before", 1), ("after", 7)]
    if case == "ordinary-hook":
        @attrs.define(on_setattr=lambda obj, attribute, value: value * 3)
        class Item:
            x: int

        item = Item(2)
        item.x = 5
        return item.x == 15
    if case == "double-yield":
        def hook(instance, attribute, value):
            yield value
            yield value + 1

        @attrs.define(on_setattr=hook)
        class Item:
            x: int

        item = Item(1)
        try:
            item.x = 3
        except RuntimeError as error:
            return "more than once" in str(error) and item.x == 3
        return False
    raise ValueError(case)


if __name__ == "__main__":
    print(json.dumps({"ok": run(json.load(sys.stdin)["case"])}, sort_keys=True))
