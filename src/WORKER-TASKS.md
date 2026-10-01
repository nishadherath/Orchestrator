# Durable worker tasks

Use `/worker-task` in an interactive Claude Code session, or run
`python3 tools/worker_tasks.py --help`. The command wraps the N1 executor;
only `run` can start provider calls. It keeps one task budget, frozen
acceptance, independent verification, receipts and recoverable state.
The automatic policy is B0: Sonnet low, one Sonnet low repair after a verified
failure, then one Opus high fallback. A verified pass stops immediately.

This is an explicit alternative to the prompt-driven Agent-tool workflow.
Choose one owner for a task. Do not launch an Agent worker for work already
admitted to the executor. The CLI cannot intercept arbitrary Agent-tool
launches, prove filesystem isolation or attest served reasoning effort.
`capability` reports the host's actual claims; the general adapter currently
reports `enforcement_proven: false` and rejects managed child execution.
Corpus-specific WSL evaluation isolation does not qualify arbitrary consumer
projects. Use an isolated checkout and a reviewed acceptance command.

## Capability matrix

| Capability | Current consumer behaviour | Evidence and limit |
| :--- | :--- | :--- |
| Automatic task routing | Fixed B0 sequence | Earlier reserved comparison qualified B0; Q4U did not replace it |
| Durable root execution | Explicit CLI or Python API | Offline acceptance, accounting and recovery tests; host isolation unproven |
| Interactive Agent launches | Session follows the routing prompt | No runtime interception or shared-budget enforcement for arbitrary launches |
| Explicit model/effort choice | N3 shadow recommendation across eligible registry cells | Does not dispatch or qualify a requested cell; host proof may reject it |
| Managed children | Static N2 API under a shared budget | Fake-host graph and envelope tests; general live adapter rejects admission |
| Cancellation and continuation | Durable stop, local CLI signal and linked revision | Unknown writer or cost evidence blocks safe continuation |
| Automatic Controller | Outside the qualified default | Experimental controls exist; remediation and quality qualification remain |

`preflight.py --status --json` includes `worker_tasks` with open roots,
held funds and rollback readiness. A missing CLI or unreadable record remains
visible rather than being reported as an empty healthy task set.

## Admit, inspect and run

Create an acceptance contract using `acceptance-contract.example.json`, then
write a task request such as:

```json
{
  "goal": "Implement the requested change and satisfy the acceptance contract",
  "scope": ["app.py"],
  "acceptance_path": "acceptance.json",
  "budget_usd": 1.0,
  "authority_id": "operator_task_001",
  "actor": "operator",
  "root_id": "task_001"
}
```

The amount is an example local allocation, not a cost estimate. Use a unique
authority per admission and an agreed task budget. Optional fields are
`task_id`, `input_paths`, `deadline_at` (timezone-aware ISO timestamp) and
`axes` (the sensitivity, horizon and blast assessment). Paths are relative to
the consumer project; frozen inputs cannot overlap write scope. An admission
does not call a provider. It rejects unknown fields, including experimental
dispatch specifications.

```text
python3 tools/worker_tasks.py capability --project . --mcp-config actor-mcp.json
python3 tools/worker_tasks.py admit --project . --mcp-config actor-mcp.json --request task.json
python3 tools/worker_tasks.py status --project . --root task_001 --json
python3 tools/worker_tasks.py run --project . --mcp-config actor-mcp.json --root task_001
```

The explicit MCP file must expose only Graft and bind its index root to
`${CLAUDE_PROJECT_DIR}`. Register the launcher available on the consumer host.
Use the same configuration at admission and execution. `run` invokes the local
Claude Code CLI and inherits its authentication environment; it has no API-key
argument. Confirm the intended login and billing mode on that host before
spending. State the expected cost and elapsed time before a live run. Local
allocation controls admission and each requested cap; final provider charges
may exceed it. Missing charge evidence retains the reservation.

Exit code 0 from `run` means independently accepted. Exit code 2 means the
task stopped without acceptance, or the operation was rejected. `status`
returning 0 only means the record was read successfully. `--json` exposes the
full journal, requested cell, actual model evidence and budget snapshot.
A process lock prevents two CLI drivers from running the same root at once.

## Recovery and operator controls

Operations below use `--root <id> --request operation.json`. They change state
without launching a worker; call `run` separately when resumption is justified.

| Operation | Required JSON fields | Optional fields |
| :--- | :--- | :--- |
| `cancel` | `actor`, `reason` | none |
| `resume` | `actor`, `reason` | none |
| `continue` | `actor`, `authority_id`, `reason` | `acceptance_path` |
| `review` | `decision`, `reviewer` | `notes` |
| `reconcile` | `actor`, `reason`, `cost_usd`, `evidence`, `writers_stopped` | none |
| `partial` | `actor`, `reason` | none |
| `shadow` | `facts` | `override` |

`resume` applies only to a blocked task whose recorded recovery phase permits
it. A cancelled task requires `continue`, which creates a linked revision
under the original budget after all writers and charges are resolved.
It does not refund spending. `review` uses `pass` or `fail` for rubric
acceptance. `reconcile` requires observed cost and stopped-writer evidence;
never infer either from silence. `partial` preserves an explicitly incomplete
result after accounting is settled.

Cancellation stops new admissions. A live CLI run observes the durable cancel
record and signals its local worker process; Ctrl-C follows the same route.
Process exit, descendant termination and final billing still require evidence.
A crash or a process outside this CLI may leave a writer or charge unresolved.
Keep the root journal and investigate before resuming or starting other work
on the same scope. The CLI does not replay a worker with an uncommitted receipt.

`shadow` takes the public `facts` and optional explicit-cell override described
in `WORKER-SELECTOR.md`; provide the same MCP config. It records a recommendation
beside B0 and never changes dispatch. Unsupported cells or absent host proof
remain rejected. Q4U's development canary did not qualify a new default; its
grader and dependency-seal findings also prevent promotion. Those experimental
campaign tools are source-repository research, not installed consumer commands.

## Managed children and rollback

`MANAGED-DELEGATION.md` defines the N2 Python API, static child graph, nested
envelopes and host capability gate. The general live adapter refuses that path
until it can enforce child isolation. Fake-host tests are state-machine and
accounting evidence, not a claim that live child execution is qualified.

Stop new task admissions and run `python3 tools/worker_tasks.py audit --project .`
before changing the bundle. Exit 2 blocks rollback while a root is open or a
charge is unresolved. This is a point-in-time audit, not a lock against later
admissions. Preserve `.claude/task-executor-v2/`, `.claude/acceptance/` and the
routing ledger. Use the installer's recorded backup ID to roll back the bundle;
do not remove task records or relaunch the task through the legacy Agent path.
