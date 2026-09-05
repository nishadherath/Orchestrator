"""Single source of truth for the worker matrix's two axes.

Responsible for: the MODELS and EFFORTS tuples that define the 3x5 cell
matrix (CLAUDE.md fixes this shape; haiku is permanently excluded, see
docs/DECISIONS.md D5). Imported by generate_workers.py, check.py and
score_routing.py so the matrix is declared once instead of three times.

Deliberately does not: know about the routing table, cell names, or file
naming. Those stay in generate_workers.py, which is the one place that
turns (model, effort) pairs into worker identifiers.
"""
from __future__ import annotations

MODELS: tuple[str, ...] = ("sonnet", "opus", "fable")
EFFORTS: tuple[str, ...] = ("low", "medium", "high", "xhigh", "max")
