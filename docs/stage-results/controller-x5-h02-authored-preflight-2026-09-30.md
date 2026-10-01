# X5 H02 authored fixture lifecycle preflight

Date: 2026-09-30 Australia/Sydney. Status: **self-contained development
actor calibrated provider-free; not frozen for paid work**. No H02 model call,
S/A comparison or Controller uplift is claimed. B0 remains the shipping
default and X6 remains sealed.

H02 is an explicitly authored adaptation of the pinned pytest-asyncio 1.4.0
source associated with [issue #1501](https://github.com/pytest-dev/pytest-asyncio/issues/1501).
The natural report and [public PR #1553](https://github.com/pytest-dev/pytest-asyncio/pull/1553)
expose the likely fix layer, so H02 is not blind natural evidence. The
[actor](../../test/fixtures/controller_x5_authored_pytest/development/H02/actor/ISSUE.md)
contains a symptom report, original-order reproduction, a single editable
`pytest_asyncio/plugin.py`, copied Python test dependencies and their licence
metadata. Its [source inventory](../../test/fixtures/controller_x5_authored_pytest/development/H02/actor/SOURCE.json)
records per-file hashes and the pinned plugin SHA-256
`ba47c25a4a22b117891e9214940729c41af936d3dafbb18b4284de8a88ed3375`.
The [vendor script](../../test/results/2026-09-30-controller-x5-pytest-h02-vendor.py)
checks that hash before copying. The actor public command runs using its own
dependency snapshot on Windows and the WSL worker host. Both reproduce one
passing async test followed by one sync fixture setup error.

The Q4U boundary admits one editable source file but limits an actor to 200
files, 1,000,000 bytes per file and 5,000,000 bytes total. The initial actor
had 497 copied dependency files. A [packing step](../../test/results/2026-09-30-controller-x5-h02-pack-deps.py)
preserved every Pygments source byte in an archive, and a separate
[subset step](../../test/results/2026-09-30-controller-x5-h02-minimise-pygments.py)
kept the [full archive](../../test/results/2026-09-30-controller-x5-h02-pygments-full.zip)
outside the actor while retaining the core and selected lexer modules in a
234,556-byte actor archive. The
[subset receipt](../../test/results/2026-09-30-controller-x5-h02-pygments-subset.json)
lists retained and excluded member hashes. The final actor has **159 files,
2,451,817 bytes**. It still reproduces the original WSL failure. The subset
is qualified for these tests, not for arbitrary Pygments use.

The [calibration](../../test/results/2026-09-30-controller-x5-h02-calibration.json)
ran 19 provider-free checks across four source variants:

| Variant | Public symptom | Two-factory forward and reverse | No-hook control | Upstream loop-factory suite |
| :--- | :--- | :--- | :--- | :--- |
| Unmodified baseline | fail | fail, fail | pass | 40 pass |
| Narrow single-factory control | pass | fail, fail | pass | not run |
| Published proposal overlay | pass | pass, pass | pass | 40 pass |
| Independently authored alternative | pass | pass, pass | pass | 40 pass |

The narrow control demonstrates that passing the symptom alone can still
omit one factory. The alternative uses a unified test-generation path rather
than the proposal's additional wrapper hook. These are two repairs that pass
the frozen *preflight checks*, not proof of all pytest compatibility. The
[upstream suite](../../test/oracles/controller_x5_authored_pytest/H02/upstream/test_loop_factory_parametrization.py)
and independent forward, reverse and no-hook controls sit outside the actor.
The upstream suite's nested pytester processes need normal plugin discovery;
an initial run with auto-loading disabled failed all 40 because those child
processes did not load pytest-asyncio. Re-running baseline, proposal and
alternative with normal discovery passed 40/40 each. The final calibration
runner encodes this distinction.

The [Q4U isolation receipt](../../test/results/2026-09-30-controller-x5-h02-isolation.json)
records four fresh, unprivileged WSL actor variants. Each denied a direct
read of the protected oracle; public outcomes matched the table. This
checks the copied runtime in the one-editable boundary, with no provider call.

The [frozen catalogue](../../test/fixtures/controller_x5_authored_pytest/development/H02/catalogue-h02.json)
binds all 159 actor files, all six private test files, the one editable and
the scoring weights. The [evaluator-owned grader](../../tools/controller_x5_h02_grade.py)
rejects protected-file changes and module-level plugin edits, then runs each
check in a fresh Q4U namespace. It sends protected tests through stdin, outside
the actor inventory. Its [provider-free calibration](../../test/results/2026-09-30-controller-x5-h02-grade-calibration.json)
scored baseline 30, the public-only control 50 and two distinct repairs 100.
It rejected changed public test bytes and a grader-output spoof as critical.
The score is bounded evidence for this authored case, not a proof that arbitrary
candidate code could not recognise or game every hidden test.

**Remaining before paid admission:** freeze the paid case, runtime, analysis,
budget and dated spend notice. The producer entry and any S/A continuation
must use predeclared public evidence, not a protected score. The first producer
may still pass all checks immediately, as prior X5 cases did. The temporary
source checkout and package cache are build inputs only; the actor and
evaluator copies now hold the bytes needed for the recorded tests.

The full offline harness then passed **83/83** with no failures or skips.
Its [result](../../test/results/2026-09-30-controller-x5-h02-harness.json)
also reported 890 prose files clean. This verifies repository regression
checks after packaging; it does not score an H02 repair.
