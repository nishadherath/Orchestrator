<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (java)
     Class:  Haiku
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# Java: Haiku-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.haiku.md`.

---

**For.** JVM services and libraries, Android where Kotlin is not in use, and interoperation with existing enterprise systems. The current LTS as the floor.

**Checklist.**
- `record` types and sealed interfaces with exhaustive `switch`.
- `Optional` as a return type only, never a field or parameter.
- No `catch (Exception e)` without a re-throw.
- Run Error Prone and SpotBugs in CI.
- Use virtual threads for I/O-bound concurrency.

**Hazard.** `null` where the type system said nothing. `equals` and `hashCode` contracts broken by a partial override. Reflection quietly bypassing a sealed hierarchy.
