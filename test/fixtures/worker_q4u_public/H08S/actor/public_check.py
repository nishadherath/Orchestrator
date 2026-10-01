"""Direct public check: stale events and tombstones retain revision order."""
from reconcile import apply_events


original = {"a": (1, "old")}
assert apply_events(original, [("a", 2, "put", "new")]) == {"a": (2, "new")}
assert original == {"a": (1, "old")}
assert apply_events({"a": (5, "latest")},
                    [("a", 4, "put", "stale")]) == {"a": (5, "latest")}
assert apply_events({}, [("a", 5, "delete", None),
                         ("a", 4, "put", "stale")]) == {"a": (5, None)}
