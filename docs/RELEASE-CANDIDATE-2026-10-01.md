# Bounded release candidate

## Scope and acceptance

Finish an unpublished RC of the installed B0 bundle, with Controller explicitly
experimental. This closes packaging and operational readiness; Controller uplift
remains an unfinished qualification goal. Preserve existing research evidence,
local configuration and the qualified routing policy. Done means reviewed
shipping changes, accurate consumer guidance, a checked build, a frozen bundle
with SHA-256 provenance, exact-bundle install/upgrade/rollback evidence and a
passing complete offline harness. Use the existing builder and installer.
Allow 6-12 focused hours, with no paid experiment calls. Development API cost is
unknown because the user's selected model and billed usage are not exposed.
The main risk is treating narrow host or authored-case evidence as general
qualification; the RC must state those limits.

## Supported boundary

- B0 is the default: Sonnet low, one same-cell repair after observable failure,
  then one Opus high fallback. No automatic Controller promotion.
- The explicit durable task CLI covers admission, execution, accounting,
  cancellation and recovery. Interactive Agent calls outside it are unmanaged.
- Controller controls and its N1 workflow remain experimental. An evidence
  packet or handoff does not replace independent task acceptance.
- Fake transports establish offline behaviour. Existing WSL trials establish
  only their recorded host, tools, identities and task conditions. General
  filesystem isolation, descendant termination and served effort are not proven.
- Live managed child execution remains rejected by the general adapter.

## Release work

1. Review shipping code and dependency changes since the source baseline,
   focusing on acceptance integrity, replay prevention, charge retention,
   cancellation, scope controls and packaging.
2. Correct release blockers with meaningful regression tests and align root
   and consumer documentation with current evidence.
3. Rebuild `dist/` through `tools/build_dist.py`. Freeze exact bundle bytes,
   an allowlisted source snapshot and a hash manifest. Retain an honest dirty
   stamp when the source checkout is uncommitted.
4. Verify the frozen bundle in isolated consumer directories: clean install,
   upgrade from the baseline bundle, rollback, drift rejection and preservation
   of user configuration, task records and unrelated files.
5. Run the full offline harness and release checker; record exact commands,
   results, artefact hashes and unresolved limits in the RC result.

## Publication and unfinished qualification

A content-addressed unpublished candidate can be reviewed without committing
the user's accumulated work. A dirty stamp is not clean-source release evidence.
Publication still needs an approved source commit, a checked build from that
commit and explicit publication authority. Do not weaken the release checker's
clean-stamp or publication gates.

Controller uplift remains open. Its future qualification requires a sound,
frozen evaluator and prospective matched comparisons with equal public evidence,
budget accounting and independently protected acceptance. Preserve all stopped
X5 results and their no-replay decisions. H03b remains unscored after its frozen
grader exception; no retrospective score or further paid screen belongs in this
RC. General host enforcement and frontier/served-effort qualification also remain
outside the supported claim.

## Review findings

- Confirmed: build stamping ignored Git inspection failures, and the release
  checker accepted unknown, arbitrary and rationale-only stamps as clean.
  Four provenance regression tests reproduced the defect before repair and
  passed after the fail-closed repair.
- Confirmed: consumer documentation described the X4 worker bridge as closed
  and the root README still named X3 as next. Update these historical claims
  without presenting subsequent X5 work as measured uplift.
- Examined: the production Controller handoff compares the raw invocation
  receipt cost against the retained raw budget row. The separate H03b research
  gate's rounded-total comparison defect does not establish the same defect
  here; no accounting policy change is justified by that analogy.

## Focused shipping review

The review followed the changed dispatch and acceptance boundaries, rather than
claiming an independent audit of every retained subsystem. Inspected paths:

| Boundary | Files and checks |
| :--- | :--- |
| Bundle provenance and ownership | `build_dist.py`, `release_check.py`, `install.py`, installer regression tests |
| Frozen acceptance and command evidence | `acceptance.py`, `system_controller.py` Framer correction at all three entry paths, integrity and acceptance suites |
| Root ownership, resume and charges | `task_executor.py` public assessment, selection freeze, Controller claim/handoff, run, receipt, verification, cancellation and continuation; N1 and X2/X4 suites |
| Controller packet and host boundary | `controller_dispatch.py`, `controller_workflow.py`, public assessor/interpreter, profile selection, X4 handoff and host tests |
| Operator interface and installed instructions | `worker_tasks.py`, control status, preflight, routing core/reference and consumer guides; installed N8 tests |
| Model identity and output provenance | `claudep.py` stream evidence, `model_registry.py` Generator assignments, adapter receipt extensions; identity and dispatch suites |

Observed source controls preserve B0, immutable acceptance, retained uncertain
charges and explicit experimental admission. This is code-review evidence;
behavioural claims depend on the offline runs recorded in the final result.
No new quality, performance, live authentication or general host-enforcement
claim is inferred from this review.

Bounded RC verification is complete. See
`docs/stage-results/release-candidate-2026-10-01.md` for the exact artefact,
final offline results and publication prerequisites. Controller uplift remains
an unfinished qualification goal.
