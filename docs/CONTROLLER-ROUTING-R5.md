# Controller-aware routing R5: evaluation implementation

Date: 2026-09-18. Status: **offline implementation complete; live calibration
and pilot pending**.

R5 now has a provider-free, content-addressed evaluation system. It freezes the
corpus, score, model/effort screen and pilot before any paid call. This record
does not claim live model identity, effort quality, price calibration, pilot
success or production generalisation.

## Frozen contract and corpus

`src/controller_evaluation_contract.json` defines 12 families, eight positive
and four negative/control families. Each has two development and two reserved
mechanisms, producing 24 task blueprints per split. Reserved mechanisms differ
from development mechanisms rather than changing only names or constants.

The same contract fixes the five-component quality vector and weights:
milestones 40, reliable evidence 25, diagnosis/decision 15, useful continuation
10 and calibrated reporting 10. Critical invariant violations force the
primary score to zero while preserving raw components. A false completion
claim is reported independently. A useful incomplete result can therefore earn
evidence, diagnosis and continuation credit without being counted as accepted.

`tools/controller_corpus.py` deterministically creates one declarative corpus
with 48 tasks and 288 labelled variants: reference, alternative,
partial-useful, confident-wrong, superficial-public-pass and
dishonest-completion. Each actor receives only its materialised public package:
`issue.md`, `task.json`, `observations.json` and `public_check.py`. The protected
oracle and variant fixtures stay outside the actor root and are applied only
after an episode. Reference and valid alternative results score 100, useful
partial work retains non-zero credit, bad results are rejected, and dishonest
completion is a critical violation.

`test/fixtures/controller-routing-v1/routing-vignettes.jsonl` contains 60
deterministic routing cases, five per family. They exercise plain, urgent,
technical, brief and verbose surface forms while decisions depend only on the
structured assessment. Every row is routing-only and cannot be cited as
model-quality evidence.

This corpus is synthetic by design. It proves evaluator mechanics and provides
controlled causal comparisons. It does not establish performance on external
repositories or production tasks.

## Calibration and pilot runtimes

`tools/controller_evaluation.py` creates and verifies two separate manifests:

- the 15-cell screen contains one identity call and three fixed reasoning
  microtasks for each Sonnet, Opus and Fable effort cell, 60 calls total;
- the pilot contains six development tasks across B, S and A, 18 episodes
  total, with four predeclared automatic Controller entries.

Calibration order is effort-major across the three models, then rotated in
three task blocks so model and task order are not identical. The manifest
records cache state as an observation to collect, never an assumed saving.
Identity calls cap at USD 0.25 and microtasks at USD 1, for an absolute USD
48.75 matrix ceiling. This is an admission ceiling, not an expected invoice.
A reasonable planning range is USD 1-20 and one to three hours of serial
runtime; observed Fable/max availability, latency and price remain unknown.

`tools/controller_matrix_runtime.py` validates the manifest and exact
authorisation, binds all inputs by SHA-256, passes exact model and effort flags,
disables tools, records served model, requested effort, usage, cost and latency,
and persists dispatch intent before each call. It never retries. An interrupted
or failed call stops later admissions because provider billing may be
uncertain. Claude's result stream does not independently report served effort,
so the evidence distinguishes the requested CLI flag from observed served
model identity instead of claiming stronger proof.

`tools/controller_pilot_runtime.py` materialises isolated actors and implements
the frozen B/S/A comparison. B uses the bounded Sonnet-low repair then
Opus-high sequence; S uses the selected worker without Controller; A uses the
production `rigour-auto-v1` policy and `TaskDispatcher`, followed by the
selected worker. The Controller and worker share one task budget. Protected
grading occurs only after the actor finishes. The standard and
`frontier-candidate` role profiles propagate through the real dispatcher to
`LiveRoleRunner`; the frontier profile is exercised by C05-D1.

The current matrix manifest is
`a4254fe3d60f35cd86f347232c4f08a4a915ee84d308f87f76e620148a09850f`.
It is launch-ready except for exact operator authorisation. The pilot manifest
is `9a4f9d3efc1667871479a62c73dd1fb4ba8f0efbe6e1a2d25a02e89022a859a2`.
It remains execution-disabled until matrix evidence exists and a later exact
pilot authorisation is issued. Both checked-in templates remain
`NOT_AUTHORISED`.

## Offline evidence

The focused R5 suite passes **33/33** checks with zero provider calls. It covers
the 48/24/24 task shape, all 60 routing vignettes, all 15 model/effort cells,
the 288 variants, actor/oracle isolation, public-pass separation, scoring,
manifest tamper detection and exact authorisation. Fake transports execute all
60 matrix calls and all 18 pilot episodes once, exercise every cell flag, reach
four automatic Controller entries across standard and frontier profiles,
complete four Controller-to-worker handoffs, and reject replay after a crash.
The approved deep Graft refresh then completed 2,284 nodes, 4,736 edges and
431 file cards with zero stale or pending meanings; both freshness checks
passed.

## Work still required

R5 remains incomplete until the authorised live matrix records actual served
identity, usage, cost, latency and output for all 15 cells. Those observations
must be reviewed before enabling or repricing the pilot. The later 18-episode
pilot must then record four automatic Controller entries, including the
frontier profile, and at least one successful Controller-to-worker handoff with
complete accounting. Live failures, gaps and useful partial results count as
evidence; completion alone is not the quality measure.
