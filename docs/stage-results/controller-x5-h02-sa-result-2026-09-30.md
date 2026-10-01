# X5 H02 matched continuation result, 2026-09-30

## Decision

The authored H02 S/A continuation measured no Controller quality gain and
does not qualify a promotion. Both workers failed the isolated public check
and scored 30/100 protected quality. The observed A-minus-S quality difference
is zero. A cost USD 0.6434197 more than S and failed the predeclared
actionable-handoff condition, so the primary paired-uplift criterion is not
qualified. Do not replay either arm or revise the frozen score. B0 remains the
shipping default.

## Settled observations

Both arms started from the same 159-file, 2,452,408-byte post-H02c public
failure snapshot under manifest
`c09983df46b2c38f5d746d7d5fb6f6bf71c3b94328f90db13d3ef9da9620a5f4`.
The operator specifically authorised this payload to Claude.ai after the
automatic approval review rejected the broad test approval. The full
prelaunch offline harness passed 83/83. No root was replayed.

| Arm | Public | Protected | Qualified | Reported API-equivalent |
| --- | --- | ---: | --- | ---: |
| S, direct Sonnet-low | Fail | 30/100 | Yes | USD 0.406186401 |
| A, Controller then Sonnet-low | Fail | 30/100 | No, handoff not actionable | USD 1.049606101 |

The pair settled USD 1.455792502 against its USD 10 hard cap. A's USD
1.049606101 comprises USD 0.037994 for public assessment, USD 0.644317501
for Controller, USD 0.3672946 for its worker, and a USD 0 verification hold
released after the handoff. Both worker receipts report Claude Sonnet 5,
valid identity, terminal completion and a stopped writer. The Controller's
two Framer calls report valid worker-opus-high identity and settled budget;
one used Graft freshness and file API, and the other used Graft freshness.
The earlier H02c producer cost USD 0.5318208, separate from the pair cap.

A was explicitly routed to Controller. Its dispatch reached `worker-ready`,
then the worker ran exactly once. The Controller packet ended as a provisional
`gap`. It contained useful source observations, but its safe next action was
"Restore the frozen acceptance criteria before continuing." This did not
identify an executable repair in `pytest_asyncio/plugin.py` or a concrete
public test step for the worker, so the frozen actionable-handoff check failed.
The A worker's subsequent edit also failed the public check. The grader's
forward and reverse cases failed in both arms; the no-hook and upstream checks
passed.

## Diagnosis and limit

The externally frozen `ProblemRecord` had one acceptance criterion: "The
isolated public check passes." The accepted Framer `FrameRecord` expanded it
to four criteria covering the public command, both execution orders, loop
factory selection and the edit boundary. The integrity check compares the
lists exactly. It stopped the Controller at `no_improvement` after two Framer
calls, before Verifier or Generator could run. This explains the generic
handoff. The current read-only Controller host also did not execute the
public check; its packet left the reported setup failure unverified.

The mismatch is an observed integration failure, not evidence that a
fully admitted Controller investigation could not solve the task. The two
workers' equal score is an observed outcome for this single authored case.
The public upstream issue and PR disclose the repair, and the case is not
blind natural-task evidence. There is no justified X5 default change or X6
entry from this result.

## Provider-free repair after the result

The Controller now asks the Framer to echo externally frozen acceptance
criteria exactly. It checks each Framer batch before the Scribe commits any
record. A mismatch gets one bounded correction request for the complete
batch; a second mismatch closes as a gap with the external criteria still
listed as unmet. The focused integrity suite passed 12/12, including
correction and persistent-mismatch cases. This repair was made after the
paid pair and does not change its outcome or qualify a replay. The checked
distribution build passed, the bundled Controller matches source by SHA-256,
and the final full offline harness passed 83/83. Its machine result is
`test/results/2026-09-30-controller-x5-h02-postbuild-harness.json`.

## Next development work

On a fresh case, freeze a complete external acceptance contract and give both
arms the same verified public-failure evidence. Do not reuse H02's roots,
manifest or dated notice. A new prospective comparison needs its own
admission and cannot treat this provider-free repair as measured uplift.

Evidence: `test/results/2026-09-30-controller-x5-h02-sa-run/analysis.json`,
the adjacent `S-result.json` and `A-result.json`, the immutable root receipts,
and `test/results/2026-09-30-controller-x5-h02-sa-analyse.py`.
