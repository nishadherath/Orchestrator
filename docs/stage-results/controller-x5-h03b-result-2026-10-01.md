# X5 H03b result, 2026-10-01

## Decision

H03b stopped after one settled B0 attempt costing USD 0.184233601 in the
local ledger. Its repair failed the frozen public check, so the public-risk
review entry condition was not met. No risk review, S continuation or A
Controller continuation ran. There is no matched Controller effect or uplift
claim. B0 remains the shipping policy. Do not replay H03b or resume its ready
executor root as part of this pilot.

The operator explicitly approved the 52-file, 879,471-byte B0 input and
conditional 56-file reviews within USD 16. The approved manifest is
`218e0f70b4f2e80a313b07c90cd0275ce65416b4a1ce12a8c82ab8724b5c02f8`.
The unused ceiling does not waive the manifest's eligibility rule.

## Observed result

| Item | Evidence |
| --- | --- |
| B0 root | `0475ead5cd55ed149d3747cf` |
| Attempts | One, terminal writer, identity valid |
| Served root model | `claude-sonnet-5` |
| Requested effort | Low; served effort telemetry unavailable |
| Worker wall time | 41.999747 seconds |
| Public acceptance | Failed, command exit 1 |
| Protected actor files | All 51 unchanged; only the allowed Controller file changed |
| Protected quality | Unscored: the frozen grader raised an exception |
| S/A calls and spend | Zero |
| Budget | No unresolved charge or breach |

The provider reported USD 0.18423360000000003; the ledger conservatively
recorded USD 0.184233601. Usage was 18 input tokens, 28,771 cache-write input
tokens, 176,058 cached-read input tokens and 3,259 output tokens. This is
reported API-equivalent subscription usage, separate from the development
session estimate, and not an invoice claim. The receipt includes both the
Sonnet root and a billed Haiku helper; no child worker was observed.

The worker's structured report labelled the work `partial`, said the public
command was `not_run`, and disclosed that no shell/execution tool was
available to it. This matches the frozen Q4U launcher's required built-in
tool list, `Read,Edit,Write,Glob,Grep`, plus the six Graft retrieval tools
(`tools/worker_wsl_namespace_q4u.sh:112`). The host then ran the frozen public command independently
inside the credential-free Q4U verification namespace. There was no unsupported
worker claim that this command passed.

## Public failure diagnosis

The exact patch adds a correction loop after the initial Framer batch has
already been committed. A provider-free observer reran the unchanged public
check against the hash-verified stopped source and captured the temporary
ledger before cleanup. It recorded two Framer calls, two Verifier calls and
12 committed records. The first committed frame contained both
`fix the duplicate` and the unauthorised `check every related path`; the
second contained only the correct criterion. The run then raised
`AssertionError: selftest script exhausted for (phase='verify', role='verifier')`.

This establishes a violation of the public immutable-criterion requirement
independently of how a future grader handles the exception. A correction
after commit does not remove the invalid committed frame. The evidence does
not establish that a Controller continuation would repair it better than an
ordinary worker continuation.

## Measurement limitation

The frozen private oracle raised the same Verifier-script exception before
returning its aggregate result. Its quality score and critical-error field
remain unavailable; they are not assigned zero or inferred from a different
grader. The public invariant violation above is a separate observation.
The oracle source, manifest and paid actor were preserved unchanged.

The case is an authored retrospective reconstruction and cannot support a
population uplift or default-promotion claim. Its stopped source is now seen
development evidence. The private grader is not qualified against malicious
candidate introspection, as already stated in the preflight.

## Verification and next design requirements

The full offline harness completed with 82 passing checks, including DIST,
RELEASE and HANDOFF, and one PROSE failure for a US spelling in the handoff's
cost estimate. That spelling was corrected. The complete original result is
`test/results/2026-10-01-controller-x5-h03b-result-harness.json`; the focused
post-correction PROSE and HANDOFF result is
`test/results/2026-10-01-controller-x5-h03b-doc-checks.json`. No runtime code
changed after the full run. The installed credential-store `inspect` also
exited 0 after the producer, confirming freshness and no unreconciled session.

A separate provider-free admission calibration found exact float equality
between receipt cost and rounded ledger cost in `accepted_producer`. Using
the authentic receipt and settled budget, but counterfactually setting the
state and public verification to accepted/pass, that frozen function rejects
the producer. Normalising the receipt to the ledger's USD 0.184233601 makes
the same counterfactual pass. This did not cause H03b's actual public failure.
The next gate must compare costs using the ledger's canonical integer units
and retain the identity, finality and budget checks. H03b's runner is unchanged.

Before another paid candidate, make the next oracle produce a bounded result
for each failed or exceptional scenario, with a separate infrastructure-error
status. Calibrate it against this stopped patch as an explicit development
negative control without changing H03b's historical grade. Predeclare both
public-failure and public-success-with-residual-risk entry branches before
the next producer, with identical public evidence and acceptance in S/A.
Use the existing host verifier to provide the complete first-attempt public
result to both continuation arms. State that workflow explicitly in the worker
brief, since this runtime has no worker execution tool. A matched second worker
attempt can then receive real verification feedback without adding general
shell access. Freeze a new runtime, manifest and schedule before
spending. None of these changes authorises replaying H03b or treating it as a
reserved task.

## Evidence files

- `test/results/2026-10-01-controller-x5-h03b-pilot-cost-notice.json`
- `test/results/2026-10-01-controller-x5-h03b-pilot-run/producer-result.json`
- `test/results/2026-10-01-controller-x5-h03b-pilot-run/B0-analysis.json`
- `test/results/2026-10-01-controller-x5-h03b-pilot-run/B0.patch`
- `test/results/2026-10-01-controller-x5-h03b-pilot-run/B0-public-diagnosis.json`
- `test/results/2026-10-01-controller-x5-h03b-pilot-run/cost-equality-diagnosis.json`
- `test/results/2026-10-01-controller-x5-h03b-analyse.py`
- `test/results/2026-10-01-controller-x5-h03b-public-diagnosis.py`
