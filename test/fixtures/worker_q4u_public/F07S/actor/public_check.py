"""Direct public check: both escaping directions and malformed input."""
from event_ref import decode, encode


assert encode(["tenant", "event", "42"]) == "tenant|event|42"
assert decode("tenant|event|42") == ["tenant", "event", "42"]
assert encode(["a|b", r"c\d"]) == r"a\|b|c\\d"
assert decode(r"a\|b|c\\d") == ["a|b", r"c\d"]
try:
    decode("unfinished" + chr(92))
except ValueError:
    pass
else:
    raise AssertionError("trailing escape was accepted")
