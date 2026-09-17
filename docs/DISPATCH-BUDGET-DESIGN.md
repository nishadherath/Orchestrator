# Controller dispatch budget

Stage 3 scope: implement a durable reservation boundary for every Controller
role, classifier and retry, including parallel generators. The observable gate
is deterministic budget, process-race, failure and recovery tests plus the full
offline harness. Routing, acceptance verification and real-world evaluation
are outside this stage. Planning allowance is USD 10-35 OpenAI API equivalent
and 8-16 engineer-hours from the approved handoff; no paid Claude tests.

## Authority and invariant

The scope is one Controller run. `dispatch-budget.json` owns the configured
limit, invocation IDs, allowances, known charges and unresolved holds.
`budget.jsonl` is a reporting projection. Different runs have independent
budgets; there is no implicit project-wide cap. Quick mode excludes the later
instantiation worker, which needs its own allowance from its caller.

Under one OS lock, a reservation takes at most `limit - spent - held`. Money
uses integer nanodollars; limits round down and costs round up. Dispatch intent
is persisted before launch. Reusing an invocation ID never dispatches twice.
Every failed or interrupted invocation remains in history. Unknown usage holds
the unused allowance until explicitly reconciled with terminal evidence.
Reported overruns remain visible and stop further dispatch. This enforces a
local admission rule; it cannot guarantee the provider's invoice or undo an
already running call. A child process being killed does not prove billing ended.

## Storage choice and failure analysis

Reuse Stage 1's OS lock and atomic file replacement. A small JSON snapshot is
sufficient for a bounded Controller run and is inspectable without a database.
SQLite would also supply transactions, but introducing it here would duplicate
the existing persistence boundary. Corruption or an unsupported version blocks
dispatch; do not guess a balance from a truncated log. No existing consumer
history is migrated or deleted. Reopening a snapshot never resets its budget.

The principal failure is a lost provider reply: retain the allowance, known
partial cost and invocation identity, then request explicit reconciliation.
Tests attack simultaneous reservations, crash-before/after-launch ambiguity,
duplicate settlement, inconsistent cost, non-finite amounts and overspend.
There is no automatic refund timeout. Recovery shows known spend, held funds,
available funds and unresolved invocation IDs.

## Recovery and cancellation

`--recover-run runs/<id>` reopens the original snapshot and rebuilds
`budget.jsonl`, individual budget records, `budget-status.json` and
`RECOVERY.md`. It never replays model calls or automatically continues phases.
The recovery report identifies unresolved calls and the remaining human action;
accepted content stays in the ledger, and received replies stay in invocation
telemetry even if a crash preceded the Scribe write. A repeated explicit run ID
is rejected rather than silently creating a new budget and duplicating work.

With terminal provider evidence, add `--reconcile-invocation <id>
--final-cost-usd <amount> --evidence <reference>` to recovery. Equal repeated
settlements are no-ops; conflicting settled costs or a decreasing known charge
fail closed. Prior partial evidence is retained. An OS ownership lock excludes
reconciliation while the Controller is active and releases on process death.
The reference is an operator attestation, not independently verified billing.

`--cancel-run runs/<id>` persists cancellation while a run is active. It blocks
future admissions; already running calls keep their timeouts and reservations.
Ctrl-C also records cancellation and writes a gap report after in-flight work
unwinds. Neither command promises immediate remote termination or a refund.
Reconciliation never clears cancellation. Follow-on work needs an explicit new
scope and budget, carrying completed artefacts forward without repeating effects.

## Limits and partial results

Each role allowance is at most USD 2 and at most the available balance; the
existing USD 0.50 role minimum remains policy. Classifiers reserve at most
USD 0.10. Conservative admission may stop a parallel batch while another call
still holds an allowance it later releases. This stage favours a simple safe
stop over a new scheduling policy; it does not claim optimal utilisation.

`--timeout` bounds each local invocation. `--elapsed-limit-s` optionally bounds
the dispatch window and clips role and classifier timeouts to time remaining.
Accounting, lock acquisition and local cleanup can extend wall time beyond that
window. `--max-output-tokens` defaults to 8192 and sets the child-only
`CLAUDE_CODE_MAX_OUTPUT_TOKENS` variable. This is a policy ceiling for most
individual requests, not a measured optimum or a run-wide token bound. Provider
or model limits may be smaller. Live enforcement has not been probed.

A terminal error with final cost contributes spend and releases only proven
unused funds. A timeout, malformed reply or interruption keeps unused allowance
held. Invalid provider counters become unknown without discarding valid cost.
Budget exhaustion and role failure produce `REPORT.md` and a `GapReport` with
remaining work; successful parallel siblings are saved before attempting repairs.
Reports label known cost and unresolved accounting separately.

The output setting is documented by [Claude Code's environment-variable
reference](https://code.claude.com/docs/en/env-vars), checked 2026-09-17.
Documented availability does not establish invoice enforcement. Compatibility
probes and real-world scheduling evaluation remain deferred.


## Verification

`test/harness/dispatch_budget_tests.py` supplies 28 deterministic cases, wired
into the full harness as `DISPATCH-BUDGET`. It tests independent processes and
threads, an actual process crash, idempotent recovery, active-owner exclusion,
known and unknown failure charges, output-setting isolation, elapsed admission,
parallel output preservation and schema compatibility. All provider replies
are mocked. R3's original USD 0.60 regression now passes. The full 36-check
result is recorded in `test/results/2026-09-17-harness.md`.
