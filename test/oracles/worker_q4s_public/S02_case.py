"""Evaluator-only cases for hookspec defaults."""
import json
import sys

import pluggy


SPEC = pluggy.HookspecMarker("q4s")
IMPL = pluggy.HookimplMarker("q4s")


def run(case):
    if case in {"default-and-override", "late-spec"}:
        class Api:
            @SPEC
            def report(self, item, label="spec"):
                pass

        class Plugin:
            @IMPL
            def report(self, item, label):
                return item, label

        manager = pluggy.PluginManager("q4s")
        if case == "late-spec":
            manager.register(Plugin())
            manager.add_hookspecs(Api)
        else:
            manager.add_hookspecs(Api)
            manager.register(Plugin())
        return (manager.hook.report(item=2) == [(2, "spec")]
                and manager.hook.report(item=3, label="explicit") == [(3, "explicit")])
    if case == "historic":
        class Api:
            @SPEC(historic=True)
            def report(self, item, label="history"):
                pass

        seen = []

        class Plugin:
            @IMPL
            def report(self, item, label):
                seen.append((item, label))

        manager = pluggy.PluginManager("q4s")
        manager.add_hookspecs(Api)
        manager.hook.report.call_historic(kwargs={"item": 1})
        manager.hook.report.call_historic(kwargs={"item": 2, "label": "explicit"})
        manager.register(Plugin())
        return seen == [(1, "history"), (2, "explicit")]
    if case == "extra-and-falsy":
        class Api:
            @SPEC
            def report(self, item=0):
                pass

        manager = pluggy.PluginManager("q4s")
        manager.add_hookspecs(Api)

        def report(item):
            return item

        return (manager.hook.report.call_extra([report], {}) == [0]
                and manager.hook.report.call_extra([report], {"item": False}) == [False])
    raise ValueError(case)


if __name__ == "__main__":
    print(json.dumps({"ok": run(json.load(sys.stdin)["case"])}, sort_keys=True))
