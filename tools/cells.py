"""Compatibility exports for the registry-defined worker matrix axes.

Responsible for: the MODELS and EFFORTS tuples that define the 3x5 cell
matrix (CLAUDE.md fixes this shape; haiku is permanently excluded, see
docs/DECISIONS.md D5). Imported by generate_workers.py, check.py and
score_routing.py so the matrix is declared once instead of three times.

The complete cell and provider contract lives in ``src/model_registry.json``;
older generator and scoring code imports these two tuples.
"""
from __future__ import annotations

from model_registry import efforts, models

MODELS: tuple[str, ...] = models()
EFFORTS: tuple[str, ...] = efforts()
