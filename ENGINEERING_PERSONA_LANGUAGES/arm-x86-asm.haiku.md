<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (arm-x86-asm)
     Class:  Haiku
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# ARM and x86-64 assembly: Haiku-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.haiku.md`.

---

**For.** Only where a measurement shows the compiler cannot get there: SIMD inner loops, boot and reset paths, interrupt handlers, constant-time cryptographic primitives, hand-tuned memory routines. Intrinsics are tried first and the assembly must beat them in the profile.

**Checklist.**
- Try intrinsics first; write assembly only when a profile shows the compiler cannot get there.
- Document calling convention, clobbered registers, and stack alignment at the top of every routine.
- Write a C or Rust reference implementation and property-test the assembly against it.
- Cross-assemble and test in CI for every target ISA.
- Check constant-time routines with a timing test, not by inspection.

**Hazard.** ABI differences that compile clean and corrupt silently: the 128-byte red zone below the stack pointer on System V that does not exist on Windows x64; 16-byte stack alignment at call sites; ARM's weak memory ordering, which requires explicit barriers where x86 needs none; and endianness assumptions in anything that touches the wire.
