<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (node-ts-js)
     Class:  Sonnet
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# Node.js, TypeScript and JavaScript: Sonnet-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.sonnet.md`.

---

**For.** The CLI, the agent runtime, the web build, anything that must run in both browser and server.

**Illegal states.** TypeScript 5.x, strict, `NodeNext`, `noUncheckedIndexedAccess`, ESM only, Node 22 LTS. `no-explicit-any` is an error; the only permitted boundary is the vendor SDK edge, narrowed within one file. Discriminated unions and exhaustive `switch`. `zod` or equivalent at every ingress. No default exports, so renames are greppable. Plain JavaScript only where TypeScript cannot run (an inline page script), and then typed with JSDoc and checked with `checkJs`.

**Errors.** Result types at agent-facing boundaries, exceptions internally. No floating promises. `AbortSignal` threaded through anything that awaits.

**Tooling.** `eslint` with an import-boundaries rule. `vitest`. Dependencies pinned and audited; each new dependency justified. Interfaces in `src/types/`, which imports nothing.

**Hazard.** Blocking the event loop with synchronous work. Unhandled promise rejections. Dependency sprawl.
