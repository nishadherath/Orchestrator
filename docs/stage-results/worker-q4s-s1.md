# Q4S S1 evaluation admission and evidence hardening

Date: 2026-09-26 Australia/Sydney. Scope: prospective, provider-free
evaluation instrumentation. No Q4S corpus, paid manifest, model call or
shipping-route change was made. Q4 and Q4R sources, receipts and scores remain
frozen.

## Implemented boundary

The Q4S-only [structured adapter](../../tools/worker_q4s_structured.py)
keeps the Q4R schema and local 16 KiB exact-field report validator. A terminal
`success` without a valid structured report now produces a settled failed
receipt when the provider supplies a final cost, even if the process exits
zero. The receipt keeps model identity, reported usage and cost, return code,
turn count if present, bounded event counts and error codes, and hashes and
byte counts of stdout and stderr. It does not retain their raw text. Synthetic
root markers are separate from real model markers. Exactly one matching real
root and no child model are required; billed models remain separate evidence.
Requested effort remains unverified served effort.

The [admission and settlement module](../../tools/worker_q4s_admission.py)
requires a source-bound, provider-free WSL authentication and isolation proof
before creating a campaign directory. Each provider-call intent is written
once. A stopped, charged failure can be graded for executable partial credit
and snapshotted after ledger and protected-source checks. A missing report
receives no report credit and cannot qualify. An unresolved charge, active
writer, protected drift or mismatched receipt fails closed. A settled failure
is recorded and blocks further calls without replay.

The separate [WSL launcher](../../tools/worker_wsl_namespace_q4s.sh) admits
Sonnet-low, Sonnet-medium and Opus-high with the same schema and isolated
actor boundary. It sets `MAX_STRUCTURED_OUTPUT_RETRIES=2`,
`CLAUDE_CODE_MAX_OUTPUT_TOKENS=8192` and `CLAUDE_CODE_MAX_TURNS=20`.
The pinned Claude Code 2.1.273 help omits `--max-turns`; the
[official environment reference](https://code.claude.com/docs/en/env-vars)
documents `CLAUDE_CODE_MAX_TURNS` as equivalent. The launcher checks a
USD 4 per-call ceiling and the exact allowed command shape. These settings
bound the later canary and screen; the fake probe proves they reach the
isolated actor, not that a live model will complete within them.

## Verification

- `python -m unittest test.harness.worker_q4s_s1_tests -v`: seven of seven
  provider-free cases passed. They cover absent structured output, retry
  error, nonzero exit with settled cost, synthetic and substituted model
  markers, unexpected child, malformed stream, expired authentication,
  protected drift, partial grading, raw-byte hashes, duplicate results and
  no replay.
- `bash -n tools/worker_wsl_namespace_q4s.sh` and
  `bash -n tools/worker_wsl_q4s_install.sh`: passed in WSL.
- `tools/worker_wsl_q4s_attestation.py`: authentication passed and all 12
  provider-free boundary checks passed. The [source-bound host evidence](../../test/results/2026-09-26-worker-q4s-wsl-host.json)
  has digest `32a4c7193c912eb595ec8688bedf0cd41dd446339d8a703279abc69880d874cc`;
  it reports zero provider calls and zero provider cost. Its saved proof also
  passed a temporary campaign-admission integration check.
- The full offline repository gate result is saved at
  [Q4S S1 offline check](../../test/results/2026-09-26-worker-q4s-s1-offline-check.json).

## Limits and next stage

No live Claude run has tested whether the two-retry and 20-turn limits preserve
task completion. The terminal cause of Q4R's missing object remains unknown.
S2 must freeze six new independent public issue families, trigger labels,
oracles, manifest and analysis rules before the two-call S3 canary. The
historical B0 route and Q5 gate remain unchanged.
