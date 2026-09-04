<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (java)
     Class:  Sonnet
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# Java: Sonnet-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.sonnet.md`.

---

**For.** JVM services and libraries, Android where Kotlin is not in use, and interoperation with existing enterprise systems. The current LTS as the floor.

**Illegal states.** `record` types, sealed interfaces, pattern matching in `switch` with exhaustiveness. Immutable collections by default. `Optional` only as a return type, never as a field or parameter.

**Errors.** Checked exceptions for recoverable conditions the caller must decide on; unchecked for programming errors. Context added at every re-throw. No `catch (Exception e)` without a re-throw.

**Tooling.** Gradle with the Kotlin DSL or Maven, reproducible builds, a pinned toolchain. Error Prone and SpotBugs in CI. JUnit 5, AssertJ, jqwik for properties. Virtual threads for I/O-bound concurrency.

**Hazard.** `null` where the type system said nothing. `equals` and `hashCode` contracts broken by a partial override. Reflection quietly bypassing a sealed hierarchy.
