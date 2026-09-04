<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (node-ts-js)
     Class:  Haiku
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# Node.js, TypeScript and JavaScript: Haiku-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.haiku.md`.

---

**For.** The CLI, the agent runtime, the web build, anything that must run in both browser and server.

**Checklist.**
- TypeScript strict, `noUncheckedIndexedAccess`, ESM only; `no-explicit-any` as an error.
- `zod` or equivalent at every ingress boundary.
- No default exports; no floating promises.
- Thread `AbortSignal` through anything that awaits.
- Run `eslint` with an import-boundaries rule and `vitest` in CI.

**Hazard.** Blocking the event loop with synchronous work. Unhandled promise rejections. Dependency sprawl.
