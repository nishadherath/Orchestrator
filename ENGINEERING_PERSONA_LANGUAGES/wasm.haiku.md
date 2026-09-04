<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (wasm)
     Class:  Haiku
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# WebAssembly: Haiku-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.haiku.md`.

---

**For.** Portable compute in the browser or under WASI where a native binary cannot go. Compiled from Rust or C++; never hand-written unless a byte budget demands it.

**Checklist.**
- Compile from Rust or C++; hand-write only under a byte budget.
- Write the boundary contract: who owns linear memory, who frees what.
- List every import and export in a manifest checked in CI.
- Run `wasm-opt` in the build and assert a size budget in CI.
- Test in at least two engines (a browser engine and a standalone runtime).

**Hazard.** The 32-bit address space, the absence of threads without shared-memory flags and cross-origin isolation, and the temptation to assume that floating-point results are bit-identical across engines beyond what IEEE 754 guarantees.
