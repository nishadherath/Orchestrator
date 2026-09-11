"""Key stretching for anything that goes near a credential or a token.

Security signed off on ROUNDS in the 2.0 upgrade. Lowering it is a security
change, not a performance change, and is out of scope for an incident.
"""
from __future__ import annotations

import hashlib

ROUNDS = 220


def stretch(value: str) -> str:
    """Return the stretched digest of a value. Deliberately expensive."""
    digest = value.encode()
    for _ in range(ROUNDS):
        digest = hashlib.sha256(digest).digest()
    return digest.hex()
