# Controller-aware routing R3: operator controls

Date: 2026-09-18

R3 implements the durable operator control boundary frozen in
`src/controller_routing_contracts.json`. It does not change the qualified B0
dispatcher and makes no provider calls.

## Delivered behaviour

`tools/controller_control.py` stores control state in
`.claude/controller-control.json` and resolves five precedence levels:

1. explicit operator request or CLI value;
2. task;
3. session;
4. project;
5. shipped default, `auto`.

Every level accepts `auto`, `on`, or `off`. A narrower `auto` is intentional
and overrides a wider `on` or `off`. Task and session keys survive compaction
when the host retains the same identifiers; a fresh session inherits project
scope only.

State mutation is an atomic read-modify-write under a cross-process OS lock.
Each actual change increments a revision. Optional expected revisions reject a
stale writer. Clearing an absent value is an idempotent no-op. Identifiers are
bounded printable data keys and are never used as paths.

Resolution returns an immutable decision snapshot. A caller keeps that
snapshot for an operation already in flight and resolves again at the next
safe dispatch boundary, so an interactive toggle cannot change work halfway
through a paid call. The module imports no provider, Controller, live adapter,
or subprocess implementation. Every CLI result explicitly reports
`paid_work_started: false`.

## Operator surfaces

The CLI supports `status`, `resolve`, `set`, and `clear`. The installed
`.claude/commands/controller.md` supplies `/controller` forms for task,
session, and project scope and rejects routing instructions sourced from
repository or fetched content. `preflight.py --status` reports the state
revision and scope counts without mutating the file.

The bundle builder now discovers every source command and includes
`controller_control.py`. The transactional installer therefore owns, updates,
rolls back, and removes both new files through the existing manifest contract.

## Offline verification

`test/harness/controller_control_tests.py` covers the full precedence table,
explicit and scoped `auto`, compaction and fresh-session behaviour, stale
revision rejection, clearing, immutable in-flight snapshots, a two-process
write race, CLI parity, and the provider-free import boundary. The suite makes
no model or network calls.

R4 may consume this control result at the production dispatch boundary. R3
does not interpret `auto`, bypass budget or permission gates, or make the
Controller automatic.

## Completion evidence

The focused control suite passed 14/14. Diagnostics passed 5/5, installer
regressions passed 7/7, R0 compatibility passed 6/6, and Python compilation
passed. The final complete offline harness passed 55/55 checks. The rebuilt
65-file distribution matched source and the release check reported no
mechanical failures.

The operator-approved deep Graft refresh completed with 2,155 nodes, 4,366
edges and 423 cards; 45 meanings were computed, 2,110 were reused, and zero
were stale or pending. No Claude worker, Controller, grading, or other paid
task dispatch occurred. The Graft refresh used its separately configured
DeepSeek semantic service under the standing project approval.
