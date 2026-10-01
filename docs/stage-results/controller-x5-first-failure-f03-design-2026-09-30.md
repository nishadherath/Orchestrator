# X5 F03: cancellation and retry-boundary development case

Date: 2026-09-30 Australia/Sydney. Status: frozen provider-free fixture;
no live producer or Controller call. F03 uses the Apache-2.0 Tenacity working
tree at pinned local HEAD `3e58094d3bc414975aad9eadf343a32bdb3b89b3`.
The public incident is adapted from [Tenacity's cancellation report
#529](https://github.com/jd/tenacity/issues/529). It adds a separately
authored async-default regression and sync control-flow case. The actor is
an experimental case, not a claim that the upstream issue described every
added defect.

The issue presents one shutdown symptom with several plausible owning layers:
negative retry predicate, async attempt loop and stop policy. The frozen
trace records a second attempt after `CancelledError` or
`KeyboardInterrupt`, without naming a repair. The public check and actor
source are available to the worker; the reference repair and protected
oracle are outside the actor. Only `tenacity/retry.py` and
`tenacity/asyncio/__init__.py` may change.

The [F03 catalogue](../../test/fixtures/controller_x5_first_failure/catalogue-f03.json)
has SHA-256 `ea4859b4cf86a57c5b4d45f824263c69ac728cd69341ff91437f9162fbb83db8`
and binds all actor files, the three repair overlays and external protected
oracle. Provider-free calibration on isolated copies passed:

| Variant | Public check | Protected checks |
| --- | --- | ---: |
| Baseline | fail, 3/3 public failures | 4/9 |
| Async-only partial repair | fail | 7/9 |
| Layer-specific reference repair | pass | 9/9 |
| Central retry-policy alternative repair | pass | 9/9 |

The protected checks include ordinary sync and async retries, explicit
ValueError exclusion, broad async retry policy, cancellation at entry and
during backoff, and sync control-flow interruptions. The two complete repair
strategies differ materially: the reference guards cancellation in the async
loop and narrows the negative predicate, while the alternative rejects
control-flow exceptions centrally in retry strategies and restores the
ordinary async default. The issue leaves more of the causal diagnosis open
than F01/F02, but its live difficulty and Controller value remain untested.

Before any paid call, the WSL actor/packet/grader probe and final full offline
harness must pass; a new single-use manifest, analysis and dated cost notice
must be frozen. A first public success ends the case. Any comparison after a
qualified first failure uses matched S/A snapshots and counts the producer
once. F03 is a development case; X6 remains sealed.
