# X5 P02 first-failure engineering smoke: dated cost notice

Date: 2026-09-30 Australia/Sydney. The operator approved all planned tests
until the work is done. This notice binds that approval to manifest
`dc2dfd1953832b107a4333b1d80d3b72cd50ad8d74d46645eb68577dbf1c2353`.
The [machine notice](../../test/results/2026-09-30-controller-x5-first-failure-p02-smoke-notice.json)
is the paid gate. The [manifest](../../test/results/2026-09-30-controller-x5-first-failure-p02-smoke-manifest.json)
fixes the P02 actor, protected oracle digest, runtime package, host, order,
model policy and local allocations.

Scope: one B0 producer call stopped after its first verified public failure.
Only if that call is settled and publicly eligible, S gets one Sonnet-low
repair call. Only if S settles, A gets one public assessment, one bounded
Controller investigation and one Sonnet-low repair call. The three roots each
have a USD 5 local task ceiling, giving a **USD 15 maximum local allocation**.
No root or provider call is replayed after its started marker. P02 is a known
public canary and cannot contribute to a prospective uplift estimate. X6
remains sealed.

Projected reported API-equivalent usage is **USD 0.3–6** across the conditional
sequence. This range uses P02's earlier two Sonnet-low calls (USD 0.355438002)
and the v7 Controller-arm receipts as empirical scale, with allowance for
variation in task duration and Controller role calls. It is not a subscription
invoice estimate. The host may not expose served effort; model identity,
terminality, writer stop, public verification and cost settlement are checked
separately. Actual reported costs will be recorded after each attempt, and
any uncertain charge stops the sequence.

The provider-free preflight passed: P02 baseline failed public acceptance and
scored 30/100 protected quality; the reference passed both and scored 100/100.
The public assessment packet has five sources, three exact citations and
27,796 bytes. The full repository offline harness passed 83/83. The frozen
WSL root and Controller Graft preflight prepared one producer with zero
provider calls.
