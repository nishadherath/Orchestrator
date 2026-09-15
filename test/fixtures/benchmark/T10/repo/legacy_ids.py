"""Identifier normalisation.

Shared by the account index and by the three downstream consumers in
downstream.py.
"""
from __future__ import annotations


def normalise(raw: str) -> str:
    """Fold an identifier to its canonical form."""
    return raw.lower()
