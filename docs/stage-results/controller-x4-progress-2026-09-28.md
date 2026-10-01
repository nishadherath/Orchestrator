# Controller X4 progress — validated root handoff

Date: 2026-09-28. Stage status: **in progress; no live qualification or default promotion**.

`TaskExecutor.accept_controller_handoff` now revalidates the persisted
Controller decision, source digest, evidence packet, on-disk packet, derived
worker handoff and settled root budget before releasing the downstream worker
hold. The same frozen N1 root then issues the worker request, includes the
Controller findings as explicitly untrusted evidence, and still requires
independent acceptance. A changed packet or cancelled root remains closed.

Provider-free focused suites passed 13/13 across X2, paired X3 and X4 handoff
tests. `git diff --check` passed. The full harness previously passed 81/81
before this X4 change. Its first rerun hit a 150-second wrapper timeout in
X1; X1's expanded corpus suite had separately passed in 159 seconds. The
wrapper limit was raised to 300 seconds and the X3/X4 pair was added to the
offline gate. A second full rerun produced no result after a long silent run
and was stopped; therefore no new full-harness pass is claimed.

An instrumented rerun then reached all checks and exposed historical Q4
evidence access restrictions, an obsolete N4 fixed-call-count assertion, a
stale live Q4 host gate inside historical tests, sandboxed Python trampoline
denial, and expected pre-build bundle drift. N4 now compares journalled
attempts and passes 5/5 both sandboxed and unsandboxed. Historical Q4 screen
tests pass 5/5 while a separate test retains the strict live-host gate;
root-owned Q4 result tests and the compaction self-test pass outside the
sandbox. The gated `tools/build_dist.py` subsequently exited 0 and regenerated
78 consumer files. A direct post-build DIST check passed 78/78. These are
provider-free checks. A post-build full-harness run remains to be recorded
after further X3/X4 source changes settle.

The X4 exit remains open: automatic/explicit interactive control resolution,
qualified worker cell and Controller role profiles, live interpreter identity
and billing, restart and cancellation recovery, and full fake production-path
coverage still need implementation and verification. X3's immutable campaign
manifest and paired campaign exit also remain open. No Claude Controller
provider calls were made in this work.

The N1 root now reserves and starts a public-assessment invocation before an
interpreter call. It validates the cited result, settles observed telemetry on
that same root, persists the assessment and binds the remaining budget into
the rigour decision. A lost response leaves the invocation unresolved and the
root blocked; an allocation overrun retains the charge and blocks subsequent
dispatch. Restart cannot replay the assessment on the same revision. The
provider-free assessment suite passed 3/3, and its first two cases passed with
52 adjacent X2/X3/X4/N1 regressions (55/55). No paid assessment call occurred.

The explicitly admitted experimental N3 path can now leave its worker cell
pending while the assessment is charged, then freeze N3's selected cell and
common repair tail before Controller or worker reservation. Unsupported or
unaffordable cells block; the rejected worker candidate is not promoted to
the qualified B0 default. A full fake assessment -> N3 freeze -> Controller
handoff -> worker -> independent acceptance path passed, and 65 adjacent
regressions passed together. Live interpretation and served-model billing,
automatic control resolution, labelled role-profile selection, restart and
cancellation races, and X5 campaign qualification remain open. The latest
source changes have not yet been propagated to `dist/`.

The root now freezes a validated Controller routing decision on the settled
public assessment and selected worker cell. Changed operator settings cannot
rewrite that decision or bypass a required Controller through direct worker
dispatch; a new task revision clears the prior assessment and decision.
`tools/controller_workflow.py` provides an explicit experimental admission path
that resolves auto/on/off, selects the worker or Controller, validates the
Controller handoff, and then dispatches the worker on the same root. Its
provider-free workflow tests passed 10/10, including restart, forced on/off,
useful-gap and empty-gap cases. The adjacent focused suites passed 69/69; the
experimental worker-dispatch suite passed 8/8 separately. The workflow tests
are now included in the offline X3/X4 gate. These checks do not qualify the
live WSL Controller host, interactive command, or role-profile policy, and no
paid Controller calls have occurred. `dist/` remains stale after these source
edits and must be regenerated after X4 settles.

The installed `/controller` source command can now request a read-only N1 root
status view. `controller_control.status_view` reports current intent separately
from the frozen effective action, the root's applicability state, Controller
admission and worker-attempt count. It explicitly leaves provider-call
confirmation unknown; an admitted invocation is not a billing receipt. A
subsequent project `off` setting was observed without rewriting a previously
frozen explicit `on` Controller decision. The provider-free X4 workflow suite
passed 11/11 and the existing R3 control suite passed 14/14. The interactive
wrapper has not yet been exercised in a clean installed consumer session.

The new `controller-profile-v1` rule now selects the retained standard profile
for automatic experimental routing and requires an explicit experimental N3
root plus a named request for the unqualified frontier profile. It checks that
the root can reserve both the Controller cap and downstream worker floor, then
freezes its source, registry status and qualification claim alongside the
routing decision. A provider-free fake frontier trial passed end to end;
ordinary automatic routing retained standard, an unauthorised frontier request
was rejected, an underfunded request was rejected, and a modified frozen
selection was rejected on read. This is an admission and audit mechanism, not
evidence of frontier quality, complete live affordability or served effort.
Frozen v1 selections are validated from their own versioned fields on read;
admission additionally compares them with the current registry. A simulated
later registry-resolution failure did not make an already accepted task root
unreadable.

The public assessor now validates terminal telemetry independently of the
interpretation. If a charged response has invalid classifications or citations,
N1 records the known final charge, marks the assessment invalid and blocks the
root. A lost or unpriced response still retains its unresolved reservation.
The focused public-assessment, X4 assessment and workflow suites passed 26/26
after this change. Live WSL interpretation remains unimplemented; the current
WSL Claude Code auth status was inspected read-only and reported `loggedIn` with
Claude.ai subscription auth, which does not by itself qualify a paid run.

The consumer build plan now includes the new profile policy, public assessor
and one-root workflow modules. `planned_files` reports 81 intended bundle files
with all three present. This is a source-plan check only; `dist/` has not yet
been regenerated or validated against the new plan.

After the profile-selection and failed-assessment accounting changes, the
adjacent X2/X3/X4/N1/experimental-dispatch regression suites passed 81/81.
This is not the complete offline harness. `git diff --check` passed; the
checked consumer build and live qualification remain open.

The public-assessment path now has an injectable WSL Claude Code interpreter.
It checks Claude.ai subscription auth before N1 reserves a call, sends only
the bounded public packet through stdin with tools disabled, requests a schema
constrained result, checks the served root model and terminal billing, and
returns cost to the same root. A terminal malformed result retains its final
charge; timeout with partial charge remains unresolved. A missing auth JSON
response is handled as a preflight failure. One scripted interpreter-to-
Controller-to-worker test and the focused assessment/workflow suites passed
44/44; a new empty-auth regression passed separately. These are fake subprocess
tests, not a qualified WSL provider call. Source packaging, host attestation,
live CLI behaviour, interactive installation and the complete offline gate
remain open. The Graft structural index was rebuilt locally after the corpus
expansion; its MCP freshness check exceeded the old 60-second tool timeout,
so the next session's project MCP timeout is set to 180 seconds. No paid Graft
semantic rebuild or Claude call was made for this step.

The checked consumer build then passed the full offline harness and regenerated
the consumer bundle including the first WSL interpreter. Its first attempt
exposed a five-second, host-sensitive wait in the historical X1 campaign race
test. The isolated race passed with a 30-second admission wait and clearer
early-exception reporting; the subsequent complete checked build exited zero.
Later source changes described below make that bundle stale again until the
next checked rebuild.

Live WSL Claude Code 2.1.273 reported Claude.ai subscription auth. The first
C03-D1 public probe blocked with an unresolved USD 0.50 hold after a CLI
failure, but it did not retain raw transport diagnostics, so its actual charge
is unverified and that root remains closed. A separate diagnostic root showed
the exact local error, `--json-schema is not valid JSON`, exit code 1 and empty
stdout. Provider-free argv probes confirmed that Windows `wsl.exe` rewrites
raw JSON quotation marks and braces, while URL-safe base64 survives. The
diagnostic root was reconciled as a final zero charge from its retained CLI
error and stopped-process evidence; it remains blocked with no replay.

`controller_wsl_launch.py` now decodes the schema and prompt inside WSL and
execs Claude Code with a fixed, tool-free argument list. Its preflight passed
against the installed WSL path and auth; six focused interpreter tests passed.
A third, separately admitted C03-D1 root produced a live terminal Sonnet 5
public interpretation and settled USD 0.0345912 API-equivalent usage on N1.
The result was structurally valid, with a served-model stream event and no
child model. The fixture supplied only two short citations, so this probe
qualifies transport and accounting, not classification quality or suitability
of a default Controller decision. Live Controller role dispatch and the X3/X4
exit gates remain open. The new launcher and reconciliation code passed the
focused assessment/workflow suites (49/49). The subsequent checked consumer
build exited zero and regenerated the 2026-09-28-15ecf66-dirty bundle with
both WSL interpreter files matching source. The full offline gate required
longer subprocess watchdogs for the expanded R5, X1 and X3/X4 suites; their
assertions were unchanged. A separate post-build `git diff --check` passed.

A subsequent fresh C03-D1 probe used 11 task-relevant public citations. Its
Claude Code 2.1.273 Sonnet 5 assessment settled USD 0.0387786 API-equivalent
usage on N1 with no unresolved allocation. The script's reporting step then
raised `KeyError('facts')`; a read-only root inspection recovered the settled
interpretation without replay. It selected `recoverable`, `none` premise
uncertainty, `one-established` alternatives and `local` coupling, so the
current automatic policy would use a worker despite the deterministic fake
pair selecting Controller. This is a real candidate-screen discrepancy, not
proof of a quality loss. Independently freeze suitable-task criteria and
calibrate on development tasks before claiming task-sensitive live routing.

The enum-definition prompt refinement was then checked on a fresh C03-D1
root using the same 11 citations. The terminal Sonnet 5 call settled
USD 0.0430122 API-equivalent usage and classified the task as consequential
with a visible implementation failure, but with no unresolved premise, one
established repair direction and local coupling. Auto still recommends a
worker. This corrected the consequence and failure-cause interpretation
without forcing a Controller call for a clear repair. C03-D1 is now treated
as a high-stakes negative control for invocation; trigger-positive pilot
cases need independently predeclared public ambiguity or material competing
constraints. The prompt revision passed 23 focused offline tests before the
call. The subsequent checked consumer build exited zero and propagated the
prompt to `dist/`; source and bundle SHA-256 both equal
`6b891a1b800dad50d807415f1dcdd081fea24fc40119708457a90275a92bdc56`.
`git diff --check` passed after the build. This still does not qualify a
Controller default, a live role invocation or the full X4 interactive path.

A fresh staged consumer install then passed a provider-free `/controller`
command and control-CLI smoke test. It verified project, session, task and
explicit precedence (`off`, `on`, `auto`, `off` respectively), clear operations,
read-only status, and `paid_work_started: false` on every CLI result. The
installed command file was present and pointed to the bundled control CLI.
The focused install test passed 1/1. This verifies installed files and CLI
behaviour, not Claude Code's live interactive command interpretation or a
Controller role invocation. It was added after the preceding checked build
and must enter the next full offline gate.

The first synthetic WSL live Controller run reached Framer on Opus High and
settled two terminal calls for USD 0.7297 API-equivalent usage, with no
unresolved hold. It ended in a correct `no_improvement` gap before downstream
roles because the Framer produced 25 PremiseRecords on the first call and one
on retry, but no FrameRecord or B0 candidate. The first call's complete
transcript spanned two assistant text messages; the terminal JSON envelope
retained only the last. Its direct CLI path did not request stream identity,
so no served-role qualification is claimed. The subsequent source candidate
caps quick-mode premises at 12, orders FrameRecord/B0 first, collects all
root assistant text from stream events and enables stream identity on the
direct CLI. Provider-free budget/stream tests passed 32/32 and the Controller
self-test passed 12 scenarios. This candidate awaits a fresh live run and a
checked bundle rebuild.

The second fresh synthetic WSL run passed the revised Framer, Verifier and
both Controller checkpoints with served-model identity, then reached Sonnet
High Generators. All nine calls settled for USD 1.7035 API-equivalent usage
and no hold. It stopped with `budget_spent` despite USD 2.2965 available at
the end: standard-profile parallel Generators had no complete-cohort plan,
so the first two live reservations held USD 2 and USD 0.76 while a third
could not reserve its USD 0.50 minimum. Source now computes per-Generator
caps from the remaining budget while preserving the Critic/Selector floor,
for standard as well as frontier profiles. A concurrent three-sibling test
and the adjacent budget suite passed 33/33; the Controller self-test passed
12 scenarios. This fix awaits a checked build and a new live host trial.

The complete-cohort change passed the subsequent checked consumer build, with
source/bundle parity for the Controller and stream parser. A third fresh WSL
run settled 11 calls for USD 1.652309002 API-equivalent usage, with no
unresolved hold. It framed ten premises, measured seven, reframed, and reached
both Controller checkpoints. It stopped before any Generator: USD 2.347690998
remained, below the USD 2.50 minimum for three Generator reservations and the
Critic/Selector floors. The complete-cohort admission behaved as designed;
this trial does not qualify a full live role path. Seven sequential Verifier
calls consumed time and budget, mostly establishing that this statement-only
fixture has no inspectable implementation or job log. The run is terminal and
will not be replayed.

The same run exposed a separate checkpoint defect. The live Sonnet Low
stability call hit its former USD 0.10 cap after settling USD 0.1035346, so
`classify` silently substituted the Framer's `stable=True` field. The family
selection call returned valid structured output at USD 0.0842804. Source now
reserves up to USD 0.25 for either classifier and turns a failed or malformed
live classification into an accounted gap instead of reporting a fallback as
independent Controller judgement. The focused dispatch budget suite passed
34/34. A fresh host qualification with sufficient task-wide headroom and a
checked build are still required; the USD 4 pilot envelope is not changed by
this source fix.

The checked build then exited zero and regenerated `dist/`; the Controller
source/bundle SHA-256 matched, and `git diff --check` passed. A fourth fresh
WSL run used a USD 6 local allowance, a 1,800-second limit and Claude.ai
subscription authentication. It completed 17 terminal calls for
USD 3.227475305 API-equivalent usage, USD 0 held, and complete accounting.
Every role call had a matching served root-model identity: two Opus High
Framer, seven Sonnet Medium Verifier, two Sonnet Low Controller, three Sonnet
High Generator, two Opus Medium Critic and one Sonnet Medium Selector. The
corrected stability checkpoint returned a real structured result; family
selection chose `subtract` and `abduce`. Both Generators produced three
candidates in total. The first Critic response exceeded schema field-length
caps; its one bounded retry produced four valid critiques.

This was a full live role-host path through Selector, not an accepted
Controller solution or a production Controller-to-worker run. It ended in a
`no_improvement` GapReport after deterministic integrity screening rejected
all candidates, including B0, because five load-bearing premises remained
unverified in this statement-only investigation task. The report contains the
ranked candidates and uncertainty ledger, but its next-test text is generic.
This is a useful negative outcome for quality tuning: the pipeline must keep
those premises unverified while producing a specific, safe partial handoff.
The terminal run will not be replayed. X3 campaign freeze and X4 interactive,
Controller-to-worker and partial-gap qualification remain open.

The partial-gap source change retains the integrity rejection but selects a
specific unverified premise's `cheapest_verification` for the next-test field.
A fake end-to-end Controller run confirmed that this produces a concrete
handoff while keeping the outcome `gap` and omitting an accepted answer.
The focused integrity suite passed 11/11, then the integrity and budget suites
passed together 45/45. The subsequent complete checked build exited zero,
regenerated `dist/`, and source/bundle SHA-256 for `system_controller.py`
matched `81477390668C5E9B30409BE194B8522ADF89867A099738C79C308AFFCC3612E5`.
`git diff --check` passed. This source change has not been live-retested;
the fourth paid run remains the final observed host result.

The new installed-consumer X4 smoke copied the generated bundle into two
fresh task projects, invoked the packaged `controller_control.py` command,
and then called packaged `controller_workflow.execute` in isolated Python
processes with controlled assessor and worker adapters. Project `on` froze
a Controller action and blocked because no Controller adapter was supplied;
it did not silently run a worker. Project `off` froze worker-only, dispatched
one fake worker and reached independent N1 acceptance. Both retained complete
accounting and the read-only status command reported the frozen action. The
focused test passed 1/1. It is now part of the offline X3/X4 gate, and the
subsequent full checked `tools/build_dist.py` exited zero, regenerating
`dist/`. `git diff --check` passed. This proves installed command-to-next-task
control behaviour for these two cases, not a live interactive Claude session
or a production Controller-to-worker invocation. WSL reachability passed;
no provider call was made in this check.

A first single-use WSL root on N04-D1 exercised the live public interpreter
under explicit `on`. Sonnet 5 assessment settled USD 0.0340572, then the
Controller adapter failed before a role invocation: the workflow had sent
only an acceptance digest, while `run_quick` requires the frozen contract
content and its digest. No Controller run directory existed and no worker
started. The root's two later holds were reconciled at zero from that exact
pre-dispatch evidence; total spend was USD 0.0340572, with USD 0 reserved.
`controller_workflow.execute` now passes the complete frozen contract. A
provider-free regression exercises `freeze_acceptance` at the adapter
boundary; the 17-test focused workflow suite and subsequent full checked
build passed. The original root remains blocked and will not be replayed.

The next fresh WSL root passed the same private host preflight. Its live
assessment settled USD 0.0210972. The Controller reached a validated `gap`
handoff after one Opus High Framer call at USD 0.272239; the served root model
matched Opus 5 with no child model. N1 admitted one worker attempt, but passed
the full USD 11.7066638 task remainder to a Q3 launcher that only permits
USD 6 per call. The launcher returned code 64 before its actor `start`
record or credential session. N1's uncertainty API reconciled the worker at
zero and retained the root as blocked: USD 0.2933362 total spent, USD 0 held.
The Controller-to-worker *handoff* is live-proven, but accepted worker
continuation is not. The low-cost Framer gap also makes no uplift claim.

N1 now validates an optional `max_single_call_usd` host capability and caps
each worker reservation to it without reducing the task-wide budget. The Q3
WSL adapter declares its existing USD 6 launcher limit. Invalid cap values
are rejected at admission. Two focused N1 regressions passed; the full
checked build passed and regenerated `dist/`. The current X3 source seal is
the [v5 manifest](../../test/results/2026-09-28-controller-x3-fake-manifest-v5.json),
whose four provider-free paired episodes completed under this source.
A third fresh root was not staged; its preflight stopped before provider work:
the WSL Claude.ai credential fell below its required five-minute freshness
margin. A new WSL sign-in is waiting for the operator's browser code. No
automatic Controller default or X4 exit is claimed.

The operator completed a fresh Claude.ai sign-in and the repository's WSL
credential sync passed. A fresh v3 root reached a validated Controller gap
handoff and one terminal Sonnet worker, but verification blocked. The
single-use preflight froze only three protected paths, whereas Q3's isolated
verification proof sealed all four non-editable actor inputs, including
`acceptance.json`. The worker had completed, and the root settled
USD 0.445757402 API-equivalent with no hold. The blocked root will not be
replayed. This was an experiment-driver contract mismatch, not an accepted
task result. The v4 preflight derives protected paths from the same frozen
actor-file set as Q3 and runs a provider-free isolated proof comparison before
admission.

The v4 provider-free preflight passed and created a new ready root. The live
run then completed assessment, a Controller `worker-ready` handoff, one
Sonnet 5 worker and independent isolated command verification on that same
N1 root. Its terminal state is `accepted`; the worker receipt is terminal,
verification status is `pass`, protected files are unchanged, and the root
has no unresolved budget hold. Total settled usage was USD 0.3748026
API-equivalent, including USD 0.023236 for assessment and USD 0.0408706 for
the worker. The four X4 integration roots together settled USD 1.147953402
API-equivalent. This qualifies a live Controller-to-worker integration path
under explicit `on` for one ordinary fixture, not automatic routing quality,
Controller uplift or a release default.

The live v3 Controller handoff reported that its role had no Graft tool.
Source inspection corroborated a specific mechanism: `CONTROL_ARGS` in
`tools/controller_dispatch.py` restricts the role to `Read,Glob,Grep` under
`--strict-mcp-config`, so Graft is absent from that allowed tool list. This
conflicts with `AGENTS.md` and `docs/GRAFT.md` for Controller roles. Repair
and verify role-level Graft access before X4 exit; do not infer that the
worker's separately qualified Graft setup applies to Controller roles.

The Graft repair added a pre-spend Controller host check, a frozen Graft-only
MCP config and the six explicit retrieval permissions. V5's fresh root
settled USD 0.0262122 for assessment and then blocked before a role call
because the old X2 default-adapter safety gate still applied; it has no held
balance and will not be replayed. V6 used the production role factory through
an explicitly experimental wrapper, reached independent acceptance and
settled USD 0.3964385. Its Framer nevertheless reported no Graft tool. The
installed Claude Code help confirmed that `--safe-mode` disables MCP servers;
the role launcher now omits that flag while retaining restricted built-in
tools, a strict explicit MCP config and the Graft allowlist.

V7's fresh root accepted and settled USD 0.4686023. A separate CLI-init
probe showed the `graft` server connected, all six retrieval tools visible
and no execution tools. Its empty-credential assumption did not prove zero
model activity; its cost is **unknown**, excluded from the root subtotal, and
no zero-cost claim is made. The role stream parser now records MCP status,
available tool names and actual tool-use names in durable telemetry without
persisting tool inputs. V8 then accepted and settled USD 0.304484302. Its
Framer ledger proves `graft_check_freshness` and `graft_repo_map` were called,
with all six Graft tools available and the server connected.

The X2 blanket default-adapter block was replaced by a validated Graft host
preflight and a terminal role-evidence guard. V9 used the **ungated default**
`ControllerRuntimeAdapter`, reached independent acceptance after one worker
attempt and settled USD 0.373506201 with no hold. Its Framer ledger records
connected Graft MCP, all six retrieval tools and actual freshness, file-API
and repo-map calls. Roots v1-v9 together settled USD 2.717196905
API-equivalent, excluding the separate CLI-init probe with unknown cost.
This qualifies a narrow explicit-`on` production integration path; it does
not establish automatic routing quality, multi-role Graft adherence, role
profile suitability or default promotion.

The Controller-only validation was initially factored into
`tools/worker_adapter.py`, which invalidated historical Q4/Q4R source-bound
attestations despite preserving worker behaviour. The qualified worker source
was restored byte-for-byte from the last generated bundle, and the Controller
now projects and validates its Graft-only config locally using the unchanged
worker capability. The Q4/Q4R boundary checks no longer fail on worker source
drift. The full checked build subsequently passed with access to root-owned
historical evidence, and the final X3 v8 paired fake campaign passed with zero
provider calls. The focused X4 suite passed 36/36. The X4 integration exit
and remaining live qualification limits are recorded in
[the X4 result](controller-x4-2026-09-28.md).
