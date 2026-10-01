# X2: named Generator cells and task-wide Controller admission

Date: 2026-09-27 Australia/Sydney. Status: **complete for offline X2 scope**.
The operator confirmed GPT-5.6 Sol / High;
the host does not independently expose the active model or effort. Checkout
`v1.0-rc1` at `15ecf66`, with earlier uncommitted work preserved.

## Behaviour changed

`src/model_registry.json` now assigns each canonical Generator technique to
an explicit cell. The standard profile retains Sonnet high for all three;
the experimental frontier assigns `subtract` to Sonnet high,
`re-represent` to Opus xhigh and `abduce` to Fable high. The quick-mode state
machine passes the technique through each initial and repair call, so
concurrent completion order cannot swap cells. It rejects an unlabelled
frontier call or an unknown/duplicate technique set. Before a frontier
Generator cohort starts, it checks that all selected initial calls and the
Critic/Selector minimum floors fit the remaining Controller allowance, then
uses bounded per-call caps. It does not silently drop a selected technique.

`TaskDispatcher` now claims one Controller admission per task revision across
different RoutingDecision IDs. Legacy decision-specific state from before X2
is treated as used authority rather than replayed. With an N1 root, the
claim is also journalled against its immutable root revision, and Controller
spend is charged once to the N1 root budget. USD 3.50 is held in that same
budget for downstream worker and verification. N1 worker dispatch stays
closed while the Controller claim is pending. A cancelled task releases the
unused follow-on hold, retains the Controller charge and can start a new,
linked N1 revision only under explicit continuation authority. An uncertain
Controller charge retains its hold and prevents a second admission.

This stage qualifies offline admission mechanics. It does not qualify an
automatic Controller default or the N1-to-worker handoff. The default real
`ControllerRuntimeAdapter` remains blocked at this experimental dispatch
path until X4 implements and verifies that bridge. B0 stays the shipping
policy. An explicitly authorised second Controller intervention within the
same revision is unavailable; no changed decision or override can create
one. X4 must design and test that exception before exposing it.

## Verification and source

`test/harness/controller_x2_tests.py` passes eight provider-free tests. They
cover named dispatch, complete-cohort affordability, a quick-mode pipeline
capture, two concurrent decisions on both legacy and N1 roots, inherited
legacy state, root-budget cost and follow-on hold, cancellation, linked
continuation, and uncertain billing. The existing R4, R5, registry,
Controller self-test and N1 executor focused suites passed after the changes.
The checked `tools/build_dist.py` completed successfully after running the
full offline harness as its gate. It initially stopped on a historical Q4
continuation test that compared a frozen M3 source manifest with current X2
runtime bytes. The test now proves that production rejects source drift, then
pins the historical manifest only for its provider-free continuation-arithmetic
assertion. No historical manifest or paid receipt was rewritten. After the
build, the targeted `DIST` check passed with 78/78 generated files matching,
and `tools/release_check.py --json` passed source equivalence and redistribution
exclusions. Its `release_ready: false` records the expected dirty build stamp
and the operator's separate publication action. No Claude provider calls were
made for this stage.

Changed consumer source is `src/model_registry.json`, `src/CONTROLLER.md` and
`src/README.md`, plus `tools/model_registry.py`, `tools/system_controller.py`,
`tools/controller_dispatch.py` and `tools/task_executor.py`. The historical
probe and relevant fake-run tests were updated without changing archived
manifests or paid receipts. `dist/` was generated only by `tools/build_dist.py`.

The direct development-session API charge is unavailable; unknown is not
zero. The dated staged plan estimated USD 3.25-19.50 API-equivalent and 4-8
engineering hours for GPT-5.6 Sol / High, under the token/cache and
Standard/Fast pricing assumptions in the
[execution protocol](../REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md).
That is a forecast, not measured spend. Controller experiment spend was
USD 0 because all X2 adapters were provider-free.

## Remaining risks and next action

Graft freshness timed out on this session, though scoped file/API and call
graph retrieval worked and refreshed changed source. This does not prove the
committed semantic graph is fully current. Served effort for live Claude
calls remains unknown. The frontier profile's quality, cost and Fable
identity are not established by fake calls. X3 now owns the new real-world corpus,
isolated protected grading and fair assessment; X4 owns the complete
production workflow and interactive control path before any X5 paid pilot.
