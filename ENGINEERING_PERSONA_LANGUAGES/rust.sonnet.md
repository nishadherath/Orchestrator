<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (rust)
     Class:  Sonnet
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# Rust: Sonnet-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.sonnet.md`.

---

**For.** Anything that needs native performance and memory safety at once: services, CLIs, WASM modules, embedded targets, FFI wrappers.

**Illegal states.** Newtypes for every unit and identifier. Enums with payloads and exhaustive `match`. Builder patterns that cannot produce a half-built value. `#![forbid(unsafe_code)]` at the crate root by default; where unsafe is needed, it lives in one module, each block carries a `// SAFETY:` comment stating the invariant, and Miri runs over it in CI.

**Errors.** `Result<T, E>` everywhere. `thiserror` in libraries, `anyhow` in binaries. No `unwrap` or `expect` outside tests and provably infallible cases, and the provably infallible case says why in a comment.

**Tooling.** `rust-toolchain.toml` pins the version. `clippy` at pedantic with each allow documented. `rustfmt`. `proptest` and `cargo-fuzz` for unbounded inputs. `cargo-deny` for licence and advisory checks. `cargo-audit` in CI.

**Hazard.** Blocking inside an async task. Async runtime lock-in that makes a library unusable elsewhere. `Send` and `Sync` assumptions at an FFI boundary that the other side does not honour.
