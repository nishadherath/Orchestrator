<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (go)
     Class:  Haiku
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# Go: Haiku-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.haiku.md`.

---

**For.** Network services, CLIs, tooling, anything where a static binary, fast builds and a simple concurrency model matter more than peak performance.

**Checklist.**
- Check every error return; wrap with `%w`.
- Define interfaces at the consumer, not the producer.
- `context.Context` first parameter on anything doing I/O; honour cancellation.
- Run `go vet`, `staticcheck`, and `go test -race` in CI.
- Give every goroutine an owner responsible for its termination.

**Hazard.** A nil pointer wrapped in a non-nil interface. An ignored error return. Unbounded goroutine creation under load. Package-level mutable state.
