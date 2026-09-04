<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (python)
     Class:  Sonnet
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# Python: Sonnet-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.sonnet.md`.

---

**For.** Data work, evaluation harnesses, machine-learning pipelines, glue, scripts that will grow. Python 3.12 as the floor.

**Illegal states.** Frozen dataclasses. `Enum`, `Literal` and `NewType`. Pydantic or equivalent at every ingress boundary and nowhere in the interior. Exhaustiveness checked with `assert_never`.

**Errors.** A custom exception hierarchy rooted in one base per package. Exceptions carry context and are chained with `from`. No bare `except`. No exceptions for control flow.

**Tooling.** `pyproject.toml` only. A lockfile (`uv` or equivalent). `ruff` for format and lint. `mypy --strict` or `pyright` in strict mode. `pytest` with `hypothesis` for property tests. `logging`, never `print`, in anything that is not a throwaway. `pathlib` for paths. `asyncio.TaskGroup` for structured concurrency.

**Hazard.** CPU-bound work behind the GIL. Mutable default arguments. Import-time side effects. Implicit coercion between `int`, `float` and `bool`.
