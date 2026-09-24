# N4 worker corpus and campaign boundary

Status: offline corpus and fake campaign implemented. Live worker isolation is
unproved and paid launch remains disabled. No paid run or reserved worker grade
has occurred. Local reference and shortcut tests exercise evaluator-only
oracles; their outputs cannot tune a candidate policy.
This document implements the N4 scope in
`WORKER-CONTROLLER-SEQUENCING-PLAN-2026-09-24.md` and
`WORKER-ROUTING-ACTION-PLAN-2026-09-19.md`. The older real-world D/H fixtures
and R5 synthetic tasks are development references only. Their reserved labels
and results are already known to this project and cannot supply new N6
holdout evidence.

## Corpus

The corpus contains 24 self-contained Python standard-library tasks, six families with
two development and two newly reserved mechanisms each. Synthetic code is
acceptable only when the issue, implementation surface and executable
behaviour resemble a real consumer defect. Each actor package contains a
specific issue, runnable baseline, shallow public checks and a bounded edit
scope. Evaluator-only oracles test behavioural properties and acceptable
alternatives, not prescribed wording or the author's reference patch.

| Family | Development mechanisms | Reserved mechanisms |
| :--- | :--- | :--- |
| Configuration and CLI | D01 layered CLI/file/environment precedence; D02 reject invalid configuration without silent defaults | R01 secret reload without leaking stale values; R02 path normalization that stays under an allowed root |
| Service resilience | D03 idempotent retry on selected HTTP failures; D04 end-to-end timeout across redirects | R03 circuit-breaker half-open admission; R04 cancellation releases a bounded permit |
| Data integrity | D05 atomic CSV batch import; D06 resumable SQLite schema migration | R05 exactly-once JSONL checkpoint recovery; R06 Decimal ledger rounding and balance invariants |
| Concurrency and cache | D07 tenant-scoped cache keys; D08 single-flight exception fan-out | R07 TTL refresh race without stale overwrite; R08 bounded shutdown that drains accepted work |
| API and protocol | D09 conditional ETag response; D10 webhook signature over exact request bytes | R09 pagination cursor under concurrent insertion; R10 length-prefixed codec with partial frames |
| Diagnosis and operator decisions | D11 reject a misleading hotspot using measurement; D12 ask for a missing retention rule before deletion | R11 make no code edit when an upstream configuration fault is proven; R12 leave a verifiable safe partial result when a required external key is absent |

Each mechanism needs a different failure trigger and oracle. D12, R11 and R12
must credit justified clarification, no-change and useful partial work without
accepting confident false completion. Reference and independently structured
alternative implementations must pass; public-label copying, a happy-path
hardcode, protected-test edits, omitted constraint disclosure and unsupported
success claims must fail the relevant grade. Keep the 12 reserved packages and
oracle outputs out of development tuning; author and freeze them before N5.

## Protection boundary

Materialise only the actor package into an isolated work root. Keep task IDs,
family labels, reference variants, independent oracles and result files in an
evaluator root unavailable to the actor user. The actor's Graft instance must
index only its materialised root. No inherited `AGENTS.md`, `CLAUDE.md`, MCP
configuration, environment variable, symlink or parent path may disclose an
oracle. The runner checks the real filesystem boundary, shell reads, recursive
search, Graft search, and attempted symlink traversal using a sentinel unique
to evaluator files. A prompt telling the worker not to look is not isolation.
The provider-free runner cannot launch a live adapter. Its fake actor receives
only the materialised actor root; the evaluator alone receives catalogue
metadata. Both still run as the same Windows user in these tests, so this is
an interface check, not an OS proof.

The WSL2 `realworld_isolation.py` test proves one local Unix-user filesystem
boundary. A separate fresh `worker_graft_probe.py` MCP test proves that an
actor-root Graft instance indexes only actor files and rejects parent-scoped
queries. Neither proves Claude transport or an actual worker's full filesystem
boundary. N4 must bind a fresh actual-host attestation to
the campaign manifest. A fake transport can exercise accounting and workflow,
but cannot qualify live access control. Any unproved boundary blocks paid
launch; a failed isolation check must not be waived by authorisation.

## Campaign contract

Use `TaskExecutor` as the sole root task owner, `worker_selector` as a shadow
advisor, and `DispatchBudget` for every admitted charge. The campaign runner
owns only the sequence of root episodes and aggregate analysis. It freezes
actor input, acceptance definition, model registry, selector, executor,
adapter, prompts, Graft configuration, dependency versions, oracle hashes,
package revision, task ordering, budget ceilings and scoring code in one
content-addressed manifest. The manifest and operator authorisation bind the
same digest and maximum USD exposure. N4 itself uses fake transports only.

Persist admission and dispatch intent before side effects. On restart, a
terminal failure stays terminal and admits zero new calls. An ambiguous started
call remains uncertain with its budget held until a receipt or explicit
reconciliation proves writer and charge state. Concurrent launches of one
campaign have exactly one owner. Record actual model, requested effort, served
effort evidence if available, usage, cache counters, wall time, all attempt
costs and missing telemetry. Unknown is not zero. Graders run after the actor
stops and cannot modify its files.

## Scoring and statistical preflight

Keep public operational acceptance separate from independent post-episode
quality grading. Score full acceptance, useful partial milestones, diagnosis,
clarification, critical safety errors and false success from executable
evidence. A task that is incomplete may improve in quality; that improvement
is counted without calling it accepted. Task is the paired statistical unit;
two repetitions are repeated measurements on the same task, not 24
independent reserved tasks.

Before N5 spending, implement and run a simulation of the proposed N6 joint
95% intervals and safety gates under plausible win/loss and cost scenarios.
The v2 contract's quality penalty is 78.41 points at 12 tasks. A zero or
modest positive quality difference cannot clear its -5 point lower bound;
even a 35-point gain cannot. In a fixed-seed 1,000-trial illustrative
simulation, +80 points with 90% candidate-only wins cleared both quality
floors in 99.7% of trials, while equal, +10 and +35 scenarios cleared in 0%.
These are calculations under assumed task-level effects, not measured power or
evidence of model performance. Under the frozen gate, N6 is exploratory for
plausible modest gains; retain B0 absent stronger independent evidence. Do not select
a more permissive interval method after seeing reserved outcomes or silently
expand the paid campaign.
