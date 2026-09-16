# Routing 2: the resolver, the ledger, the Controller rule, the handoff

Written 2026-09-15 for `docs/PLAN-2.md` Stage 1.5 (D64). This is the
specification Stages 2, 3 and 4 execute. It names every file those stages
touch, every format, and the pass condition of every check, so that a
sonnet-class session can implement it from this document alone and the
harness can say whether it did. Where a choice was open, this document
makes it and says why; a later stage that finds a choice wrong records a
decision entry rather than silently choosing otherwise.

Inputs already on disk: `src/routing_priors.json` (Stage 1.4, the
priors, the ladder, the thresholds, the Controller rule), `src/cost_table.json`
(Stage 1.3, unit costs with provenance), `tools/route.py` (D39's resolver),
`tools/validate_records.py` and `src/System/schemas/` (Stage 9's validator),
`tools/build_dist.py --rubric-only` (the bundle without the table),
`test/results/*.md` (every recorded verdict and benchmark run).

## 1. The assessment line

The orchestrator emits, before spawning, exactly one line:

```
assessment: <sensitivity>, <horizon>, <blast>; self_directed: <true|false>; prior_failure: <none|failed_at_xhigh>
```

Values are the enumerations in `routing_table.json`'s `axes`. This is the
two-stage format `score_routing.py` already parses (`TWO_STAGE_RE_3AXES`),
chosen so the recorded two-stage batches replay without translation. The
prose batches recorded `assessment: a, b, c; worker: w; action: x`; the
replay harness parses both.

The orchestrator never names a cell in the line. Under the rubric-only
bundle it has no table to name one from; that is the point (D44, D64).

## 2. The ledger

Path, in the consumer project: `.claude/routing-ledger.jsonl`. Append-only
JSON Lines, one entry per routed task, written by `route.py --record`.
Schema, to be added as `src/System/schemas/RoutingLedgerEntry.schema.json`
in the same subset of JSON Schema `validate_records.py` accepts:

| Field | Type | Meaning |
| :--- | :--- | :--- |
| `type` | const `RoutingLedgerEntry` | |
| `id` | string, `^led-[0-9]{3,}$` | assigned on append |
| `ts` | string, ISO 8601 | when the entry was written |
| `task_slug` | string, 1 to 80 chars | the orchestrator's short task name |
| `bucket` | string, `^(mechanical|structured|open)/(short|medium|long)/(contained|consequential)$` | from the assessment line |
| `self_directed` | boolean | recorded, not used |
| `first_cell` | string, a cell name or `controller` | what was tried first |
| `escalations` | array of `{cell, outcome}` | each later rung tried, in order; `cell` a cell name or `controller` |
| `final_outcome` | enum `pass`, `fail`, `unknown` | against the task's acceptance criteria, as the orchestrator judged it; `unknown` when it could not |
| `cost_usd` | number, minimum 0 | total reported for the task, all rungs |
| `wall_clock_s` | number, minimum 0 | total |
| `controller_run_dir` | string or null | `runs/<id>` when the Controller ran |
| `winning_technique` | string or null | from the Controller's `SolutionRecord`, the training signal `SYSTEM.md` section 8 asks for |
| `notes` | string, max 300 | free text |
| `ledger_version` | integer, 0 | constant; present so the validator's common fields hold |
| `references` | array, empty | constant; as above |

Fixtures: two valid lines and one broken line (a bucket outside the enum)
appended to `test/fixtures/system/valid.jsonl` and `broken.jsonl`, and the
SCHEMA check's documented broken-line count raised by one.

What counts as an outcome. `pass` is the orchestrator's own judgement that
the returned work met the acceptance criteria it wrote into the handover;
`fail` is that it did not and a rung was tried or the task abandoned. The
ledger records the orchestrator's judgement, which is the only signal a
live project has; the benchmark's deterministic graders do not exist
there. This is the caveat Gate A recorded (`docs/PLAN.md`, "the benchmark
gives B0 a free and perfect failure detector") and the ledger inherits it.

## 3. `tools/route.py`

Existing functions keep their signatures and behaviour; the harness's
TABLE-DATA and ROUTE-TOTAL checks call them and must not change. New:

**`load_priors(path=PRIORS_PATH) -> dict`** and **`load_ledger(path) ->
list[dict]`**, the latter returning `[]` for a missing file and skipping a
line that fails to parse with a warning on stderr, as `claudep.Checkpoint`
does.

**`posterior(priors, ledger, bucket) -> dict`**: for the bucket, the floor's
Beta `(alpha + passes, beta + fails)` where passes and fails are ledger
entries in that bucket whose `first_cell` is the floor and whose outcome
against the floor is known (a `pass` final outcome with no escalations, or
a `fail` recorded as the first escalation's reason); and per rung, the same
over entries where that cell appears in `escalations` (the conditional on
failure below is exactly what an escalation record is). Returns the means,
the counts, and the list of active rungs in cost order: `default_ladder`
plus any cell meeting `steering_rung_activation_min_n` and
`steering_rung_activation_min_pass` for this bucket.

**`expected_ladder_cost(post, costs) -> dict`**: `E_ladder` as the sum over
active cell rungs of `cost(rung) x P(reach rung)`, where P(reach) is the
product of the failure probabilities of every cheaper rung; `P_fail_all`;
per-rung `P(reach)`. Cost per rung from `cost_table.json`, or from the
ledger's mean for that cell once it has `ledger_overrides_after` entries.
The Controller is not a cell rung in this sum; it is what the sum is
compared against. **As built (2026-09-16, Stage C.3, B13): the
ledger-mean override was missing until Stage B.8 (A5, `docs/AUDIT-2026-09-16.md`)
added it, and it is not literally inside this function; `plan()` computes
`ledger_cell_means()` and merges it into the `costs` dict this function
receives, so the override reaches `expected_ladder_cost` through its
argument, not through code written inside it.**

**`controller_decision(priors, post, costs, bucket) -> dict`**: returns
`{proactive: bool, reason: "policy"|"expected_cost"|"none", E_ladder,
P_fail_all, failure_cost, controller_cost}`. `policy` when
`proactive_policy.enabled` and the bucket's sensitivity and blast are in
`when`. `expected_cost` when `E_ladder + P_fail_all x failure_cost >
controller_cost`, with `failure_cost` = `E_ladder` for contained and
`consequential_usd` for consequential.

**`plan(assessment, priors, ledger, costs) -> dict`**: the one function the
orchestrator calls. Returns `{first: <cell or "controller">, ladder: [...],
controller: <decision>, bucket, posterior, projection: {cost_usd_expected,
cost_usd_range, wall_clock_s_expected}}`. **As built (2026-09-16,
docs/PLAN-6.md Stage C.3, B13): `projection` carries `cost_usd_expected`
and `wall_clock_s_expected` only; `cost_usd_range` was never added.**
`first` is `controller` when the
decision is proactive, else the cheapest active rung whose posterior pass
mean is at least `steering_first_rung_min_pass`, else the floor. If
`prior_failure` is `failed_at_xhigh`, `first` is the frontier rung (the
existing rule, unchanged).

**CLI.** `--from-line "<assessment line>"` parses section 1's format;
`--ledger <path>` (default `.claude/routing-ledger.jsonl` under `--project`,
default cwd); `--explain` prints the posterior, the expected-cost arithmetic
and the decision with its reason, one line each, so a human can check it;
`--record --task-slug S --first-cell C --outcome pass|fail|unknown
--cost-usd X --wall-clock-s Y [--escalation cell:outcome ...]
[--controller-run-dir D] [--winning-technique T]` appends a validated entry
and prints its id; `--selftest` runs the scenarios below with no file I/O
outside a temp directory. Exit codes: 0, 1 for a documented gap, 2 for an
input defect, unchanged.

**Selftest scenarios** (each a named check, PASS/FAIL lines like
`system_controller.py --selftest`): (a) an empty ledger reproduces
`resolve()`'s cell for every fixture triple with `first` at the floor; (b)
three floor failures in one bucket raise `P_fail_floor` above 0.5 and move
`first` to `worker-opus-high` only if that rung's posterior clears
`steering_first_rung_min_pass`; (c) three `worker-sonnet-xhigh` passes as
escalations in a bucket activate that rung and insert it before
`worker-opus-high`; (d) `open/long/consequential` returns `first:
controller` with reason `policy`, and `first: worker-sonnet-low` with the
dial disabled; (e) a bucket whose ledger has enough opus-high failures to
push `E_ladder + P_fail_all x 10` above the controller cost returns reason
`expected_cost`; (f) `--record` then `load_ledger` round-trips and a
malformed line is skipped, not fatal; (g) `prior_failure: failed_at_xhigh`
returns the frontier rung regardless of the ledger.

## 4. Replay harness: `test/harness/replay_routing.py`

Reads every `test/results/*routing*-run*-of-*.md` and the standalone
routing files, extracts each fixture's recorded assessment (both formats
in section 1), resolves it through `plan()` with an empty ledger, and
compares `first` against the fixture's `expected_cell` (F16 expects
`clarify` and is scored on the recorded action, not the cell). Reports,
per source batch and pooled: agreement, Wilson interval, how many verdicts
returned `first: controller` and by which reason, and how many landed on a
non-floor cell. `--record` writes `test/results/<date>-replay-routing.md`.

Pass condition: pooled agreement on the recorded two-stage opus batches
(the ones made with the table out of context, the same condition the new
bundle creates) at or above D40's 92.2 percent; and zero `first:
controller` on any contained fixture. The prose batches are reported but
not gated: their assessments were made with the table in context and are
the attractor's own record, not the resolver's.

## 5. Backtest harness: `test/harness/backtest_ledger.py`

Maps each benchmark task to its bucket (the mapping in
`docs/FRONTIERS.md`: T1 mechanical/short/contained, T2 mechanical/long,
T3 structured/short, T4 structured/long, T5 and T8 open/short, T9 and T10
open/medium, T6, T7 and T11 open/long, all contained), reads every per-run
row from `test/results/*benchmark*.md` in file order, and turns each
task's runs into ledger entries: a floor pass is `first_cell` floor,
outcome pass; a floor fail followed by higher cells is a first-cell fail
with the higher cells as escalations and their pass or fail. Feeds them
through `posterior()` with the shipped priors and prints each bucket's
final posterior, active rungs and Controller decision.

Pass condition: every bucket's `first` stays the floor; `worker-opus-high`
is an active rung with posterior mean at or above 0.9 for
`open/medium/contained`; no sonnet rung between the floor and
`worker-opus-high` activates in any bucket (D42); `controller_decision`
is `proactive: false` for every contained bucket (D45). If the learning
rule reproduces D42 and D45 from the data it learned nothing the benchmark
refuted; if it activates anything else, it does not ship.

## 6. `check.py` additions (Stage 2.5)

| Check | Asserts |
| :--- | :--- |
| ROUTE-PRIORS | `tools/generate_priors.py`'s output equals the committed `src/routing_priors.json` byte for byte; every bucket entry carries a non-empty `provenance` and a `kind` in the allowed set |
| COST-TABLE | every cell, controller and verdict row in `src/cost_table.json` carries `provenance`, `regime` and `n`; a null cost is accompanied by `n: 0` |
| REPLAY | `replay_routing.py` exits 0 at section 4's pass condition |
| BACKTEST | `backtest_ledger.py` exits 0 at section 5's pass condition |
| HANDOFF (Stage 3.2) | every file under `handoffs/` passes `handoff.py check` |

## 7. `tools/handoff.py` (Stage 3)

**Template.** A handoff is a Markdown file `handoffs/<YYYY-MM-DD>-<slug>.md`
with these headings in this order, each non-empty:

```
# Handoff: <slug>
Written <date> by <model, effort>. Reason: model-change | effort-change | spawn.
## Goal
## Decisions already made
## Files and links that matter
## Verified facts
## Work completed
## Unresolved questions
## Exact next action
## Model and effort to set
## Cost projection
## Time projection
```

"Model and effort to set" names the class and effort in the words `/model`
accepts and, for a spawn, the cell name. "Cost projection" and "Time
projection" are computed lines the tool writes; the author may add prose
under them but may not edit the computed line.

**`new`**: `handoff.py new --slug S --reason R --to-model M --to-effort E
[--cell worker-x-y]... [--cells worker-x-y:N]... [--controller-runs N]
[--verdicts N] [--project P]` writes the skeleton with the headings, the
front matter, and the two computed sections: cost as the sum of `N x
cost_per_run_usd` per cell plus `controller runs x (quick_mode_run_usd +
instantiation_usd)` plus `verdicts x opus_prose_router_usd`, with a range
from each row's min and max, each addend named with its source row and
regime; time as the same sum over wall clocks, stated as a range. **As
built (2026-09-16, Stage C.3, B13): no cell, controller or verdict count
is ever passed in this repository's own handoffs (`docs/PLAN-6.md`'s
handoffs are all model/effort changes, "spawn"-reason handoffs use
`--pending-workers` instead), so `new` has never been exercised with
`--cell`, `--cells`, `--controller-runs` or `--verdicts` arguments, and
the min/max range this paragraph describes has never been produced or
checked against a real run. The two computed-line paragraph below,
session load and estimate, is the path every handoff on record has
actually taken.** Values come from the project's ledger means for a cell
once it has `ledger_overrides_after` entries, else `cost_table.json`, and
the line says which. A cell with a null cost (the frontier cells) is
written as "unmeasured" and the total is marked "excludes N unmeasured".
A model or effort change with no cells is a session handoff: the cost
line then states the session load estimate from `cost_table.json`'s
`session` row, labelled an estimate.

**`check`**: `handoff.py check <file>` exits 1 naming the first missing
or empty heading, the first heading out of order, or a computed line that
does not match what `new` would compute from the same arguments recorded
in the front matter (the tool writes its own arguments into an HTML
comment under the title so `check` can recompute).

**`--selftest`**: writes a handoff to a temp directory, checks it,
corrupts each section in turn and asserts `check` names it.

Stage 3.3 regenerates `handoffs/2026-09-15-plan2-stage2.md` through `new`
with the arguments its front matter records and diffs against the
hand-written file; the computed lines must match.

## 8. The orchestrator side (Stage 4)

`src/ROUTING.md` section 2 becomes: assess (section 1 line), then run
`python3 tools/route.py --from-line "<line>" --explain` and spawn `first`,
stating the line, the cell and the reason in the routing line. If the
script cannot run (Bash not permitted, file missing), spawn
`worker-sonnet-low` and say in the routing line that the resolver did not
run; never fall back to choosing a cell from the rubric, which is the
silent failure D39 named. After the task, `route.py --record` with the
outcome. Section 4 becomes the ladder: on failure, the next active rung
from the plan's `ladder`; the Controller when the rungs are exhausted or
on the falsified-constraint signal (D63, unchanged); the frontier last.

`build_dist.py`: the rubric-only variant becomes the default
`ORCHESTRATOR.md`; the full-table variant remains available under a flag
for the harness. Ships `tools/route.py`, `tools/handoff.py`,
`src/routing_priors.json`, `src/cost_table.json`, and the ledger schema.
`preflight.py` gains: priors and cost table present; `route.py --selftest`
passes from the installed copy; a warning if `.claude/settings.json` does
not permit `Bash(python3 *)`.

`routing_table.json` keeps its two rules; rows above the floor are not
table rules but rungs in the priors' ladder, so ROW-BACKED and TABLE-DATA
hold as they are. Fixtures' `expected_cell` values are unchanged: with an
empty ledger `plan()` returns the floor for every non-frontier fixture,
which is what they expect.

## 9. Propagation (Stage 5)

`CLAUDE.md`: a "Handoffs" section stating the rule (when, where, the
tool, the projections) as standing configuration. `src/LIFECYCLE.md`: the
same section for consumers, hence in `ORCHESTRATOR.md`.
`dist/CLAUDE.template.md`: a starting `CLAUDE.md` for a new project with
the pointer line and the handoff rule. `src/README.md`: the template, the
ledger, and what `route.py` needs (Bash permission).

## 10. What this design does not do

It does not measure the resolver against a consumer's task mix; the
replay proves agreement with this repository's fixtures. It does not make
the orchestrator's pass/fail judgement reliable; the ledger learns from
that judgement and inherits its errors. It does not detect T10's shape
from the assessment; D63's trigger does. It does not run a single live
call.
