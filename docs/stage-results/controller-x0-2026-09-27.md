# X0: Controller contract and evidence revalidation

Date: 2026-09-27 Australia/Sydney. Status: **X0 complete; all 79 offline checks
passed**. The operator directed execution after
the Astra / High transition request. This records the requested setting;
the host does not independently expose the exact model or effort.

Checkout: branch `v1.0-rc1`, HEAD `15ecf66`, with pre-existing uncommitted work
preserved. The requested X0 setting is recorded without a model-identity claim.

## Scope and result

X0 reproduced all six planned defect classes and one additional accounting
projection defect, using injected adapters and disposable directories. It
froze the [integration/evaluation contract](../CONTROLLER-REMEDIATION-CONTRACT-X0.md)
for X1-X8. No Controller runtime, worker policy, registry, consumer source,
historical campaign manifest or paid output was changed. B0 remains default.
The Controller defects are still present and assigned to their implementation
stages. Passing X0 means the defects and repair contract are characterised,
not that the Controller is qualified.

## Reproduced observations

The [probe receipt](../../test/results/2026-09-27-controller-x0-probes.json)
binds the source hashes and records these results:

| Finding | Observation | Owner |
| :--- | :--- | :--- |
| Terminal restart | Matrix and pilot each returned stopped after sequence 1; a second execute admitted sequence 2. Both fake charges were settled. | X1 |
| Incomplete binding | Each validator accepted mutations to nine omitted files while correctly rejecting the bound-file control. Its existing inventory has 15 files. | X1 |
| Unearned credit | A C01-D1 answer built only from materialised public labels scored accepted/100; only result.json was added, with all original files unchanged. | X3 |
| Assessment bias | Identical actor, problem and revision routed to Controller under private family C01 and to worker under N01. | X3/X4 |
| Canned clarification | N03-D1 arm A scored accepted-clarification/100 with zero worker or Controller calls. The pilot wrote the answer itself. | X3/X4 |
| Collapsed Generator | The frontier profile configured three Generator cells, but all three technique calls reached the provider boundary as Sonnet high. | X2 |
| Duplicate admission | Concurrent auto and on decisions for one revision admitted two Controller calls, each with USD 4 fake allowance. Replaying one unchanged decision admitted zero further calls. | X2 |
| Lost cost projection | The durable budget held settled spend of USD 0.25 with no uncertainty; the blocked pilot episode reported cost null and accounting incomplete. | X1 |

All monetary observations above are fake accounting units. Actual provider
calls and new Claude experiment spend were zero. The probes do not establish
that a paid historical run suffered these failures. The dependency mutation
probe tests validator acceptance, not execution of the mutated copied code.
The nine examples are not an exhaustive dependency audit.

Source-inspection observation for X8: the maintained Controller guide says the
production Controller cannot select the frontier profile, while the R4 adapter
already accepts and forwards that profile. Its Generator diversity is what the
probe shows missing; live quality remains unqualified. Correct that distinction
when updating the consumer guide. Quick mode also closes under Librarian
ownership in code; a registry assignment does not imply a Librarian model call
or implemented deep-mode/cross-run library learning.

## Contract decisions

Use the N1 executor as the only root lifecycle/budget owner. Bind legacy
Controller identities to its immutable task revisions. Persist intervention
admissions under a task lock so changed decisions cannot reset invocation
limits. Preserve cancellation across late receipts, reconcile costs without
dispatch and retain writers/holds until their disposition is proven.

X3/X4 must add a shared production public-evidence bridge: N3 currently
validates supplied facts and cannot substitute for evidence collection. The
same bridge, worker policy and acceptance path must serve production and
evaluation. Controller findings are untrusted evidence, never new acceptance
or operator authority. Interactive auto/on/off uses the existing control
precedence at admission boundaries.

X1 binds a complete runnable package and host attestation, including dynamic
data dependencies; static imports alone are insufficient. X3 isolates actor
execution from trusted score calculation and serialisation, with adversarial
tests informed by N7's monkeypatch exploit. X2 uses named technique-to-cell
assignments rather than the first configured Generator for every call.

## Feasibility and cost decision

The [prospective analysis](../../test/results/2026-09-27-controller-x0-power.json)
evaluated hypothetical outcome distributions, not actual Controller quality.
Zero candidate-only harms among 24 independent tasks leaves an exact one-sided
95% upper bound of 11.735%; a zero-event upper bound below 5% requires at least
59 independent tasks. This is not proof that 59 supports the full gate set.

For 16 suitable tasks, a mean quality improvement of 6/100 cleared the proposed
strict lower-bound >5 quality gate in only 2.3-4.7% of simulations. Even a
13/100 assumed improvement cleared it in 47.2-53.5%. Correlation within the
eight suitable families reduced interval coverage in tested scenarios. The
receipt supplies seeds, Monte Carlo error and exact directional-test sensitivity.

**Keep the 24-task/96-episode X6 comparison exploratory, with no automatic
promotion authority.** This is the explicit small-sample disposition allowed
by X0's stage contract. Do not increase spending or lower thresholds to force
a release claim. A promising result can justify a separately frozen extension
with an explicit cost/sample decision. X7/X8 can still qualify mechanics and
safe labelled manual use. B/S execution may be aliased to save calls only
when their entire treatment fingerprints match and the alias is frozen before
scheduling. Count the shared observation and its cost once.

## Verification

- `python -B tools/controller_x0_probe.py --output
  test/results/2026-09-27-controller-x0-probes.json` exited 0 and produced eight
  characterisation records covering the six classes plus clarification and
  accounting details. It made zero provider calls.
- `python -B tools/controller_x0_power.py --output
  test/results/2026-09-27-controller-x0-power.json` exited 0. Six scenarios used
  600 synthetic samples and 400 hierarchical resamples each. Exact harm bounds
  and sign-test power were also calculated.
- `python -B test/harness/controller_x0_tests.py` passed six tests, including
  invalid sample rejection, strict margin behaviour, reproducibility, exact
  zero-event boundaries and unchanged historical manifest bytes. The suite
  is included in the full harness as `CTRL-X0`; it does not assert defect closure.
- Full `python -B test/harness/check.py --json` aborted after 936.98 seconds
  when the existing Q4 screen test exceeded its 90-second outer timeout. The
  [first-attempt receipt](../../test/results/2026-09-27-controller-x0-harness-attempt1.json)
  preserves that failure; no full JSON check report was emitted.
- The focused Q4 suite then failed in setup after 30.261 seconds because its
  WSL runtime-hash check timed out. Static host evidence and source hashes
  validated; a longer read-only installed-hash diagnostic returned the expected
  hash in 25.81 seconds. The [focused rerun](../../test/results/2026-09-27-controller-x0-q4-diagnostic.json)
  then passed all four tests in 68.820 seconds (69.64 seconds including startup).
- The Q4 harness watchdog now permits 180 seconds for its three individually
  bounded 30-second WSL hash checks plus fixture I/O. Production guards and
  test assertions are unchanged. A watchdog expiry now records a failed check
  rather than aborting before JSON reporting.
- The second full gate aborted after 807.67 seconds when the existing N5
  live-screen suite exceeded its 420-second watchdog. The
  [second-attempt receipt](../../test/results/2026-09-27-controller-x0-harness-attempt2.json)
  preserves the failure. That suite contains three nearly complete fake
  60-row schedules, not one. Its watchdog now permits 900 seconds and reports
  expiry as a failed check. No schedule row, assertion or production timeout
  was changed. Injected timeout checks verified that both corrected watchdogs
  report failure. The [focused N5 run](../../test/results/2026-09-27-controller-x0-n5-diagnostic.json)
  passed all eight tests in 494.363 seconds, confirming that the former bound
  was insufficient on this host.
- The [final full gate](../../test/results/2026-09-27-controller-x0-harness.json)
  passed all 79 checks with zero failures or skips, exit 0, in 1,343.20 seconds.
  It invoked the unchanged harness entry point with a reporting-only progress
  callback; every check executed. The receipt binds the harness source hash.
  This includes `CTRL-X0`, both corrected watchdog suites, adversarial corpus,
  historical replay, bundle parity, installer and handoff checks. There were
  zero provider calls. Both earlier aborted attempts remain preserved.
- The reproduction receipt's nine source hashes and the feasibility receipt's
  two tools-relative hashes matched the X0 source snapshot. X1/X2 subsequently
  changed runtime source; the historical receipts were not rewritten. Twelve
  new-document local links resolved at X0.

Graft freshness timed out. A later scoped call also timed out, then recovered
on retry. Scoped MCP retrieval supplied the relevant APIs/source spans. Semantic completeness
was not established. No paid semantic retry was performed. Existing protected
WSL campaign evidence required the full offline harness to run outside the
filesystem sandbox under the project's standing verification authorisation.

## Remaining work and next action

Use the validated [X1 handoff](../../handoffs/2026-09-27-controller-remediation-x1.md)
and set GPT-5.6 Sol / High. X1 repairs campaign terminal handling, complete
execution binding, duplicate-driver protection, reconciliation and failed-cost
projection. X2-X8 remain unstarted. X0 does not close any implementation defect.
Keep shared historical replay source intact before modifying live modules.
No commit, merge, tag, push or publication was performed.
