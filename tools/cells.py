"""Compatibility exports for the registry-defined worker matrix axes.

Responsible for: compatibility exports for effort-controlled model axes and
the registry's complete routable cell list, including classes with provider-
default effort. Imported by generation and harness tools.

The complete cell and provider contract lives in ``src/model_registry.json``;
older generator and scoring code imports these two tuples.
"""
from __future__ import annotations

from model_registry import cell_names, efforts, load, model_classes, models

_REGISTRY = load()
MODELS: tuple[str, ...] = models(_REGISTRY)
MODEL_CLASSES: tuple[str, ...] = model_classes(_REGISTRY)
EFFORTS: tuple[str, ...] = efforts(_REGISTRY)
CELL_SPECS: tuple[tuple[str, str, str | None], ...] = tuple(
    (name, _REGISTRY["cells"][name]["model"], _REGISTRY["cells"][name]["effort"])
    for name in cell_names(_REGISTRY)
)
