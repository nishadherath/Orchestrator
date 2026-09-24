# N4: worker corpus and campaign boundary

Date: 2026-09-24. Gate: **N4 provider-free exit met; WSL host startup attested;
authenticated N5 work and the paid runner remain disabled**. No paid worker
calls were made. The [corpus design](../WORKER-N4-CORPUS-DESIGN.md),
[sequencing plan](../WORKER-CONTROLLER-SEQUENCING-PLAN-2026-09-24.md) and
[worker plan](../WORKER-ROUTING-ACTION-PLAN-2026-09-19.md) govern this result.

## Delivered and observed

- `tools/worker_corpus.py` deterministically generated 24 synthetic consumer
  tasks in six families, two development and two newly reserved mechanisms per
  family. Each has an actor package, shallow public acceptance and a data-only
  evaluator oracle. R11 begins with correct code and rewards no edit; D12 and
  R12 include clarification and useful partial semantics.
- `tools/worker_evaluation.py` freezes source, registry, distribution manifest,
  task inventory and oracle hashes. Its fake-only campaign uses `TaskExecutor`
  and `worker_selector` shadow decisions. Actor adapters receive only the
  materialised actor root, not catalogue labels or oracle paths. It persists
  checkpoint and root records; an ambiguous receipt blocks replay.
- The 24-task fake campaign completed with one call per task, resumed with zero
  extra calls, and copied no oracle files to actor output. Public-answer copies
  passed operational checks but failed protected grading. Correct reference
  proxies passed all 23 implementation oracles; an independently written
  alternative passed one task in each family. R11's untouched implementation
  passed; an unnecessary edit became a critical error.
- The two-task fault miniature passed freeze/tamper, independent false-success,
  ambiguous receipt and concurrent-start checks. These are fake-transport
  tests and establish no provider or host isolation property.
- The local WSL2 actor/evaluator filesystem probe passed and wrote
  `test/results/2026-09-24-worker-n4-isolation.json`. Its first cold-start
  attempt timed out; a repeat passed. It proves only a local Linux user/mode
  boundary, not that the Claude process, inherited instructions or Graft MCP
  runs behind that boundary.
- A separate fresh actor-root Graft MCP probe passed all seven checks. Its
  six-tool server found an actor marker, found no sibling evaluator marker,
  rejected parent-scoped search and file API requests, and exposed no
  evaluator path in map or semantic search. The digest-bound evidence is
  `test/results/2026-09-24-worker-n4-graft-probe.json`. This proves the scoped
  local index behaviour, not what a live Claude host actually loads.
- A disposable Windows Sandbox viability probe started the binary but its
  logon command did not run. The operator selected WSL instead. Native Linux
  Claude Code 2.1.273, Node 22.22.0 and Graft 0.18.0 now run from WSL ext4;
  the Windows-mounted executables are excluded from the actor namespace.
- The fresh WSL host attestation passed 40 checks and is bound to the current
  frozen N4 manifest and runtime/source hashes in
  `test/results/2026-09-24-worker-n4-wsl-host.json`. The actor ran as UID
  65534 in private mount/PID namespaces. It could edit its own `app.py` and
  could not read the root-owned evaluator through a direct path, symlink,
  recursive search or `/proc/1/root`; Windows C/D mounts and interop sockets
  were hidden. Native Graft built and served an actor-only index. The
  materializer copied only four public files; the actor could not alter
  acceptance or create a new root-level file.
- The actual unauthenticated Claude CLI started inside that boundary. Its
  startup event reported exactly one connected MCP server, Graft, and all six
  required tools; no command-running, web or delegation tool appeared. It
  ended with a zero-token authentication failure. This verifies startup and
  tool wiring, not an authenticated model's edit or a paid result.
- The production adapter's CLI argument assembly was corrected to use
  `--key=value` for variadic options; previously the MCP path could consume
  subsequent options as file names. The fix passed focused regressions.
- A project-side `WslWorkerAdapter` now stages a single admitted invocation,
  runs Claude in the attested namespace and collects only an allowed `app.py`
  edit after a terminal event. A transport probe accepted an allowed edit and
  rejected protected-file drift. The actual adapter returned a matched,
  stopped-writer, zero-cost authentication-failure receipt with unchanged
  source. This is no paid worker run.
- The full provider-free project harness passed 59 checks. Graft deep refresh
  completed and its freshness tool reported both semantic and wiring graphs
  in sync. A Windows temporary-log deletion race in the refresh helper was
  corrected and the helper reran successfully.

## Statistical preflight

`tools/worker_statistics.py` implements the v2 contract's task-level
Clopper-Pearson acceptance and Hoeffding quality lower bounds. Its fixed-seed
1,000-trial illustration at 12 independent tasks has a 78.41-point quality
penalty. Equal, +10 and +35 assumed quality gains cleared both floors in 0%
of simulated trials; an extreme +80 gain with 90% candidate-only wins cleared
in 99.7%. The assumed quality is deterministic within each scenario, so these
figures are illustrations, not measured statistical power. Two repetitions on
one task never count as independent samples. With the frozen gate, a 12-task
N6 is exploratory for modest effects. B0 stays the default absent stronger
independent evidence and operator promotion.

## Remaining N4 gate

The current corpus consists of small single-file JSON-line exercises. It
tests the mechanics of orchestration and grading, but does not yet reproduce
multi-file repository edits, real dependency failures or actual concurrent
execution. Treat any quality result on this corpus as limited to these
synthetic mechanisms, not as evidence of general real-world readiness.

The generic `WorkerAdapter.capability()` still reports
`enforcement_proven: false`; the attested WSL adapter is project-side. The fake
campaign uses the same Windows identity as its evaluator; only the WSL probe
exercises OS isolation. The startup probe has no
provider credentials and cannot prove an authenticated worker's behaviour or
cost receipt. The attestation is a content-digested local record, not a
cryptographic signature. It does not authorize paid calls or a reusable live
campaign entry point.

The next N5 implementation action is a campaign runner that passes the
attested adapter to `TaskExecutor`, binds its manifest and authorisation,
handles credentials and restart-safe receipts, and repeats the probe against
that final launch path. Keep the current fake-only runner
closed until those checks and the full offline harness pass. See the
[WSL host guide](../WORKER-N4-WSL-HOST.md).

## N5 authorised run inventory, contingent on that gate

1. Screen exactly 15 registry model/effort cells: one identity call capped at
   USD 0.25 and three fixed microtasks capped at USD 1 each per cell. At most
   60 calls and USD 48.75 local admission allocation; unsupported identities
   stop their tranche without substitution.
2. Use only D01-D12 for at most one B0, one candidate and one predeclared
   alternative episode per task: at most 36 episodes, USD 3 total per episode,
   USD 108 local allocation. Assessment, attempts, verification and unknown
   charges share the episode cap. Do not buy a dominated arm automatically.
3. Total N5 ceiling under this inventory: USD 156.75 in local admission
   allocations, not a predicted bill. Reprice and issue the plan's concrete
   spend notice before any live calls. N6 reserved tasks and grades are excluded.

N5's development work can reassess statistical feasibility using its own
unprotected evidence. It cannot change the reserved N6 gate after viewing
reserved outcomes. N4 does not change the Controller or shipping B0 policy.
