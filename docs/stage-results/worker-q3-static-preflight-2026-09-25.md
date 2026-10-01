# Q3 static preflight and paid boundaries

Date: 2026-09-25 UTC. Status: **provider-free implementation and preflight
complete; no Q3 paid call or two-task canary has run**.

The separate Q3 launcher and credential-name wrapper are installed in WSL.
The N5 single-file and Q1 provider-free launchers were not overwritten. The
multi-file adapter uses Q1 actor staging, a restricted Claude Code
subscription invocation, root-owned stop/collection records, scoped write-back
of only the two declared existing files, and a fresh uncredentialed actor for
public acceptance. A root-only hidden grader copies the stopped candidate's
editable files into a separate grading actor; the worker never sees an oracle,
reference overlay or partial overlay. The one-shot canary driver prepares a
task intent before WSL dispatch and rejects an existing run directory on
restart.

## Verified observations

- N4 host attestation was refreshed and passed 55 provider-free checks. Q1
  multi-file attestation was refreshed and passed 38 boundary plus five
  accounting checks. Q2's six saved baseline/partial/reference grades matched
  the frozen source and oracle.
- The renewed WSL Claude.ai login was promoted by the checked sync helper.
  Q3's isolated `claude --restricted auth status --json` probe reported valid
  subscription login, a stopped Q1 writer and reconciled credentials. It made
  no model request.
- [Q3 WSL evidence](../../test/results/2026-09-25-worker-q3-wsl-host.json)
  passed 28 provider-free checks across the launcher, a fake two-file adapter,
  a full fake B0 TaskExecutor episode and hidden-grader baseline/reference
  comparisons. Evidence digest:
  `6704e480bbae81351ba4686dcfd2ee5893ed26daaa86ae0745bfdb05bd9dde16`.
  The fake worker proves transport and accounting behaviour only; it does not
  qualify served model or actual provider cost.
- A separate adversarial adapter check rejected a protected `ISSUE.md` drift
  between actor collection and root write-back. Q1's prior probes cover
  actor-file mutation, oracle and evaluator denial, symlinks, duplicate
  collection and accounting holds. The new Q3 approval tests reject changed
  manifest, allocation, call ceiling and credential method. A concurrent
  two-runner test confirmed the sentinel's durable intent lock allows only
  one provider dispatch.
- A separate [Q3 timeout result](../../test/results/2026-09-25-worker-q3-uncertain.json)
  passed seven provider-free checks: a simulated missing terminal receipt
  kept the USD 6 budget hold unresolved, retained the actor, left source
  bytes unchanged and did not replay the fake worker on a second executor
  run. Its evidence digest is
  `1e246ce3d662e265c5ac4e006a10da09a07a36a2769ce3076ce710e114800646`.
  The prospective canary manifest validates and binds this result.
- `python test/harness/check.py` passed **66/66** offline checks after the Q3
  changes. `tools/release_check.py` found matching source/bundle files and no
  sensitive material; its `release_ready=False` reflects the dirty build
  stamp and publication action. No consumer `src/` file changed in Q3, so no
  redistributable rebuild was needed for this stage.

## Paid gates still pending

The earlier N5 Read-denial sentinel is tied to the old N4 host attestation.
The separately frozen [Q3 sentinel manifest](../../test/results/2026-09-25-worker-q3-sentinel-manifest.json)
has digest `ab78db7bc5273863bfb68192941b580f3843d52c066940ba0f4cd6342c4c395b`.
Its [dated notice](worker-q3-sentinel-spend-notice-2026-09-25.md) requests one
Sonnet-low Claude Code subscription call, USD 0.10 local allocation and USD
0.03-0.15 projected API-equivalent usage. It awaits a separate exact approval
record. No sentinel intent or Q3 sentinel result exists yet.

The [two-task canary notice](worker-q3-canary-spend-notice-2026-09-25.md) is a
draft. `worker_q3_canary.py` correctly refused to freeze its manifest before a
current, approved Q3 Read sentinel exists. After that evidence is available,
freeze and review a separate exact USD 12, six-call, B0-only manifest before
dispatch. The canary is diagnostic for B0 difficulty, cost and grader
stability. Two public families cannot qualify a routing change or satisfy
Q0's eight-family thresholds.

## Limits and next action

The paid adapter has not served a real model, and cancellation during an
actual Claude invocation remains unobserved. Requested effort is evidenced
by CLI arguments; Claude Code does not expose served effort in its terminal
receipt. Graft MCP was used for scoped retrieval, but its repository graph
remains stale for the new untracked Q3 files; no semantic-cost saving is
claimed from its full-file comparison estimate. On exact sentinel approval,
write its matching approval record and
run `tools/worker_q3_sentinel_gate.py --run` once. If it passes and current
host evidence remains valid, freeze the canary manifest and request its
separate exact approval.
