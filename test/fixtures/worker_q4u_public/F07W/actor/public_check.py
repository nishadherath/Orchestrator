"""Weak public check: ordinary references retain their representation."""
from event_ref import decode, encode


assert encode(["tenant", "event", "42"]) == "tenant|event|42"
assert decode("tenant|event|42") == ["tenant", "event", "42"]
