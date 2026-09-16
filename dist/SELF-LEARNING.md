# Self-learning: mechanics, capabilities and limitations

This is a living document. It is shipped in `dist/`, read by whoever installs
the bundle and wants to know what "the project's own ledger learns" actually
means before they trust it. Unlike `src/ROUTING.md`, which states the
procedure a session follows, this file explains the mechanism underneath it
and states plainly what it can and cannot do. Keep it current: whenever
`src/routing_priors.json`'s `steering` block, `tools/route.py`'s `posterior()`
or `plan()`, or the ledger schema changes, this file's numbers and claims
need re-checking against the change in the same commit, the same discipline
`CLAUDE.md`'s "Atomic edits with guards" already asks of everything else.

## What "self-learning" is here

There is no model training, no weights, no fine-tuning and no network call
involved. Learning is deterministic Bayesian arithmetic over a local file,
recomputed from scratch on every single invocation of `tools/route.py`. Two
files hold everything:

- **`src/routing_priors.json`**, shipped identically in every install.
  A Beta-distribution prior per assessment bucket (eighteen
  `sensitivity/horizon/blast` combinations), generated once from this
  repository's own benchmark by `tools/generate_priors.py` and frozen at
  build time. A consumer project never writes to this file.
- **`.claude/routing-ledger.jsonl`**, created empty the first time a project
  uses the bundle, one `RoutingLedgerEntry` per line
  (`src/System/schemas/RoutingLedgerEntry.schema.json`): the bucket, the
  cell tried first, every escalation with its own pass or fail, the final
  outcome, cost, wall clock, and whether the run compacted. This file is
  local to one project. It is never read back into this repository, never
  shared with another project, and never regenerates `routing_priors.json`.
  Learning is scoped to one deployment and starts over, from the shipped
  priors, in any other.

## The per-task cycle that produces a ledger entry

1. **Assess** (`src/ROUTING.md` section 1). The orchestrator writes one
   assessment line without ever seeing a destination table:
   `ORCHESTRATOR.md` ships with the table stripped out specifically so the
   judgement cannot bend toward a cell it can see, a measured failure mode
   (D13, D44).
2. **Resolve** (`src/ROUTING.md` section 2). `python3 tools/route.py
   --from-line "<line>" --project <root> --explain` combines the shipped
   prior with this project's ledger and prints the cell to spawn, or the
   literal word `controller`.
3. **Spawn** (`src/ROUTING.md` section 3). The Agent tool spawns that cell;
   `route.py --spawn` immediately writes a *pending* ledger entry
   (`final_outcome: unknown`), before the worker finishes, so a mid-session
   compaction can recover the work in flight rather than losing the record.
4. **Record** (`src/ROUTING.md` section 2, "After the task finishes").
   `route.py --record --pending <id> --outcome pass|fail|unknown --cost-usd
   ... --wall-clock-s ... [--escalation cell:pass|fail ...]` completes the
   entry. This step is the only one that teaches the project anything.
   `ROUTING.md` states plainly that skipping it "is not a shortcut; it is
   the project staying on the shipped, generic priors forever."

## What specifically shifts as entries accumulate

All of the following is recomputed by `posterior()` and `plan()`
(`tools/route.py`) from the whole ledger file, fresh, every call. There is
no cache and no incremental state beyond the file itself.

- **The floor's own pass rate, per bucket.** `floor_pass`/`floor_fail` use
  Laplace smoothing, `(passes + 1) / (n + 2)`, against the prior's effective
  sample size (capped at 10 for a measured prior, 4 bracketed, 3
  policy-inherited), so a handful of a project's own outcomes can move a
  bucket's mean noticeably rather than being swamped by the shipped count.
  A plain `--outcome fail` with no `--escalation` counts as a floor failure
  too: a bucket where the floor keeps failing and the orchestrator just
  gives up or does the work itself still moves the posterior (this was a
  real bug until fixed, `docs/AUDIT-2026-09-16.md` A4, `docs/DECISIONS.md`
  D81, `docs/PLAN-6.md` B.5).
- **Which cell is tried first.** `first` is the cheapest active rung whose
  posterior pass mean clears `steering_first_rung_min_pass` (0.6 as
  shipped); if none does, the floor is still tried by default.
- **Whether a whole new rung becomes reachable for a bucket.** The main way
  the ladder grows without a bundle change: a cell outside
  `default_ladder` becomes an active rung for one bucket once that
  bucket's ledger holds at least `steering_rung_activation_min_n` (3)
  escalation outcomes at that cell with a conditional pass rate at or
  above `steering_rung_activation_min_pass` (0.5), inserted in cost order.
  It starts from an uninformative Beta(1,1) prior, mean 0.5, since no
  benchmark data exists for that cell in that bucket; it moves purely on
  this project's own evidence from there.
- **Cost and wall-clock projections.** Once a cell has at least
  `ledger_overrides_after` (5) ledger entries anywhere in the project,
  `ledger_cell_means()` replaces the generic figure in
  `src/cost_table.json` with this project's own measured mean, splitting
  each entry's total evenly across every cell it actually touched.
- **Whether the Controller pre-empts a task at all.**
  `expected_ladder_cost` and `controller_decision` recompute the expected
  cost down the active ladder against the Controller's own cost, using
  the (possibly now overridden) per-project figures. The shipped priors
  trigger this on no bucket; a project whose ladder keeps escalating
  expensively can cross that threshold on its own data alone. The priors
  file itself names this "the path a project's own ledger opens."
- **The decomposition advisory.** A second, independent Beta tracker per
  bucket counts compaction outcomes only, from `context.compactions` on
  every entry where that was actually observed (an entry with unknown
  compaction status contributes to neither side, "absence is not
  evidence"). Once it has at least `overflow_advisory_min_n` (3)
  observations and a mean at or above `overflow_advisory_min_mean` (0.3),
  `--explain` prints a line telling the orchestrator to split the task
  into sub-handovers before spawning. This never changes which cell is
  chosen: a compaction is treated as a horizon signal, not a capability
  one (D68, `docs/COMPACTION-DESIGN.md` section 6). Runs that did compact
  are excluded from the capability posterior above, so a mid-task
  compaction is never misread as the cell being incapable.

## What never changes

`src/routing_table.json`'s two static rules, the floor and the frontier
(reached only via `prior_failure: failed_at_xhigh`), are fixed for the life
of a bundle version; the ledger never rewrites them. The fifteen worker
personas, the cell definitions, and `src/routing_priors.json` itself are
likewise immutable from inside a consumer project. Any change to what the
resolver can return at all (a new cell in `default_ladder`, a changed
steering threshold, a changed policy dial) needs a decision entry and a
clean run of `test/harness/replay_routing.py` and `backtest_ledger.py`
before it ships, the same discipline a table row once needed
(`src/ROUTING.md` section 2's own constraints).

## Capabilities

- Starts safe on day one: an empty ledger resolves purely on the shipped,
  benchmark-seeded priors, which route almost everything to the cheapest
  cell and only proactively invoke the Controller on the one labelled
  risk-appetite dial (open, consequential work).
- Moves fast on real evidence: the effective-sample-size caps mean a
  bucket's posterior can shift meaningfully after single-digit outcomes,
  not hundreds.
- Learns three independent things per bucket, not just "which cell":
  whether the floor still holds, whether a specific higher cell is worth
  activating, and whether tasks in that bucket tend to overflow context.
- Degrades to a named, visible failure rather than a silent one: if
  `route.py` cannot run at all, `ROUTING.md` requires spawning the floor
  and saying so in the routing line, never substituting a remembered
  judgement.
- Fully auditable: every number `--explain` prints traces to a ledger line
  or a `routing_priors.json` entry a human can open and read; nothing is
  opaque model state.

## Limitations

- **Skippable, and silently so.** Nothing enforces that a session actually
  runs the `--record` completion step. `ROUTING.md` states the
  consequence in prose, but no code path refuses to proceed, warns loudly
  mid-session, or flags a stale ledger; `--explain` does print the current
  pass/fail counts for the bucket, so `(ledger: 0 pass, 0 fail)` is visible
  to a careful reader, but nothing calls that out as a problem.
- **No recency weighting.** Every entry in the ledger counts equally
  forever; there is no decay, no rolling window, and no code path that
  discounts an old outcome against a newer one. A project whose task mix
  changed six months ago is still averaged against outcomes from before
  the change.
- **No pruning or rotation.** The ledger file grows without bound; nothing
  in this bundle trims, archives or rotates it.
- **No transfer across buckets.** Evidence in `open/medium/contained`
  moves nothing in `open/short/contained`, even though a human would
  likely treat them as related. Each of the eighteen buckets learns in
  total isolation from the other seventeen.
- **No transfer across projects, and no path back to this repository.**
  A project's ledger is never read by anything outside that project;
  the shipped `routing_priors.json` is generated solely from this
  repository's own benchmark (`tools/generate_priors.py`,
  `docs/FRONTIERS.md`), never from any consumer's accumulated ledger.
  Reinstalling a fresh bundle, or using a different project, starts over.
- **The compaction signal it depends on is not fully verified.** The
  overflow tracker reads `context.compactions`, populated by
  `tools/context_probe.py`'s status-line hooks; whether the companion
  per-worker token-sample data behaves reliably in every configuration is
  still an open question in `CLAUDE.md`'s "Open questions worth
  developing" (`.claude/context-tasks.json`'s `tokenSamples`), so the
  overflow advisory should be read as evidence-based but not
  exhaustively verified across every Claude Code version.
- **Two of five assessed fields are recorded but never used to resolve.**
  `self_directed` and `prior_failure` aside, `self_directed` is kept in
  every ledger entry for the record but, per `ROUTING.md` section 2's own
  text, "not an input to resolution any more: no rule in the current
  table names it in its conditions." Learning cannot happen on a
  dimension resolution never reads.
- **Bounded escalation, not open-ended optimisation.** The ladder can only
  activate cells the shipped bundle already made reachable in principle;
  it cannot discover or promote a cell absent from `COST_ORDER` (the six
  cells `ROUTING.md` calls "not reachable by this resolver at all today"
  stay unreachable no matter what the ledger records).
- **A wrong outcome label teaches the wrong lesson.** The mechanism trusts
  `--outcome`/`--escalation` exactly as recorded; nothing cross-checks a
  claimed `pass` against independent evidence. A session that mis-grades
  its own work moves the posterior in the wrong direction with the same
  weight as a correctly graded one.

## Keeping this current

The numeric thresholds quoted above (0.6, 3, 0.5, 5, 3, 0.3) are read from
`src/routing_priors.json`'s `steering` block as shipped at the time of
writing. When that block, `tools/route.py`'s `posterior()`/`plan()`, or the
`RoutingLedgerEntry` schema change, update the affected bullet in the same
commit; do not let this file describe a mechanism the code no longer has.
A change that adds a new learned signal (a third Beta tracker, for
example) gets its own bullet under "What specifically shifts", not a
footnote. A change that closes one of the open items under "Limitations"
moves that bullet to "Capabilities" with the finding or decision that
closed it, following this repository's own convention of citing the
evidence rather than restating the claim.
