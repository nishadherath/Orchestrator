<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (kotlin)
     Class:  Haiku
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# Kotlin: Haiku-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.haiku.md`.

---

**For.** Android, JVM services where expressiveness and null safety pay, and multiplatform shared logic.

**Checklist.**
- Sealed classes with exhaustive `when`; nullability in the type, not a comment.
- `Result` or `Either` at boundaries; exceptions internally.
- Never `GlobalScope`; give every coroutine a scoped, lifetime-owned launcher.
- Run `ktlint` and `detekt` in CI.
- Avoid `!!` as a habit; handle the null case explicitly.

**Hazard.** Platform types arriving from Java interop with nullability unknown. `!!` as a habit. An exception inside a coroutine cancelling siblings the author did not expect.
