# Action plan 2: complexity routing, Controller gating, handoffs

Adopted 2026-09-15 on branch `the-system`, after `docs/PLAN.md` closed.
Authored by Claude (Fable 5.1) at Jeb's direction; the shape was described
and approved in conversation before this file existed. Status of the plan
as a whole: **in progress (since 2026-09-15)**.

Jeb's brief, in his words: route agents and sub-agents to the appropriate
model and effort level based on task complexity; bring the Controller in
when the lowest capable configurations fail, and also before routing when
the task is complex enough, on an ongoing, per-project, self-learning
judgement; produce a concise handoff for a fresh session whenever the model
or reasoning level must change or a new agent is launched, with a direct
API-cost projection and a time projection; make that behaviour part of the
project configuration, of any new project built from it, and of the
redistributable; build it by improving the existing infrastructure and
using existing test data and insights, not by running new tests.

## The design decision this plan rests on

Two measured findings stand in the way of complexity routing as it was
last tried, and the design goes through them rather than around them.

D44 found that the orchestrator's free-text assessment bends toward
whatever destination is in its context, which is why the table collapsed
to the floor. That is a property of letting the model that knows the
destinations judge in prose. D40 measured the alternative, a schema-forced
assessment made with the table removed from context and the cell resolved
by code, at 92.2 percent cell agreement and USD 0.103 per verdict, and
rejected it against the prose router's 95.7 percent at USD 0.1645. Since
then the prose router's verdict cost has doubled platform-side (E27, USD
0.23), and the prose router cannot do complexity routing at all without
reintroducing D44's attractor.

So: **separate the judge from the resolver.** The model assesses on a
rubric with no destination table in context (the rubric-only bundle
`build_dist.py --rubric-only` already produces). Deterministic code
(`tools/route.py`, which already exists) resolves the cell from that
assessment and a per-project outcome ledger. The attractor cannot act on a
judge that never sees the destinations. The ledger is the self-learning:
Bayesian updating of per-bucket pass probabilities from observed outcomes,
seeded from this repository's measured results, never from a model's
opinion of its own judgement.

One honest limit, stated up front rather than discovered later: the
three-axis triple is blind to the one task shape the floor measurably
fails (T10: D42 called it a disposition frontier, and T9 shares its
triple and passes at the floor). So no proactive rule on the triple can
single out that shape. It stays covered by the reactive
falsified-constraint trigger (D63). The proactive Controller rule is
therefore a combination of expected-cost arithmetic, which on current
evidence fires nowhere, and an explicit risk-appetite dial on blast
radius, which is labelled a policy where a consumer reads it.

## Rules

The rules `docs/PLAN.md` ran under, carried forward with one change:

1. One stage per session where the model class changes. Each stage names
   its model class and effort; the session states them and Jeb confirms
   before work starts.
2. Each task is its own commit on `the-system` with `python3
   test/harness/check.py` green first. Checkboxes and status lines in this
   file change in the same commit as the work.
3. A `claude -p` run is started by the session, after stating what will
   run and the projected cost; Jeb is asked first only above USD 100
   (D57). This plan projects **zero** live-run spend: every validation is
   against recorded data.
4. Every reopened decision (D40, D44, D45, D61, D63) gets its own entry in
   `docs/DECISIONS.md`. Nothing is reversed silently.
5. New: a stage boundary that changes the model or effort produces a
   handoff file under `handoffs/`, written to the contract Stage 1 fixes
   and Stage 3 automates. This plan's own transitions are the first uses.

## Stage 1. Design, priors from existing data, the spec

Status: **in progress (since 2026-09-15)**
Model: fable, high. Judgement over the evidence; everything after this
stage is implementation from what this stage writes down.

Tasks:

- [x] 1.1 This file, committed.
- [ ] 1.2 D64: the reopening, the judge/resolver separation, the triple's
      blindness to T10's shape, the proactive rule as arithmetic plus a
      labelled policy dial, and what each later stage may not change.
- [ ] 1.3 `src/cost_table.json`: per-cell cost and wall clock, the verdict
      cost, the Controller's per-run and instantiation costs, each row
      with its provenance (result file, n, date) and the cost regime it
      was measured under (E27). Derived from recorded results only.
- [ ] 1.4 `src/routing_priors.json`: per-bucket Beta priors on the floor
      passing and on each ladder rung passing given failure below,
      derived from confirmed benchmark results (`docs/FRONTIERS.md`) with
      a capped effective sample size so a project's own ledger can move
      them; the default ladder; named steering thresholds; the Controller
      rule's parameters including the policy dial. Provenance per bucket.
- [ ] 1.5 `docs/ROUTING-2-DESIGN.md`: the spec Stages 2 to 4 execute.
      Ledger schema, `route.py` extensions (posterior, rung activation,
      expected ladder cost, Controller rule), the assessment line and the
      rubric-only default bundle, `handoff.py`'s contract and template,
      the replay and backtest harness contracts and their pass conditions,
      the `check.py` checks, the propagation into `CLAUDE.md`,
      `LIFECYCLE.md`, the template and the README, and the `self_directed`
      decision (D40's defect).
- [ ] 1.6 `handoffs/2026-09-15-plan2-stage2.md`: the handoff to Stage 2,
      hand-written to the contract 1.5 fixes, with cost and time
      projections computed from 1.3. The first instance of the mechanism.
- [ ] 1.7 Update this stage's status line and commit it.

Exit criteria: D64 present; both JSON files committed with provenance on
every row; the design doc names every file Stage 2 to 4 will touch and
the pass condition of every check; the handoff file exists and names the
model and effort to switch to; harness green.

## Stage 2. The resolver and the ledger

Status: **not started**
Model: sonnet, high. Implementation from a written spec.

Tasks:

- [ ] 2.1 `src/System/schemas/RoutingLedgerEntry.schema.json` plus valid
      and broken fixture lines under `test/fixtures/system/`, so
      `validate_records.py` and the SCHEMA check cover the ledger.
- [ ] 2.2 `tools/route.py`: load priors and a ledger; per-bucket posterior;
      rung activation; expected ladder cost; the Controller rule;
      `--from-line` parsing of the orchestrator's assessment line;
      `--record` appending an outcome; `--explain` printing the arithmetic.
      Existing `resolve()` behaviour unchanged for callers that pass no
      ledger.
- [ ] 2.3 `test/harness/replay_routing.py`: re-resolve every recorded
      assessment in `test/results/` through the new resolver with an empty
      ledger; report agreement against `expected_cell` and the proactive
      Controller fire rate. Pass condition in the design doc.
- [ ] 2.4 `test/harness/backtest_ledger.py`: feed recorded benchmark
      outcomes into the ledger in recorded order; assert the learned
      activations reproduce D42 and D45 and nothing the benchmark refuted.
- [ ] 2.5 `route.py --selftest`; `check.py` gains ROUTE-PRIORS (priors
      consistent with FRONTIERS.md), COST-TABLE (every row has provenance),
      REPLAY and BACKTEST (both harnesses pass on the committed data).
- [ ] 2.6 Update this stage's status line and commit it.

Exit criteria: replay and backtest pass at the conditions the design doc
fixes; harness green with the four new checks counted; zero live calls.

## Stage 3. Handoffs

Status: **not started**
Model: sonnet, high.

Tasks:

- [ ] 3.1 `tools/handoff.py`: `new` writes a handoff to the template with
      computed cost and time projections (from `cost_table.json`, or the
      project's ledger means once it has enough entries); `check` refuses
      a handoff with a missing or empty section; both ship in `dist/`.
- [ ] 3.2 `check.py` gains HANDOFF: every file under `handoffs/` passes
      `handoff.py check`.
- [ ] 3.3 Regenerate Stage 1's hand-written handoff through the tool and
      diff; the tool must reproduce its projections.
- [ ] 3.4 Update this stage's status line and commit it.

Exit criteria: `handoff.py --selftest` and HANDOFF green; the Stage 1
handoff validates unchanged.

## Stage 4. The orchestrator side

Status: **not started**
Model: sonnet, high.

Tasks:

- [ ] 4.1 `src/ROUTING.md` section 2 rewritten: the assessment line's
      exact format; resolve by `route.py` with the project ledger; if the
      script cannot run, route to the floor and say so (never fall back to
      own judgement, the silent failure D39 warned of). Section 4
      rewritten around the ladder and the two Controller triggers.
- [ ] 4.2 `build_dist.py`: the rubric-only variant becomes the shipped
      `ORCHESTRATOR.md`; `route.py`, `handoff.py`, the priors and the cost
      table ship; `preflight.py` checks them and that Bash is permitted.
- [ ] 4.3 Regenerate worker definitions; ROW-BACKED and TABLE-DATA adapted
      to a table whose rows carry activation conditions.
- [ ] 4.4 Update this stage's status line and commit it.

Exit criteria: harness green; `dist/` rebuilt and installed into
`orchestrator-scratch` with preflight clean; no fixture's expected cell
changed without a decision entry.

## Stage 5. Propagation and close-out

Status: **not started**
Model: sonnet, medium.

Tasks:

- [ ] 5.1 `CLAUDE.md`: the handoff rule and the routing rule as standing
      project configuration.
- [ ] 5.2 `src/LIFECYCLE.md`: a "Handoffs" section, hence in every
      consumer's `ORCHESTRATOR.md`; `dist/CLAUDE.template.md` for a new
      project; `src/README.md` updated for both.
- [ ] 5.3 `docs/COST.md` recomputed; `docs/FINDINGS.md` consolidated.
- [ ] 5.4 D65: what this plan delivered, one line per brief item; this
      file marked complete.
- [ ] 5.5 Final `check.py --record`.

Exit criteria: harness green; plan marked complete; D65 present.

## Projection

Live API spend: USD 0 (rule 3). Session cost, estimated since no telemetry
exists for it: USD 40 to 90 equivalent across four to six sessions. Time:
six to ten hours of session time across the five stages.
