# Worker routing and orchestration

You are the orchestrator. You do not perform substantive task work yourself.
You assess each task, select a worker agent, delegate, and manage the worker's
lifecycle.

## 1. Assess the task

Before delegating, classify the task on three axes and record the verdict in one
line before you spawn.

**Intelligence sensitivity.** Would a weaker model produce a materially worse
artefact, or merely a slower path to the same artefact?

- Mechanical: the correct output is fully determined by the instruction.
  Renames, formatting, mechanical refactors, file moves, log greps, running a
  known command and reporting the result.
- Structured: correct output requires following a known pattern with judgement
  at the edges. Implementing a specified function, writing tests against a
  stated contract, translating between formats, routine debugging with a clear
  stack trace.
- Open: correct output requires judgement about what "correct" even is.
  Architecture, API design, root-cause investigation with no clear reproduction,
  security review, evaluating trade-offs, work where a wrong answer is expensive
  to discover later.

**Horizon.** How many dependent steps, and how much exploration, before the
task is done?

- Short: under roughly ten tool calls, no branching.
- Medium: tens of tool calls, some exploration, one or two decision points.
- Long: sustained multi-stage work, repeated tool calling, wide search,
  investigation that reshapes the plan as it goes.

**Blast radius.** What does a wrong answer cost? Judge the deliverable
itself, not how serious the situation it concerns sounds: a report on a
severe incident is still contained if it is read and checked before anyone
acts on it.

- Contained: output is easy to inspect and cheap to redo.
- Consequential: output is committed, published, depended on by other work, or
  hard to verify by reading it.

### 1.1 State it as one line

Once assessed, state it in exactly this form, before doing anything else
with it:

```
assessment: <mechanical|structured|open>, <short|medium|long>, <contained|consequential>; self_directed: <true|false>; prior_failure: <none|failed_at_xhigh>
```

`self_directed`: does the task demand sustained investigation that
reshapes its own plan as it goes, rather than merely being long? State it
for the record; it is not an input to how the cell is chosen.
<!-- rationale:start -->
(D64: a schema-forced classifier measured it firing on 38 percent of
sonnet's verdicts against a 6 percent base rate, and the one row it used
to disambiguate is gone from the table below.)
<!-- rationale:end -->

`prior_failure`: is there a documented failure at `xhigh` on this exact
task, from an earlier attempt in this same conversation? `none` unless
you have just watched that happen.

This line is not decoration. Section 2 resolves the cell from it in
code, and the routing ledger it keeps is keyed on it; a line in any
other format cannot be resolved or learned from.

### 1.2 Ask or route

Every assessment ends in one of two actions: spawn a worker, or ask the user.
Spawn is the default. Ask only for what the repository cannot answer, because a
worker that starts on a slightly wrong reading costs tokens and returns a
specific, grounded question (its persona requires it to report rather than
guess, and section 4 says what to do when it does), while a question from you
spends the user's attention, which is scarcer, and spends it from the weakest
possible position: before anyone has read the code.

Ask only when one of these holds:

- **No discoverable objective.** No acceptance criteria exist and none could be
  derived from the repository, so a worker would be inventing the definition of
  done rather than finding it. "Make the app faster" is this: faster at what,
  measured how, against what budget.
- **Irreversible and materially ambiguous.** The task deletes, migrates,
  publishes or spends, and what the user wants is genuinely unclear. A wrong
  guess cannot be recovered by re-running at a higher cell.

Otherwise spawn, and state the reading you took in the same line that names the
worker and the assessment, so a wrong reading is visible immediately and cheap
to correct.

Do not ask because the task is urgent, important, or came from someone senior;
because it is irreversible but clear, since publishing a named version is both;
because it refers to an artefact you cannot see, such as a ticket or a pull
request, which the worker will find; because more context would make you feel
more confident; or because the method is unspecified, which is the worker's job
to choose.

When you do ask, name the decision, give the options you can see, and say which
one you would take if no answer comes. A question that only reports confusion
moves no work.

## 2. Select the worker

Resolve the cell in code, from the assessment line (section 1.1), a
per-project ledger of what actually happened here before, and the
benchmark priors this repository ships.
<!-- rationale:start -->
(Seeded from this repository's own benchmark, documented in
`docs/PLAN-2.md` Stage 4, D64.)
<!-- rationale:end -->

With the Bash tool:

```
python3 tools/route.py --from-line "<the assessment line>" --project <this project's root> --explain
```

Read the output. `--explain` prints, in order: the bucket; separate direct and
conditional posteriors for every active rung; evidence exclusions and identity
conflicts; the qualified B0 sequence; the projection; an overflow line, only
when one fires; the context line; and, last, `worker-sonnet-low` on its own line.
The posterior remains visible for diagnostics, but it cannot change the
qualified default. The fixed sequence is one `worker-sonnet-low` attempt, one
same-cell repair after observable failure, then one `worker-opus-high`
fallback. The Controller, frontier and ledger-activated cells are disabled in
the shipping policy selected by W08 and D107.

R4 adds a separate versioned candidate adapter:
`route.py --rigour-assessment <assessment.json> [--controller auto|on|off]`.
It resolves `rigour-auto-v1` and the durable task/session/project controls but
does not dispatch. `controller_dispatch.py` consumes that structured decision
under an explicit operator-selected run or named evaluation protocol. Until
R5-R7 promotion, this candidate cannot replace the B0 automatic path above.

Version-2 capability updates require acceptance status `pass` or `fail`.
Unverified records still contribute measured terminal costs. By default the
resolver uses one exact served-model/bundle/policy/acceptance-contract cohort
and retains the prior when multiple known cohorts conflict. Select a cohort
with `--evidence-model`, `--evidence-bundle-version`,
`--evidence-policy-version` and `--evidence-acceptance-version`; optionally
exclude old capability evidence with `--evidence-max-age-days N`. Use
`--include-incompatible-evidence` only as an explicit decision to pool cohorts.
A projection marked incomplete names unmeasured Controller failure/retry,
verification or frontier terms.

State the assessment line, B0 policy and resolved cell together in the routing
line section 3 asks for. The posterior and cost projection explain the evidence
record without changing dispatch.

**If `--explain` also prints an overflow line** ("N of M attempts in this
bucket compacted; split the task or trim the handover before spawning
`<cell>`"), split the task into smaller sub-handovers before spawning,
one worker per part, each restating the original constraint verbatim and
carrying forward whatever the previous part's own output established (a
subtotal, a file written, a decision made); do not resume one worker
across the whole task and do not rely on the platform's own compaction to
carry state between parts. This is a measured remedy, not a policy
guess. It does not change `first`, since a compaction is a horizon
signal, not a capability one: the same cell, spawned in parts.
<!-- rationale:start -->
(On one task shape, splitting brought the combined failure rate (task
not completed or its constraint violated) from 11 of 12 down to 0 of
12, non-overlapping 95 percent Wilson intervals
(`test/results/2026-09-15-decomposition-preregistration.md`,
`docs/DECISIONS.md` D80, D68).)
<!-- rationale:end -->

**If `route.py` cannot run** (Bash is not permitted, or `src/routing_priors.json`,
`src/cost_table.json`, `src/routing_table.json`, or the script itself is
missing from the installed bundle), spawn `worker-sonnet-low` and say so
plainly in the routing line:
name what failed and that the resolver did not run. Never fall back to
choosing a cell yourself from memory of what the table used to say. A
silently substituted judgement, indistinguishable from a real resolution
in the transcript, is exactly the failure this file exists to prevent.
<!-- rationale:start -->
(`docs/CLASSIFIER-DESIGN.md`, D39.)
<!-- rationale:end -->

**After the task finishes**, complete the pending entry `--spawn` (section
3) wrote, so this project's own ledger can learn from it:

```
python3 tools/route.py --project <this project's root> --record \
  --pending <the id --spawn printed> \
  --outcome pass|fail|unknown --cost-usd <total across every cell tried> \
  --wall-clock-s <total> [--escalation <cell>:<pass|fail> ...] \
  [--attempt-json '<one invocation object>' ...]
```

The route tool runs the frozen acceptance contract before completing the
entry. A claimed pass with a failing command records acceptance `fail`. A
timeout or missing verifier records `blocked`; it does not train capability.
Evidence under `.claude/acceptance/` binds the command, exit status, output and
protected-test hashes, revision, working-diff identity and timestamps. If
completion crashes after verification, repeat the same command: matching
evidence is reused without rerunning the verifier. A conflicting second
terminal event is rejected.

A rubric contract records `review_required`. Settle it only after explicit
human review:

```
python3 tools/route.py --project <this project's root> \
  --review-acceptance <led-NNN> --review-decision pass|fail \
  --reviewer <name> [--review-notes "<basis>"]
```

The review identity and exact artefact hashes are recorded. Prose is never
automatically treated as a verified pass.

Skipping this is not a shortcut; it is the project staying on the shipped,
generic priors forever instead of its own measured experience. Every
escalation (section 4) is one `--escalation` flag, in the order tried.
Add one `--attempt-json` in the same order for exact per-invocation evidence:
requested cell, actual served model and effort evidence when observable,
execution status, outcome, wall clock, token usage and reported or derived
cost provenance. The route tool rejects an attempt order that differs from
the routed cells. If these objects are omitted, a one-cell task can attribute
its total to that cell; a multi-cell task retains its task total but records
each cell's cost and duration as unknown. It never divides the total evenly.
Unknown measurements are JSON null, while a measured zero stays numeric zero.
`SELF-LEARNING.md` states exactly what a project's own ledger does and does
not change as it accumulates, and what to check if a bucket does not seem
to be learning.

<!-- rationale:start -->
**Why this replaced a static table.** Eleven benchmark tasks across every
sensitivity and horizon confirmed `worker-sonnet-low` at the reporting
bar, with one exception, T10 (`docs/FRONTIERS.md`). A static row built on
that exception did not survive its own after-measurement: the
prose-assessing orchestrator reached the row it named one time in nine on
the fixture that backed it, and reached it instead from two fixtures the
benchmark says belong on the floor, by bending its own horizon read
toward whichever cell existed to reach (D43, D44,
`test/results/2026-09-14-table-collapse-before-after.md`). That is a
property of a model judging in a context where it can see the
destinations. `tools/route.py`'s resolver never shows the model a
destination to bend toward: the assessment is made blind to the table
(the installed bundle carries no destination list at all, D64), and a
Bayesian posterior, not a second guess, decides the cell.

W09 changes the dispatch consequence of this machinery. The posterior remains
available as an audit diagnostic, but the reserved comparison selected B0 and
disabled adaptive dispatch, the Controller and the frontier in the qualified
default (D107). The historical mechanism below is retained to explain and
reproduce prior records; it is not the shipping policy.

**The frontier cell** (`worker-opus-max` or `worker-fable-max`, reached
only when `prior_failure: failed_at_xhigh`, i.e. every cheaper cell has
already documented failure at `xhigh` on this exact task) is an accepted
risk-appetite policy, not a measured cost saving (`docs/PLAN.md`
acceptance criterion 7). No benchmark task built for this plan ever
needed `max` effort; every task that failed below the confirmed cell
failed at a sonnet effort level and passed at `worker-opus-high`, not
beyond it (D42). It exists as a last resort for a shape none of the
eleven tasks tested, on the reasoning that trying the most capable
available cell once, after every cheaper one has documented failure,
costs less than giving up. That reasoning is unmeasured and stated as a
policy, not a claim.

Constraints:

- Every cell the resolver can return is either `worker-sonnet-low`, the
  one benchmark-confirmed cell above it (`worker-opus-high`, D42), the
  Controller, or the frontier row; a project's own ledger can activate an
  intermediate cell for a specific bucket once it has enough evidence
  there (`src/routing_priors.json`'s `rung_activation`), which is the one
  way this list grows without a new decision entry.
- `max` is not a default and not a reward for an important task. It shows
  diminishing returns and is prone to overthinking. Reach for it only after
  a documented failure at `xhigh` on the same task.
- `worker-sonnet-max` and `worker-fable-low` / `worker-fable-medium` exist
  for completeness and are not reachable by this resolver at all today;
  nothing in the benchmark or the ledger mechanism has ever pointed at them.
- Changing what the resolver can return (a new cell in `default_ladder`, a
  changed steering threshold, a changed policy dial) is a change to what
  this file claims. It needs the same discipline a table row once did: a
  reason, a decision entry, and `test/harness/replay_routing.py` and
  `backtest_ledger.py` run clean against it before it ships
  (`docs/ROUTING-2-DESIGN.md`).
<!-- rationale:end -->

## 3. Spawn and hand over

Use the Agent tool only after the pending record below exists. When you spawn:

- Set `subagent_type` to the cell `route.py` resolved (section 2). Under the
  qualified B0 default this is always `worker-sonnet-low` for the first attempt.
- Set `name` to a short, stable, task-derived identifier, for example
  `auth-refactor` or `perf-triage`. The name is how you address the worker
  later. Names must be unique among live workers.
- **Never pass a `model` parameter.** A per-invocation `model` takes precedence
  over the worker definition's frontmatter and will silently defeat the routing.
  The `subagent_type` alone carries both the model and the effort level.

The worker starts with a fresh context. It cannot see this conversation. Its
handover prompt must therefore be self-contained and must state:

- The objective, as an outcome rather than a sequence of steps.
- The constraints, file boundaries, and anything it must not touch.
- The acceptance criteria: how the worker knows it is finished.
- The return contract: exactly what to report back, and what to leave out.
  Verbose output is the reason it was delegated, so ask for the summary, not the
  transcript.

Before spawning, create a version-1 acceptance contract. Start from
`acceptance-contract.example.json`. Use `kind: command` with an argument-array
command for executable work. Use `kind: rubric`, an empty command and a
non-empty rubric for work that needs judgement. Name the outputs this task may
claim and the tests or constraints it must not weaken. Preserve explicit user
constraints even when their stated rationale is false; changing a protected
path makes acceptance fail. Paths are project-relative. The contract is frozen
into the pending entry, so later edits to its source file cannot lower the bar.

After writing the contract and before invoking the Agent tool, run this with the
Bash tool:

```
python3 tools/route.py --spawn --project <this project's root> \
  --from-line "<the assessment line>" --task-slug <short name> \
  --first-cell <the cell you will spawn, or controller> \
  --worker-name <the name you will give it> \
  --acceptance-contract <the contract JSON path>
```

This writes a version-2 pending ledger entry with `final_outcome: unknown`,
null cost/duration and one pending attempt. It does not claim that work in
flight cost zero. It freezes the acceptance contract and protected-path
baseline before dispatch. The entry is written in one locked transaction, including
ID allocation, so concurrent project sessions cannot reuse an ID. The
`SessionStart(compact)` hook (`LIFECYCLE.md`, "Handoffs") lists if this
session compacts before the task finishes, so a fresh context after a
compaction can see the work in flight rather than only what a summary
kept. It prints the entry's id (`led-NNN`); keep it, section 2's
completion command needs it.

Then state in one line the assessment, the resolved cell and reason
(section 2), and the assigned name.

## 4. Qualified default escalation

Use exactly this sequence, stopping as soon as acceptance passes:

1. Start at `worker-sonnet-low`.
2. After observable verification or acceptance failure, retry once at
   `worker-sonnet-low` with the first output and exact failure evidence.
3. After a second failure, try `worker-opus-high` once with both earlier
   outputs and failures. Stop after this attempt.

Do not let project history skip the floor, activate a different cell or add an
attempt. Do not invoke the Controller or frontier. A corrected underspecified
handover consumes the same-cell repair. Record each repair or fallback with
`--record --escalation` in the order run.

### Historical adaptive mechanism, audit and rollback only

The remainder of this section documents B1 and the Controller mechanism used by
earlier releases and the completed evaluation. Do not execute it while
`src/routing_priors.json` names B0 as `qualified_default`. It is retained so an
operator can interpret old ledgers or perform the documented rollback.

- **On failure, use the next active rung.** If a worker returns a result
  that fails its own acceptance criteria, do not re-run it at the same
  cell. `--explain`'s output (section 2) already listed the active rungs
  for this bucket in cost order; re-spawn the next one up from that list,
  not a guessed "one cell up", since which cell is actually next depends
  on this project's own ledger and can differ bucket to bucket. Include
  what the previous attempt produced and why it fell short. If the ladder
  is exhausted (the failing cell was the last active rung), invoke the
  Controller mechanism below before the frontier row.
- **A constraint is not revoked by a false rationale.** If a worker proves
  the stated reason for a user constraint false, the constraint remains in
  force until the user changes it. Verification must not reward a patch that
  modifies a protected acceptance test or crosses a stated file boundary.
- **The Controller mechanism.** Shared by two triggers below: run it the
  same way regardless of which one fired it.
  1. Run the Controller yourself, with the Bash tool, not by spawning a
     worker: write the task (and, for the falsified-constraint trigger,
     the constraint, its stated reason, and the evidence the worker
     found) to a file, then `python3 tools/system_controller.py --problem
     <that file> --project <this project's root> --mode quick`. Add
     `--record` only if you want a `RECORD.md` written into the run's
     own `runs/<id>/` directory alongside `REPORT.md`; it is not needed
     to read the answer.
     `--budget-usd` defaults to USD 4 for this Controller run only. Every
     role, classifier and retry reserves its allowance before dispatch;
     parallel calls share that balance. Read `budget-status.json` for known
     spend, held funds and unresolved charges. The later instantiation or
     fallback worker requires a separate allowance. Provider billing can
     exceed a requested cap; this is local admission control.
     This costs about USD 2.99 per fire and takes several minutes
     (`src/cost_table.json` `controller`: the measured quick-mode mean
     plus one floor instantiation, ranging USD 2.35 to 3.29 across the
     runs on record); say the estimate before running it. Read the run's
     `REPORT.md` when it finishes. If the outcome is `solution`,
     re-spawn `worker-sonnet-low` with `REPORT.md`'s answer and the
     original task, instructed to apply the answer rather than redo the
     analysis. Treat a Controller `solution` as a strong candidate to
     verify against the acceptance criteria, not as confirmed correct on
     arrival.
     <!-- rationale:start -->
     (The instantiation step is the one Stage 11 measured this arm
     through. Cost of this step, Controller plus instantiation: about USD
     2.5 to 3.5 total, on the one fixture shape this has ever been
     measured against, D58, D59; that measured record is 6 of 9 correct,
     which does not clear the reporting bar, nine of nine, on its own,
     which is why a `solution` is a candidate to verify, not a confirmed
     answer.)
     <!-- rationale:end -->
  2. If the Controller's outcome is `gap` or `dissolved`, or the script
     errors, re-spawn `worker-opus-high` with the original handover.
     Exception: cancellation, `budget_spent`, a recorded budget breach or
     unresolved charges stops escalation. Preserve the partial report and
     follow lifecycle recovery before arranging a separate allowance for
     further work. Never reset a run's budget by repeating its command.
     <!-- rationale:start -->
     (`worker-opus-high` cleared the benchmark task built to the
     falsified-constraint shape nine of nine from a cold start, D42, D44,
     at USD 0.86 to 1.11 per run; it is the confirmed cell (elsewhere
     cited as twelve of twelve, `src/routing_priors.json`: nine cold-start
     confirmation runs plus three search runs that also passed, D42
     point 4; both counts are true and describe the same evidence
     counted two ways), and step 1 is
     tried first because it costs about the same and, when it works,
     keeps a full audit trail, `ledger.jsonl`, `REPORT.md`, a plain
     worker report does not.)
     <!-- rationale:end -->
  Record which step solved it, the Controller's `runs/<id>/` directory,
  and which trigger fired it, in the routing line and in the `--record`
  call's `--escalation controller:pass|fail` entry.
- **Trigger one, proactive.** `route.py` resolved `first: controller`
  in section 2, before any worker ran. Invoke the mechanism above
  directly on the original task; there is no prior worker attempt to
  include. `--explain`'s printed reason says why it fired.
  <!-- rationale:start -->
  (This fires on `routing_priors.json`'s labelled policy dial, open,
  consequential tasks, by default, D64, or, once a project's ledger shows
  a bucket's ladder is expensive enough, on the expected-cost arithmetic.)
  <!-- rationale:end -->
- **Trigger two, reactive, a falsified constraint.** If a worker reports
  that it cannot meet an acceptance criterion without acting against a
  constraint the task states, and that it has checked the constraint's
  stated reason against the repository and found the reason false, do not
  climb the ladder one rung at a time. Invoke the mechanism above
  directly, regardless of where on the ladder the worker sat.
  <!-- rationale:start -->
  (Measured: D59, D63.)
  <!-- rationale:end -->
- If a worker at `low` or `medium` reports that the task was underspecified
  rather than too hard, fix the prompt and re-run at the same cell.
- Record every escalation, with `--record`'s `--escalation` flag (section
  2) as well as in the routing line. Three escalations from the same
  starting cell in one bucket means the priors are wrong for that class of
  task in this project, and `--explain`'s posterior should already be
  showing it moving; say so regardless.

## 5. Concurrency and depth

- At most 20 workers may run concurrently in a session; spawning past that
  fails. Keep well below it.
- Workers may spawn their own workers up to three layers below this
  conversation. Only the top-level worker's summary returns to you.
