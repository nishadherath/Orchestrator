# Q3 public-contract audit and Q4 design review

Date: 2026-09-25. Status: **provider-free audit complete; measurement repair and
Q4 freeze remain incomplete**. B0 remains unchanged. No paid model call,
reserved task, Controller task or historical campaign replay ran in this audit.

## Reproduced observations

The [audit tool](../../tools/worker_q3_contract_audit.py) copied the stopped,
hash-bound P03 and P07 candidate revisions through the existing Q1 boundary and
executed diagnostic probes in fresh isolated WSL actors. It verified protected
files, original grade/revision hashes and unchanged stopped workspaces. The
[machine evidence](../../test/results/2026-09-25-worker-q3-contract-audit.json)
has digest `cccb964a8127908ec44cc6abb2c3dda914fe1e270cec47ad9b2c64f21b685278`.

P03 returned sorted `declare, refine` command and `--bound, --count` option
suggestions with exit code 2. Its wording omits the colon after `one of` which
the oracle requires, accounting for 35 lost points. Valid command/option probes
exited 0 with expected output; an unrelated command failed without a hint.
Another 10 points require a new exported `NoSuchCommand` class that the public
issue never requests. The frozen 55/100 therefore does not demonstrate failure
of those public requirements.

P07 rejected the malformed marker and requirement states with `InvalidMarker`
and `InvalidRequirement`, both `ValueError` subclasses. The frozen oracle
deducts 10 points because it requires `TypeError`; the public issue specifies
validation without that type requirement. Both original grades remain unchanged.

| Interpretation | Accepted tasks | Mean executable score | Maximum remaining mean score gain |
| :--- | :---: | ---: | ---: |
| Original frozen Q3 oracles | 3/8 | 87.5 | 12.5 |
| Retrospective contract sensitivity for P03/P07 | 5/8 | 94.375 | 5.625 |

The sensitivity credits the disputed 45 and 10 points; it is not a new official
grade, exhaustive correctness proof or reserved result. P05/P06/P08 retain
observed omissions described by their public issues. Unknown regressions remain
outside all these scores. Both interpretations stay inside Q0's acceptance
difficulty window, but the ten-point quality pathway has a ceiling problem
under the contract sensitivity. An acceptance improvement remains possible.

## Source findings and resulting decision

`worker_wsl_q3_public._grade` assigns executable scores only. It does not grade
diagnosis, clarification or report truthfulness. Its `false_success` flag is a
root-public-pass/hidden-fail indicator. It is not an independently observed
false statement by a worker. All P03-P08 hidden cases set `critical: false`,
so zero critical errors there is no evidence that critical-error detection was
exercised. The new design keeps these concepts separate.

`task_executor._experimental_policy` uses `[selected, selected, fallback]`.
Changing the initial cell changes the retry cell as well. This is valid for
its historical whole-policy comparison but does not isolate the first-cell
effect required by Q0. Both the Q3 adapter and launcher restrict admitted
cells, so extending only the Python adapter would be insufficient.

Decision: defer further paid screening until a versioned measurement contract
and common repair tail pass offline and WSL calibration. The
[implementation contract](../WORKER-Q4-MEASUREMENT-AND-FREEZE-2026-09-25.md)
defines report capture, contract-mapped scoring, safety coverage, an at-most
USD 99 public screen, candidate abstention, independent reserved sampling and
Q5's separate approval boundary. It does not claim a candidate is selected or
that a reserved frame is already frozen.

## Verification and limits

`wsl.exe -d kali-linux -u root --cd
/mnt/c/Users/Bob/Desktop/Code/Claude/Orchestrator -- /usr/bin/python3 -B
tools/worker_q3_contract_audit.py --run` returned `PASS`. This used two isolated
probe processes and zero provider calls. Actual experiment cost for this audit
was USD 0; development-session usage is separate and not measured here.
The four focused `worker_q3_contract_audit_tests.py` tests passed, including
negative checks for incorrect ordering, missing suggestions, successful typo
exits, broken normal parsing and accepted malformed state. The full
`python3 test/harness/check.py` run passed **69/69 checks** at `15ecf66`,
including the new audit, all 19 handoffs and 75-file source/bundle parity.
Focused prose validation passed on 670 authored files; `git diff --check`
and the new handoff's structural validation also passed. The saved audit's
source and original-evidence SHA-256 bindings were independently rechecked.

Graft MCP structural freshness passed at session start. Eight pre-existing
semantic summaries in `tools/task_executor.py` were stale; source spans were
used for the relevant conclusion. No paid semantic rebuild was needed.
No commit was made; the branch is `v1.0-rc1` at `15ecf66` with pre-existing
changes preserved. These are developer audit/design artefacts, so no consumer
bundle change or `dist/` rebuild was required.
