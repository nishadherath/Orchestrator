# X5 recovery R4: dated spend notice

Date: 2026-09-30 Australia/Sydney. Status: **approved and completed**.
The frozen R4 manifest is
`test/results/2026-09-30-controller-x5-recovery-feasibility-r4-manifest.json`,
identity `12bcbc9ae48f016196867b46b298915dae7e29ea935c8e37a73f83ad59539b23`.
The 83-check full prelaunch harness passed. The single R02 B0 root is ready
with zero provider calls and zero spend. Its source package and the isolated
Controller host capability passed provider-free preflight.

R4 tests the already-authored, unrun R02 development case. It is a separate
single-use continuation after the stopped R3 campaign, with no R3 root or
receipt reused. R02 was frozen before the R01 result was observed. Its
producer enters a matched S/A continuation only for a settled public check
failure or an explicit partial or blocked report containing a concrete
unresolved test. A public success cannot qualify because of a later protected
grade. If R02 has no public headroom, the screen ends after its producer.

At most three roots may run: one B0 producer, then S and A from identical
frozen public bytes if eligible. Each has a USD 5 API-equivalent ceiling, so
the absolute maximum is USD 15. A's Controller, public assessment and worker
spend share its root ceiling. The projected API-equivalent total is USD
0.2–6, based on the R3 producer receipt and earlier X5 receipts. The token
mix is unknown and no cache discount is assumed. Claude.ai subscription
billing may differ from the API-equivalent receipts.

The protocol stops for source drift, replay, unresolved accounting, invalid
identity, nonmatching twin snapshots, or a Controller handoff without a
code-cited finding and concrete next check. R4 remains development evidence;
one case cannot establish Controller uplift or authorise X6. The X6 reserve
remains sealed and B0 remains the default.

The paid entry point requires a dated notice bound to this exact manifest.
The user approved the planned tests, including this prepared R4 scope and
ceiling. The notice has `approved: true` and records that approval source.
The R02 producer settled USD 0.1179006 API-equivalent and was ineligible for
recovery; no S/A root ran. See
`controller-x5-recovery-r4-result-2026-09-30.md`. Do not replay R4.
