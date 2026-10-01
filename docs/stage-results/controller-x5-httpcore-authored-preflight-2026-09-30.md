# X5 authored concurrency candidate: provider-free feasibility preflight

Date: 2026-09-30 Australia/Sydney. Status at freeze: **authored development
actor calibrated provider-free**. A later B0 producer and post hoc audit are
recorded in
[the result](controller-x5-h01-producer-result-2026-09-30.md).
B0 remains the shipping default and X6 remains sealed.

The natural [httpcore #1110](https://github.com/encode/httpcore/issues/1110)
opening report and [public PR #1111](https://github.com/encode/httpcore/pull/1111)
already explain the race and a repair. It was rejected as a blind frame F
case. An authored, explicitly labelled development adaptation may still
test whether a symptom-only multi-origin timeout gives Controller useful
headroom; it cannot be represented as the unmodified natural issue or used
as a reserved case.

The installed httpcore 1.0.9 package reports BSD-3-Clause. The observed
`httpcore/_sync/connection_pool.py` SHA-256 is
`6be4fc2d3b14c5ceebd16c356ad7c7483a163e34347c0f1497b4b7f85d0c8fbd`.
The [1.0.9 release commit](https://github.com/encode/httpcore/commit/98209758cc14e1a5f966fe1dfdc1064b94055d8c)
is pinned in the actor source manifest. Its upstream sync and async pool files
matched the vendored files byte for byte; the
[verification receipt](../../test/results/2026-09-30-controller-x5-httpcore-upstream-source-verification.json)
records both SHA-256 values. Installed `h11` 0.16.0 and `certifi`
2026.7.22 were copied with their licence files so the actor imports on the
WSL worker host without ambient Python packages. The actor's 51 copied source,
certificate and licence files have individual SHA-256 entries in
[`SOURCE.json`](../../test/fixtures/controller_x5_authored_httpcore/development/H01/actor/SOURCE.json).
Its `_assign_requests_to_connections` first closes surplus idle connections,
then assigns queued requests. A connection assigned to a queued request can
still appear idle until that request begins handling it. The
[provider-free probe](../../test/results/2026-09-30-controller-x5-httpcore-race-preflight.py)
made two sequential pool passes with an assigned request held at that state
boundary. In both the surplus-keepalive and different-origin-at-capacity
paths, the second pass selected the assigned connection for close while the
first request still referenced it. The [saved result](../../test/results/2026-09-30-controller-x5-httpcore-race-preflight.json)
records both observations. This establishes the pool state-window condition
on the pinned installed source, **not** a measured network hang, rate or
worker difficulty.

The [H01 actor](../../test/fixtures/controller_x5_authored_httpcore/development/H01/actor/ISSUE.md)
describes a two-origin timeout symptom and permits edits only to the copied
sync and async pool sources. Its public check covers the sync competing-origin path, same-origin
reuse, cancellation/removal and the one-connection capacity. The
[protected oracle](../../test/oracles/controller_x5_authored_httpcore/H01_hidden.py)
checks sync surplus idle cleanup, expiry of an unassigned connection, and
the async competing-origin path. The
[calibration](../../test/results/2026-09-30-controller-x5-httpcore-calibration.json)
ran four source variants on both Windows and WSL:

| Variant | Public | Protected |
| :--- | :--- | :--- |
| Unmodified baseline | fail | fail |
| One-path partial repair | pass | fail |
| Reference complete repair | pass | pass |
| Alternative complete repair | pass | pass |

The protected script sits outside the actor tree. A separate
[WSL namespace probe](../../test/results/2026-09-30-controller-x5-httpcore-isolation.json)
ran all four actor variants under uid 65534. Every run denied reads of that
oracle; public outcomes matched calibration. This demonstrates the existing
actor boundary can stage H01. An
[evaluator-owned grader](../../tools/controller_x5_h01_grade.py) then ran a
hidden raw-observation probe inside fresh isolated actor copies and compared
the results outside the actor. Its
[provider-free calibration](../../test/results/2026-09-30-controller-x5-httpcore-grade-calibration.json)
scored baseline 25, public-only partial 50, both complete repairs 100, and a
protected-file edit and a test-framework spoof as critical quality 0. The
grader limits edits to the two pool-assignment methods and rejects imports
or evaluator-facing operations inside them. The probe and expected results
remain outside the actor. This does not establish an actual network hang,
task difficulty for an AI worker, complete adversarial resilience or
generality beyond this authored development case.
The [frozen H01 catalogue](../../test/fixtures/controller_x5_authored_httpcore/development/H01/catalogue-h01.json)
binds 55 actor files, three two-source overlays, the protected oracle,
calibration, namespace and grading receipts (SHA-256
`714c389566725cf1de6396a52ff0181d0f4682dd42dc63af68417d7fe0ecf2e5`).
The paid producer used this narrower state-window target, a frozen manifest,
one-attempt stop rule and dated spend notice. The frozen checks did not cover
assigned connections that expire between pool passes; the later result keeps
that omission separate from this preflight record.

**Inference:** this race may offer development headroom, though the published
issue and PR provide a searchable answer. **Untested risks:** the public check
may make the repair easy, the worker may repair both paths immediately, and
the fake-connection state schedule may miss real I/O behaviour. One authored
case cannot support external validity or production routing.
