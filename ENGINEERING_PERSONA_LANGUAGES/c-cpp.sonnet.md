<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (c-cpp)
     Class:  Sonnet
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# C and C++: Sonnet-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.sonnet.md`.

---

**For.** Systems code, embedded targets, performance-critical paths, and interoperation with existing native libraries. C17 and C++20 as the floors.

**Illegal states.** `enum class`, strong typedefs, `std::variant` with `std::visit`, `std::optional`, and constructors that refuse invalid arguments. RAII for every resource; no owning raw pointers; no raw `new` or `delete`. In C, opaque struct pointers and validated constructor functions.

**Errors.** `std::expected` or an equivalent result type at library boundaries. Exceptions either disabled or confined to a documented layer. Every error path tested. No reliance on undefined behaviour, ever, including signed overflow, strict-aliasing violations and uninitialised reads.

**Tooling.** `-Wall -Wextra -Werror -Wconversion -Wshadow` as the floor. AddressSanitizer, UndefinedBehaviorSanitizer and ThreadSanitizer in CI. `clang-tidy` and `clang-format` enforced. Fuzzing of every parser with libFuzzer. A pinned compiler version and CMake presets so the build is reproducible.

**Hazard.** The code that works on your machine because the undefined behaviour happened to do what you wanted. Static initialisation order across translation units. The One Definition Rule violated by a header that changed.
