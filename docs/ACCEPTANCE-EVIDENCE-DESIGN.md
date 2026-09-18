# Acceptance evidence contract

Date: 2026-09-17. Scope: improvement Stage 4.

## Boundary

The routing ledger keeps three facts separate: execution state, a worker's
claimed outcome and acceptance evidence. A claim never qualifies capability
learning. A version-2 acceptance record is qualified only when this repository's
owned verifier has frozen a contract, run its command or recorded an explicit
human review, and bound the result to the artefacts it inspected.

The contract exists before dispatch and contains:

- required output paths;
- protected paths a worker must not weaken;
- constraints and acceptance criteria;
- either an argument-vector verification command or a human-review rubric;
- a timeout for executable verification.

Paths are project-relative, resolve inside the project and cannot traverse a
symbolic link outside it. Commands are argument arrays and run without a shell.
The contract digest and protected-file baseline are stored in the pending
ledger entry, so editing the input contract after dispatch has no effect.

## Evidence

Executable verification captures the command, exit status, bounded output,
timestamps, required-output manifest, protected-file manifest, Git revision
and working-diff digest. A pass requires exit status zero, every required output
present and every protected file unchanged from the pre-dispatch baseline.
Missing commands or timeouts are blocked, not failed capability observations.
A failing command or changed protected test is acceptance failure even when the
worker claims success.

The verifier writes `.claude/acceptance/<ledger-id>.json` before completing the
ledger transaction. If the process dies between those writes, recovery sees the
pending entry and reusable evidence. A retry reuses evidence only when its
contract and current artefact manifests still match. Otherwise it runs a fresh
verification. Repeated terminal or review events with the same decision are
idempotent; conflicts fail closed.

Rubric contracts enter `review_required`. They become pass or fail only through
an explicit review command naming the reviewer. This records judgement and
provenance without presenting prose as mechanically verified. Blocked,
unverified, pending and review-required records never train capability.
Measured terminal costs remain available to cost reporting.

## Scope and limits

Hashes bind bytes, paths and the recorded revision. They do not prove semantic
correctness, test completeness or reviewer competence. Protected paths prevent
the verifier from rewarding a worker for weakening named acceptance tests; the
contract author must name the right paths. Git identity is diagnostic and does
not replace the artefact manifest, which includes relevant untracked outputs.

External Claude lifecycle events remain partly observable. Missing transcripts,
status-line data or hooks stay labelled missing. Recovery lists pending work,
orphaned verification evidence, review requirements, unresolved Controller cost
and the next command. It does not infer success or failure from silence.

Controller runs and recorded harness runs also write machine-readable terminal
or interrupted status alongside their human reports. These records make owned
exit paths diagnosable; they do not automatically add routing capability
evidence without a routing-ledger acceptance contract.

## Verification

The deterministic acceptance suite passes 10 cases, including each mandatory
Stage 4 failure and recovery shape. Route selftest passes 23 scenarios and the
Controller dispatch suite passes 29 tests. The repository harness has 37 checks
including the acceptance gate. These are offline results and made no model or
provider call.
