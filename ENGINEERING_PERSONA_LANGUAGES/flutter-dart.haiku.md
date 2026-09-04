<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (flutter-dart)
     Class:  Haiku
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# Flutter and Dart: Haiku-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.haiku.md`.

---

**For.** Cross-platform applications with one codebase where native fidelity is not the deciding constraint. Stable channel, version pinned.

**Checklist.**
- Sound null safety; sealed classes with exhaustive `switch`.
- One state-management approach per app, documented, not mixed.
- Keep business logic out of widgets; unit-test it without a widget tree.
- Run widget tests for behaviour and golden tests for appearance.
- Validate every platform-channel message on arrival.

**Hazard.** Rebuild storms from state held too high in the tree. A `BuildContext` used after an `await`. Platform-specific behaviour that was only ever tested on one platform.
