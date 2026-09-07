# Pre-registration: T7, a fair-scale proxy for F13's row

Written before any run, per the same discipline as the full six-task
pre-registration. Commit adding this file is the proof of precedence.

## What this run is for

D19 lowered two of ROUTING.md's rows on double-confirmed benchmark
evidence but deliberately left `worker-fable-xhigh`'s row untouched: T6,
its benchmark fixture, cleared at `worker-sonnet-low` twice, but T6's
actual shape (a defect reachable through three files in one repository) is
considerably smaller than F13's own task (a multi-service p99-latency
regression traced through traces and profiles). T7 is built at that larger
scale specifically to settle whether the fable-xhigh row should move too,
or whether T6's result does not generalise to what the row is actually for.

## Design

`python3 test/harness/benchmark.py --project <orchestrator-scratch> --tasks T7 --confirm --record --fresh`

`--fresh` is required: the existing checkpoint's `tasks` identity field is
the six-task set, and `--tasks T7` alone does not match it. Same protocol
as the full run otherwise: R_search = 3, steer threshold 2 of 3, R_confirm
= 9, 95% Wilson lower bound above 0.7.

## Predictions

**Frontier cell.** T7 requires noticing that catalogue and checkout slow
down with payload size while gateway does not, that auth's own slowness is
flat and unrelated, and tracing the actual cause to a caching helper inside
a shared module three of the four services import. That is more than a
single-chain trace (T6) but still fundamentally code reading plus running
a provided script at a few sizes, not open-ended architecture judgement.
Predict `worker-sonnet-medium` or `worker-sonnet-high`.

- If T7 also clears at `worker-sonnet-low`: strong second-generation
  evidence that this triple, even scaled up, does not need more than the
  floor, and the fable-xhigh row should very likely be lowered on the
  strength of two independently-sized fixtures now, not one.
- If T7 needs `worker-sonnet-xhigh` or `worker-opus-high`: scale and
  red-herring density does matter for this triple, and the honest reading
  is that T6 undersold the row rather than that the row is wrong; F13's
  row would then warrant its own targeted re-measurement rather than a
  blanket change.
- If T7 fails to clear the ladder below `worker-fable-xhigh` itself: F13's
  row would stand confirmed as written, and D19's caution about T6 would
  have been the right call.

**Grader reliability.** Deterministic string match on two required terms
(`serialize.py`, plus `to_wire` or `_encode_string`), the same shape as T5
and T6. Both graders were checked at construction against a correct
diagnosis and two plausible wrong ones (blaming `catalogue`'s
`apply_promotions`, blaming `checkout`'s unrelated dependency bump).
Predict zero false results, with the same caveat both prior open-task
graders carried: a correct diagnosis phrased without either accepted term
would false-negative, and only failing reports are captured to check this
against.

**Tokens and wall clock.** No comparable data point yet: T7 is the first
task in this benchmark requiring a worker to run a script itself before it
can diagnose anything, at more than one input size to see the shape of the
regression. Predict wall clock exceeds T6's (19 to 44 seconds) by a
meaningful margin, plausibly into the low minutes at the frontier cell;
falsified by anything at or below T6's range, which would suggest the
extra scale did not translate into extra investigative work.

**Containment and reset.** Same predictions as every prior run: zero
containment violations outside `bench-T7/`, zero `reset_task` failures.

**Cost.** Twelve search runs plus, if the frontier is not the floor, up to
eighteen confirmation runs at two cells. Using the full run's per-run cost
range at comparable cells (USD 0.10 to 0.35), predict total cost for this
single task lands between USD 2 and 10.
