# N5 live worker-cell screen

Later status: the separately approved development comparison is complete;
see the [N5 stage result](worker-n5.md). This document preserves the earlier
screen-only result and its then-current next gate.

Date: 2026-09-25. Scope: the approved 60-call screen only; N5 development
selection and N6 reserved evaluation have not run. The [frozen manifest](../../test/results/2026-09-25-worker-n5-screen-manifest.json)
has SHA-256 `1dbb33f603f756998e30c48346b89b3359de0330b78c70c4a49bc33b9e065e94`.
The operator approved that exact manifest and its [dated spend notice](worker-n5-screen-spend-notice-2026-09-25.md).
The [checkpoint](../../test/results/2026-09-25-worker-n5-screen-run/campaign.json)
and [budget ledger](../../test/results/2026-09-25-worker-n5-screen-run/budget.json)
are the durable accounting evidence. The [actor archive](../../test/results/2026-09-25-worker-n5-screen-run/actors.zip)
preserves all 240 public actor files byte-for-byte; its SHA-256 is
`1b75c2d63e74cb7069ee70878135ad9b55696bb37ef04c87d90e06e2d8864c01`.
The unarchived working copies are excluded from Git and Graft indexing.

## Verified outcome

The runner completed all 60 scheduled calls: 15 identity probes and three
independently graded microtasks per cell. Every call returned a terminal receipt,
reported the requested model identity, and settled in the budget ledger. There
were no stopped cells, protected-file blocks, unknown charges or automatic
replays. All 45 microtask artefacts were graded. The CLI received the requested
effort flag, but the provider did not independently report a served effort;
the screen therefore establishes *requested* effort, not verified served effort.

The three grades below are S01 configuration parsing, S02 atomic inventory
change and S03 leave-correct-code-untouched. Each is on a 0–100 scale. The
identity probe has no quality grade. `Accepted` counts complete independent
microtask acceptance, not a successful CLI exit.

| Cell | S01/S02/S03 | Accepted | Critical errors | False success | Reported USD | Call time, s |
| :--- | :---: | ---: | ---: | ---: | ---: | ---: |
| Sonnet low | 40/0/100 | 1/3 | 2 | 2 | 0.0929 | 51.1 |
| Sonnet medium | 40/0/100 | 1/3 | 2 | 2 | 0.1575 | 66.6 |
| Sonnet high | 40/100/100 | 2/3 | 1 | 1 | 0.1734 | 92.7 |
| Sonnet xhigh | 100/100/100 | 3/3 | 0 | 0 | 0.2062 | 113.8 |
| Sonnet max | 100/100/100 | 3/3 | 0 | 0 | 0.4349 | 247.2 |
| Opus low | 40/100/100 | 2/3 | 1 | 1 | 0.2621 | 74.8 |
| Opus medium | 40/100/100 | 2/3 | 1 | 1 | 0.3035 | 107.8 |
| Opus high | 100/100/100 | 3/3 | 0 | 0 | 0.4700 | 141.1 |
| Opus xhigh | 40/100/100 | 2/3 | 1 | 1 | 0.4174 | 127.0 |
| Opus max | 40/25/100 | 1/3 | 2 | 2 | 0.6731 | 223.6 |
| Fable low | 40/100/100 | 2/3 | 1 | 1 | 0.5359 | 87.5 |
| Fable medium | 40/100/100 | 2/3 | 1 | 1 | 0.4163 | 96.0 |
| Fable high | 100/100/100 | 3/3 | 0 | 0 | 0.5487 | 110.4 |
| Fable xhigh | 40/100/100 | 2/3 | 1 | 1 | 0.7413 | 164.9 |
| Fable max | 40/100/100 | 2/3 | 1 | 1 | 1.9776 | 377.1 |

Across the screen, 31/45 microtasks were accepted; 14 had a critical error and
14 falsely claimed success. In particular, Opus-max S02 scored 25/100 with an
independent `critical_error=true` and `false_success=true` result. Higher effort
was not monotonically better on these observations.

## Cost and time reconciliation

The sum of provider-reported, API-equivalent receipts is **USD 7.410898**. This
is not an incremental Claude Code subscription invoice. The approved USD 48.75
was a sum of per-call *local admission allocations*, not a predicted or charged
amount; all 60 reservations settled. Receipts report 2,384 ordinary input,
289,037 cache-creation input, 2,079,548 cache-read input and 126,090 output
tokens. Summed call wall time is 2,081.827 seconds (34.7 minutes). The first
call started 2026-09-24 22:35:14 UTC and the last ended 2026-09-25 00:15:13
UTC, about 100 minutes of elapsed campaign time including staging and grading.

## Interpretation and next gate

On these three tasks, Sonnet-xhigh is the least costly observed cell with
3/3 acceptance. Sonnet-high had 2/3 at slightly lower cost. Opus-high and
Fable-high also reached 3/3, but at higher cost. This is screening evidence,
not a stable cell ranking: each cell ran each task once, the cells ran in fixed
order, cache mix differed, and served effort was not independently visible.
The tiny screen does not represent the six-family development corpus.

The subsequent [N5 development preflight](worker-n5-development-preflight-2026-09-25.md)
implemented and fake-tested explicitly admitted candidate and alternative
dispatch, built a separate task-sensitive corpus, refreshed the host and
subscription evidence, and froze the new cost notice and schedule. The
development campaign remains unlaunched pending its own exact approval. Use
the 12 development tasks only; keep the 12 reserved tasks sealed for N6.
