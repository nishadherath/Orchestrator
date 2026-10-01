# X1: Controller campaign integrity before spending

Date: 2026-09-27 Australia/Sydney. Status: **X1 offline gate complete; 80/80
checks passed**. The operator requested GPT-5.6 Sol / High; this is a
user-confirmed setting, not an independently observed host identity. The
checkout is `v1.0-rc1` at `15ecf66` with pre-existing uncommitted work preserved.

## Behaviour changed

The R5 matrix and pilot launchers now accept only fresh schema-v2 manifests.
Historical R5 manifests and paid receipts stay unchanged and cannot launch
again. A stopped, cancelled or completed checkpoint is terminal for ordinary
`execute`; uncertain in-flight work is also closed. The campaign driver takes
an OS lock, records a per-episode intent before dispatch, and prevents a second
driver from starting the same schedule. Matrix calls have individual durable
budget reservations. The pilot retains its task budget and now carries known
Controller charges into failed or blocked episode summaries.

The new read-only-dispatch reconciliation path reads durable budget ledgers,
reports settled spend, holds and unresolved writer or accounting gaps, and
admits no provider calls. A cancellation is recorded independently of the
driver lock, prevents further admissions and survives a late result. Late
settled charges still count. Cancellation does not yet prove termination of
an active provider process tree; the writer barrier remains until evidence
can settle it. A fresh continuation requires an exact operator-authorised
schedule of unused rows, is linked to the predecessor manifest and checkpoint,
inherits its spend against the original cap, and has one durable predecessor
grant. A retry after partial successor-file writing reuses only that grant;
different files or a second grant are rejected.

The v2 manifest binds the complete first-party `tools/`, `src/`, harness and
R5 corpus fixture trees by exact file inventory and SHA-256. A separate
materialised package is checked for changed, missing and added files, unsafe
links and bytecode caches. It records Python executable/version and relevant
non-secret override presence. The live CLI rejects dispatch before state or
budget creation because Claude Code host version, third-party installation
provenance, loaded-module identity and process isolation are not yet attested.
That gate is deliberate: a passing offline package check does not qualify a
live host. X3/X4 must close the runtime and actor-isolation boundaries before
any paid Controller experiment.

The approval object for a continuation is bound to its schedule and grant. It
is an exact local authority record, not cryptographic proof of the human
operator's identity. No live use is authorised by an offline fixture approval.

## Verification

`test/harness/controller_x1_tests.py` passed 12 provider-free tests. They cover
settled-failure restart, archived and tampered state rejection, duplicate
drivers, cancellation after budget start and during a call with a late receipt,
one-call pilot stop,
failed-cost projection, ledger-only reconciliation, strict package mutation
and addition checks, schedule caps, the live host gate and single-grant
continuation recovery. The historical R5 suite passed 33/33 after fake runs
were changed to use fresh v2 manifests; archived R5 files remain read-only.
The [full gate](../../test/results/2026-09-27-controller-x1-harness.json)
passed 80/80 checks with zero failures or skips, including `CTRL-X1` (12 tests
in 65.776 seconds on that run), historical replay, source/bundle parity,
installer and handoff checks. It used the authorised host context to read
protected historical WSL evidence. No provider calls or Controller experiment
spend occurred in X1.

Changed implementation files are `tools/controller_matrix_runtime.py`,
`tools/controller_pilot_runtime.py`, `tools/controller_campaign_state.py`,
`tools/controller_campaign_manifest.py` and `tools/controller_x0_probe.py`.
The new `test/harness/controller_x1_tests.py`, R5 fake-run updates and
`CTRL-X1` harness entry provide regression evidence. Consumer `src/` files
did not change, so the redistributable was not rebuilt at this stage.

The direct development-session API charge is unavailable from this host;
unknown is not zero. The dated plan estimated USD 3.25-19.50 API-equivalent
and 3-6 engineering hours for GPT-5.6 Sol / High, assuming the token/cache
categories and Standard/Fast price range in the
[execution protocol](../REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md).
That is a forecast, not a measured charge. Actual Controller experiment
charges were USD 0 because all adapters were provider-free.

## Limits and next action

This is campaign-integrity evidence with fake transports, not Controller
quality evidence or live-host qualification. It does not repair the X0
Generator collapse or task-wide duplicate Controller admission; those are X2.
B0 remains the default. The X1 gate passed, so X2 may now implement named
Generator-cell dispatch and durable task-wide Controller admission. X1's
host/process limitations remain blockers for X5 live work.
