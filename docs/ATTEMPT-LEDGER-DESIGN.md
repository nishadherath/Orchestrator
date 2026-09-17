# Attempt ledger design

Date: 2026-09-17. Status: implemented for improvement Stages 1, 2 and 4.
Decision: [D84](DECISIONS.md#2026-09-17-d84-version-2-keeps-jsonl-and-adds-locked-per-attempt-accounting).

## Contract

`.claude/routing-ledger.jsonl` remains the canonical, human-readable task
ledger. A version-2 `RoutingLedgerEntry` retains the task summary used by old
readers and adds three independent facts:

- `execution_status`: whether the task is pending, running or terminal.
- `attempts`: ordered invocation records with requested cell, actual model and
  effort evidence when observable, invocation relationships, version identity,
  timestamps, execution state, outcome, duration and provider usage.
- `acceptance`: acceptance status, evidence references and contract version,
  separate from the worker/orchestrator's claimed `final_outcome`.

Each attempt's usage separates ordinary input, cache creation, cache reads and
output. Cost is nullable and carries currency, source, price snapshot and
whether a parent total includes descendants. Missing values are null. A real
zero is numeric zero with `cost_source: measured_zero`.

Stage 1 records acceptance as `unverified` under `unverified-v1`. Stage 2 uses
only acceptance `pass`/`fail` for version-2 capability learning and partitions
that evidence by served model, bundle, routing policy and acceptance contract.
Stage 4 adds `acceptance-v2`: a frozen pre-dispatch contract, owned command
verification or explicit rubric review, and evidence bound to the current
artefact and protected-path manifests.

## Ownership and roll-up

One task row owns one ordered attempt list. An attempt may link to an invocation
and a parent invocation. Provider-reported task totals remain on the task row.
Per-cell cost means use terminal attempts whose cost and duration are both
known. They do not add task totals to child attempts, and they do not allocate
a multi-cell task total between attempts.

Version-0/1 rows remain readable. A legacy total is attributable to a cell only
when exactly one cell ran. Multi-cell totals stay available for whole-task cost
reporting but are unknown by cell.

`claudep.py` raises `ClaudeCallError`, a `RuntimeError` subclass, when an
invocation fails. Its `partial` result retains cost, provider usage, elapsed
time, raw response and command identity whenever stdout exposed them. Invalid
or absent telemetry remains null. Existing callers that catch `RuntimeError`
remain compatible. Stage 3 will make Controller persistence and reservation
reconciliation unavoidable on every failure path; this stage supplies the
lossless invocation boundary it needs.

## Transaction boundary

Every mutation locks `<ledger>.lock` through the full read, ID allocation,
state check and write. Windows uses `msvcrt.locking`; Unix uses `fcntl.flock`.
The operating system releases the lock if a process exits. The persistent lock
file contains no ownership state and needs no stale-lock deletion.

Append flushes and syncs before releasing the lock. Completion writes a unique
sibling temporary file, syncs it and replaces the ledger atomically. It retains
unparseable lines exactly. An identical completion retry is idempotent; a
conflicting retry fails. This supports a caller that lost the first response
without permitting it to rewrite a settled result.

## Explicit migration and reversal

Ordinary reads, routing explanations and records never bulk-migrate history.
The operator controls migration:

```text
python3 tools/route.py --project <root> --migrate-ledger-v2 --dry-run
python3 tools/route.py --project <root> --migrate-ledger-v2
```

Migration refuses malformed JSON or an unsupported version. Before replacement
it writes the exact original bytes to `routing-ledger.jsonl.pre-v2.bak`. A
second run is a no-op. For one-cell history it creates one attributable attempt;
for multi-cell history it creates ordered attempts with null per-attempt cost
and duration while preserving the task total.

Reversal is also explicit:

```text
python3 tools/route.py --project <root> \
  --restore-ledger-backup <root>/.claude/routing-ledger.jsonl.pre-v2.bak
```

Restore retains the current ledger as `.pre-restore.bak`, refuses to overwrite
a conflicting backup and restores the selected backup byte-for-byte.

## Verified Stage 1 and 2 cases

The offline route selftest covers pending records, measured zero, unequal USD
0.10/USD 1.90 attempts, concurrent ID creation in six processes, idempotent and
conflicting completions, malformed-line preservation, dry-run migration, exact
backup/restore, migration idempotence and an injected replace failure. The
schema fixture validates a complete version-2 entry. `claudep.py --selftest`
covers successful, nonzero, malformed and timed-out subprocess results and
proves recoverable failure telemetry survives. No paid model call is required
for these properties.

Stage 2 adds separate direct and conditional capability populations, exact
identity cohorts, an optional maximum evidence age, selected-start ladder
projections and explicit unknown Controller economic terms. Its offline cases
cover twenty direct failures, conditional isolation, unverified/stale evidence,
identity conflicts and exact selection, unresolved terminal spend, selected
ladder reach and projection completeness. Stage 3 owns Controller budget
reservation.

## Verified Stage 4 cases

`route.py --spawn` freezes acceptance before it appends a pending task.
`route.py --record` runs a command contract without a shell and writes evidence
under `.claude/acceptance/` before atomically completing the ledger row. A pass
requires exit status zero, all required outputs and an unchanged protected
baseline. Missing commands and timeouts are blocked. Rubric contracts require
an identified review and retain its provenance. `qualified()` validates the
contract digest, result digest and outcome facts instead of trusting a status
field supplied by a caller.

The offline acceptance suite covers claimed success with a failing check,
missing outputs and commands, timeout, edited artefacts, tampered evidence,
protected-test weakening, rubric review conflict, supplied booleans, the
evidence-before-ledger crash window, missing hook output and terminal-event
reconciliation. Controller and harness runs also write durable completed,
blocked or interrupted status records. These checks qualify declared local
oracles; they do not establish semantic correctness outside the contract.
