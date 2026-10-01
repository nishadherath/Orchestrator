# X5 external E01: pytest-asyncio provider-free preflight

Date: 2026-09-30 Australia/Sydney. Status: **reproduced, rejected as a blind
paid X5 case**. No Controller or worker provider call occurred.
The machine-readable observation record is
`test/results/2026-09-30-controller-x5-external-e01-preflight.json`.
The repository offline harness passed 83/83 checks in
`test/results/2026-09-30-controller-x5-external-e01-lifecycle-harness.json`.

The upstream [pytest-asyncio issue #1501](https://github.com/pytest-dev/pytest-asyncio/issues/1501)
reports an order-dependent fixture teardown when a custom loop-factory
hook coexists with a session-scoped async fixture used by a sync test. The
upstream signed [v1.4.0 release](https://github.com/pytest-dev/pytest-asyncio/releases/tag/v1.4.0)
resolved locally to Git commit
`6e14cd2af9292dca1fa2b027a06bbc40b0e0e425`. Its
`pytest_asyncio/plugin.py` SHA-256 is
`ba47c25a4a22b117891e9214940729c41af936d3dafbb18b4284de8a88ed3375`,
identical to the installed 1.4.0 wheel file. The test runtime was pytest
9.1.1 with plugin version 1.4.0 confirmed from package metadata. The
original-order, reverse-order and no-hook results below were observed on
both Windows Python 3.12 and the actual WSL worker host's Python 3.14.7.
Packages and the source clone were isolated under the
host temp directory, outside the project; the small reproduction files are
under `test/fixtures/controller_x5_external/development/E01/`.

| Check | Observed result |
| --- | --- |
| Original order, custom loop factory | `test_async` passed; `test_sync` failed at fixture setup because `parent` had already been torn down; 1 passed, 1 error. |
| Reverse test order, same hook and bytes | 2 passed. |
| Original order, no hook | 2 passed. |
| Upstream `tests/test_loop_factory_parametrization.py` on unchanged source | 40 passed on Windows with normal pytest plugin discovery. |
| Independent two-factory lifecycle check, unchanged source on WSL | 4 tests passed: two async variants, one unparametrised sync consumer, and one ordinary sync test. Each factory created a distinct fixture loop, and both loops were set up and torn down. |

These observations corroborate the external report on a different platform
and show that the release's existing targeted suite misses this interaction.
They do not establish a suitable X5 benchmark. The report suggests the
likely fix layer, and no independent protected oracle or two distinct
complete repairs have been calibrated. The worker-visible issue, target
population, public residual-risk entry check, protected oracle and sample
plan remain unfrozen. Do not spend on E01 or classify it as a Controller
pair. In particular, passing the
original two tests after a code edit is not proof that fixture scope,
factory selection and teardown remain correct in other orders.

An [unmerged upstream proposal #1553](https://github.com/pytest-dev/pytest-asyncio/pull/1553)
adds 80 lines of plugin changes and 437 lines of loop-factory tests relative
to its own base. Its author reports 55 targeted tests passing on pytest
9.1.1. A reviewer requested changes because the initial implementation
manipulated pytest internals; the author later revised it. This is useful
evidence that compatibility is substantive, but an open proposal is not an
accepted gold patch or independent oracle. The fetched proposal did not
alter the pinned v1.4.0 checkout or the reproduction results above.

The proposal's plugin-only patch applied cleanly to a separate, detached
v1.4.0 checkout. On this isolated variant, the original issue tests passed
2/2 on both Windows and WSL, and the unchanged upstream 40-test loop-factory
suite passed on Windows. A separately authored two-factory check collected
five WSL cases and passed all five: async and sync fixture consumers were
both parametrised for `first` and `second`, while an ordinary sync test ran
once. The check uses two distinct factory callables, and an independent
session-finish assertion confirmed that each named factory created one of two
distinct fixture loops, each with one setup and teardown. The async test also
checked that its fixture ran on its own test loop. The same check on the
unchanged release collected four and completed the two fixture lifecycles.
An earlier draft used the
same callable under both factory labels; its lifecycle observations were
discarded before this qualification. This is one
calibrated candidate repair plus a narrow functional control. It does not
validate the proposal's broader compatibility claims, produce an
independent alternative repair, or establish a residual post-repair risk.

The `qualification` fixture now has an executable public coverage condition:
with `X5_EXPECT_SYNC_VARIANTS=1`, it requires exactly one sync consumer for
each named factory. On WSL, the unchanged release ran four individually
passing cases but exited 1 with the coverage mismatch; the isolated proposal
ran five and exited 0. A disposable negative-control copy of the proposal
was modified to select only the first factory for sync consumers (plugin
SHA-256 `121696c4633991eeccc1284919031f732f8a285cf1bc6c0265637f9d30952513`).
It passed the original two-test issue on WSL, then exited 1 on the public
coverage condition after four individually passing cases. This demonstrates
that the follow-up detects a plausible single-factory shortcut. The control
was constructed from the proposal for oracle validation; it is not an
independent repair or evidence that an unprompted worker would make that edit.

The public issue explicitly says the fix should handle loop factories for
sync tests using managed async fixtures. Its linked, still-open PR #1553
publishes a detailed implementation and compatibility plan. A paid actor
given the natural issue would receive the fix layer, and a benchmark that
withheld that sentence or the linked proposal after selecting this case
would no longer be a blind natural-issue test. The negative control is useful
for validating a public follow-up gate, but it cannot remove that exposure.
E01 is rejected for paid X5 screening. The next case search must find a
natural report with deterministic reproduction and independent acceptance
whose public text does not disclose the repair. B0 remains default and X6
sealed.
