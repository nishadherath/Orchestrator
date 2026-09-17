# Context reduction design

Date: 2026-09-17. Scope: improvement Stage 5. Decision: D88.

## Measured surfaces

`tools/context_inventory.py` measures exact UTF-8 bytes, Unicode characters and
SHA-256 hashes. Its token figure is `ceil(characters / 4)`, used only for a
consistent before/after comparison. It is not a provider tokenizer or bill.
The immutable baseline is `docs/CONTEXT-BASELINE-2026-09-17.json`; the measured
result is `docs/CONTEXT-MEASUREMENT-2026-09-17.json`.

| Surface | Before estimate | After estimate | Change |
| :--- | ---: | ---: | ---: |
| Repository-development standing instructions | 7,848 | 2,224 | -71.7% |
| Installed orchestrator template plus stable core | 8,750 | 2,665 | -69.5% |
| One selected worker, mean across 15 definitions | 606.3 | 423.7 | -30.1% |
| Controller role static brief | 931-1,128 | 553-750 | -378 each |

The 8,051-token detailed orchestrator reference still ships. It is conditional,
not counted in the standing core. Controller technique briefs are unchanged and
remain conditional on one Generator family. Dynamic task input, schemas,
records, tool definitions, retrieved code, output and reasoning are excluded.

## Structure

`src/ORCHESTRATOR_CORE.md` is the stable operating contract. It contains the
assessment, resolver, pre-dispatch acceptance, dispatch, completion, escalation,
handoff and recovery rules needed on ordinary tasks. `tools/build_dist.py`
publishes it as `ORCHESTRATOR.md`.

The detailed `src/ROUTING.md` and `src/LIFECYCLE.md` remain the source for
`ORCHESTRATOR-REFERENCE.md`. The core names the exact conditions for reading a
relevant reference section: stop/resume details, transcript addressing,
handoff accounting, crash recovery, Controller charge reconciliation, evidence
cohorts and historical platform limitations. A consumer can audit the detail
without paying its full static load on routine tasks.

The compact consumer template carries only the Graft and transition rules that
must be visible before delegation. Worker definitions retain Graft, acceptance,
scope, escalation, communication and permission rules. Controller prompt
assembly still extracts only the shared rules plus one role section, one
technique where needed and schema summaries. Historical explanation was removed
from the shared role prefix; role-specific contracts and technique briefs were
left unchanged.

## Requirements map

| Mandatory behaviour | Standing instruction | Conditional detail | Regression evidence |
| :--- | :--- | :--- | :--- |
| Graft on every task and child | consumer template, core, worker persona, shared role rules | `docs/GRAFT.md`, bundle README | CONTEXT, PERSONA, PROSE |
| Preserve permissions and file boundaries | core dispatch/escalation, worker persona | lifecycle reference | CONTEXT, ACCEPTANCE |
| Freeze acceptance before dispatch | core section 3 | routing reference and acceptance design | CONTEXT, ACCEPTANCE |
| Owned verification and explicit rubric review | core section 4 | acceptance recovery reference | CONTEXT, ACCEPTANCE |
| Durable Controller allowance and unknown charges | core sections 5-6 | Controller budget recovery reference | CONTEXT, DISPATCH-BUDGET |
| Handoff before every transition or child | template and core section 6 | handoff reference | CONTEXT, HANDOFF, HANDOFF-SELFTEST |
| Resolve in code and never pass Agent `model` | core sections 2-3 | routing reference and self-learning guide | CONTEXT, INV2, ROUTE-SELFTEST |
| Actionable recovery without invented outcome/cost | core section 6 | acceptance and Controller recovery reference | CONTEXT, ACCEPTANCE, DISPATCH-BUDGET |
| Preserve prompt rationale isolation | core build plus stripped reference | with-rationale comparison bundle | CONTEXT, DIST |

## Additional correction

The previous detailed routing sequence created the acceptance contract before
dispatch but told the orchestrator to run `route.py --spawn` after invoking the
Agent tool. That left a dispatch window before the contract and protected-path
baseline were frozen. Both core and detailed reference now run `--spawn` before
Agent invocation. A pending row left by a failed launch is visible to recovery,
which is safer than unrecorded work already in flight.

## Rollback and limits

The baseline records exact hashes for the prior consumer, development, worker
and Controller instruction surfaces. Revert the core assembly, template,
persona and shared role rules, regenerate workers and rebuild `dist/` to return
to those hashes. The detailed reference preserves the prior operational text,
apart from the pre-dispatch ordering correction.

Static reduction is not proof of lower billed tokens or money. Cache behaviour,
provider tokenisation and task-dependent reference loads can change the result.
It also does not prove equal model behaviour. Stage 5 therefore keeps the
existing offline fixtures and rollback hashes, changes no TTL, routing choice or
model setting, and leaves any paid compatibility measurement to the fixed
corpus rather than the deferred real-world campaign.
