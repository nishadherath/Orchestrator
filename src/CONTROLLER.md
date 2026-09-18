# Controller

This document is the maintained description of the retained Controller: what
it does, how it reaches a result, what evidence it preserves, and where it
sits relative to the qualified default router. Update it whenever Controller
behaviour, routing eligibility, budgeting, recovery or evaluation status
changes.

## Purpose

The Controller is the orchestrator's heavyweight, evidence-first
problem-solving pipeline. It accepts a difficult task, makes the underlying
assumptions explicit, tests uncertain assumptions, compares several solution
techniques and produces auditable technical guidance for a coding worker.

The Controller is a deterministic state machine around specialised model
calls. The code controls phase order, admission, retries, stopping and record
ownership. Model roles supply bounded judgements and candidate content inside
that structure.

The Controller does not currently participate in ordinary qualified B0
routing. It remains available for explicit diagnostics, historical replay,
experimentation and rollback analysis. The R3 control plane records durable
operator intent. R4's structured policy and production adapter can consume it
at a dispatch boundary; changing a control alone still does not invoke the
Controller or alter the qualified B0 automatic runtime.

The supporting contracts are:

- `src/System/SYSTEM.md`: the full blackboard-system design, including quick
  and deep modes;
- `src/System/STEPS.md`: phase ownership, artefacts and termination rules;
- `src/System/ROLES.md`: the complete role briefs, input slices, output
  records and isolation rules;
- `src/System/TECHNIQUES.md`: the bounded technique families supplied to
  Generators;
- `src/System/schemas/`: the record contracts enforced by the Scribe.

Paths in this document are relative to the project or installed bundle root,
except where the implementation map labels a development-only file.

## Quick-mode flow

```text
Problem
  -> freeze an external acceptance contract, or the first frame provisionally
  -> frame the problem and record premises
  -> verify uncertain premises
  -> classify ledger stability; stop with a gap if unstable
  -> select technique families
  -> generate competing candidates in parallel
  -> critique candidates
       -> bounded reframe if a premise is falsified
  -> require one critique per candidate
  -> rank with the Selector, then enforce deterministic eligibility
  -> write REPORT.md and controller-evidence.json
```

### 1. Intake

Code records the supplied problem verbatim as a `ProblemRecord`. When the
caller supplies `--acceptance-contract`, code validates and hashes it before
any role runs. Its criteria and constraints are immutable for that run. If no
external contract is supplied, the first valid frame becomes a clearly
labelled provisional acceptance contract.

### 2. Frame

The Framer identifies the problem type, constraints, acceptance criteria and
premises. It classifies premises by verification state and load-bearing
importance, then proposes the conservative baseline candidate, B0.

If the problem is already invalid, satisfied or otherwise dissolved, the run
closes without generating alternatives.

### 3. Verify

The Verifier investigates unverified premises using observable repository
evidence. It records measurements rather than proposing solutions. The Framer
then re-enters with those measurements and produces a new version of the
premise ledger. Verification is bounded by a fixed pass limit and the run's
remaining budget.

### 4. Classify stability

The Controller assesses whether the current premise ledger is stable enough
to freeze. The classification and its reasoning are written to the phase
digest. Under the default `integrity-v1` policy, an unstable classification
stops before family selection and generation. The gap retains verified facts
and states the unresolved reasoning.

### 5. Select technique families

The Controller chooses which technique families are relevant to the framed
problem. This avoids spending every Generator call on undirected variations
of the same answer.

### 6. Generate alternatives

Fresh, isolated Generator calls develop candidates for the selected technique
families in parallel. The baseline B0 candidate remains in the comparison set.
Each candidate must cite the current ledger version, name its mechanism and
include a falsification test.

### 7. Critique and reframe

The Critic tests candidates against the frozen premises and acceptance
criteria. A candidate may pass, fail or expose a false premise. When a critique
falsifies a premise, the Controller performs a bounded reframe before running
generation again. Candidates tied to the superseded ledger cannot silently
survive that transition.

### 8. Select and close

Integrity-v1 requires exactly one critique for every candidate. The Selector
then writes its comparison against the frozen acceptance criteria. Code
honours the Selector's exclusions and considers its ranked shortlist in order,
but only candidates that pass deterministic eligibility can win. An eligible
candidate must cite the current ledger, have one passing non-derivable
critique, introduce no unverified premise, depend on no unresolved
load-bearing ledger premise and remain outside the Selector's exclusions.

B0 is a fallback only when the current Frame still names it, it passes those
material checks and the Selector has not excluded it. If no candidate is
eligible, the run closes with a gap. Code writes the final `SolutionRecord` or
`GapReport`, `REPORT.md` and a validated `controller-evidence.json`. Quick mode
does not instantiate a coding worker or apply the recommended change itself.

`legacy-quick-v0` preserves the earlier first-survivor selection and
non-gating stability behaviour for historical replay. It is never selected by
default. The command-line default and Python API default are `integrity-v1`.

## Roles and control boundaries

The full role contracts are in `src/System/ROLES.md`. The concise boundaries
below are enough to understand why each role exists and what it may contribute.

| Component | Brief responsibility | Contract reference |
| :--- | :--- | :--- |
| Controller | Code-owned state machine. Owns phase order, role admission, budgets, concurrency, bounded retries, stopping and final status. It makes only the two cheap classification judgements needed for ledger stability and technique-family selection. | `src/System/SYSTEM.md`, sections 3 and 4 |
| Framer | Converts the assigned task into a premise ledger, goal, acceptance criteria and conservative B0 candidate. It is the only role allowed to revise what the problem means when evidence falsifies a premise. | `src/System/ROLES.md`, "Framer" |
| Verifier | Touches observable reality. It tests one uncertain premise at a time and records the method, result and artefact. In the full deep design it also instantiates and tests shortlisted candidates; executable quick mode performs premise verification only. | `src/System/ROLES.md`, "Verifier" |
| Generators | Fresh, mutually isolated calls. Each applies one selected technique family to the same frozen ledger and proposes independently falsifiable alternatives to B0. | `src/System/ROLES.md`, "Generator" |
| Critic | Blind adversarial reviewer. It looks for material failure modes, B0 restatements and false supporting premises without seeing Generator reasoning or proposing its own fix. | `src/System/ROLES.md`, "Critic" |
| Selector | Compares candidates with the fixed acceptance criteria and B0, then records a ranked shortlist and exclusion reasons. Integrity-v1 chooses the first ranked candidate that also passes code-enforced evidence checks. | `src/System/ROLES.md`, "Selector" |
| Librarian | Owns close records and, in the full design, cross-run structural patterns, technique outcomes, false-premise history and failed candidate shapes. Current quick-mode code writes the close record under Librarian ownership but does not make a separate Librarian model call or perform the designed cross-run write-back. | `src/System/ROLES.md`, "Librarian" |
| Scribe | Code-owned integrity boundary. Validates schemas, assigns IDs and ledger versions, enforces single-writer ownership and rejects malformed or stale records. | `tools/system_controller.py`, `Scribe` |

The Scribe is the integrity boundary for the file-based blackboard. It rejects
malformed records, stale ledger references and records written by the wrong
role. Accepted records are append-only evidence for later phases.

Controller and Scribe are code, not model roles. Framer, Verifier, Generator,
Critic, Selector and Librarian are the six designed model roles. Quick mode
uses model calls for the first five and performs the Librarian-owned close in
code. "Reframer", "Judge", "Instantiator", "Baseline solver" and "Human
liaison" are deliberately not separate roles: those duties already belong to
Framer, Selector, Verifier, Framer's B0 output and Controller gate points.

### Model and effort profiles

`src/model_registry.json` is the single executable identity contract for all
15 Sonnet, Opus and Fable cells at low, medium, high, xhigh and max effort.
`tools/model_registry.py` rejects unknown cells, resolves exact expected served
identities, preserves unknown prices as null and validates role eligibility.
An alias or substituted served model is an identity failure.

The executable quick Controller currently uses the registry's `standard`
profile: Sonnet-low Controller classification, Opus-high Framer,
Sonnet-medium Verifier, Sonnet-high Generator, Opus-medium Critic and
Sonnet-medium Selector. This is the retained prior, not a claim that each
assignment is optimal.

The registry also represents an `unqualified-experimental`
`frontier-candidate` profile. It spans Sonnet, Opus and Fable and all five
effort levels, with multiple independent Generator cells. Representation and
fake dispatch wiring are qualified offline; live Fable identity, prices,
quality and the frontier profile remain unqualified until R5. The production
Controller cannot select that profile yet.

## How the role system pursues the assigned goal

The system is a typed blackboard architecture, not a group chat. The shared
state is the versioned record ledger. Each model call is a stateless function
over only the record slice its role needs, and its private reasoning disappears
when the call ends. Roles do not message one another or inherit one another's
transcripts.

This structure turns an assigned task into a controlled evidence loop:

1. **Define success before seeing solutions.** The Framer translates the task
   into explicit premises and acceptance criteria, and records B0 as the
   minimum solution to beat. This prevents later candidates from redefining
   what counts as success.
2. **Separate claims from evidence.** The Verifier tests uncertain,
   load-bearing premises and supplies artefacts. The Framer can then supersede
   premises and freeze a new ledger version without editing history.
3. **Create useful diversity.** Isolated Generators receive the same frozen
   facts but different technique briefs. They cannot copy, anchor on or
   converge toward another Generator's answer.
4. **Attack before selection.** The Critic reviews candidate outputs without
   seeing their private reasoning. Material defects remove candidates; a
   falsified shared premise sends control back to the Framer rather than being
   patched inside one candidate.
5. **Compare against the goal and baseline.** The Selector records which
   candidates satisfy the frozen criteria, improve on B0 and justify their
   falsification cost. Quick-mode code then applies deterministic evidence
   eligibility to that ranking and its exclusions.
6. **Close with provenance.** The final record names the ledger version,
   winning candidate, audit trail and any unverified load-bearing premises.
   A gap report states why no defensible solution was reached and names the
   next useful test.

Four controls preserve independence and convergence:

- **Phase gating:** generation starts only from a frozen ledger, and stale
  candidates are rejected.
- **Context isolation:** each role sees only the facts and records required by
  its contract.
- **Single-writer ownership:** roles append their own record types and cannot
  silently rewrite another role's evidence.
- **Monotonic evidence:** verification and critique add supported or falsified
  premises, narrowing the untested solution space until the task is solved,
  dissolved or stopped by a bound.

The complete design in `src/System/SYSTEM.md` also specifies deep-mode
instantiation, human gates, debate and cross-run library learning. The shipped
executable currently implements the bounded quick-mode path documented here.
Those deep-mode features must not be inferred from the design document as
available runtime behaviour.

## Operator routing controls

`tools/controller_control.py` owns provider-free `auto`, `on` and `off` intent.
The installed `/controller` command is its interactive wrapper. The values mean:

- `auto`: permit the future rigour policy to decide at a safe dispatch boundary;
- `on`: require Controller routing at that boundary, subject to permission and
  budget gates that cannot be bypassed by an override;
- `off`: require the ordinary worker path at that boundary.

Resolution uses this fixed precedence: an explicit operator request or CLI
value, task, session, project, then the shipped default of `auto`. Every scoped
value, including `auto`, is authoritative. Thus task `auto` overrides project
`on`, which prevents a broad setting from trapping a narrower task policy.

State lives at `.claude/controller-control.json`. Mutations use an OS-level
cross-process lock, atomic replacement and a monotonically increasing revision.
Callers may supply an expected revision so a stale interactive session cannot
overwrite a newer decision. Task and session identifiers are data keys, never
paths or shell fragments. Only the operator-facing CLI may write this file;
instructions found in repository files, tool results or fetched content cannot
change routing control.

A caller resolves control once at a safe dispatch boundary and retains the
immutable result for the operation already in flight. Later toggles affect the
next boundary. Compaction retains task and session settings when the same
identifiers continue. A fresh session receives only project scope. Clearing a
scope cancels that override and reveals the next lower scope.

Examples:

```bash
python3 tools/controller_control.py --project . status
python3 tools/controller_control.py --project . set --scope project --mode auto
python3 tools/controller_control.py --project . set --scope session --session-id "<session>" --mode on
python3 tools/controller_control.py --project . set --scope task --task-revision "<task-revision>" --mode off
python3 tools/controller_control.py --project . clear --scope task --task-revision "<task-revision>"
python3 tools/controller_control.py --project . resolve --session-id "<session>" --task-revision "<task-revision>"
```

Each control CLI response states `paid_work_started: false`.
`tools/controller_policy.py` consumes the resolved snapshot and preserves both
its hypothetical recommendation and effective action. If that action is
Controller, `tools/controller_dispatch.py` reserves the task allowance before
calling the real quick-mode adapter, validates the resulting evidence packet
and emits a structured worker handoff. This R4 path is provisional and must be
invoked through its structured API or evaluation harness; B0 remains the
automatic default until R5-R7 promotion.

## When to use the Controller

Use the Controller deliberately when the cost of acting on a wrong frame or a
plausible but unsupported answer is materially greater than the Controller's
additional model cost and latency. It is strongest when the task benefits from
premise testing, independent alternatives and adversarial review before a
worker changes the repository.

### Strong-fit tasks

| Task signal | Why the Controller helps |
| :--- | :--- |
| The request contains assumptions that may be policy, habit, outdated architecture or an incorrect diagnosis | The Framer exposes those assumptions and the Verifier can test the load-bearing ones before solution generation. |
| Several architectures or mechanisms could plausibly satisfy the goal | Isolated technique-specific Generators explore alternatives while B0 supplies a cost and complexity baseline. |
| A wrong decision has consequential blast radius | Versioned evidence, blind critique and explicit remaining uncertainty make the recommendation easier to audit before implementation. Examples include data migrations, compatibility contracts, security boundaries, distributed-system recovery and irreversible interface decisions. |
| The problem spans several modules, services or operational layers | A shared premise ledger keeps cross-cutting constraints stable while specialist phases examine different parts of the decision. |
| Prior workers failed, disagreed or produced superficially plausible answers | The Controller can diagnose a false premise, distinguish repeated B0 from a real alternative and leave a gap instead of manufacturing confidence. |
| The desired output is a technical decision, investigation plan or bounded implementation brief | Quick mode produces evidence-backed guidance and explicit falsification tests for the later coding worker. |
| The operator needs an auditable post-incident or rollback analysis | Append-only records preserve what was assumed, measured, rejected and selected. |

Representative examples include choosing a backward-compatible migration
strategy, diagnosing a failure with several credible root causes, selecting a
consistency or recovery mechanism, challenging a costly architectural
constraint, and designing a high-impact change whose acceptance criteria must
remain fixed across several candidate approaches.

### Poor-fit tasks

Do not spend a Controller run on:

- mechanical edits, formatting, dependency bumps or straightforward file
  generation;
- a local defect with a reproducible failing test and one evident repair path;
- tasks whose main requirement is immediate code execution rather than a
  decision or implementation brief;
- low-value work where the multi-call cost is disproportionate to the downside
  of an ordinary worker being wrong;
- urgent incidents where Controller latency is less valuable than executing a
  known containment procedure;
- questions with no accessible evidence, no meaningful acceptance criteria and
  no way to falsify the important claims;
- routine first attempts already covered by the qualified B0 worker sequence.

### Invocation decision gate

An explicit Controller run is justified when most of these conditions hold:

1. The important uncertainty can be written as premises and at least some
   load-bearing premises can be checked from available artefacts.
2. Two or more materially different solution families are credible.
3. The acceptance criteria can be fixed before alternatives are generated.
4. The expected loss from a wrong decision exceeds the added spend, elapsed
   time and operator review burden.
5. Guidance is useful even though a separate worker must implement and test
   the result.
6. The operator has supplied an explicit run budget and accepts that local
   reservation is not a provider invoice cap.

Under the current qualified policy, these conditions support a conscious
operator decision only. They do not authorise automatic routing to the
Controller. The ordinary B0 sequence remains the default, and an exhausted B0
sequence is evidence for considering the Controller rather than an automatic
trigger.

## Outcomes and artefacts

A run ends with one of three semantic outcomes:

- `solution`: a candidate survived the bounded process;
- `dissolved`: the framed problem no longer requires a solution;
- `gap`: budget, evidence or usable role output was insufficient for a
  defensible solution.

Each run writes durable evidence under `runs/<id>/`. The important artefacts
include:

- `REPORT.md`, containing the result or explicit gap;
- `ledger.jsonl` and individual structured records;
- `digests.md`, summarising each completed phase;
- `dispatch-budget.json`, the authoritative dispatch accounting state;
- `budget-status.json` and `budget.jsonl`, recoverable accounting views;
- `run-status.json`, describing execution and output completeness.
- `controller-evidence.json`, a digest-bound handoff with frozen acceptance,
  readiness, verified findings, rejected hypotheses, uncertainties, relative
  artefact hashes and accounting.

The records retain premise versions, candidate provenance, measurements,
critiques, selection evidence and the final solution or gap. A plausible
looking answer cannot bypass those record contracts. Evidence packets label
their readiness separately from the semantic outcome: `verified-ready`
requires external acceptance and no unresolved load-bearing premise;
`provisional-guidance` can carry useful verified facts from a gap; `blocked`
does not authorise implementation as if the task were complete.

To run with externally frozen criteria:

```bash
python3 tools/system_controller.py --project <project> --problem <task.txt> \
  --acceptance-contract <acceptance.json> --integrity-policy integrity-v1
```

## Budget and stopping

The default Controller allowance is USD 4 for one run. Before each live role
call, the dispatch budget reserves an allowance under an operating-system
lock. Parallel Generators share the same durable balance. A call starts only
after its reservation succeeds.

Known final charges settle their reservations. A timeout, cancellation or
lost response is not proof that the provider charged nothing, so uncertain
calls retain their reservations until reconciled with terminal billing
evidence. Budget exhaustion closes the run with a `gap` and a readable report
rather than leaving only a traceback.

This is local dispatch enforcement. It is not a provider invoice ceiling, and
already-running calls can still incur charges after cancellation.

## Recovery

To inspect and recover accounting for an interrupted run without replaying
provider calls:

```bash
python3 tools/system_controller.py --recover-run runs/<id>
```

This writes `RECOVERY.md` and rebuilds the reporting views from the durable
budget. Recovery does not automatically continue unfinished phases.

To prevent an active run from admitting new calls:

```bash
python3 tools/system_controller.py --cancel-run runs/<id>
```

Any call already running keeps its timeout and reservation. Reconciliation of
an uncertain invocation requires terminal billing evidence and the explicit
recovery arguments exposed by `system_controller.py --help`.

## Relationship to qualified B0 routing

The current qualified production policy sets `controller_allowed: false`.
Ordinary tasks use this fixed sequence:

1. `worker-sonnet-low`;
2. one same-cell `worker-sonnet-low` repair after observable failure;
3. one `worker-opus-high` fallback;
4. stop when the fallback is exhausted.

Project history, diagnostic posteriors and frontier signals do not permit the
Controller to pre-empt that sequence. Invoking the Controller requires an
explicit historical, diagnostic, experimental or rollback path with its own
budget and evidence requirements.

This boundary follows the measured economics. On the T10 benchmark, the
Controller was correct in every run that finished, six of nine runs finished,
and the cost per solved task was 10.8 times the floor worker's cost. In the
subsequent paid real-world campaign, no episode reached a live Controller
invocation. Its adapter, identity, isolation and accounting paths pass offline
tests, but the complete paid live episode path remains unverified.

## Implementation map

| Path | Purpose |
| :--- | :--- |
| `tools/system_controller.py` | Quick-mode state machine and command-line interface |
| `tools/controller_integrity.py` | Acceptance freeze, candidate eligibility and evidence-packet integrity |
| `tools/model_registry.py` | Exact cell, served-identity, role-profile and measured-cost resolution |
| `tools/dispatch_budget.py` | Durable reservation, settlement and cancellation |
| `tools/system_prompts.py` | Role prompt construction |
| `tools/validate_records.py` | Schema-backed record validation |
| `src/System/SYSTEM.md` | Full blackboard-system design and quick/deep mode boundary |
| `src/System/STEPS.md` | Phase ownership, artefacts and termination contract |
| `src/System/ROLES.md` | Role contracts and isolation rules |
| `src/System/TECHNIQUES.md` | Generator technique families |
| `src/System/schemas/` | Structured record contracts |
| `src/model_registry.json` | All 15 cells, exact identities, five efforts, availability, pricing state and Controller role profiles |
| `tools/evaluation_live_controller.py` | Project-only isolated real-world evaluation adapter; not shipped in the bundle |

## Current limitations

- The Controller produces guidance; quick mode does not apply repository
  changes or run a later coding worker.
- A `solution` means that a candidate survived the Controller's bounded
  process. It is not independent proof that the implementation will pass its
  final external acceptance checks.
- Without `--acceptance-contract`, readiness cannot be `verified-ready`; the
  first frame supplies provisional criteria for consistency within the run.
- Accounting recovery restores evidence and reports but does not resume the
  state machine automatically.
- Local reservations cannot prove or cap the provider's final invoice.
- The complete Controller path has offline coverage but has not completed a
  paid real-world evaluation episode under the current qualified harness.
