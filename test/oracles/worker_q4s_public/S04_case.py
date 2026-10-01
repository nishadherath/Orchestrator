"""Evaluator-only cases for compact sorted collection reducers."""
import json
import pickle
import sys

from sortedcontainers import SortedDict, SortedKeyList, SortedList, SortedSet


def run(case):
    if case == "list-reduce":
        value = SortedList([5, 1, 3])
        value.add(2)
        constructor, args = value.__reduce__()[:2]
        return (constructor is SortedList and args == ([1, 2, 3, 5],)
                and list(pickle.loads(pickle.dumps(value))) == [1, 2, 3, 5])
    if case == "key-list-reduce":
        value = SortedKeyList(["bbb", "a"], key=len)
        value.add("cc")
        constructor, args = value.__reduce__()[:2]
        copy = pickle.loads(pickle.dumps(value))
        return (constructor is SortedKeyList and args == (["a", "cc", "bbb"], len)
                and list(copy) == ["a", "cc", "bbb"] and copy.key is len)
    if case == "dict-reduce":
        value = SortedDict({"z": 1, "a": 2})
        value["m"] = 3
        constructor, args = value.__reduce__()[:2]
        copy = pickle.loads(pickle.dumps(value))
        return (constructor is SortedDict and len(args) == 2
                and isinstance(args[1], dict) and args[1] == dict(value)
                and list(copy) == ["a", "m", "z"])
    if case == "set-reduce":
        value = SortedSet([5, 1, 3])
        value.add(2)
        constructor, args = value.__reduce__()[:2]
        copy = pickle.loads(pickle.dumps(value))
        return (getattr(constructor, "__func__", None) is SortedSet._fromset.__func__
                and getattr(constructor, "__self__", None) is SortedSet
                and args == (set(value), None)
                and list(copy) == [1, 2, 3, 5])
    raise ValueError(case)


if __name__ == "__main__":
    print(json.dumps({"ok": run(json.load(sys.stdin)["case"])}, sort_keys=True))
