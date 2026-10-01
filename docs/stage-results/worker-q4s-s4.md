# Q4S S4 balanced public screen: stopped after S03

Date: 2026-09-26 UTC. Status: **stopped under the frozen invalid-transport
rule; 3 of 18 episodes and one of six families completed**. No S4 policy
qualification or population-level routing claim is available. The shipping
B0 default, Controller boundary, M4 and Q5 remain unchanged.

## Frozen scope and admission

The S2 parent manifest is
`test/results/2026-09-26-worker-q4s-screen-manifest.json` at digest
`c8e5b7e6370eb46011551d48d56a8bc9905eb13b50ac3798f8ab414ac50bd8b1`.
The corrected S4 child manifest is
`test/results/2026-09-26-worker-q4s-s4-manifest.json` at digest
`5d51db8eed091668d984351ceba87f3b7bc531803b0f82743e2623ddb9e1e144`.
Its exact approval permits at most 18 episodes, 54 provider calls and USD 72
in local allocations. The dated planning estimate was USD 6–30 in direct
API-equivalent usage and 2–7 hours; Claude Code subscription invoice impact
is unknown. The S3 two-call canary had passed before S4 admission.

The campaign journal at
`test/results/2026-09-26-worker-q4s-s4-run/campaign.json` is root-owned,
sealed at state digest
`963e7c1849b1b097c1b3cdd897a637a7cfed273d6fb960ecdd5162dec0eee11f`.
Its provider-free preflight proof digest is
`9a8ea70f7736278ae1628350a8c5ba94e02998dc3242a160843cc7479d8ea95b`.
All three S03 arms started from separate pristine actor workspaces. Each
has one terminal, stopped and charged Sonnet 5 call, a protected-source check,
an isolated public check, a hidden executable grade and a preserved patch.
No invocation was replayed.

## Observed S03 results

S03 was a preclassified trigger-positive h11 family. Scores are the frozen
quality-v2 points; executable score is the protected behaviour check, not
the report score.

| Arm | Root | Public | Executable | Quality-v2 | Hidden accepted | Report | Cost USD |
| --- | --- | --- | ---: | ---: | --- | --- | ---: |
| B0 A, Sonnet-low | accepted | pass | 100 | 90 | yes | present | 0.209838601 |
| B0 B, Sonnet-low | accepted | pass | 75 | 80 | no | present | 0.140356000 |
| Sonnet-medium | blocked | pass | 100 | 80 | no | transport-invalid | 0.230938600 |

The two B0 repetitions disagree on hidden acceptance and differ by ten
quality points. Any later Q5 design therefore needs the predeclared two
reserved repetitions. The medium patch passed every protected executable
case, including the invariant B0 B missed, but received zero diagnosis and
report points because no valid structured report arrived. It has no hidden
acceptance. None of the three grades recorded a critical error or unsupported
completion. The three sealed grade digests, in arm order, are
`5ee912604cd52ffd4eeeb19e0feb212a559a9820ca72424d19cdbfdcb9497f34`,
`06d91c53819289f45a1a7d70a011a722843b209281358611818f47deb7cc75b5`
and `b9de1ad8ff553eda9315cb3906f9da809985ae4600244b1ec2d8943936fac31a`.

The medium call used the requested `claude-sonnet-5` root model with valid
model identity, one terminal stopped writer and a settled USD 0.2309386
charge. Its final CLI subtype was `error_max_structured_output_retries`,
return code 1, after 14 turns. The final event lacked `structured_output`;
the stream had zero invalid JSON lines and no captured stderr bytes. The
provider reported 32,802 cache-created input tokens, 216,368 cache-read
input tokens and 5,511 output tokens. Billing metadata listed Sonnet 5 and
Haiku 4.5, while the real root model list contained only Sonnet 5 and no
child models. This does not establish a model substitution or a served effort
level. B0 A and B0 B both returned a `success` subtype and a structured
output field, in 15 and 10 turns respectively.

## Stop, cost and limits

The frozen S2 manifest says to stop on invalid transport and to score a
settled missing structured report without replay. The runner applied that
rule after the complete S03 family and sealed all three grades. It did not
start S02 or the other four families. The S4 total is **3 provider calls and
USD 0.581133201 provider-reported API-equivalent cost**, against the USD 72
local allocation. Actual subscription invoice impact is not measured.

The prose S4 plan can also be read as allowing a terminal invalid report to
be scored and then continuing. The frozen manifest explicitly calls for a
stop on invalid transport. Do not reinterpret that rule after seeing S03 or
append the unstarted families to this campaign. Resolve the wording and
transport policy prospectively in a new reviewed manifest if more public
testing is authorised. A later campaign must retain this entire S03 outcome
as development evidence and cannot replay these three invocations.

The exact root cause of Claude Code's exhausted structured-output retries is
unknown from bounded event metadata. The medium arm's executable success is
evidence of useful code repair despite the reporting failure; it is not
evidence that medium is safe to route by default. Six-family cost, quality,
report-validity and acceptance comparisons remain unmeasured.

## Verification and operational note

Before paid dispatch, the corrected S4 manifest check passed, the isolated
Claude.ai auth and Q4S adapter probes each passed with zero provider calls,
the focused S4 suite passed 5/5, and the full offline harness passed 77/77
with normal host access. The Windows-only coordinator guard was added after
an earlier provider-free launch from inside WSL failed. A later Windows
preflight found an expired WSL access token even though `claude auth status`
reported logged in; the operator completed the browser sign-in and the
checked sync helper promoted it. Both preflight stops created no campaign
journal or provider call. Their preserved evidence is in
`worker-q4s-s4-preflight-blocked-2026-09-26.md` and the corresponding
`test/results/*preflight-blocked*.json` files.

After the stop, the campaign journal seal verified, all three rows remained
graded with preserved snapshots, the cost and call totals reconciled, and no
Claude Code process remained active in WSL.

Next action: review this stopped result and decide whether to design a new,
source-bound structured-report transport experiment. Preserve B0 as the
shipping policy while that work is assessed. Do not proceed to S5's
six-family selection decision from these three episodes.
