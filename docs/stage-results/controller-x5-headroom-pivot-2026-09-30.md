# X5 headroom decision after first-failure screens

Date: 2026-09-30 Australia/Sydney. Decision: **stop paid screens on the
current self-contained authored-regression pattern**. Retain B0 as the
shipping default. No X6 reserve is opened. This is a development allocation
decision, not a claim that Controller uplift is impossible.

## Observations

R3 R01, R4 R02, the P02 engineering smoke, and fresh F01/F02 development
cases each produced one terminal, writer-stopped first worker attempt. All
five passed their public check. Four scored 100 protected quality; R01 scored
85 with a critical protected miss that was unavailable as a public trigger.
The five settled receipts total **USD 0.597339801** reported API-equivalent.
No matched S/A first-failure pair was eligible. The fresh F01/F02 baselines
failed their public checks and had meaningful provider-free partial repairs,
yet Sonnet-low repaired both fully on the first live call.

The historical v7 X5 pilot provides a separate read-only context check:
the three X5-PAY arms and three X5-FEAT arms each made one worker attempt,
were accepted and scored 100 protected functionality. This is not new
prospective evidence for the first-failure design, but it reinforces the
observed first-call saturation in the current task class. The previous v7
four suitable pairs found no A-over-S quality gain; A cost 2.67 times S and
took 1.84 times as long on average.

## Inference and next candidate

The first-failure checkpoint is technically qualified but the selected
self-contained issues rarely reach it. Creating more two-module regressions
with a stated symptom and short public test is unlikely to yield a useful
Controller comparison. F01/F02 were source-backed and independently graded,
but their issue language still narrowed the likely repair. They do not meet
the stronger multi-hypothesis task-selection need identified in the prior
X5 candidate audit.

The next development set should contain genuinely competing, consequential
public hypotheses. For each task, freeze a public trace and at least two
plausible causes that require different source-level checks before editing;
remove cause-revealing comments from the actor; keep the reference and
protected edge cases outside the worker view. A provider-free audit must
reject a case if its public issue/source already identifies the fix. Include
ordinary-worker and missing-decision controls. The observable eligibility
rule remains a settled, writer-stopped public first failure; no hidden result
may open an arm. Both continuations get the same actor bytes, failed report,
worker model/call ceiling and tools. A alone gets the bounded Controller.

Freeze the full next-case list, arm order, analysis and cost notice before
the first model call. A bounded producer calibration slice should measure
entry frequency. If it again yields no public first failures, close this
route rather than paying for more copies of the same tasks. If enough
eligible cases arise, compare A minus S on protected acceptance, critical
errors, honest claims, cost and latency. A development signal is not a
promotion gate; X6 requires a separately frozen power and reserve contract.

## Untested risk

The live failed-report S/A path has passed fake-provider and WSL
provider-free checks but has never been exercised after a paid first
failure. Better task selection may still yield first-call success. A
Controller that has no new information may add cost and time without quality
gain, as v7 did. A selective review after public success is a different
prospective hypothesis and would require its own public-only entry rule,
separate cost accounting and fresh cases; R01's hidden miss cannot be used
to select it retrospectively.

## F03 follow-up

F03 adapted a public Tenacity cancellation incident, removed its explicit
diagnosis from the actor issue and added a second repair layer. It passed the
provider-free baseline/partial/reference audit and the 83/83 offline gate.
Its one new producer then passed public and protected acceptance on the first
call, settling USD 0.2023272. The six first-call screens now total USD
0.799667001 with no eligible S/A pair. The first-failure-only route is closed
for further screens of this task shape. Its mechanism remains available for
genuinely different tasks, but no Controller uplift or X6 admission follows.
