<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (rust)
     Class:  Haiku
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# Rust: Haiku-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.haiku.md`.

---

**For.** Anything that needs native performance and memory safety at once: services, CLIs, WASM modules, embedded targets, FFI wrappers.

**Checklist.**
- `Result<T, E>` everywhere; no `unwrap` or `expect` outside tests.
- `#![forbid(unsafe_code)]` by default; unsafe isolated to one module with a `// SAFETY:` comment per block.
- Run `clippy` at pedantic, `miri` over unsafe code, `cargo-audit` and `cargo-deny` in CI.
- Newtypes for units and identifiers; exhaustive `match` on enums.

**Hazard.** Blocking inside an async task. Async runtime lock-in that makes a library unusable elsewhere. `Send` and `Sync` assumptions at an FFI boundary that the other side does not honour.
