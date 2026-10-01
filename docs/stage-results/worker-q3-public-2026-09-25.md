# Q3 public eight-family B0 gate

Date: 2026-09-25 UTC. Status: **eight independent public B0 episodes complete;
Q3 candidate selection and Q4 freeze remain open**. B0 is still the shipping
default. No reserved task or experimental Controller task ran.

Later review: the [provider-free contract audit](worker-q3-contract-audit-2026-09-25.md)
reproduced disputed P03/P07 failures. Frozen scores below are unchanged;
their contract-based sensitivity is 5/8 and 94.375/100. Further paid screening
now waits for the [measurement and comparison repairs](../WORKER-Q4-MEASUREMENT-AND-FREEZE-2026-09-25.md).

## Frozen material and actual spend

P01 cachetools and P02 ItsDangerous were the earlier
[two-family canary](worker-q3-canary-2026-09-25.md). The separate P03-P08
[manifest](../../test/results/2026-09-25-worker-q3-expansion-manifest.json)
has digest `59358e16730482036176e417ea29ce63368ea855ccbd4cc6d9cd325d2a8b56f1`
and binds six distinct pinned upstream source trees, licences, issues,
protected public checks, root-only hidden oracles, calibrated reference and
alternative implementations, WSL isolation evidence, a fixed B0 ladder and
the [dated spend notice](worker-q3-expansion-spend-notice-2026-09-25.md).
All six additions passed baseline/partial/reference/alternative calibration.
The source and fix-commit bytes were independently compared with their pinned
local upstream clones. P04 and P08 needed one generated version module each to
make their upstream source imports work without a build step; those exact bytes
are documented in their `provenance.json` files.

The operator's standing approval through Q4 covered this exact six-task
campaign. Its local USD 36 allocation and 18-call ceiling were admission
limits, not a subscription charge. The [complete one-shot evidence](../../test/results/2026-09-25-worker-q3-expansion-evidence.json)
records six settled Sonnet-low calls and **USD 1.774540602** of
provider-reported API-equivalent usage, with no unknown charge or Opus
fallback. Together with the earlier canary, the eight B0 episodes used nine
calls and **USD 2.215058204** API-equivalent. The separate security sentinel
cost USD 0.0530436 API-equivalent. Actual Claude Code subscription invoice
impact is not observable. All calls reported `claude-sonnet-5` and requested
low effort; served effort was not independently reported.

| Public task | Upstream project | Hidden accepted | Executable score /100 | Root acceptance gap | Calls | API-equivalent USD |
| :--- | :--- | :---: | ---: | :---: | ---: | ---: |
| P01 | cachetools | yes | 100 | no | 1 | 0.0850796 |
| P02 | ItsDangerous | yes | 100 | no | 2 | 0.355438002 |
| P03 | Click | no | 55 | yes | 1 | 0.2353996 |
| P04 | urllib3 | yes | 100 | no | 1 | 0.260206201 |
| P05 | Tenacity | no | 85 | yes | 1 | 0.1743372 |
| P06 | PyJWT | no | 80 | yes | 1 | 0.1329656 |
| P07 | packaging | no | 90 | yes | 1 | 0.2668178 |
| P08 | platformdirs | no | 90 | yes | 1 | 0.704814201 |
| **Total** | eight independent projects | **3/8** | **87.5 mean** | **5/8** | **9** | **2.215058204** |

The six-task [independent adjudication](../../test/results/2026-09-25-worker-q3-expansion-adjudication.json)
verified protected-file hashes and the stopped actor revisions, then saved
the [actual patches](../../test/results/2026-09-25-worker-q3-expansion-patches/).
P03 failed the frozen multi-suggestion and exception predicates; the later
contract audit found those predicates over-specified. P04 correctly preserved explicit port zero through URL,
pool and proxy handling. P05 fixed falsy waits in synchronous and asynchronous
paths but omitted callable-plus-strategy composition. P06 fixed parsed JWK
normalisation but missed transformed-fetch cache consistency. P08 fixed most
returned-path creation but missed one macOS cache-path case. P05, P06 and P08
are observed partial repairs, so incomplete acceptance must not be scored as zero.

The historical JSON field `false_success` means root acceptance followed by
hidden failure. It does not establish a worker's false completion claim.
These executable scores do not measure diagnosis or truthful reporting, and
all expansion oracle rows have `critical: false`, leaving critical-error
coverage unmeasured. New evaluation must measure these separately.

P07 requires an explicit grading caveat. The frozen hidden oracle expects
`TypeError` for malformed marker and requirement pickle states. The stopped
patch rejects those states with `InvalidMarker` and `InvalidRequirement`,
both subclasses of `ValueError`. The public issue promised validation of
malformed state but did not specify an exception class. The frozen grade
therefore remains **90/100 and not accepted**, while the two 5-point misses
are **rubric-disputed**, not proven failures of the stated public contract.
Its state handling may have other untested defects. A reviewer must resolve
the exception contract prospectively before using this family as a reserved
analogue. If P07 were judged contract-equivalent, public B0 acceptance would
be 4/8 instead of 3/8; neither result triggers Q0's difficulty ceiling or
floor. Do not alter the bound oracle or replay the paid episode to change its
score.

P08's patch is comparatively broad (97 lines added, 42 removed) and moves
directory creation from a shared helper into several platform methods. The
frozen hidden cases measure intended returned-path side effects, but do not
exhaust all platform property combinations. Unmeasured regression risk remains
outside its 90-point score.

## Gate decision and next action

Q0's ceiling is more than six of eight hidden-accepted, and its floor is
fewer than two. The observed **3/8** clears both. Five public-pass/hidden-fail
episodes originally suggested headroom for task-sensitive selection, but they do not
show that any alternative cell improves quality or offsets its cost. P01's
unchanged candidate and baseline were each regraded ten times without a
provider call and remained stable; model-run variability across the harder
P03-P08 tasks has not yet been measured. The eight one-shot grades are an
admission and difficulty result, not a routing-effect estimate.

The original next action was a **small public candidate screen** on selected P03-P08
tasks at common repair cap, using cells with host identity evidence. Compare
raising Sonnet effort with at least one model change only where the expected
information justifies the premium. Bound calls and spend in a new manifest,
validate the adapter with a fake provider, and preserve all stopped patches.
Do not treat the same public tasks or repeated episodes as independent reserved
units. Q4 then freezes a distinct reserved sample, candidate policy and
analysis. The later audit supersedes that immediate screen with measurement
repair and common-tail calibration first. Stop before Q5 dispatch as the
operator directed.

The six-task runner is one-shot: **do not rerun `tools/worker_q3_expansion_live.py
--run`**. `python3 tools/worker_q3_expansion.py --check` validates its bound
inputs when current WSL evidence is still fresh. The suite also includes
provider-free adversarial checks of protected edits, unsafe links, false
completion and public-pass/hidden-fail discrimination. The source and grader
are local evidence, not a proof of all behaviour on untested inputs.
After this record was written, the manifest check passed for digest
`59358e16730482036176e417ea29ce63368ea855ccbd4cc6d9cd325d2a8b56f1`,
the four focused Q3 expansion tests passed, and `python3 test/harness/check.py`
passed **68/68** offline checks. `git diff --check` was clean. No provider
call was made by those checks. A focused `check_prose` run passed on 666
authored files.
