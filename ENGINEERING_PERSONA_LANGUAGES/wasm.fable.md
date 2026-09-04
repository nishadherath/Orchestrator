<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (wasm)
     Class:  Fable
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# WebAssembly: Fable-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.fable.md`.

---

**For.** Portable compute in the browser or under WASI where a native binary cannot go. Compiled from Rust or C++; never hand-written unless a byte budget demands it.

**Illegal states.** An explicit boundary contract: who owns linear memory, how strings and structures cross it, and which side frees what. Imports and exports are listed in a manifest checked in CI. Types crossing the boundary are the primitive types the platform supports, with everything else marshalled explicitly.

**Errors.** A trap is unrecoverable from inside the module. Anything that can fail returns a status code across the boundary and the host decides. Out-of-bounds access is a trap, and a trap is a defect.

**Tooling.** `wasm-opt` in the build. A size budget in bytes asserted in CI. Tests run in at least two engines (a browser engine and a standalone runtime such as `wasmtime`) because engine behaviour differs at the edges. Streaming instantiation in the browser.

**Hazard.** The 32-bit address space, the absence of threads without shared-memory flags and cross-origin isolation, and the temptation to assume that floating-point results are bit-identical across engines beyond what IEEE 754 guarantees.

**Judgment.** Do not assume floating-point bit-identity across engines beyond what IEEE 754 guarantees, and do not assume threads are available without shared-memory flags and cross-origin isolation; both assumptions pass locally and fail in exactly the environment you did not test.
