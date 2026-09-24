# Worker remediation N0A: shared-contract amendment

Date: 2026-09-24. Result: **design complete for operator review; N1 not started**.

## Scope and baseline

Task: resolve the worker-first dependency-review findings by amending the design
and N1 acceptance requirements, without implementing the executor or Controller.
Success means legal B0 lifecycle witnesses, explicit identity/accounting owners,
concrete adapter/test boundaries, corrected evaluation semantics and a checked
N1 handoff. Out of scope: production code, paid campaigns, delegation, default
promotion and release operations. No subagents were used.

Branch `v1.0-rc1`, HEAD `a70e311`. The preceding sequencing-plan changes were
already uncommitted: CLAUDE/README, three programme/protocol documents, three
historical handoffs, plus the new sequencing plan and N0A handoff. They were
preserved and their current-state pointers updated. No commit was requested.
Graft semantic/wiring freshness passed; scoped file API, source queries and
import tracing supplied the evidence below. This is design work, not a measured
improvement in live task quality or routing cost.

## Decisions and outputs

| Area | Finding | N0A resolution |
| :--- | :--- | :--- |
| Lifecycle | v1 terminates the task after an attempt and has no repair edge | v2 separates task, attempt, verification and accounting; explicit ready/review/reconciliation paths |
| Identity | Mutable acceptance and policy request were hashed with the definition | Freeze acceptance definition/baseline only; decisions, overrides and evidence have separate records |
| Root allowance | Existing budget limits cannot be amended by reopening | Specify explicit audited N1 lifecycle operations, root lineage and no balance reset |
| Cancellation | New revision could otherwise escape old work/holds | Terminal predecessor immutable; continuation waits for stopped writers and settled root |
| Records | Rich attempts are not accepted by the strict old ledger | Versioned sidecars and allowlisted route-v2 projection with explicit enum mapping |
| Adapter | Evaluation worker imports test harness code | Extract worker_adapter.py; compatible evaluation wrapper; early installed-consumer tests |
| Graft/host | Tool configuration is not proof of isolation/interception | Explicit capability and scoped-Graft requirements; block unsupported managed paths; N4 isolation gate |
| Controller | Legacy identity and dispatcher own different boundaries | X2 mapping/counts; X4 allocated inner step; executor remains overall owner |
| Historical tests | Frozen manifests bind shared registry source | Three-way historical/current/mutation test split, with no historical rehash or runtime bypass |
| Evaluation | v1 bounds gross losses and overstates a universal sample minimum | Net paired acceptance estimand, explicit aggregation and conservative simultaneous bounds |
| Sequencing | X1/X3 prerequisites understated; X3/X4 integration ambiguous | X1 requires N4, X3 requires N3/N4, X4 owns integrated path before X5 |

Current entry: [execution contract index](../WORKER-EXECUTION-CONTRACT.md).
Normative design: [v2](../WORKER-EXECUTION-CONTRACT-v2.md).
Implementation gate: [34-case N1 matrix](../WORKER-N1-ACCEPTANCE-v2.md).
The [original v1](../history/WORKER-EXECUTION-CONTRACT-v1.md) is preserved
byte-for-byte; the N0 record now links it and identifies the superseded claims.
No source or generated bundle file changed; rebuilding dist is unnecessary.

## Source observations, inferences and untested risks

Observed through source retrieval: acceptance.load_contract returns status,
evidence and review alongside frozen contract data; verify can require review.
route._normalise_attempt rejects unknown fields and uses only direct/escalation
start kinds. DispatchBudget rejects changing an existing limit and has no
authorised continuation operation. The live-worker adapter imports realworld
from test/harness. build_dist has an explicit tool list. Controller manifests
bind model_registry source and validate its current digest. These are current
implementation facts, not defects reproduced by paid execution.

Inferences resolved in the design: task/attempt confusion would block legal B0
repairs; full acceptance-state hashing would make review mutate identity;
embedding the whole Controller dispatcher would create competing owners; a
production adapter importing evaluation fixtures would fail consumer isolation.
The v1 retry contradiction is also demonstrated by the design graph check.

Untested until implementation: cross-process fencing, external writer shutdown,
budget migration, interactive interception, scoped Graft isolation, served effort
and live quality/cost. An allowed state edge is not proof that its runtime guard
is enforced. Current green tests cannot close these future requirements.

## Validation

Design evidence is recorded in
[the design JSON](../../test/results/2026-09-24-worker-n0a-design.json).
The [full harness output](../../test/results/2026-09-24-worker-n0a-harness.json)
records **PASS, 57/57**, against HEAD `a70e311`. It validated 17 handoffs,
415 authored files and unchanged parity for all 69 bundle files. It ran with
the child-process permissions already required by the offline fixtures. No
production acceptance row is marked passed by these checks.

Design check: **PASS**, 12 states, 35 allowed edges, 15 legal witnesses and
9 explicit forbidden-edge checks. All four terminal states have no outgoing
edges. The archive matches HEAD's original v1 bytes. v1 has neither the new
ready state nor a verification-to-next-admission edge, reproducing its design
blocker without claiming a failure in a nonexistent executor. New local links,
handoff validation and `git diff --check` passed.

Statistical arithmetic checks passed. At 12 tasks with all candidate-only wins,
the chosen acceptance lower bound is 0.38816; with all quality differences 100,
the chosen quality lower bound is 21.58997. These artificial edge cases show
that a universal 59-task minimum is false for the corrected gate; they are not
experimental results or a power claim. At 12 tasks with no discordances, the
acceptance lower bound is -0.30592, so this conservative procedure retains B0.

The design check parses the v1/v2 Markdown transition tables, checks legal and
forbidden witness paths, terminal states, archive bytes and document links,
and calculates statistical edge cases. It does not implement a task executor.
The full offline command is `python test/harness/check.py --json`; its captured
JSON provides each check and result. It uses offline fixtures, no paid calls.

The core lifecycle evidence can be replayed with this Python snippet from the
repository root (the original check also verified links, archive and arithmetic):

```python
from pathlib import Path
import hashlib, json, re
data = json.loads(Path('test/results/2026-09-24-worker-n0a-design.json').read_text())
text = Path('docs/WORKER-EXECUTION-CONTRACT-v2.md').read_bytes()
assert hashlib.sha256(text).hexdigest() == data['contract_sha256']
rows = {}
for line in text.decode().splitlines():
    cells = [cell.strip() for cell in line.split('|')]
    if len(cells) == 5 and cells[1].strip('`') in data['states']:
        rows[cells[1].strip('`')] = re.findall(r'`([a-z_]+)`', cells[2])
assert rows == data['states']
for path in data['witnesses'].values():
    assert all(b in rows[a] for a, b in zip(path, path[1:]))
assert {s for s, targets in rows.items() if not targets} == set(data['terminal_states'])
```

## Acceptance, costs and next action

| N0A exit | Result and evidence |
| :--- | :--- |
| A: legal task/attempt lifecycle and review/recovery | Complete design; 15 graph witnesses, terminal and forbidden-edge checks |
| B: identity, override, lineage and allowance boundary | Complete design; immutable definition, root authority, legacy projection and N1-17 through N1-25 |
| C: adapter, distribution, Graft and future Controller interface | Complete design; named production modules, ownership/lock order and N1-26 through N1-34 |
| D: historical test split, fair grading and stage dependencies | Complete design; contract sections 9-10 and corrected X1/X3/X4/X5 prerequisites |
| Validation and handoff | Full harness 57/57; N1 handoff valid; no implementation claim |

N0A freezes a conservative statistical method, not a claim of adequate power.
N4/N5 must assess the declared task population, independence and development
power before paid qualification. A different method needs a reviewed amendment
before N5 and before reserved results; sample expansion is never automatic.
Mechanical worker release can retain B0 and still provide the platform for X0.

Requested development setting: GPT-6 Astra / High. The host exposes that target
in model metadata, but this session has no independent served-model/effort
telemetry, so the requested setting is not claimed as verified. No switch was
made. Development invoice/token categories are unavailable; actual API-equivalent
cost is unknown. The planning range was USD 3-20 and 2-4 hours, not a measured
bill or elapsed-time claim. Paid Claude experiment spend: USD 0. Graft provider
charges are unknown; retrieval estimates are not measured invoice savings.

Stop for operator review. The next stage is N1 using
[the new v2 handoff](../../handoffs/2026-09-24-worker-routing-n1-v2.md),
**GPT-5.6 Sol / High**, estimated **USD 3.25-19.50 API-equivalent and 5-9 hours**,
with no planned paid Claude experiment. N1 must prove the full matrix and
installed path; it must not begin N2 or deferred Controller implementation.
