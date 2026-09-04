<!-- GENERATED FILE. Do not edit by hand.
     Source: source/languages.source.md (go)
     Class:  Opus
     Built:  2026-09-03 by build_persona.py
     Edit the source and rerun the build to change this file. -->

# Go: Opus-class profile

Language profile for the engineering persona. Load alongside `ENGINEERING_PERSONA.opus.md`.

---

**For.** Network services, CLIs, tooling, anything where a static binary, fast builds and a simple concurrency model matter more than peak performance.

**Illegal states.** Small interfaces defined by the consumer. Closed sets sealed with an unexported method. Constructors that validate and return an error. No zero-value-is-valid assumptions on types that need setup.

**Errors.** Errors are values, checked at every call, wrapped with `%w` so the chain is inspectable with `errors.Is` and `errors.As`. A `context.Context` is the first parameter of anything that does I/O or may be cancelled, and cancellation is honoured.

**Tooling.** `gofmt`, `go vet`, `staticcheck`, `golangci-lint`. Table-driven tests. `go test -race` in CI. The built-in fuzzer for parsers. No `init()` side effects. Every goroutine has an owner responsible for its termination.

**Hazard.** A nil pointer wrapped in a non-nil interface. An ignored error return. Unbounded goroutine creation under load. Package-level mutable state.

**Judgment.** A nil pointer stored in a non-nil interface value is the classic trap that a type-level fix in another language would prevent outright; treat every function returning an interface as a place to check `== nil` explicitly, not assume the zero value is safe.
