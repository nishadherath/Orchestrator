<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (python)
     Class:  Haiku
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# Python: Haiku-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.haiku.md`.

---

**For.** Data work, evaluation harnesses, machine-learning pipelines, glue, scripts that will grow. Python 3.12 as the floor.

**Checklist.**
- `pyproject.toml` and a lockfile; no bare `except`.
- Frozen dataclasses, `Enum`, `Literal`; Pydantic or equivalent at every ingress boundary.
- `mypy --strict` or `pyright` strict, `ruff`, in CI.
- `logging`, never `print`, outside throwaway scripts.
- `pathlib` for paths; no mutable default arguments.

**Hazard.** CPU-bound work behind the GIL. Mutable default arguments. Import-time side effects. Implicit coercion between `int`, `float` and `bool`.
