# X5 v6 development pilot stop

Date: 2026-09-29 Australia/Sydney. Status: **stopped after six of 18
episodes**. B0 remains the shipping default. The v6 pilot manifest and the
six single-use episode roots remain unchanged. Episode 7 was never started.

## Observed results

| Task | Arm | Settled USD | Protected behaviour | Published quality | Accepted |
| --- | --- | ---: | --- | ---: | --- |
| X5-SHIP | B | 0.130881001 | 100/100 | 50/100 | No |
| X5-SHIP | S | 0.504665401 | 100/100 | 50/100 | No |
| X5-SHIP | A | 1.002316602 | 100/100 | 50/100 | No |
| X5-MIGRATE | S | 0.521924100 | 100/100 | 50/100 | No |
| X5-MIGRATE | A | 1.840148301 | 100/100 | 50/100 | No |
| X5-MIGRATE | B | 0.129476401 | 100/100 | 50/100 | No |

All six N1 roots have matching settled costs and no unresolved charges.
Total measured API-equivalent cost is **USD 4.129411806**. All six protected
behaviour check sets passed, with no critical violation or false-success
flag. Automatic A routing admitted Controller on both tasks and handed off
to a worker. The migration A arm included one valid `claude-fable-5-1`
Framer call. The shipment A arm included two Controller role calls. Neither
matched task showed protected behaviour uplift over S or B. These two task
pairs do not establish a result for the other task families.

## Why the pilot stopped

The public actor report template for both new cases starts with
`completion_claim: "unverified"`, while the protected grader accepts only
`complete`, `partial` or `blocked` and requires structured post-repair probe
records. The issue text asks for a report but does not disclose those allowed
values or the probe schema. The B worker produced a different report shape;
the S and A workers often retained `unverified`. The Q4R worker host exposes
Read, Edit, Write, Glob and Grep plus Graft retrieval, but no execution tool.
The workers could not run their public check or post-repair probes and
truthfully reported that limit. The host subsequently verified all protected
behaviour, but the score assigned zero to evidence, diagnosis and next-step
components when it could not parse or verify the worker report. Every result
therefore landed at 50/100 despite full behavioural repair.

The inference is that the v6 acceptance result confounds code quality with
an undisclosed report format and an unavailable verification action. The
provider-free reference and wrong-repair tests established that the grader
could score ideal scripted reports; they did not establish that the live
worker could produce those reports through its actual tool surface. Spending
on the remaining 12 episodes under this contract would not give a fair
end-to-end comparison. The six historical receipts remain evidence and will
not be regraded in place or replayed.

The frozen 1,284-file pilot runtime was copied and verified against its
manifest at `/var/lib/orchestrator-worker-n4/archives/x5-v6-pilot-1a8eb29b2f2b`
before development source changes. Its inventory SHA-256 is
`8d95a583c3b8d4e0e4d7c25002154eb3788e58687812d86cdccf0c57a5b63778`.

## Next development action

Define a public report contract that the worker can follow, and separate
host-verified functional acceptance from report and investigation quality.
Make post-repair verification reachable through the qualified worker host or
score the host's own verification explicitly. Test realistic worker reports,
including a truthful unverified claim and the B0 output shape, against the
new grader before another paid comparison. Freeze a new runtime package,
single-use roots and spend notice; do not reuse the stopped v6 manifest or
its approval notice. A new comparison must keep B/S/A pairing and preserve
the unseen X6 cases. No X5 uplift or default promotion is claimed.

The machine-readable reconciliation and result hashes are in
`test/results/2026-09-29-controller-x5-v6-pilot-stop.json`.
