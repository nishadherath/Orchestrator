# Q4T transport repair: implementation and offline verification

Date: 2026-09-26 Australia/Sydney. Q4T is a prospective evaluation path. No
new Claude model call, campaign replay, routing change or redistributable
change was made in this stage.

## Observations

The sealed Q4S S4 S03 Sonnet-medium episode ended with
`error_max_structured_output_retries` after 14 turns. Its report was correctly
classified `transport-invalid` and its protected executable patch scored
100. The exact internal cause is unavailable from the bounded receipt. The
old screen's child manifest still validates at
`5d51db8eed091668d984351ceba87f3b7bc531803b0f82743e2623ddb9e1e144`.

## Changes

- A new Q4T transport retains the six-field JSON schema and local strict
  parsing, restores five structured-output validation attempts, shortens the
  final-report instruction and records a versioned transport mode plus
  bounded diagnostics. It never turns an absent report into a valid one.
- A separate Q4T WSL launcher and installer preserve the attested Q4S runtime
  paths. The Q4T adapter retains actor isolation, source-revision binding,
  model identity and stopped-writer evidence.
- A prospective stop-policy helper permits a terminal, settled report-format
  failure to be scored without automatically stopping the entire screen.
  It still stops on unknown blocked roots, unverified protected source,
  accounting or identity faults, allocation overrun, inconclusive grade and
  critical error in a predeclared positive candidate arm. A new campaign
  driver must validate digests and bind this helper before paid dispatch.
- The new auth probe reports an early login/launcher failure before trying to
  collect an actor that never started.

## Verification

- `worker_q4t_transport_tests.py`: 6/6 provider-free tests passed.
- The frozen S4-focused suite remained 5/5 passing.
- Python compilation: all new Q4T Python modules passed.
- Q4T WSL launcher: `bash -n` passed. The isolated fake-worker boundary probe
  passed all 12 checks across Sonnet-low, Sonnet-medium and Opus-high, with
  zero provider calls and USD 0 provider-reported usage.
- The isolated Claude.ai auth probe passed with zero provider calls.
- The historical Q4S S4 manifest check passed at its original digest.
- The repository's full offline harness returned `PASS` with zero failing
  checks. It was run without `--record` so historical result files were not
  overwritten.
- Graft retrieval was used for source discovery. A local structural `graft
  build .` completed, but `graft check` still reports the repository graph
  stale: many untracked Q-series sources, including Q4T, remain outside the
  tracked graph and four older changed files retain stale semantic summaries.
  This is index coverage, not evidence that Q4T's verification failed.

## Inference and untested risk

Five attempts and a compact report may reduce intermittent final-report
failure, but the offline checks cannot establish its live failure rate or
cost. The stop-policy change prevents one *settled* report-format failure
from erasing later measurements only when a new, source-bound driver adopts
it. This repair stage preceded the later
[C1 paid canary](worker-q4t-c1-2026-09-26.md); the six-family candidate is
still unqualified, and shipping B0 remains the default. The next screen needs
a fresh non-replayed corpus, exact manifest and dated spend notice before any
provider invocation. See the [Q4T design](../WORKER-Q4T-REPORT-TRANSPORT-REPAIR-2026-09-26.md).
