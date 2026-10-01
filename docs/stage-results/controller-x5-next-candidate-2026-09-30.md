# X5 next candidate: intervene at a genuine first public failure

Date: 2026-09-30 Australia/Sydney. Status: **development design, no new
provider call or promotion claim**. The R3 and R4 producer screens are closed.
Their two new cases passed public acceptance on the first worker attempt, so
they yielded no matched recovery pair. The older Q3 public canary recorded one
natural first-check failure, P02, followed by a successful direct local
repair. That precedent establishes an observable intervention point without
using a protected oracle as a trigger; it does not establish a Controller
benefit.

The next hypothesis is narrower than the finished R3/R4 route: after a
terminal, writer-stopped first worker attempt fails a public check, choose
between a direct second worker attempt and one Controller investigation
followed by that same second-worker policy. The current TaskExecutor normally
continues its B0 ladder within `run`. A provider-free `stop_after_attempts`
option now returns from a verified, settled failure while the task is `ready`,
before the next cell dispatches. It checks the deadline before returning a
checkpoint. The executor suite passed 42/42, including ordinary B0, resumed
repair and an uncertain writer that did not qualify for a checkpoint. The
post-rebuild full offline harness passed 83/83 before the further changes
below.

`controller_x5_first_failure.py` now requires exactly one B0 Sonnet-low
attempt, a stopped writer, identity-valid settled receipt, empty unresolved
budget, qualified failed verification with unchanged protected files, and an
independent failed public assertion. It creates single-use S/A actor snapshots
and hashes every public file, including nested source paths. A fake worker
test demonstrated identical actor and report bytes, one Sonnet-low call in
each successor, and rejections for public success, an open charge, an active
writer, an uncertain attempt, unexpected source, a redirected source and
replay. The Controller workflow gained an optional worker-attempt limit so
both S and A can stop after one continuation call. Its X4 suite passed 21/21,
including a Controller handoff whose fake worker failed and stopped after one
call. These are provider-free mechanism checks. The checked distribution
build completed, and the final full offline harness passed 83/83 after the
nested-file helper and fake test were added. The helper is development-only;
the bundled executor and workflow match the checked build.

No active writer, unknown charge or uncollected receipt may be cloned or
resumed. Successor roots start from the failed actor's public bytes with the
same next B0 cell, Sonnet low. The first-failure candidate measures one
immediate repair call per successor; it does not claim a full B0 ladder
comparison. The producer cost is counted once, and the Controller assessment
and role costs belong only to A.

Build a fresh, predeclared development set of independent upstream-backed
issues with executable public checks and protected edge cases. Baseline and
known partial repairs must fail the public check; reference and independent
alternative repairs must pass. Calibrate actual first-attempt failure rate
with bounded producers before estimating Controller effect. Do not choose
replacement cases after seeing producer or protected outcomes, and do not
reuse R01, R02 or P02 as prospective effect units. A public success ends the
case regardless of hidden quality. The X6 reserve remains sealed.
P02 was used only as a separately bounded engineering smoke. Its new producer
passed public and protected acceptance on the first attempt, costing USD
0.113327401; no S/A continuation started. See the
[smoke result](controller-x5-first-failure-p02-smoke-result-2026-09-30.md).
It cannot contribute to the prospective effect estimate or be replayed. F01
is now a frozen new development case on the clean local `attrs` working tree
at pinned HEAD, with authored regressions rather than a claimed upstream
issue. Its baseline fails public and passes 2/6 protected checks; a partial
repair still fails public and passes 4/6; original upstream and independent
alternative repairs each pass public and 6/6 protected checks. See the
[F01 design](controller-x5-first-failure-f01-design-2026-09-30.md). The local
clone is partial, so the provenance claim is the pinned present working tree,
not unavailable historical objects.
The frozen F01 producer subsequently passed public and protected acceptance
on its first live call, settling USD 0.1270084. It supplied no first-failure
checkpoint or S/A continuation; see the
[F01 result](controller-x5-first-failure-f01-result-2026-09-30.md). Do not
replay it. The next development case must be a newly frozen independent issue;
the existing four first-call screens cannot be converted into a matched
Controller estimate.
F02 is now a separately frozen Click styled-help issue with a failing public
baseline, a still-publicly-failing partial repair and two complete repairs;
see its [design](controller-x5-first-failure-f02-design-2026-09-30.md).
The two cases are development screens, not a powered effect sample.
F02 subsequently passed public and protected acceptance on its first live
call, settling USD 0.0695534. It produced no S/A continuation and must not
be replayed; see the
[F02 result](controller-x5-first-failure-f02-result-2026-09-30.md).
The first-failure-only entry rule now has five first-pass producer screens
and no matched pair. Further synthetic two-module screens are paused while
the next candidate is designed around genuinely ambiguous public evidence
and a predeclared, observable entry signal.
The [headroom pivot](controller-x5-headroom-pivot-2026-09-30.md) records the
stop on similar authored-regression screens and the requirements for a new
multi-hypothesis development set.
F03 is the first new case under that requirement. It adapts a public Tenacity
cancellation report, gives the worker a shutdown trace with multiple plausible
owning layers, and has a frozen external oracle with two materially different
complete repairs; see the [F03 design]
(controller-x5-first-failure-f03-design-2026-09-30.md). Its provider-free WSL
packet probe passed. This provider-free qualification alone did not establish
Controller uplift.
F03 subsequently passed public and protected acceptance on its first live
call, settling USD 0.2023272; no S/A arm started. See the
[F03 result](controller-x5-first-failure-f03-result-2026-09-30.md). The
first-failure-only screen is closed for this task shape after six public
first-pass producers. A future candidate needs a distinct headroom premise
and prospectively frozen entry rule.

For each qualifying stopped first attempt, fork identical public snapshots.
S receives one B0 Sonnet-low repair call. A receives one bounded
Controller invocation and then one call of the same worker cell, tool surface,
acceptance contract and task ceiling. Controller may read the issue,
failed report, public check and editable source only. It must produce a
source-cited finding and a concrete discriminating next check; generic gap
text is a failure of the candidate. Grade protected functionality after the
public entry decision and reconcile every provider receipt. Compare A minus
S in acceptance, quality, critical errors, cost and elapsed time, with the
producer cost counted once.

Do not run a paid screen until isolation, an independent corpus, fake
receipts, negative controls, the final full offline harness and build,
manifest, analysis and dated cost notice are frozen. The current fake test
does not exercise a live Controller handoff at this checkpoint. A small
positive development signal remains
insufficient for X5 promotion. A larger run needs a power-based sample
contract, distinct reserved cases and independent review.
