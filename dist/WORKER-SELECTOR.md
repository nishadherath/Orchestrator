# Experimental worker selector (N3)

`tools/worker_selector.py` is a deterministic, versioned worker-only policy
(`worker-shadow-v1`). It consumes structured public facts from the existing
task assessment turn. It does not read task wording, hidden grades, corpus
labels or reserved task IDs, make a new paid assessment call, invoke the
Controller, or dispatch a worker. The qualified B0 executor remains the
automatic route.

Supply `assess(facts)` with task kind, complexity, verification strength,
estimated context tokens, deadline, failure cause, previous local repair
count, frame confidence, required artefacts and public evidence references.
The schema rejects unknown fields and non-public evidence sources. The
evidence cohort hashes the structured facts, not the wording of the evidence
claims. The caller must ensure a claimed public source truly is public; the
schema cannot prove provenance by inspecting arbitrary text.

Call `select(assessment, supported_cells=..., remaining_usd=...,
budget_enforced=..., override=...)`. The host must positively declare its
supported cells and capped-call capability; the registry alone is not live
host proof. Every one of the 15 model/effort cells receives a row with
availability, qualification, historical or unknown cost projection, deadline
fit, eligibility and rejection reasons. The default prior is Sonnet low for
routine work, Sonnet high for moderate work and Opus high for complex work.
These are labelled experimental priors, not measured quality winners. The
response exposes viable alternatives across model and effort; it assumes
neither monotonic quality nor monotonic cost. It never credits unobserved
cache reuse as a saving. Historical per-task means are not current price
quotes or task-specific ceilings.

Missing facts stop for clarification. An uncertain task frame stops as
`unresolved_frame` because Controller framing is deferred. Context overflow
suggests decomposition. Infrastructure, permission, identity and accounting
faults block host repair, not model escalation. One observable local failure
may justify a bounded repair; a second stops. An override needs a cell, actor,
unique authority, reason and optional USD ceiling. Unsupported cells and
limits are rejected without substituting another model. Unknown projected
cost requires an explicit ceiling and a host that enforces capped calls.

`TaskExecutor.shadow_select()` records the selection and override provenance
in the root's hash-chained journal beside the B0 cell for the next attempt.
It checks remaining root budget and the frozen host capability. A decision
recorded during an active worker call concerns only a later attempt, and the
current reservation remains unavailable until settlement. Shadow records
never change B0 dispatch, attempt limits or the task budget. An operator may
inspect the record from `TaskExecutor.status()`; promotion to automatic
dispatch requires the later N5/N6 qualification gates.

The production adapter currently does not attest a complete supported-cell
set or capped-call enforcement through its capability record, so the shadow
selector cannot claim a live eligible cell from that record. N5 will screen
availability, identity and cost before an operational candidate is enabled.
Offline fake-host tests prove the 15-cell mapping, command pinning, journal
isolation, invalid input rejection and the failure taxonomy. They do not prove
served effort or live model quality.
