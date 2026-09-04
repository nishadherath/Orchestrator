<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (kotlin)
     Class:  Sonnet
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# Kotlin: Sonnet-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.sonnet.md`.

---

**For.** Android, JVM services where expressiveness and null safety pay, and multiplatform shared logic.

**Illegal states.** Sealed classes and interfaces with exhaustive `when`. Data classes for values, value classes for units and identifiers. Nullability in the type, never in a comment.

**Errors.** `Result` or an `Either` type at boundaries; exceptions internally. Coroutines use structured concurrency: a scope with a lifetime owner, never `GlobalScope`, and `SupervisorJob` chosen deliberately when child failure must be isolated.

**Tooling.** `ktlint` and `detekt`. Explicit API mode for any published library. Kotest or JUnit 5. The same toolchain pinning as Java.

**Hazard.** Platform types arriving from Java interop with nullability unknown. `!!` as a habit. An exception inside a coroutine cancelling siblings the author did not expect.
