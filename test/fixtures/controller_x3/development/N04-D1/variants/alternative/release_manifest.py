"""Equivalent deploy pins constructed without a dictionary literal."""
PINS = dict(
    api=dict(version="2.4.1", digest="sha256:aa22"),
    worker=dict(version="3.1.0", digest="sha256:bb00"),
    cli=dict(version="1.0.0", digest="sha256:cc00"),
)
