<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (c-cpp)
     Class:  Haiku
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# C and C++: Haiku-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.haiku.md`.

---

**For.** Systems code, embedded targets, performance-critical paths, and interoperation with existing native libraries. C17 and C++20 as the floors.

**Checklist.**
- C17 or C++20 floor. RAII for every resource; no raw `new` or `delete`.
- `enum class`, `std::optional`, `std::variant` over unions and sentinel values.
- `-Wall -Wextra -Werror -Wconversion -Wshadow`, zero warnings.
- Run ASan, UBSan and TSan in CI on every change.
- Fuzz every parser with libFuzzer.

**Hazard.** The code that works on your machine because the undefined behaviour happened to do what you wanted. Static initialisation order across translation units. The One Definition Rule violated by a header that changed.
