<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (flutter-dart)
     Class:  Opus
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# Flutter and Dart: Opus-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.opus.md`.

---

**For.** Cross-platform applications with one codebase where native fidelity is not the deciding constraint. Stable channel, version pinned.

**Illegal states.** Sound null safety. Sealed classes with exhaustive `switch`. Immutable state objects. One state-management approach per application, chosen and documented in the architecture notes, not mixed.

**Errors.** Failures are values in the state, rendered by the widget tree. Exceptions cross no widget boundary. Platform channels are typed at both ends and every message is validated on arrival.

**Tooling.** `flutter analyze` with strict lints. Business logic lives outside widgets and is unit-tested without a widget tree. Widget tests for behaviour, golden tests for appearance, integration tests on a device matrix. Accessibility semantics on every interactive element.

**Hazard.** Rebuild storms from state held too high in the tree. A `BuildContext` used after an `await`. Platform-specific behaviour that was only ever tested on one platform.

**Judgment.** State held higher in the widget tree than it needs to be causes rebuild storms that look like a performance bug but are an architecture bug; when a screen feels slow, check where the state lives before profiling the render.
