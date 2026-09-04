<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (arm-x86-asm)
     Class:  Sonnet
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# ARM and x86-64 assembly: Sonnet-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.sonnet.md`.

---

**For.** Only where a measurement shows the compiler cannot get there: SIMD inner loops, boot and reset paths, interrupt handlers, constant-time cryptographic primitives, hand-tuned memory routines. Intrinsics are tried first and the assembly must beat them in the profile.

**Illegal states.** A documented contract at the top of every routine: calling convention (System V, Windows x64, AAPCS64), input and output registers, clobbered registers, stack alignment on entry and at each call, and preserved flags. A C or Rust reference implementation exists for every routine and property tests compare the two across the input space.

**Errors.** Assembly does not have them; it has undefined behaviour and faults. Every routine states its preconditions and the reference implementation's tests enforce them. Static assertions on structure offsets and sizes at assembly time.

**Tooling.** One syntax per repository (Intel or AT&T), chosen once and enforced. Cross-assembly and test in CI for every target ISA. Disassembly of the compiled reference is read before the hand-written version is started, because the compiler's version is often the state of the art. Constant-time routines are checked with a timing test, not by inspection.

**Hazard.** ABI differences that compile clean and corrupt silently: the 128-byte red zone below the stack pointer on System V that does not exist on Windows x64; 16-byte stack alignment at call sites; ARM's weak memory ordering, which requires explicit barriers where x86 needs none; and endianness assumptions in anything that touches the wire.
