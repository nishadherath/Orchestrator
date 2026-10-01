# X3: executable Controller corpus and paired offline campaign

Date: 2026-09-28 Australia/Sydney. Status: **complete for the offline X3
scope**. The operator previously confirmed GPT-5.6 Sol / High; this host does
not independently expose the active model or effort. B0 remains the shipping
default. No Controller quality uplift or automatic-default qualification is
claimed from this stage.

## Corpus and protected evaluation

The [X3 progress record](controller-x3-progress-2026-09-27.md) describes the
48 executable tasks, with 24 development and 24 newly reserved tasks across
12 families. The inventory reported 48/48 ready, zero pending, with digest
`d308433b770d107fcfe330a982a2ee8499bb3e6a11a5dfb62da03372f233f118`.
Public actor packages contain the code and observations needed for the task;
protected oracles are separate. The
[protected sweep](../../test/results/2026-09-27-controller-x3-full-protected-sweep.json)
passed 288 controls across all 48 tasks. These include reference, equivalent,
partial and negative variants, and distinguish demonstrated partial progress
from acceptance. The
[actor-isolation sweep](../../test/results/2026-09-27-controller-x3-full-isolation-sweep.json)
passed 672 checks across the same 48 tasks. Both sweeps recorded zero provider
calls. Isolation is established for the tested WSL host and threat probes,
not every future host or attack.

The common public assessor uses bounded public source packets and validates
exact source citations. Hidden family/split metadata cannot influence its
assessment while the public package is fixed. X3 source sealing covers the
first-party runtime, public fixtures and protected oracles; mutation of an
actor generator or oracle blocks campaign verification. The X3 campaign does
not expose the protected oracle to either arm.

## Frozen production-path fake campaign

The current [candidate manifest](../../test/results/2026-09-28-controller-x3-fake-manifest-v8.json)
has SHA-256
`54e006bc2bd43481322bbb9d1b3051e1475b81ff33dd7a4782d014eeef5fa52f`.
It binds the complete runtime package, inventory, schedule and controlled
adapters. It admits only 1-6 development task IDs, rejects reserved tasks,
and alternates S/A order. A sealed source mutation is rejected even when a
caller recomputes the manifest's own digest. The v8 manifest validated against
the current runtime after the checked build.

The fresh [four-episode receipt](../../test/results/2026-09-28-controller-x3-fake-campaign-v8/state.json)
ran two paired development tasks through `controller_workflow.execute`, the
N1 public-assessment admission, N3 worker selection, the frozen N1 root,
Controller handoff when selected, worker dispatch and independent acceptance.
Each pair has identical public source and citation hashes. All four episodes
ended accepted with complete accounting and one worker attempt; all recorded
zero actual provider calls. The synthetic charges were USD 0.14 for both
N04-D1 arms, USD 0.14 for C03-D1 S and USD 0.34 for C03-D1 A. N04-D1 used
worker-only in both arms; C03-D1 used Controller in A and worker-only in S.
Those are transport and accounting observations, not measured quality or
cost. The fake C03-D1 interpreter was controlled to trigger Controller;
earlier live public assessment had routed that task to worker-only.

`tools/controller_x3_manifest.py` and
`test/harness/controller_x3_fake_campaign.py` are development-only campaign
tools, not consumer bundle files. Their two focused tests passed. The full
checked `python3 tools/build_dist.py` gate exited zero after the new campaign
tests were included in `test/harness/check.py`, and regenerated `dist/`.
The builder initially found generated actor reports with CRLF under
`test/results/`; the prose check now excludes campaign actor execution
outputs while retaining authored result documentation. The v2-v7 manifests
and receipts remain historical evidence: X4's installed test, complete
acceptance handoff, N1 per-call cap and Graft-qualified Controller role host
changed their bound source package. The v7 campaign completed under its
then-current source with zero provider calls. The v8 campaign completed after
the latest checked build, including installed auto/on/off smoke coverage,
under the current source with zero provider calls.

## Cost, limits and next action

The X3 fake campaign and protected sweeps made **zero provider calls**.
Synthetic USD amounts above are assertions of accounting behaviour, not paid
spend. The development-session direct API charge is unavailable; unknown is
not zero. The staged plan's X3 forecast was 6-12 engineering hours under the
[execution protocol](../REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md), not a
measurement of this stage's elapsed time.

X3 proves offline corpus, isolation, assessment-path and paired accounting
readiness. It does not prove the live assessor's task-sensitive accuracy,
Controller quality uplift, served effort, or a production Controller-to-worker
result. X4 must complete installed interactive auto/on/off, live role host and
worker continuation, partial-gap handling, cancellation/restart and budget
qualification before X5 paid comparisons. X5 must measure the actual
Controller admission rate rather than inferring it from fake task labels.
