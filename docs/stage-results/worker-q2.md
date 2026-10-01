# Q2: public worker-qualification material

Date: 2026-09-25. Status: **Q2 provider-free work complete for operator
review; Q3 has not started**. Branch `v1.0-rc1`, HEAD `15ecf66`. B0, the N5
results, the sealed N6 R tasks and existing dirty worktree were preserved.
The [Q2 sampling protocol](../WORKER-QUALIFICATION-PROTOCOL-Q2-2026-09-25.md)
defines the future reserved-source rule and the proposed Q3 canary amendment.

## Acceptance evidence

| Criterion | Observation | Limit |
| :--- | :--- | :--- |
| Public multi-file target material | Two independent upstream families at pinned commits, with included MIT/BSD-3-Clause licences, 1,647/1,176 clean Python source lines, two authored edits each and a frozen byte catalogue. Vendored upstream source and licence bytes matched local clones at those commits. | These are authored regressions, not upstream issues, and are public development material only. |
| Public/hidden grading | In six fresh Q1 WSL actors, baseline/partial/reference scored P01 **10/55/100** and P02 **30/60/100**. Both references passed public and hidden checks; both partials improved hidden quality without acceptance. P02 baseline and partial flagged a critical token-time error. | The P01 concurrency check uses a short scheduling window; repeated calibration is needed to measure flakiness. No worker solved either task in this stage. |
| Isolation and evidence | The actor's attempted direct read of each root-owned oracle was denied. Each public/hidden case ran in a fresh actor; protected files and source copies stayed unchanged. Offline validation binds catalogue, oracle, runtime and recorded case/score evidence. Four adversarial offline tests reject rewritten score, acceptance and false-success fields even if the outer digest is renewed. | A digest is local integrity evidence, not a signature against full filesystem rewriting. This does not validate a paid multi-file adapter. |
| Corpus independence | Historical D/H fixtures were inspected and found to be only about 13-90 Python source lines. They were excluded as target-stratum task units. P01 and P02 are two families, not six tasks because each has three variants. | Q0's eight-task public gate cannot be applied with two families. |
| Provider accounting | The Q2 grader reports **zero provider calls and USD 0 provider-reported cost** across all six runs. | Development-session API usage is not exposed by this host and is not asserted to be zero. |

The machine-readable [catalogue](../../test/fixtures/worker_q2_public/catalogue.json),
[oracle cases](../../test/oracles/worker_q2_public/) and
[result](../../test/results/2026-09-25-worker-q2-public.json) are frozen by
their source and evidence digests. The result digest is
`1bf637a995500a248703592cf7f0a75f58b5de6ecf04c7bf20f2f509187ffc62`.
The relevant project-side code is `tools/worker_q2_public.py`,
`tools/worker_wsl_q2_case.py`, `tools/worker_wsl_q2_verify.py` and
`tools/worker_wsl_q2_install.sh`. The offline harness includes Q2 catalogue,
evidence and adversarial checks. No consumer `src/` or generated `dist/` file
changed in Q2.

Focused commands and outcomes:

```text
wsl.exe -u root -- bash .../tools/worker_wsl_q2_install.sh
  exit 0; Q1/N5 binaries untouched
python tools/worker_q2_public.py --run
  PASS: 6 isolated public/hidden grades; provider_calls=0
python tools/worker_q2_public.py --check
  PASS: 2 public task packages match their catalogue
python tools/worker_q2_public.py --check-evidence
  PASS: 6 grades match frozen source and oracle
python test/harness/worker_q2_public_tests.py
  4 tests OK
```

The requested bounded implementation setting was GPT-5.6 Sol High. The host
did not expose this session's actual model or effort for verification. Q2 did
not perform a paid Claude episode or a deep semantic Graft rebuild.

Final checks:

```text
python test/harness/check.py
  PASS: 0 failing of 65 checks at 15ecf66
python tools/worker_wsl_q1_attestation.py --check
  PASS: Q1 WSL attestation current
python tools/release_check.py
  source-equivalence (75 files), generated-worker, sensitive-material and
  licence checks PASS; clean build stamp and publication are operator actions
```

The first full harness run had 64 passes and one Q2 prose-spelling failure;
the spelling was corrected, a focused prose check passed all 631 authored
files, and the uncontended full rerun passed 65/65. Graft MCP supplied scoped
retrieval. A local `graft build` completed a 615-file structural graph, but
`graft_check_freshness` still reports one changed indexed file and 38 new
untracked Q0-Q2/N5 files absent from the current graph, plus 11 stale semantic
summaries from the earlier DeepSeek forced-tool failure. Thus Graft freshness
is **not** claimed. The rebuild incurred no semantic-provider charge.

## Next action after review

Review the Q2 frame and the
[bounded Q3 admission decision](../WORKER-Q3-ADMISSION-DECISION-2026-09-25.md)
for a **two-task B0 canary**. If directed,
Q3 must first prepare an exact paid manifest and dated spend notice for P01
and P02, verify Claude Code subscription identity and the multi-file paid
adapter, then seek the required exact authorisation before dispatch. The
two-task result is diagnostic only. The original eight-task ceiling/floor gate
needs six further independent public families before it can be applied. Q3
must not reuse these public tasks as reserved evidence or unseal N6 R tasks.
