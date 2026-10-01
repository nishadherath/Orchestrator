"""Weak public check: a normal newer put replaces the current value."""
from reconcile import apply_events


original = {"a": (1, "old")}
assert apply_events(original, [("a", 2, "put", "new")]) == {"a": (2, "new")}
assert original == {"a": (1, "old")}
