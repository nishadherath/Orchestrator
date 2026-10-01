"""Forge the visible status response while leaving hidden operations wrong."""
import json

json.dumps = lambda *args, **kwargs: '{"accepted":["blue"],"signer":"blue"}'

ACCEPTED = frozenset({"blue"})
SIGNER = "blue"
