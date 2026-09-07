# Pre-registration: T8, a fair-scale proxy for F09's row

Written before any run, per the same discipline as T7's pre-registration.
Commit adding this file is the proof of precedence.

## What this run is for

Investigating F08 and F11 (D26, D28) turned up the same evidence pattern
for F09: opus reads its horizon as medium in roughly nine of ten
observations across every table state since 2026-09-05, not the
fixture's assigned short, including runs from before the difference
between the two cells mattered. D19's capability evidence for this
triple, worker-sonnet-low at the 95% Wilson bar, comes from T5, and T5's
actual task is finding one bug across two small files from a two-line
bug report. F09's own task, reviewing a 200-line pull request for
correctness risk, is a broader ask than T5's shape, the same kind of gap
D19 itself flagged once already for T6 against F13's row before T7 was
built to close it. T8 is built at F09's actual scale specifically to
settle whether worker-sonnet-low still holds, or whether T5's result
does not generalise to what F09's row is actually for.

## Design

`python3 test/harness/benchmark.py --project <orchestrator-scratch> --tasks T8 --confirm --record --fresh`

`--fresh` is required, same reason as T7: the existing checkpoint's
`tasks` identity field is the six-task set, and `--tasks T8` alone does
not match it. Same protocol otherwise: R_search = 3, steer threshold 2 of
3, R_confirm = 9, 95% Wilson lower bound above 0.7.

T8's repo is a small pull request against an orders-service HTTP client:
`retry.py` (new, a generic retry-with-backoff wrapper), `config.py` (new,
shared constants), `api_client.py` (every call site now wrapped in
retries), and `test_api_client.py` (existing tests, all passing, updated
for the new call shape). 162 lines total across the four files and the
PR description, close to F09's own "200-line pull request." The planted
risk: `with_retries` is applied uniformly to every call including
`create_order`, a POST that is not idempotent, so a lost response after a
server-side success causes a retry to create a duplicate order. The
existing tests exercise the retry-then-succeed path but never a
lost-response-after-real-success case, so they pass without catching it,
matching F09's own framing of a PR that is already tested and still
carries a risk.

## Predictions

**Frontier cell.** T5's bug (`price - percent_off` instead of a
percentage calculation) is a self-contained arithmetic error, wrong on
inspection of one function with no other context needed. T8's risk
requires holding two facts from two different files at once (retry.py's
blanket retry-on-any-failure behaviour, and api_client.py's use of that
behaviour for a non-idempotent POST) and recognising why their
combination is unsafe, a smaller-scale version of the same kind of
cross-file synthesis T7 needed, applied to a semantic property
(idempotency) rather than a numeric one. Predict `worker-sonnet-medium`.

- If T8 also clears at `worker-sonnet-low`: strong evidence that F09's
  real scale does not need more than the floor either, and the
  horizon-classification question becomes moot for routing purposes
  even if opus's own reading of the axis stays medium.
- If T8 needs `worker-sonnet-high` or higher: F09's row would warrant
  re-examination independent of the axis question, since the floor
  cell would then be under-provisioned for what the fixture actually
  describes, not merely misclassified on horizon.
- If T8 fails to clear the ladder below `worker-opus-high`: the
  orchestrator's own consistent live choice for F09 (opus-high, scored
  as over-provisioning against the current fixture) would turn out to
  be closer to correct than the fixture's asserted answer.

**Grader reliability.** Deterministic string match on three required
terms: `api_client.py`, `create_order` specifically (not `get_order`,
`list_orders`, or `cancel_order`, all genuinely safe to retry), and the
duplicate-side-effect concept in some form. Checked at construction
against a correct diagnosis in two phrasings and two plausible wrong
ones (a backoff/timeout concern naming neither file nor function
correctly; a `cancel_order`-retry concern naming the wrong function).
All four behaved as intended. One known limitation found and left
unresolved during construction: a report that happens to place the word
"twice" near `create_order` for an unrelated reason (an adversarial
phrasing invented to probe the grader, not a plausible genuine review)
could false-positive; the reverse risk, a correct diagnosis phrased
without any of the accepted terms, remains the more likely failure mode
and the one this design optimises against, the same trade-off T5, T6,
and T7 made.

**Tokens and wall clock.** No comparable data point for this exact task
yet. Predict wall clock in T5's range (its four tasks were the pilot's
fastest) rather than T7's, since T8 needs no script execution, only
reading; predict cost per run in the same USD 0.10 to 0.35 band the full
run's comparable cells have shown.

**Containment and reset.** Same predictions as every prior run: zero
containment violations outside `bench-T8/`, zero `reset_task` failures.

**Cost.** Twelve search runs plus, if the frontier is not the floor, up
to eighteen confirmation runs at two cells. Predict total cost for this
single task lands between USD 2 and 10, the same band as T7.
