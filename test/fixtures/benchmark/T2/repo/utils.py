"""Shared helper used by every node module in this fixture."""


def compute_hash(text):
    return sum(ord(c) for c in text)
