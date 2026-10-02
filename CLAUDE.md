# CLAUDE.md

## Required retrieval and persona

Every task, session, agent and subagent starts with `graft_check_freshness`.
Use scoped Graft search, file API and call graphs before broad repository reads.
Direct reads are for exact edits, verification and unindexed files. If Graft is
unavailable, repair or report the connection before discovery. Put this rule,
the repository root and relevant results in every handoff; each child verifies
its own access. Configuration and limits are in `docs/GRAFT.md`.

Load `ENGINEERING_PERSONA.<class>.md` for the configured model class, using
sonnet when unknown. Also load `ai-prompting.<class>.md`, `python.<class>.md`
for `tools/` or `test/harness/`, and `bash.<class>.md` for fixture `grade.sh`
work. The harness sets the class; never infer it from model quality.

Read the Operator engineering standards in `AGENTS.md` in every session and
carry applicable standards into worker briefs. They are the operator's durable
quality, design, honesty and efficiency requirements.

Be direct, honest and economical with tokens. Verify assumptions and distinguish
observations, inferences and untested risks. Use Australian English, no em
dashes, and plain declarative prose.

## Current work

The bounded release candidate verification completed on 2026-10-01. See
`docs/stage-results/release-candidate-2026-10-01.md` for the result.
Follow `docs/RELEASE-CANDIDATE-2026-10-01.md` and
`handoffs/2026-10-01-bounded-rc.md`. The shipping review, corrected supported claims, frozen bundle, installed
lifecycle checks and full offline gate passed. A 2026-10-02 supplement records
exact Sonnet and Opus account-served IDs and a checked rebuild at
`docs/stage-results/release-candidate-model-identity-2026-10-02.md`. The later
clean-source commit is `f9f141c`, with checked bundle stamp
`2026-10-02-f9f141c`. Its recorded full offline harness and exact-bundle
installation checks passed; publication remains an operator action. B0 remains
default and Controller experimental. The outstanding qualification analysis is
`docs/POST-RC-QUALIFICATION-ANALYSIS-2026-10-02.md`; it proposes new work and does
not reopen completed v7 or historical real-world campaigns. The operator accepted
the next offline qualification deliverable; its manual stage handovers and gates
are in `docs/OFFLINE-QUALIFICATION-IMPLEMENTATION-PLAN-2026-10-02.md`, starting at
`handoffs/2026-10-02-offline-qualification-o0.md`. The plan is prepared; O0-O6
implementation has not started. Automatic session/delegation capability is
documented in `docs/DEVELOPMENT-SESSION-CONTROLS-2026-10-02.md`; no launch was
requested. Controller uplift and the separate real-world policy pilot remain
deferred from this RC. Do not
start further paid X5 screens as part of RC completion. The programme history
below is evidence, not a direction to restart research.

Stages 0-7 of `docs/IMPROVEMENTS-ACTION-PLAN-2026-09-17.md` are complete.
The active programme is `docs/WORKER-ROUTING-ACTION-PLAN-2026-09-19.md`.
Stage N0 is complete. Its historical design contract is
`docs/WORKER-EXECUTION-CONTRACT.md` and its evidence record is
`docs/stage-results/worker-n0.md`.
N0A's design amendment is recorded in
`docs/WORKER-EXECUTION-CONTRACT-v2.md`, with the implementation matrix in
`docs/WORKER-N1-ACCEPTANCE-v2.md` and evidence in `docs/stage-results/worker-n0a.md`.
N1-N5 have been executed; N1's executor and N2's opt-in child DAG remain
subject to their documented host limits. N5 did not qualify a new default.
The 2026-09-26 Q4U development canary completed without routing-quality gain;
see `docs/stage-results/worker-q4u-u3-canary-2026-09-26.md`. N6 stopped before
reserved comparison, with its unmet exit criterion recorded in
`docs/stage-results/worker-n6-pre-reserve-disposition-2026-09-26.md`.
B0 remains the shipping policy. N7 independent review rejected Q4U default
promotion after finding no quality gain, a hidden-grader trust-boundary exploit
and an incomplete source seal; see
`docs/stage-results/worker-n7-2026-09-26.md`. Its full offline harness rerun
passed. N8 consumer integration, full build, 78-file parity and installed
upgrade/rollback checks passed within the documented host scope; see
`docs/stage-results/worker-n8-2026-09-27.md`. The X1 transition handoff is
`handoffs/2026-09-27-controller-remediation-x1.md`; GPT-5.6 Sol / High is
the user-confirmed setting for X1-X6.
Experimental Controller remediation is the current
`docs/CONTROLLER-REMEDIATION-ACTION-PLAN-2026-09-19.md` programme; X0 has
reproduced the defects, frozen its design and passed all 79 offline checks.
X1 has repaired offline campaign stop, cancellation, source binding and failed
cost accounting; its 80/80 offline gate passed. Its evidence is
`docs/stage-results/controller-x1-2026-09-27.md`. The contract is
`docs/CONTROLLER-REMEDIATION-CONTRACT-X0.md`. X2's named Generator dispatch
and task-wide admission passed its checked build and 78-file distribution
parity; see `docs/stage-results/controller-x2-2026-09-27.md`. X3 completed
its offline 48-task corpus, protected and isolation sweeps, sealed paired
provider-free campaign and checked build; see
`docs/stage-results/controller-x3-2026-09-28.md`. This does not establish
live quality uplift. X4's integration gate passed: installed auto/on/off
next-task control, fake workflow and recovery cases, checked distribution
build, and one accepted explicit-`on` live Controller-to-worker continuation
through the ungated default adapter. A Framer role's durable stream proves
connected Graft MCP and actual freshness retrieval. Other live roles,
frontier suitability, partial-gap utility and automatic routing quality
remain unqualified for the X5 pilot. See
`docs/stage-results/controller-x4-2026-09-28.md`. X5's v1 prospective screen
stopped on a worker decision and an unsupported Sonnet High host cell. V2
stopped its host canary before provider launch because the Q3 launcher
rejected Sonnet High; its USD 1 local hold remains uncertain. V3 used the
existing Q4R boundary, qualified a settled Sonnet High call and auto-routed
C03-D1 to Controller. Its second task, C03-D2, correctly presented a clear
worker frame and missed the predeclared four-of-four suitable-task gate.
The screen stopped before any worker or Controller pilot episode. A
provider-free [candidate audit](docs/stage-results/controller-x5-public-candidate-audit-2026-09-28.md)
also found that current synthetic actor source comments reveal their single
faults, limiting any simple overlay's claim to need Controller. See
`docs/stage-results/controller-x5-screen-v3-stop-2026-09-28.md`. V4 added
four X5-only actors with independent protected acceptance. Its first paid
assessment stopped at N3 on an unresolved frame (USD 0.050811401). V5 fixed
the public evidence packet and prompt field definitions; its three settled
assessments cost USD 0.194320202. Payment and feature routed to Controller,
but the lease task validly routed to worker because its executable effect was
local and recoverable. The v5 screen stopped at that first miss without a
pilot. See `docs/stage-results/controller-x5-v5-stop-2026-09-29.md`. V6 added
shipment and migration cases that model consequential outcomes, plus unchanged
payment, feature and two X3 controls. Its new cases passed actor, reference,
wrong-repair, isolated grader and actor-isolation checks; see
`docs/stage-results/controller-x5-v6-design-2026-09-29.md`. The six-task paid
public screen passed its predeclared routing gate with six settled calls
costing USD 0.338381801; see
`docs/stage-results/controller-x5-v6-screen-2026-09-29.md`. The paired
18-episode B/S/A pilot was frozen and approved with an USD 144 ceiling. It
stopped after six settled episodes costing USD 4.129411806 when a live
measurement-contract defect became clear: all six repairs passed protected
behaviour, but an undisclosed report schema and unavailable worker execution
tool kept every published quality score at 50/100. Episode 7 was never
started; see `docs/stage-results/controller-x5-v6-pilot-stop-2026-09-29.md`.
Do not resume or replay the v6 pilot. A separately approved v7 continuation
completed the remaining 12 episodes with fresh roots and USD 3.020660704
settled spend. All four suitable task pairs passed protected functionality
in B, S and A; A showed no quality or acceptance gain and cost more. The
ordinary-worker A control had an unsupported completion claim, while the
missing-decision A control correctly clarified without a worker. See
`docs/stage-results/controller-x5-v7-result-2026-09-29.md`. X5 development
comparison is complete with no promotion case; B0 remains default. X6-X8
were not entered for this candidate; see
`docs/stage-results/controller-x5-candidate-closure-2026-09-29.md`. The
separate X5 recovery R3 feasibility stopped after its first producer. R01
passed the public check but missed one critical protected case; it supplied
no public recovery trigger. A settled-budget shape bug in the eligibility
helper was repaired after the stop, invalidating R3's frozen runtime package.
Do not resume or replay R3; its only paid receipt is USD 0.16955. See
`docs/stage-results/controller-x5-recovery-r3-stop-2026-09-30.md`. The
separately prepared and approved R4 R02 producer settled USD 0.1179006,
passed both public and protected checks on its first attempt, and produced
no eligible recovery continuation. Do not replay R4. Neither R3 nor R4
measured a matched Controller uplift; see
`docs/stage-results/controller-x5-recovery-r4-result-2026-09-30.md`. The
next development candidate pauses at a settled first public failure and
compares one matched Sonnet-low continuation call with and without a bounded
Controller investigation. Its provider-free checkpoint and twin mechanism
passed the full 83/83 offline harness and checked distribution build; no new
prospective paired comparison or promotion has been established. See
`docs/stage-results/controller-x5-next-candidate-2026-09-30.md`. The
separate, manifest-bound P02 first-failure engineering smoke cost USD
0.113327401 and passed public and protected acceptance on its first call.
It yielded no Controller continuation and must not be replayed; see
`docs/stage-results/controller-x5-first-failure-p02-smoke-result-2026-09-30.md`.
The fresh F01 attrs development producer also passed public and protected
acceptance on its first call, settling USD 0.1270084 with no S/A continuation.
The four first-call screens together spent USD 0.527786401 reported
API-equivalent and yielded zero matched Controller pairs; see
`docs/stage-results/controller-x5-first-failure-f01-result-2026-09-30.md`.
The separate F02 Click producer also passed public and protected acceptance
on its first call, settling USD 0.0695534 with no S/A continuation. The five
first-call screens together spent USD 0.597339801 reported API-equivalent
and yielded zero matched Controller pairs. Do not replay any of them. See
`docs/stage-results/controller-x5-first-failure-f02-result-2026-09-30.md`.
F03, adapted from a Tenacity cancellation report, also passed public and
protected acceptance on its first call, settling USD 0.2023272. Six
first-call screens now total USD 0.799667001 reported API-equivalent with
zero matched Controller pairs. The first-failure-only route is closed for
further screens of this task shape; see
`docs/stage-results/controller-x5-first-failure-f03-result-2026-09-30.md`.
The next provider-free candidate is a public-only post-success risk review.
Its accepted-root snapshot helper and fake negative controls passed the full
83/83 offline harness; no new paid case, matched review pair or uplift is
claimed. See
`docs/stage-results/controller-x5-public-risk-review-design-2026-09-30.md`.
The fresh K01 public-success review produced an accepted USD 0.0748108
producer and a qualified USD 0.1009298 S review. A's USD 0.044417801 public
assessment and USD 0.854538 Controller investigation settled, but its worker
preflight failed in the isolated Graft mount namespace before provider launch.
That worker hold was reconciled at USD 0 and A blocked. The Controller
handoff lacked the predeclared issuer check; no protected oracle was read and
no matched effect exists. The K01 subtotal is USD 1.074696401 reported
API-equivalent. Do not replay K01. The next design must give Controller a
frozen post-success review goal and separate its hidden evaluation view from
worker launch; see
`docs/stage-results/controller-x5-public-risk-k01-stop-2026-09-30.md`.
The distinct K02 payment case repaired the two provider-free mechanism
faults: S/A share an explicit frozen review goal and Controller's worker
can launch after leaving the hidden evaluation mount view. Its checked
distribution build and final 83/83 offline harness passed. The ordinary
K02 producer settled USD 0.086191601, passed public acceptance and the
predeclared public duplicate-debit follow-up, closing the risk before
review. S/A remained ready at zero calls and zero spend. Do not replay K02;
it provides no matched Controller uplift. Further paid screening needs a
fresh external-validity audit of real multi-system tasks, not another
near-duplicate authored regression. See
`docs/stage-results/controller-x5-public-risk-k02-result-2026-09-30.md`.
The provider-free external audit rejected E01 pytest-asyncio as a blind paid
case because its public issue and linked PR expose the fix layer. E02 Alembic
reproduced duplicate CHECK constraints on Windows and WSL but showed no
consequential residual risk in the isolated reproduction. Neither case
authorises a paid X5 producer. See
`docs/stage-results/controller-x5-external-validity-audit-2026-09-30.md`.
E03 HTTPX reproduced double-cancellation pool exhaustion on Windows and
WSL. A provider-free cancellation-only control passed that symptom but
failed a separate injected close-retry probe; two repair variants passed
both and a concurrent-close probe. The later public PR already publishes
the diagnosis, retry tests and repair, so E03 is rejected as a blind paid
X5 case. No E03 producer is authorised. See
`docs/stage-results/controller-x5-external-e03-preflight-2026-09-30.md`.
The next provider-free external intake screened eight more recent open
reports. AnyIO E06 reproduced a real interpreter shutdown hang on Windows
and WSL, but a linked public PR already proposes a repair under maintainer
review. The other seven reports disclose the fault path or patch. None is a
blind paid X5 case and no Controller uplift is measured; see
`docs/stage-results/controller-x5-external-intake-b-2026-09-30.md`.
A separate hash-ordered development frame froze 29 current open issues from
seven public Python repositories. All 29 were screened in hash order with
zero paid admissions. E17 Pydantic reproduced its default-call schema
mismatch on Windows and WSL, but independent alias switches make a changed
default an unsettled compatibility question without a qualified oracle.
E17 is rejected for blind paid work; this frame has zero qualified leads.
This frame is not a reserved or representative sample. See
`docs/stage-results/controller-x5-external-development-frame-2026-09-30.md`.
A separate prospective bug-labelled frame C froze 64 open, non-PR issues
from seven other Python repositories. All 16 bug-labelled rows were screened
in hash order with zero paid admissions. Natural reports mostly disclose
the fault path or repair; the remaining CI, typing and RDS cases lack a
deterministic local task or settled independent contract. No Controller
uplift is measured. See
`docs/stage-results/controller-x5-external-bug-frame-c-2026-09-30.md`.
A third adaptive frame D froze 18 open issues created since 2026-09-27
across twenty Python repositories, without a bug-label filter. All 18
were screened in hash order with zero paid admissions; recent natural
reports still disclosed repairs or lacked a settled local task. The two
Ruff reports were ruled out by public maintainer discussion and missing
WSL Rust tooling. No Controller uplift is measured; see
`docs/stage-results/controller-x5-external-recent-frame-d-2026-09-30.md`.
A fourth adaptive frame E tested GitHub opening-event bodies rather than
current issue pages. A fixed first-event-page cohort across sixteen Python
repositories produced four openings; all four failed blind paid admission
because the opening report disclosed the repair, was a policy discussion,
or lacked a distinct consequential follow-up gap. Its exact body bindings
passed 4/4; no paid call or uplift claim followed. The event feed was not
strictly time ordered, so this is a page cohort, not a complete time window.
See `docs/stage-results/controller-x5-opening-event-frame-e-2026-09-30.md`.
A wider historical opening-event frame F froze 38 openings from 26 fixed
first-event-page cohorts and screened 30 hash-selected rows, including seven
prior overlaps. All 30 failed blind paid admission because their opening
text disclosed a cause or repair, requested policy/docs/deprecation, lacked
deterministic local acceptance, or was not a task. A provider-free Jinja
StrEnum symptom reproduced in a fresh template environment, but the
maintainer closed its proposed behaviour as not planned. There was no paid
call or measured Controller uplift; see
`docs/stage-results/controller-x5-opening-event-frame-f-2026-09-30.md`.
The authored httpcore H01 development actor calibrated sync/async assigned
connection cleanup on Windows and WSL, and its isolated evaluator resisted
two tested tamper variants. The public issue and PR disclose the repair, so
H01 is not natural blind evidence. One B0 producer settled USD 0.214186 and
passed the four frozen checks at 100/100; its first-pass stop made S/A
ineligible. A separate post hoc isolated schedule then showed its sync and
async expiry branches still close assigned connections. Preserve the frozen
score, do not replay H01 or pay S/A against a revised grader, and treat it as
evaluator calibration only. There is no measured Controller uplift or
promotion case. See
`docs/stage-results/controller-x5-h01-producer-result-2026-09-30.md`.
The next provider-free authored-case screen rejected the repository's pinned
urllib3 copy for a proxy redirect case because its low-level and high-level
calls already removed sensitive headers across origins. A fresh WSL run
reproduced the separate pytest-asyncio fixture lifecycle issue; see
`docs/stage-results/controller-x5-next-authored-feasibility-2026-09-30.md`.
The authored H02 actor is self-contained and fits Q4U's one-editable,
200-file and byte limits. Its 19-check provider-free matrix separates
baseline, a public-only narrow control and two repair variants. Its corrected
grader scores these 30, 50, 100 and 100 and rejects protected-file tampering
and grader-output spoofing. H02 and H02b producer roots stopped before a
provider call and were reconciled at USD 0. H02c's one Sonnet-low producer
settled USD 0.5318208 and failed its public check. Its corrected protected
score is 30/100; the historical zero was caused by an AST scope-check defect.
See `docs/stage-results/controller-x5-h02c-result-2026-09-30.md`. A matched
S/A pair was frozen and prepared from identical H02c bytes. Its permissioned
offline gate passed 83/83. Automatic approval review twice rejected paid S
dispatch until the operator specifically authorised sending the 159 authored
fixture files to Claude.ai. S and A then settled USD 0.406186401 and USD
1.049606101 respectively. Both failed public acceptance and scored 30/100;
A failed the frozen actionable-handoff condition. Its Controller made two
Framer calls, then stopped because the model expanded the single frozen
acceptance criterion into four, triggering an exact-match integrity gap
before Verify or Generate. No H02 Controller uplift or promotion case is
measured. Do not replay H02. The post-result provider-free repair now rejects
a Framer batch that
changes frozen external acceptance before Scribe commit, permits one bounded
correction, and preserves the external criteria on persistent mismatch. Its
focused integrity suite passed 12/12, the checked distribution build passed,
and the final full offline harness passed 83/83. This does not revise H02 or
establish Controller uplift. The next fresh case needs complete, shared public
acceptance evidence; see
`docs/stage-results/controller-x5-h02-sa-result-2026-09-30.md`.
The H03 provider-free follow-up reconstructs the H02 acceptance bug in an
isolated 52-file authored actor. Windows and WSL fake-role calibration
separates baseline, initial-only partial, and two complete repairs at
10/45/100/100 protected quality. Its source audit exposed a third,
critique-triggered Framer re-entry path omitted by the first pre-commit
repair; that production path is now guarded and the focused integrity suite
passes 13/13. H03's frozen catalogue binds its public actor, private oracle,
two host probes and source-cited public risk. No H03 provider call or uplift
is claimed. A separately frozen public critique re-entry check fails the
baseline and public-passing partial repair but passes both complete repairs
on Windows and WSL; it can close a public-success case before S/A spend.
The checked distribution build and final full offline harness passed 83/83
after the third-path edit; see
`docs/stage-results/controller-x5-h03-authored-design-2026-09-30.md`.
The separately approved H03b pilot stopped after one identity-valid Sonnet-low
producer, settling USD 0.184233601 with no unresolved charge. Its patch committed
an altered acceptance criterion before correction, then exhausted the public
Verifier script. Public acceptance failed, so no S/A review was eligible. The
frozen private grader also raised that exception; its score remains unavailable.
Do not replay H03b or assign a retrospective score. No Controller uplift is
measured; see `docs/stage-results/controller-x5-h03b-result-2026-10-01.md`.
The operator has directed autonomous
completion of both programmes
subject to their evidence gates, required host model changes and decisions
that cannot be resolved from evidence. Follow
`docs/REMEDIATION-EXECUTION-PROTOCOL-2026-09-19.md` for stage and cost gates.
The earlier Controller programme has R0-R4 records and R5 scaffolding, but its
live evaluation remains paused pending the documented remediation. The shipped
B0 default remains unchanged. Earlier plans and handoffs are historical
evidence, not active instructions.

This repository builds a cost-routing bundle for Claude Code subagents: fifteen
model/effort definitions, a ledger-aware resolver, acceptance verification,
handoffs and a budgeted multi-role Controller. The consumer guide is
`src/README.md`. Runtime behaviour belongs in `src/` and reaches `dist/` only
through `tools/build_dist.py` after the offline harness passes.

`src/ORCHESTRATOR_CORE.md`, `src/ROUTING.md` and `src/LIFECYCLE.md` are product
deliverables. They do not route development work in this repository. Do not
follow a half-edited product prompt as a session instruction. Dogfooding runs
only from a separate consumer project installed from `dist/`.

## Development handoffs and delegation

Read `docs/DEVELOPMENT-MODEL-CALIBRATION.md` before recommending or assigning
a development model/effort. It alone owns current selection calibration;
record its revision/row in each handoff. Plans and dated reviews are references,
not competing defaults. Explicit operator selections take precedence. Resolve
stale pending handoff settings before use and preserve executed history.

Before changing model or effort, starting a fresh session, or launching any
agent or subagent, create a concise handoff with `tools/handoff.py new`, fill
every section, validate it with `tools/handoff.py check`, and notify the
operator. Include target model/effort, dated direct API cost and elapsed-time
ranges, token/cache assumptions, uncertainty and any separate paid experiment
subtotal. Unknown cost is not zero. The receiving session reads the named file
first. A completed stage alone does not require a switch.

For Claude Code development delegation, record the assessment line, resolve it with
`python3 tools/route.py --from-line "<line>" --project . --explain`, and launch
the named cell. This is repository-development routing, not product dogfooding.
For Codex development, use the calibration and exposed host controls; do not
treat Claude worker cells as Codex model selections.

## Load-bearing invariants

1. Agent teams must remain off; teammates inherit the lead's effort.
2. Agent-tool delegation selects through `subagent_type` and never passes
   `model`, which overrides worker frontmatter.
3. `CLAUDE_CODE_EFFORT_LEVEL` overrides worker effort.
4. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` flattens the model dimension.
5. Haiku is available only through `worker-haiku-default`; omit the effort
   argument because Haiku uses its provider default.
6. An `availableModels` exclusion substitutes another model rather than failing.
7. A user-stopped worker is not resumable; E4 is the empirical evidence.

The harness asserts every statically observable invariant. Do not change the
routing table, persona or worker frontmatter without regeneration and the full
harness. A routing row also needs a confirmed fixture and before/after routing
measurement because visible destinations can bias assessment.

## Working practice

- Preserve pre-existing work and local configuration. Generated workers come
  from `src/WORKER_PERSONA.md`; never hand-edit all fifteen.
- Diagnose observed state before patching. Record new platform behaviour in
  `docs/FINDINGS.md`, labelled verified or unverified with date and version.
- Nothing ships from `dist/` until the harness passes. Rebuild through
  `tools/build_dist.py`; do not edit generated bundle files directly.
- A `claude -p` benchmark, probe or Controller run requires a stated USD cost
  projection before execution and measured cost afterwards. Ask first only
  above USD 100. Ordinary offline checks do not need approval.
- Model identity, routing correctness and routing appropriateness are separate.
  Use observed model/effort evidence, acceptance evidence and fixtures rather
  than treating a good-looking answer as proof of correct routing.
- Keep unresolved research in `docs/PREMISES.md`, `docs/FINDINGS.md` and the
  active roadmap instead of expanding this standing file.

## Source map

- `src/ORCHESTRATOR_CORE.md`: stable installed operating contract.
- `src/ROUTING.md`, `src/LIFECYCLE.md`: detailed shipped reference source.
- `src/WORKER_PERSONA.md`: generated worker source.
- `src/System/`: Controller role, technique and record contracts.
- `tools/route.py`: resolution, pending ledger, completion and recovery.
- `tools/system_controller.py`: budgeted quick-mode state machine.
- `tools/build_dist.py`: checked bundle assembly.
- `test/harness/check.py`: complete offline gate.
- `docs/DECISIONS.md`, `docs/FINDINGS.md`: decisions and verified behaviour.

Run dogfooding only from a consumer checkout installed from `dist/`. Record its
bundle version, tasks, selected cells and assessment in `test/results/`.
