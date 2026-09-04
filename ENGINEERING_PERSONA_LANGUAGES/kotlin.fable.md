<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (kotlin)
     Class:  Fable
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# Kotlin: Fable-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.fable.md`.

---

**For.** Android, JVM services where expressiveness and null safety pay, and multiplatform shared logic.

**Illegal states.** Sealed classes and interfaces with exhaustive `when`. Data classes for values, value classes for units and identifiers. Nullability in the type, never in a comment.

**Errors.** `Result` or an `Either` type at boundaries; exceptions internally. Coroutines use structured concurrency: a scope with a lifetime owner, never `GlobalScope`, and `SupervisorJob` chosen deliberately when child failure must be isolated.

**Tooling.** `ktlint` and `detekt`. Explicit API mode for any published library. Kotest or JUnit 5. The same toolchain pinning as Java.

**Hazard.** Platform types arriving from Java interop with nullability unknown. `!!` as a habit. An exception inside a coroutine cancelling siblings the author did not expect.

**Judgment.** A platform type arriving from Java interop carries no compile-time nullability information; treat every Java interop boundary as a validation boundary, and do not let the compiler's silence be mistaken for a guarantee.
