# Controller-aware routing R4: policy and dispatch

Date: 2026-09-18

R4 implements the versioned `rigour-auto-v1` candidate policy and the
production Controller dispatch boundary. The reserved-qualified B0 sequence
remains the shipping default while R5-R7 measure the candidate.

## Policy contract

`tools/controller_policy.py` validates a complete `RigourAssessment` and emits
a content-addressed `RoutingDecision`. The assessment uses consequence,
premise uncertainty, alternatives, coupling, verification gap, observed
failure cause, required output, evidence availability, deadline, authorised
budget and bounded provenance records. It receives no model names or routing
performance table.

The initial deterministic policy recommends the Controller for a material,
checkable contradiction; a new material premise conflict; or consequential or
irreversible work that combines unresolved assumptions with competing
mechanisms or coupled constraints. It does not trigger on task length, file
count, wording, self-confidence, infrastructure failure, or an ordinary
implementation defect alone. Missing operator decisions or unavailable
material evidence produce clarification rather than invented facts.

The R3 control snapshot is applied after the recommendation. `on` and `off`
change the effective action while preserving the hypothetical recommendation;
`auto` accepts the policy. Permission, budget, identity, acceptance, one-run
and evidence gates remain mandatory. A visible test pass cannot close
consequential work with unresolved assumptions and weak verification.

`route.plan()` and its B0 CLI remain backward compatible.
`route.plan_rigour()` and `route.py --rigour-assessment` are the versioned,
provider-free candidate adapter.

## Production dispatch boundary

`tools/controller_dispatch.py` reserves a `task_dispatch` budget before any
external side effect, starts a durable invocation before the adapter call and
will not replay an interrupted or completed decision. The Controller receives
at most USD 4 from the experimental USD 8 task envelope, leaving separately
declared worker and acceptance capacity. Nested Controller charges settle once
into the outer task budget. Partial or unknown accounting remains held.

`ControllerRuntimeAdapter` is the consumer adapter around
`system_controller.run_quick`. It uses the standard role profile with exact
identity checks and a read-only Claude tool surface. The assessment's frozen
input revision is passed into the Controller so its evidence packet binds the
same task revision even though runtime artefacts are created during execution.

Before a worker handoff, code validates the evidence-packet digest, task,
acceptance and input digests, run-directory containment, artefact hashes and a
fresh source snapshot. A solution or a gap containing verified findings can
produce a structured handoff. A gap with no useful evidence blocks. A
dissolved result requires independent contract confirmation. Raw reports and
their commands are never forwarded. The handoff marks every Controller field
as evidence that still requires independent acceptance.

An explicit cancellation stops new admissions, preserves evidence and holds
uncertain billing. A provider call already running may finish and bill.

## Offline verification

`test/harness/controller_routing_r4_tests.py` covers 28 cases: all automatic
and override paths, policy negatives, budget and invocation caps,
consequential public-pass behaviour, schemas, route API/CLI parity, direct
worker routing, the real runtime adapter under a mocked `run_quick`, valid and
invalid evidence, source mutation, useful and empty gaps, dissolution,
incomplete accounting, interruption, cancellation and replay protection. It
makes zero provider calls.

The production path is implemented and offline-qualified. Automatic use and
the frontier role profile remain provisional until the staged R5-R7 live and
reserved evaluations pass.

## Completion evidence

The focused R4 suite passed **28/28** cases with zero provider calls. The
complete offline harness then passed **56/56 checks**, including Controller
integrity, all 15 model/effort cells, controls, routing, budget recovery,
installation, diagnostics, the 24-task historical real-world corpus and all
recorded paid-evaluation evidence. The rebuilt redistributable contains **69
files** and passed exact source, manifest and release-candidate parity.

R4 also exposed a pre-build dependency cycle: the historical B0 freeze rightly
fails source/bundle parity while `route.py` has changed but `dist/` has not yet
been rebuilt. `tools/build_dist.py` now recognises only that exact single
failure when DIST is stale, every non-parity B0 qualification check passes and
the freeze reports only source/bundle parity differences. All other
real-world failures remain build-blocking. The independent post-build harness
proved that the exception closes once the new bundle exists.

No Claude worker, Controller, grader or other paid task call was made during
R4. Graft semantic maintenance uses the project's separately configured
DeepSeek service.

The approved deep Graft refresh completed with **2,209 nodes, 4,531 edges and
426 file cards**. It computed 78 changed meanings, reused 2,131 cached meanings
and left zero stale or pending meanings. Both the semantic freshness check and
the wiring-graph check passed.
