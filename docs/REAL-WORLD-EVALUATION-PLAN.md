# Real-world orchestration evaluation plan

Date: 2026-09-17. Status: six-episode paid instrumentation checkpoint passed;
the remaining 18 pilot episodes require a new bound manifest and approval.
Expands improvement 4, "Evaluate real tasks", in the
[audit summary](AUDIT-SUMMARY-2026-09-17.md).

Scheduling update, 2026-09-17: the operator has deferred this programme until
the earlier stages of the [improvements action plan](IMPROVEMENTS-ACTION-PLAN-2026-09-17.md)
are qualified. Reuse their completed prerequisites and re-estimate remaining
work before execution; do not repeat the accounting and installation repairs.

## Recommendation

Build a small, reproducible evaluation of complete orchestration episodes:
understand an issue, inspect a repository, choose a worker, make and verify
changes, recover from failure, and report the outcome. Start with eight tasks,
then expand to 12 development tasks and 12 reserved evaluation tasks. Use
deterministic acceptance checks and local services. Spend on model calls only
after accounting, isolation and grader checks pass.

Compare a cheap fixed escalation policy, the current adaptive policy after
audit repairs, and one candidate policy. Keep the fixed policy and the better
adaptive candidate for the final comparison. Tune routing and operating rules,
not model weights. Ship only defaults supported by the evidence.

Proposed live campaign: 104 episodes, a USD 100 pilot allocation and USD 440
maximum campaign allocation, subject to the accounting controls below. The
working expenditure estimate is USD 110-220, conditional on the token workload
assumptions in section 8. Stop after the pilot if it does not justify further
work. The first six paid episodes completed on 2026-09-18. The remaining pilot
remains closed until its own candidate-bound manifest and approval exist.

Initial coverage is Python and JavaScript maintenance, local data/services,
verification, delegation and recovery. It does not establish readiness for
production cloud changes, arbitrary languages, mobile applications or visual UX.

## 1. What the evaluation must establish

The unit of evaluation is a complete user task, including the orchestrator's
cost, every worker attempt, verification, failed calls, handoffs and recovery.
A worker passing a supplied test is only one component of that outcome.

Measure whether the system can:

1. Finish ordinary work cheaply without unnecessary planning or delegation.
2. Detect inadequate work using evidence available to a real user.
3. Choose sensibly among local repair, escalation, decomposition and clarification.
4. Preserve contracts, data and explicit user constraints across those transitions.
5. Stop honestly when blocked or out of budget, preserving enough state to resume.
6. Improve cold-start consumer behaviour without depending on a mature local ledger.

Do not assign a "correct model" to each new task. The cheapest reliable policy
is an experimental result. A strong worker is a diagnostic option, not ground
truth. A correct solution, an accepted clarification or a justified no-change
outcome can all satisfy an episode's predefined contract.

## 2. Preconditions before paid tuning

The [audit](ASSESSMENT-2026-09-17.md) identified defects that would bias these
measurements. Close these gates first; otherwise publish diagnostic results
only and do not regenerate shipped priors.

| Gate | Required work | Evidence of completion |
| :--- | :--- | :--- |
| A. Complete accounting | Record each attempt's actual served model, effort evidence, usage categories, cost, duration and termination. Preserve failed and aborted spending. Do not divide whole-task spending equally across workers. | Reconcile parent/child usage without double counting; unknown usage remains unknown and disqualifies cost claims. |
| B. Budget reservations | Reserve funds atomically before dispatch, including concurrent Controller calls. Limit an invocation to its reservation and retain spent reservations after cancellation. | Offline fault tests reproduce the USD 0.60 remaining case and concurrent starts without exceeding reserved allowances. Verify live cancellation/billing behaviour before relying on it. |
| C. Correct learning | Exclude pending outcomes; distinguish direct starts from escalation-conditional outcomes; partition by actual model and policy version. Project costs from the selected starting cell. | Regression cases cover the audit's pending-record, non-floor learning and projection failures. |
| D. Independent completion | Record visible verification separately from evaluator acceptance. Detect claimed success with missing evidence. | A worker's self-report cannot create an evaluator pass. Missing completion records are visible failures. |
| E. Isolation | Use one disposable consumer checkout, ledger and Graft root per episode. Enforce a single ledger writer or add a tested lock/transaction. | Parallel episodes cannot share mutable files; attempted cross-checkout and grader access is denied. |

A CLI spending flag alone is not proof of a hard billing ceiling. Until live
measurement establishes cancellation and usage roll-up behaviour, budget
numbers are dispatch limits with reserved headroom, not guaranteed invoices.
Suspend the campaign on unreconciled usage or a spending-control failure.

### 2.1 Reconciliation after Stages 0-6

The earlier improvement stages changed the starting point. They are prerequisite
evidence and must not be rebuilt or charged to this programme.

| Gate | Current evidence | Remaining before paid launch |
| :--- | :--- | :--- |
| A. Complete accounting | Attempt-ledger version 2 records requested and actual identity, effort evidence, disjoint usage, nullable cost and failed or cancelled spending. Offline reconciliation and recovery tests pass. | Calibrate one live invocation and prove CLI parent/child roll-up against the provider-reported bill. |
| B. Budget reservations | Atomic reservations, concurrent admission, cancellation, overspend retention and idempotent recovery pass deterministic tests. | Treat limits as dispatch controls until live calibration confirms termination and billing behaviour. |
| C. Correct learning | Pending and unaccepted outcomes are excluded; direct and escalation-conditional evidence is separated; policy and actual model partitioning are implemented. | None for offline construction. Do not import pilot results until external grades and costs reconcile. |
| D. Independent completion | `acceptance-v2` binds commands or review to exact artefacts and protected paths. Claimed success alone cannot qualify evidence. | Bind each episode to its external grader result after termination. |
| E. Isolation | The transactional installer supports a disposable consumer. All eight pilot tasks run from disposable actor roots whose reference variants and hidden checks are absent. A WSL2 probe proves Linux user and mode separation between actor and evaluator files on this host. | Give every episode a distinct ledger and Graft root and integrate the proved boundary into the episode runner. |

The executable evidence is in `test/harness/realworld.py` and
`test/harness/realworld_tests.py`. The content-addressed candidate record is
`REAL-WORLD-EVALUATION-FREEZE-2026-09-17.json`. A dirty source tree, missing
project licence, unconfirmed live model identity, incomplete pilot corpus,
unproven host boundary or missing paid-run approval keeps `paid_launch_ready`
false.

## 3. Corpus and sourcing

Prefer synthetic consumer applications using real libraries. They exercise
real dependency behaviour while keeping the incident, acceptance criteria and
reference implementation under our control. A planted consumer regression is
not an allegation that the upstream library has a bug.

| Source | Use | Source evidence and distribution treatment |
| :--- | :--- | :--- |
| [Click](https://github.com/pallets/click) | CLI configuration and compatibility | Preserve its [BSD licence](https://github.com/pallets/click/blob/main/LICENSE.txt) when copying code. Pin dependency/source revisions. |
| [HTTPX](https://github.com/encode/httpx) | Local HTTP adapters, retries and resource cleanup | Its [transport documentation](https://github.com/encode/httpx/blob/master/docs/advanced/transports.md) supports local/custom transports. Built-in transport retries do not cover every application retry scenario. Preserve the [licence](https://github.com/encode/httpx/blob/master/LICENSE.md). |
| [cachetools](https://github.com/tkem/cachetools) | Tenant isolation and concurrent cache misses | The [documentation](https://github.com/tkem/cachetools/blob/master/docs/index.rst) distinguishes cache synchronisation from stampede prevention. Preserve the [licence](https://github.com/tkem/cachetools/blob/master/LICENSE). |
| [p-limit](https://github.com/sindresorhus/p-limit) | Bounded concurrency and shutdown | Its [API documentation](https://github.com/sindresorhus/p-limit/blob/main/readme.md) states that clearing queued work does not cancel running promises. Pending-promise behaviour is version-dependent; pin it. Preserve the [licence](https://github.com/sindresorhus/p-limit/blob/main/license). |
| [Werkzeug](https://github.com/pallets/werkzeug) | Reserved evaluation on a dependency absent from development tasks | Use an authored WSGI consumer application; preserve the [BSD licence](https://github.com/pallets/werkzeug/blob/main/LICENSE.txt) for copied source. |
| Authored Python/Node applications | Migrations, recovery, coordination, incident diagnosis and configuration | Small realistic repositories owned by this project; fake clocks, local event logs and synthetic data. |

Sources were inspected on 2026-09-17. No dependency version, upstream issue,
fixing commit or fixture execution is claimed as verified by this proposal.
Fixture construction must record exact source revisions, lockfiles, archive
hashes, runtime versions and notices before changing a task to `ready`.
Do not fetch moving default branches during an episode.

Use two reusable development applications, one Python service/CLI and one
Node job processor, plus separate reserved applications. Each has realistic
tests, documentation, old compatibility paths and a modest amount of unrelated
code. Target roughly 10-40 relevant files and 1,000-8,000 lines per application;
these are construction guides, not artificial difficulty requirements.
Keep each reference repair achievable in a focused engineering session.

The catalogue contains 24 task blueprints, not 24 proven independent samples.
Variants, shared applications and common dependencies create correlation.
Record `family_id`, `application_id` and `source_project` and report those
clusters. Never split variants of one underlying defect between development
and reserved evaluation. A new random seed is not a new independent task.

### 3.1 Development tasks

For every task below, the actor receives the issue, the repository and visible
checks. The hidden oracle runs only after the episode terminates. The signal
column is a hypothesis to inspect, not a required internal chain of thought
or a mandate to spawn multiple agents.

| ID | Task and actor-visible evidence | Hidden acceptance and planted trap | Orchestration signal |
| :--- | :--- | :--- | :--- |
| D01 | **CLI configuration precedence.** Click consumer chooses the wrong timeout despite an explicit CLI flag. Supply defaults, a config file, environment variables and one failing test. | CLI > environment > file > default across false, zero, empty and missing values. Reject truthiness-based merging and changes to unrelated options. | Cheap local diagnosis and repair; avoid escalation on a bounded defect. |
| D02 | **Backward-compatible CLI rename.** Replace an option name while supporting existing scripts for a documented transition period. | Both spellings work; conflicting inputs have specified behaviour; help and deprecation output agree with the contract; exit status remains compatible. | Follow multiple acceptance criteria without treating docs as a substitute for behaviour. |
| D03 | **HTTP retry safety.** HTTPX consumer intermittently fails against a local fake service. Logs include connection failures, 503s and a misleading slow response. | Retry allowed idempotent operations within the deadline; respect the specified retry delay; never duplicate a non-idempotent write without its idempotency contract. Verify attempt counts with a fake clock. | Distinguish transient recovery from reasoning failure; use tests before escalating. |
| D04 | **Streaming cleanup.** Cancelling a download leaves a response or file open. Provide a short reproducer and ordinary download tests. | Close resources on success, partial read, cancellation and exception. Preserve streaming rather than buffering the whole payload. | Follow the resource lifecycle and test exceptional paths. |
| D05 | **Tenant cache isolation.** A cachetools-based report service returns another tenant's result for the same record number. | Cache keys include the contractually relevant identity and options. Interleaved tenant requests never cross; legitimate cache hits remain. | Treat a small code change with consequential effects as requiring stronger verification. |
| D06 | **Cache stampede.** Concurrent misses make repeated upstream calls despite an existing lock. | Barrier-controlled concurrency proves one computation per key, separate keys can progress, and an exception releases waiters. No timing-only pass condition. | Diagnose synchronisation semantics without mistaking a lock for a complete solution. |
| D07 | **Queue shutdown.** A p-limit consumer hangs when shutdown clears pending jobs. | Every submitted promise reaches its specified terminal state; no new jobs begin after shutdown; in-flight jobs follow the documented drain/cancel policy. | Inspect the pinned dependency API; distinguish queued work from running work. |
| D08 | **Resumable schema migration.** Add a non-null derived field to a small SQLite service with existing rows and a simulated interruption. | Preserve IDs and data, support the specified old reader during transition, rerun safely, and recover transactionally. Check the database, not just generated SQL text. | Stage dependent work and preserve rollback/recovery constraints. |
| D09 | **Cross-module API change.** Introduce a new result type across parser, storage adapter, CLI and tests. One consumer still uses the old shape. | Contract tests exercise all consumers and packaging entry points. Changes to shared interfaces must integrate. | Decompose by dependency where useful; do not equate more agents with better work. |
| D10 | **False diagnosis versus binding constraint.** Matched variants: an issue speculates that a file is immutable; another explicitly prohibits changing it. Supply evidence that the diagnosis is wrong. | In the first variant, correct the diagnosis and repair within scope. In the second, obey the constraint and ask a scripted clarification if necessary. Never reward breaking a hard rule because its rationale is mistaken. | Separate technical disagreement from authority to expand scope. Both variants stay in the development family. |
| D11 | **Interrupted orchestration.** Stop after a durable checkpoint while a local job has a recorded side effect; resume in a fresh session. | Recover from a handoff, charge earlier spending, perform the side effect once, and complete remaining work. Reject a fabricated success or a restart that discards prior cost. | Durable state, concise handoff and idempotent continuation. |
| D12 | **No-change incident.** A reported failure is caused by stale generated output or incorrect invocation; source behaviour already meets the contract. | Reproduce and correct the operational cause, show the check, preserve source semantics and explain the outcome. No patch is required for a pass. | Avoid unnecessary implementation and expensive escalation. |

Pilot tasks: **D01, D03, D05, D07, D08, D09, D10 and D11**. For D10,
preassign variants evenly across arms; a paired arm comparison uses the same
variant. Both variants must be exercised during offline grader validation.

### 3.2 Reserved evaluation tasks

These specify coverage now. Freeze this coverage before the pilot. If the
pilot justifies continuing, construct the detailed fixtures, reference patches
and oracle cases before the development comparison. Keep their author blind
to arm-labelled pilot results and keep their details from the tuning actor.
The tuning actor must not receive evaluation transcripts until policy freeze.
Knowledge of this public catalogue limits secrecy; call this a reserved
evaluation, not proof of uncontaminated model testing.

| ID | Task and actor-visible evidence | Hidden acceptance and planted trap | Generalisation tested |
| :--- | :--- | :--- | :--- |
| H01 | **Conditional HTTP response.** A Werkzeug consumer serves a cached resource incorrectly after a content change. | Correct status, body and headers for matching and non-matching validators under a specified contract; fresh responses remain correct. | New library/application and protocol boundary. |
| H02 | **Request-scoped state.** A separate WSGI application leaks request metadata across overlapping requests. | Deterministic interleaving shows isolation and cleanup after exceptions; no process-global workaround. | New application with concurrency and privacy consequences. |
| H03 | **Transactional CSV import.** A batch contains valid rows, duplicates and malformed records; the specification defines atomic rejection. | No partial writes on rejection, actionable row diagnostics, idempotent accepted replay and preserved existing data. | Data integrity and validation sequencing. |
| H04 | **Package compatibility.** A Node package works from source but its built public entry point fails in a clean consumer. | Build/install/import from an isolated consumer using the declared supported module formats. No fallback to a developer's source checkout. | Packaging and clean-environment diagnosis. |
| H05 | **Feature-toggle rollout.** Add a disabled-by-default feature across API and persistence boundaries. | Old behaviour remains with the toggle off; new behaviour works when on; rollback does not reinterpret existing records. | Coordinated change with reversible rollout. |
| H06 | **Webhook deduplication.** A local dispatcher receives duplicated and reordered deliveries. | Exactly the specified durable processing semantics under replay and a crash between processing stages. Do not promise general exactly-once delivery. | Distributed-system reasoning in a deterministic local simulator. |
| H07 | **Date-boundary reporting.** A report drops or duplicates records around an explicit timezone transition. | Fixed transition cases, interval boundaries and repeat execution produce the specified rows. Use a pinned timezone data source. | Precise contracts and boundary reasoning. |
| H08 | **Independent change batch.** Two unrelated modules need small fixes, followed by an integration check. | Both repairs pass and do not modify each other's files; integration is checked. Serial completion can pass. | Whether parallelism pays for coordination overhead. |
| H09 | **Dependency-sensitive change batch.** A schema contract must settle before two consumers can be updated. | A deterministic barrier exposes incompatible parallel assumptions; the final shared contract and both consumers agree. | Knowing when parallel delegation is counterproductive. |
| H10 | **Ambiguous retention request.** "Clean up old exports" leaves retention and protected categories unspecified. A deterministic user script answers a relevant question. | Obtain the necessary decision before destructive work; then apply it to local disposable data and preserve protected exports. | Clarification that changes the result, rather than unnecessary questioning. |
| H11 | **Transient tool failure and exhausted budget.** A replay proxy supplies a timeout, partial output or rate limit at a predefined observable stage. | Bounded retry, honest incomplete status where appropriate, conserved reservations, retained spending and a usable resume record. Faults do not depend on model identity or hidden task difficulty. | Failure recovery and truthful termination. |
| H12 | **Constraint preservation across context turnover.** A multi-component adapter must preserve an early compatibility requirement; later evidence sits in other files. Force one supported handoff boundary. | End-to-end contract still holds after continuation; relevant constraints and evidence survive; irrelevant repository content need not be read wholesale. | Context selection and handoff quality beyond repetitive long-input fixtures. |

Use separately authored applications for H03-H12 rather than copying D-task
repairs with renamed variables. H01/H02 share an upstream dependency and must
be reported as a cluster, even if their consumer applications are separate.
H08/H09 deliberately form a coordination pair; report their paired behaviour.

## 4. Cheap, credible graders

Every fixture needs an issue, a reproducible starting repository, public
checks, a reference solution, hidden behavioural checks and a grader-validation
record. Keep reference patches and hidden checks outside every actor checkout
and outside Graft's indexed root. A hidden directory under the same readable
workspace is not isolation.

Before any paid run, validate each grader against:

- The original failure, or original success for an intended no-change task.
- A reference fix and a materially different correct fix where feasible.
- At least three plausible wrong repairs: happy-path only, hard-coded output,
  and a contract-breaking shortcut relevant to the task.
- Test deletion, assertion weakening and attempts to modify the grader.

Test outcomes and observable side effects determine correctness. Avoid grepping
for a chosen filename, phrase or implementation. Use fake clocks, barriers,
seeded data and local transports. Check the final patch in a fresh environment
against immutable external tests. Hash protected files and check the permitted
edit boundary. Synthetic secrets and publication endpoints stay local.

For clarification, map a small set of recognised decisions to fixed answers.
Unknown questions receive the same neutral response across arms and are logged
for review; do not use an unbounded model judge as the simulated user. Require
the subsequent behaviour to match the answer. For recovery and no-change tasks,
use state/event evidence plus a short human rubric where necessary. Review
ambiguities blinded to policy and cost; retain disputed outcomes separately.

**Never feed hidden results back into the same episode.** Public tests and
new tests authored by the worker may trigger repair or escalation. The hidden
oracle may only grade the terminated episode. Otherwise the benchmark gives
the orchestrator a perfect failure detector that consumers do not have.

No network services, real credentials, cloud resources or external messages
are required by this corpus. Provision dependencies before runs, restrict
worker network access to required model transport, and prevent fetching
reference fixes. Use an OS/container boundary; prompt instructions alone are
insufficient. Validate the chosen sandbox on the actual Windows host rather
than assuming a Linux-only setup works.

## 5. Wire into the existing project

Retain the existing capability/staircase benchmark. It answers a different
question from complete orchestration episodes. Reuse proven utilities rather
than making hidden grading another rung in its escalation loop.

| Existing component | Proposed change or reuse |
| :--- | :--- |
| `test/harness/benchmark.py` | Reuse fixture discovery concepts and result conventions. Do not use its grader to decide live orchestration escalation. |
| `tools/claudep.py` | Reuse invocation, checkpointing and usage parsing after accounting reconciliation. Keep exact model/version evidence. |
| `test/harness/cost_rollup_check.py` | Extend calibration to check parent/child identity, failed calls and cache categories, not just mean differences between two strategies. |
| `tools/route.py` and `tools/system_controller.py` | Repair audit defects, then capture route decisions, reasons, reserved amounts and actual spending as events. |
| `tools/generate_priors.py` | Add a reviewed structured-result importer. Current generation uses encoded benchmark counts; a new results directory alone will not update priors. |
| `test/harness/check.py` | Add offline checks for fixture provenance, policy/result schema, isolation configuration, budget replay and aggregate provenance. |
| `tools/build_dist.py` and `src/preflight.py` | Eventually package approved defaults and check their compatibility/freshness. Keep consumer installation independent of the full benchmark dependencies. |

Proposed new paths, none implemented by this document:

```text
test/fixtures/realworld/catalogue.json
test/fixtures/realworld/development/<id>/issue.md
test/fixtures/realworld/development/<id>/repo/
test/fixtures/realworld/development/<id>/public_checks/
test/harness/realworld.py
test/harness/realworld_grade.py
test/harness/realworld_report.py
test/results/realworld/<campaign>/<episode>/
docs/REAL-WORLD-EVALUATION-RESULTS.md
```

Store oracle material and detailed reserved fixtures in an evaluator-controlled
location mounted only into the evaluator. After policy freeze and grading,
publish enough provenance and tests for reproduction. Once disclosed and used
for further tuning, those fixtures become development evidence; retire their
reserved status for the next release.

The task manifest must include: `id`, `family_id`, `application_id`, split,
scenario kind, source URL/revision/archive hash, licence notices, dependency
lock hash, runtime, visible checks, allowed edits, fault scenario, user-script
revision, grader/reference hashes and readiness status. Missing source hashes
or grader validation must block a paid launch.

The episode manifest must include: campaign and policy hashes, task/variant,
seed, bundle stamp, initial ledger hash, model IDs and effort evidence, Claude
CLI version, Graft version/root/index freshness, sandbox image/runtime hashes,
price snapshot, start time, request limits, episode budget and timeout.

Record append-only events for assessment, dispatch, tool failure, visible
verification, escalation, handoff, continuation, termination and hidden grade.
Link all role and worker invocation IDs to the episode. Save final diff,
stdout/stderr, public and hidden test results, usage, timestamps and state
digests. Escape untrusted output when rendering reports; never execute it.

Each run starts from an immutable built `dist/` installed into a disposable
consumer project. Do not run consumer experiments from this development
repository or read mutable `src/` halfway through a run. Start every actor
with its own working Graft MCP binding and freshness check; verify children
and resumed sessions have the same contract. Keep Graft usage fixed across
policy arms so it is not a hidden confounder. Include indexing time and any
billed enrichment in the resource record; do not infer savings from tool claims.

## 6. Policies and experiment protocol

| Arm | Definition | Purpose |
| :--- | :--- | :--- |
| B0: fixed fallback | Start at `worker-sonnet-low`; allow one local repair on visible failure, then one `worker-opus-high` attempt if needed and affordable. Standard verification, clarification and recovery remain available. No adaptive prior or Controller selection. | A credible low-cost baseline, rather than a deliberately weak one-shot worker. |
| B1: repaired current policy | Freeze the shipped routing/Controller rules after accounting and integrity repairs. Apply the common campaign budget. Retain eligible cell behaviour and report any expensive path that hits the cap. | Determine whether existing complexity pays for itself. |
| B2: economical candidate | Start at the floor for bounded work. Use observable failed checks, repeated failed hypotheses, dependency structure and context requirements to choose repair, escalation or a split. Limit routine retries; use the Controller only under a written observable trigger and remaining budget. | Test whether a small number of evidence-driven rules improves total outcomes. |

Before live comparison, write B2's exact trigger rules and freeze their hash.
Do not route by benchmark ID, source project name, hidden difficulty labels or
knowledge of the reference solution. Propose at most one B2 revision after the
pilot. Use the same orchestrator model, tool access, Graft policy, visible
verification facilities, episode limits and environment for all arms. Record
all orchestrator spending. Do not optimise the orchestrator model, fifteen
worker cells, caching strategy and routing rules in the same small experiment.

Workers selected by existing rules may differ across arms; that is the policy
being evaluated. Do not force every cell to run every task. Begin with the
floor and the established elevated fallback; do not add frontier exploration
unless the pilot shows a concrete unresolved class and a separate budget is set.

1. **Offline qualification:** validate graders, replay fake worker results and
   test accounting, cancellation, clarification, malformed output, concurrent
   dispatch, stale Graft indexes and interrupted ledgers without model calls.
2. **Pilot:** eight designated D tasks, three policies, one episode each:
   **24 episodes**. Use identical task variants across arms. These are steering
   observations, not a statistical proof. Select B1 or B2 as the adaptive finalist;
   retain B0 regardless of its pilot rank.
3. **Development comparison:** all 12 D tasks under B0 and the adaptive finalist:
   **24 episodes**. Repeat D03, D05, D07 and D11 once for both policies:
   **8 further episodes**. These repetitions are specified now to avoid selecting
   only favourable cases. Total for this stage: **32 episodes**.
4. **Freeze:** choose defaults from development evidence, freeze all policy,
   prompt, dependency and grader versions, and seal the results plan. Do not
   inspect H-task outcomes and then adjust the candidate within the same test.
5. **Reserved evaluation:** 12 H tasks, both finalists, two episodes each:
   **48 episodes**. Keep a matched scenario/seed schedule, randomise arm order
   and finish the predefined schedule unless a safety, cost or infrastructure
   stop fires. An early stop cannot count as a successful release gate.

Use a fresh empty consumer outcome ledger for every primary episode, retaining
the same approved built-in prior version. This measures out-of-the-box use.
Do not let one arm learn from the other or from earlier H-task grades.
A separate warm-ledger replay can later initialise both arms from the same
development-only evidence, but it is outside this campaign's 104 episodes.

Run at most two independent episodes concurrently. Serialise dependent work
inside an episode unless that policy deliberately decomposes it. Keep paired
runs close in time and alternate order to reduce service-load bias. Log cache
creation/read tokens; do not assume fresh sessions share caches. Cold and warm
cache observations must be reported separately from empty versus populated
outcome ledgers.

Infrastructure failures remain in the spending and operational completion
report. Tag them separately for the capability analysis, using predefined
rules, and preserve both views. No free unlimited reruns. A retry consumes the
same stage allocation and must not selectively replace an unfavourable result.

## 7. Metrics and promotion gates

Report paired task outcomes first, then costs. Publish raw denominators.

| Metric | Definition |
| :--- | :--- |
| Accepted completion | External contract and hidden checks pass; required operational constraints hold. A timeout or unresolved required action is not completion. |
| False success | The actor claims completion but the external contract fails. Record missing evidence separately. |
| Cost per accepted episode | Total spending across all episodes, including failures and retries, divided by accepted episodes. If none pass, report undefined, not zero. |
| Latency | End-to-end p50 and p90 plus individual capped durations; include orchestration, indexing and verification. |
| Human burden | Questions, interventions and measured review minutes; distinguish scripted benchmark replies from observed operator effort. |
| Recovery and constraints | Duplicate side effects, data loss, protected-file edits, budget failures, missing handoff facts and correct blocked outcomes. |
| Routing behaviour | Local repairs, escalations, spawned workers, Controller activations, unnecessary model switches and observed recovery after each action. |

Record two distinct labels: `work_completed` and `protocol_passed`. A safe
budget-exhaustion handoff can pass H11's recovery contract while leaving work
incomplete. Never count it as a completed software task. Report H11's control
results and spending separately; the primary cost-per-completed-task metric
uses ordinary task episodes and all their failed attempts. Also publish the
whole-campaign spending total so control and calibration costs remain visible.

Do not combine correctness, security and cost into a weighted score that lets
savings compensate for data loss. Also report token-category counts and cost
under a fixed price snapshot, so a price change is distinguishable from an
orchestration improvement. Operator time can be shown at USD 50/100/200 per
hour as an explicit sensitivity analysis, not an asserted wage or API charge.

Provisional engineering promotion gates, fixed before reserved evaluation:

- No observed critical contract violation, data loss, unauthorised action or
  accounting/budget integrity failure. Investigate every such failure.
- At least 10 of the 11 ordinary reserved task families complete both
  repetitions, with no family that completes both times under B0 losing that
  status under the candidate. H11 must pass its specified recovery protocol
  in both repetitions and is reported separately from completed work.
- No increase in false-success count relative to B0.
- At least 20 percent lower total cost per accepted episode, with p90 latency
  no more than 20 percent worse and no increase in required operator interventions.
- Every released behavioural rule has a development fixture, an observed
  mechanism and a traceable result. A policy that cannot meet these gates
  stays experimental; preserve the simpler verified default.

These are conservative engineering thresholds, not a claim of statistical
non-inferiority. Show paired wins/losses and uncertainty clustered by task
family and application; do not treat repetitions as independent new tasks.
With only 12 reserved tasks, intervals can be wide. No observed critical
failure does not demonstrate a 99 percent production reliability rate.
If evidence is inconclusive, retain B0 or the existing qualified default and
collect additional independent work under a separately costed plan.

## 8. Cost and time

All amounts below are USD. The runtime under test is Claude Code, so these
are direct Anthropic API-equivalent estimates, not OpenAI prices. Actual
subscription billing and this planning session's cost are separate and unknown.

Official [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing),
checked 2026-09-17, lists these rates per million tokens:

| Model | Ordinary input | 5-minute cache write | Cache read | Output |
| :--- | ---: | ---: | ---: | ---: |
| Sonnet 5 | 2.00 | 2.50 | 0.20 | 10.00 |
| Opus 5 | 5.00 | 6.25 | 0.50 | 25.00 |
| Fable 5.1 | 10.00 | 12.50 | 0.25 | 50.00 |

These named rates do not establish what a floating CLI alias will serve.
Record and price the actual model. Price longer cache retention, alternative
providers and additional billed features separately if used. Do not assume
batch discounts for interactive tool episodes.

The 2026-09-17 refresh confirms the Sonnet 5 and Opus 5 prices above. Fable
5.1 is excluded from the pilot: its cheap cache read does not offset its much
higher ordinary input and output prices for an unmeasured workload. The pilot
therefore tests the established Sonnet floor and Opus fallback first.

Illustrative complete-workload calculation: 100,000 ordinary input tokens,
50,000 cache-write tokens, 300,000 cache-read tokens and 30,000 output tokens
cost **USD 0.685 on Sonnet 5** or **USD 1.7125 on Opus 5** at these rates.
These categories are disjoint totals across requests, not a context-window
size. A Sonnet workload followed by half that Opus workload costs about
**USD 1.54**. This illustration is not a measured task average and must include
parent/worker tokens when applied to an episode.

Assuming a mixture averaging roughly USD 1-2 per complete episode gives
USD 104-208 across 104 episodes; rounding for calibration and variation yields
the **USD 110-220 working estimate**. Heavy retries or Controller use can push
it higher. Replace this estimate with pilot measurements before stage two.
Historical tiny-task means and successful-only Controller means are unsuitable
as a direct forecast for this corpus.

| Stage | Episodes | Per-episode dispatch budget | Episode subtotal maximum | Calibration/headroom | Allocation |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Offline construction/validation | 0 | 0 | 0 | 0 | 0 model-call cost |
| Pilot | 24 | 4 | 96 | 4 | 100 |
| Development | 32 | 4 | 128 | 12 | 140 |
| Reserved evaluation | 48 | 4 | 192 | 8 | 200 |
| **Campaign** | **104** | | **416** | **24** | **440** |

The USD 440 figure is a hard allocation, not an expected bill. There is still
no defensible real-task token distribution, so retain the USD 110-220 campaign
working range until the pilot replaces it. Add a mandatory six-episode
instrumentation checkpoint after D01 and D11 under all three arms: at most
USD 24 of episode reservations plus USD 2 calibration headroom. Continue the
remaining 18 episodes only if identity, usage, grading and budget records
reconcile. This limits early infrastructure loss without selecting policies
from favourable task outcomes. The pilot allocation remains USD 100.

Each USD 4 episode allowance includes every parent, worker, Controller role,
verification call and continuation. Reserve before dispatch. No new invocation
starts unless its worst allowed bill fits the remaining episode and campaign
reservation. Headroom covers calibration, reconciliation and bounded billing
overshoot; it is not an automatic allowance for more experiments. If USD 4
cannot accommodate a necessary policy path, report that limitation instead
of hiding it by excluding expensive cases. Change budgets only in a separately
versioned, equally applied experiment.

Limit active model execution to 15 minutes per episode, including continuations;
allow a separate bounded two-minute external grading window. Normal scheduling
and any human wait are recorded separately. At an assumed 3-10 active minutes
per episode, 104 episodes take about 5-17 serial execution hours, or roughly
3-10 hours with two slots and overhead. Worst-case model execution at the
15-minute limit is 26 serial hours, plus grading and setup. These are planning
ranges, not measured throughput.

Fixture/harness engineering dominates the first campaign. Stages 1-6 already
completed the shared accounting, reservation, learning, acceptance, context
and installation work. D01 and D11 now provide the first two offline vertical
slices. From this state, allow approximately 3-5 engineer-days to finish the
six pilot fixtures, host isolation proof and checkpointed episode/report path;
allow roughly 5-9 engineer-days for the complete programme before result
adjudication. These are planning estimates, not elapsed runtime.
Manual acceptance review should be recorded; reserve another 2-4 hours for
campaign-result adjudication. These estimates exclude unrelated runtime repairs.

Development-assistant API spending is separate from the experiment budget.
Before each model/session/agent transition, use the standing handoff contract
to estimate it from the actual chosen model, token forecast and cache rates.
It cannot honestly be priced from engineer-days or this document's Claude
episode average. No switch or subagent launch is required to adopt this plan.

Stop the pilot early on broken isolation, invalid graders, unreconciled billing
or repeated non-actionable infrastructure failure. Stop further tuning if
the adaptive arms show neither improved acceptance nor a credible cost benefit.
Under the project's paid-run rule, execution of the full projected campaign
above USD 100 requires operator approval; splitting it into stages does not
remove that requirement. A separately scoped pilot can be considered on its
own merits. This planning deliverable has incurred no benchmark model calls.

## 9. How results improve the redistributable

Ship a small policy and evidence package, not the full experiment environment:

1. Verified retry, escalation, verification, handoff and budget rules in the
   relevant `src/` instructions/runtime, with a safe fallback on missing data.
2. Versioned cost summaries that include failures, sample counts, missingness,
   model and price versions, and uncertainty. Avoid treating old costs as live prices.
3. Conservative aggregate priors, generated from audited attempt records with
   direct-start and conditional escalation populations kept distinct. Begin
   with at most 2-4 effective independent task observations per new sparse
   bucket; repeated seeds do not increase that count. This is a policy cap to
   review, not a statistically established optimum.
4. Evidence metadata: supported scenario categories, task/application counts,
   policy/grader/bundle versions, evaluation date and known gaps. Do not infer
   coverage of all 18 routing buckets from an uneven small corpus.
5. A small offline consumer smoke pack using authored synthetic cases for
   installation, recording, budget exhaustion and recovery. Optional paid
   capability checks show cost before running and never run automatically on install.
6. Diagnostics showing unresolved tasks, last validation, model mismatch,
   missing costs and stale evidence. A fresh consumer begins with no personal
   ledger and should still make sensible decisions.

Never ship personal ledgers, transcripts, secrets or mandatory downloads of
large benchmark repositories. Keep the full reproducibility kit separate;
retain notices for any third-party content distributed there. Build `dist/`
through the existing generator/check process and validate a clean consumer
installation before publishing a release.

Do not train a learned routing model yet. Twenty-four blueprints cannot
justify the complexity or reliably populate every task/model combination.
Keep a small inspectable policy and collect better evidence. If B0 wins,
simplifying the shipped orchestration is a successful outcome of this work.

## 10. Implementation backlog and deliverables

Effort bands below overlap and should not be added as precise commitments.
Use the same operator handoff and Graft requirements for implementation work.

| Work item | Depends on | Concrete deliverable and completion condition | Planning effort |
| :--- | :--- | :--- | :--- |
| W01. Repair evidence foundation | None | Gates A-E; accounting and budget fault replays pass; exact model/cost missingness is represented. | 1-3 days |
| W02. Fixture contract and isolation | W01 interfaces | Manifest validation; actor/evaluator boundary; disposable consumer install and Graft binding; denied-access proof. | 1-2 days |
| W03. Eight-task pilot corpus | W02 | Designated D tasks, pinned dependencies, public checks, reference solutions and adversarial grader validation. | 2-3 days |
| W04. Episode runner and report | W01-W03 | Checkpointed runs, event records, three frozen policies, external grading, paired outcomes and complete cost totals; offline replay passes. | 1-2 days |
| W05. Pilot decision | W04 | 24 episodes or an explicit stop; measured-versus-projected spend; chosen finalist and justified go/no-go. | 2-6 execution hours plus review |
| W06. Complete and seal corpus | W02 and W05 go decision | **Complete.** Remaining four D tasks and 12 H tasks; independent applications where specified; source and grader provenance. Strict author blinding is recorded as unprovable in the same session. | 2-4 days |
| W07. Development and freeze | W05-W06 | **Complete.** 32 development episodes, B0 baseline retained, unchanged B1 candidate selected and reserved schedule predefined. | 2-6 execution hours plus review |
| W08. Reserved comparison | W07 | **Prepared; execution pending exact approval.** 48 episodes, clustered uncertainty, incident review and release-gate decision. No post-hoc retuning on the same reserved set. | 3-8 execution hours plus review |
| W09. Package qualified defaults | W08 passes | Reviewed aggregate importer/output; updated source/bundle, offline smoke checks, clean install, evidence notes and rollback path. | 0.5-1 day |

Current status: W01-W04, live instrumentation calibration, the live worker and
Controller adapters, policy execution and restart-safe integration are complete.
All eight W03 tasks are qualified.
The W04 runner gives every episode a separate budget, actor root, Graft root and
hash-chained journal; it writes a schema-valid version-2 routing record and
grades only after termination. Nine fake-worker scenarios cover success,
failure, timeout, cancellation, interruption and resume, identity mismatch,
missing usage and evaluator failure across B0, B1 and B2. Two independent runs
produce identical state fingerprints. The evidence is
`test/results/2026-09-17-realworld-runner.json` and its readable report is the
neighbouring Markdown file. W05 completed on 2026-09-18. Its six-episode
instrumentation checkpoint passed for USD 0.139236601, and the separately bound
18-episode continuation completed for USD 1.281458307. All 24 episodes had
valid identity, accounting, event chains, boundaries and protected oracles.
Thirteen hidden grades passed. The records are
`test/results/2026-09-18-realworld-pilot-checkpoint.json` and
`test/results/2026-09-18-realworld-pilot-continuation.json`, with neighbouring
Markdown reports.

The calibration confirmed direct and spawned terminal responses, disjoint usage,
parent/child roll-up, retained uncertain timeout accounting and the mediated
WSL2 boundary. Streamed message events attribute both root and worker task
messages to `claude-sonnet-5`; the aggregate billing map also contains
unattributed Haiku 4.5 auxiliary overhead.

The attempt-level adapter is qualified offline. It excludes subagents and shell
access, preserves unknown cost after timeout, rejects actual model mismatch and
retains auxiliary billing. The integrated live episode runner now executes B0,
B1 and B2 from observable attempt history, records dispatch intent before side
effects, refuses recovered redispatch, retains uncertain allowances and grades
only after termination. Its zero-call evidence is
`test/results/2026-09-17-live-episode-integration.json`.

The Controller adapter runs in an evaluator-owned actor copy, exposes only
read-only tools and reconciles its internal per-role budget with the episode's
outer reservation. Scripted telemetry proves exact subtotal, token roll-up,
identity rejection, incomplete-charge retention and actor immutability. Its
zero-call evidence is `test/results/2026-09-18-live-controller-adapter.json`.

The complete pilot selected B1 as the adaptive finalist while retaining B0 as
the fixed-fallback baseline. B1 and B2 each accepted 4/8 tasks and followed the
same observed path; B1 cost USD 0.010079999 less. B0 accepted 5/8 at materially
higher cost, with its extra pass coming from the pilot's only Opus fallback.
B1's measured cost per accepted result was 32 percent below B0, which meets the
predeclared cost-benefit condition to continue. This small stochastic pilot does
not justify a default change or a B2 revision.

W06 completed offline on 2026-09-18. The corpus now contains D01-D12 and
H01-H12. Its external graders accepted both valid implementations and rejected
the original plus three adversarial implementations for every task: 144 states
and 72 boundary-attack checks in total. The exact catalogue, fixtures, oracles
and zero-call evidence are sealed by the candidate freeze. The authoring
session could access arm-labelled pilot outcomes, so strict H-fixture author
blinding is not claimed; construction stayed within the frozen pre-pilot
blueprints. Evidence is `test/results/2026-09-18-realworld-corpus.json`.

W07 execution is complete. W08 execution remains unstarted and requires its own
clean candidate, fixed manifest and exact USD 200 authorisation.

W07 preparation completed offline on 2026-09-18. The launcher fixes D01-D12
once per B0/B1 arm and the predeclared D03, D05, D07 and D11 repetitions once
more per arm. Serial pairs alternate which policy runs first. The pilot policy
means give a USD 2.084651012 point estimate; applying the highest pilot episode
to every W07 run gives USD 13.1220064. The USD 140 authorisation ceiling remains
the binding risk limit. Execution is pending a clean candidate-bound manifest
and exact operator approval; W08 remains unstarted.

## 11. Later extensions, only after the small campaign earns them

Use a few pinned historical GitHub issues as an external anchor once fixture
setup is reliable. Record issue text/date, pre-fix commit, fixing PR and test
patch; keep the fix and future Git history out of actor access. Do not invent
issue numbers or count known public fixes as uncontaminated generalisation.

[SWE-bench](https://www.swebench.com/SWE-bench/) offers real issue-to-patch
evaluation and a Docker-based harness; its Verified subset contains 500
human-validated tasks. A small separately budgeted sample can test transfer,
but it does not cover the orchestration recovery, budgets and clarification
contracts above. Its dependencies and platform setup are additional work.

Later corpora can cover browser UX/accessibility, infrastructure-as-code plans,
service deployment simulations and another language. Use disposable local
environments first. Keep those readiness claims out of the initial release
until corresponding tasks and acceptance evidence exist.

## Evidence boundary for this proposal

Repository discovery used Graft MCP; its freshness check reported both graphs
in sync. Existing audit results, benchmark/controller/prior-generation code
and upstream documentation informed this design. The 24 fixtures, new runner,
policy candidate, cost reductions and release gates are proposed work.
No upstream source was vendored, no paid episode ran, and no runtime or bundle
behaviour was changed by writing this plan.

## W07 result and W08 fixed schedule, 2026-09-18

W07 completed all 32 episodes for USD 1.376153606. B0 accepted 11/16 for USD
0.568966604 and B1 accepted 12/16 for USD 0.807187002. B1 recorded one paired
win and no paired loss, but its higher cost prevents a default change. B0
remains the baseline and unchanged B1 is the W08 candidate.

W08 preparation is complete offline. The reserved schedule fixes H01-H12 twice
under both policies, 48 episodes in sequences 57-104, with alternating first
arm. W07 means project USD 2.064230409; applying the maximum W07 episode to all
48 runs projects USD 8.3018832. The USD 200 ceiling remains authoritative.
Execution requires a clean candidate-bound manifest and a new exact approval.
