"""One node in the T2 fixture: a single call site on the shared helper."""
from utils import compute_hash


def process():
    return compute_hash("module_27payload")
