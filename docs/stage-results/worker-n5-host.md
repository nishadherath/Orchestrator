# N5 host preparation: WSL transport and grader, no paid run

Date: 2026-09-24. Status: **host transport and isolated grader qualified without provider
credentials; N5 campaign gate remains closed**. The operator reported this
development session as GPT-5.6 Sol / High; the host does not expose an
independent setting check. No paid Claude worker call or reserved grade was
run. The shipping policy remains B0.

## Implemented and verified

- `worker_wsl_materialize.py` copies only four public actor files to WSL ext4.
  The root-owned actor directory prevents deletion or creation at its root;
  UID 65534 can edit only the existing `app.py` and private home, cache,
  scratch and Graft-index directories.
- `worker_wsl_namespace.sh` removes Windows mounts and interop access inside
  private mount/PID namespaces before dropping to UID 65534.
  It overlays the shared actor parent and binds back only the current actor;
  the probe denied access to a known sibling actor path.
  The transport calls `worker_wsl_collect.py` only after a terminal event and
  wrapper exit. It accepts only an `app.py` edit. It
  rejects protected-file drift and a concurrent source change before copying
  the edit back to the Windows actor directory.
- `worker_wsl_transport.py` stages an admitted invocation, builds a fresh
  actor-only Graft index, launches native Claude with the exact restricted
  tool contract, and records an ambiguous timeout/cancellation without copying
  output or replaying. `WslWorkerAdapter` exposes the attested capability to
  `TaskExecutor`; the generic adapter remains unproven for this host.
  The WSL command validator now rejects any extra CLI flag, malformed budget
  or altered option layout, in addition to broader tools and MCP settings.
- `worker_n5_screen.py` freezes a provider-free 60-call inventory across all
  fifteen cells using separate I00/S01-S03 fixtures, with USD 48.75 in local
  allocations. Its default manifest has no credential or spend notice, so an
  approval cannot validate. The five focused screen tests pass. The
  [screen contract](../WORKER-N5-SCREEN.md) records the live runner requirements.
  The saved provisional manifest is
  `test/results/2026-09-24-worker-n5-screen-plan.json`, digest
  `a7f25d1cd839d4a4c84acde7890f599b8cffa0bc55a4b72d6593b2e45412e089`.
- `worker_n5_live_screen.py` provides a provider-free, at-most-once screen
  driver over the budget ledger and isolated WSL grading bridge. Eight
  fake-adapter tests cover complete order, identity mismatch, ambiguous
  provider stop, receipt recovery without replay, protected-file tampering,
  and budget breach. The production constructor remains closed until WSL
  credential delivery is qualified; no paid call ran.
- The manifest-bound WSL attestation passed 49 checks, including the actual
  Windows-to-WSL bridge, Claude MCP startup, six Graft tools, file/shell/search
  denial, allowed edit collection back to a Windows actor source, and
  protected/concurrent-change rejection.
  The root-owned WSL grader also passed its Windows bridge, hidden-oracle,
  partial-quality, no-edit, digest-rejection and bounded-output checks. It
  runs each case from a fresh actor copy rather than executing candidate code
  as the Windows evaluator user, and binds the stopped `app.py` digest before
  and after grading.
  Its current record is `test/results/2026-09-24-worker-n4-wsl-host.json`.
  The separate adapter probe passed seven receipt checks: matched invocation,
  attestation digest, stopped writer, zero charge and unchanged source after
  the expected unauthenticated failure.
- Focused worker campaign/executor/selector tests passed 51/51. The full
  provider-free harness passed 61/61 after the screen driver addition.
  `release_check.py` found all 75 bundled files source-equivalent with no
  mechanical failures. Graft semantic and wiring graphs reported in sync.

## Remaining gate

The actor has no provider credentials. Its zero-token authentication failure
proves startup and host wiring, not a served model, successful edit, billed
receipt or cost control under a paid response. A credential method must be
chosen and configured without copying secrets into the actor package. Then
build the N5 campaign runner and manifest/authorisation gate around
`TaskExecutor` and this adapter, freeze the exact host configuration, rerun
the sentinel checks, issue the concrete spend notice, and execute the
development-only screen. Do not infer N6 power or promote a policy from these
host tests.

The predeclared N5 inventory remains at most 60 cell-screen calls with USD
48.75 in local allocations plus at most 36 development episodes with USD 108
in local allocations, for USD 156.75 total. These caps are **not** a bill
prediction. Provider pricing, expected spend and elapsed time must be checked
before the first paid call. The 12 reserved N6 tasks and graders remain
excluded from N5 actor packages and paid runs.

Rollback is to omit `WslWorkerAdapter` from any campaign construction and
leave its actor/receipt evidence intact. No consumer routing or Controller
default was changed by this work.
