# Action plan: the-system

Adopted 2026-09-10 on branch `the-system`. Authored by Claude (Fable 5.1, the
Cowork session that produced `docs/REVIEW.md`), reviewed and approved by Jeb.
Status of the plan as a whole: **not started**.

This plan does two things. It fixes the problems `docs/REVIEW.md` found in the
orchestrator as it stands, and it integrates the problem-solving framework in
`src/System/SYSTEM.md` with the orchestrator, on the terms `REVIEW.md` sets
out. Read `REVIEW.md` first; every stage below cites it rather than restating
its evidence.

## How this plan is executed

`CLAUDE.md`'s "Active plan" section is the binding protocol. In short: one
stage per session, the session confirms with Jeb that it is on the stage's
required model class and effort before starting, Jeb approves the stage
explicitly, each task is its own commit on `the-system` with the harness
green, and the checkboxes and status lines in this file are updated in the
same commit as the work they record.

Status values for a stage: `not started`, `in progress (since <date>)`,
`done (<date>, <commit>)`, `blocked (see D<n>)`. A blocked stage is never
reworded in place; the block is recorded as a decision entry and the stage
stops.

Stages are ordered. Stages 10 and 11 depend only on Stages 0 to 2 and may be
pulled forward at the Stage 2 gate if Jeb prefers the core product improved
before the framework is integrated; that choice is recorded as a decision
entry when it is made.

Model and effort are recommendations grounded in this project's own evidence
(`REVIEW.md`: eight of eight benchmark tasks cleared at the cheapest cell) and
in `SYSTEM.md` section 5's role assignments. Where a stage names a fallback,
the fallback is used only after the recommended model has demonstrably failed
the stage's exit criteria once, and the switch is recorded in the stage's
status line.

## Model and effort by stage

| Stage | Title | Model | Effort | Persona files to load |
| :--- | :--- | :--- | :--- | :--- |
| 0 | Migration and repair | sonnet | low | `ENGINEERING_PERSONA.sonnet.md`, `ai-prompting.sonnet.md` |
| 1 | Documentation and harness hygiene | sonnet | medium | sonnet persona, `ai-prompting`, `python.sonnet.md` |
| 2 | A reporting bar for routing runs | sonnet | high | sonnet persona, `ai-prompting`, `python.sonnet.md` |
| 3 | Premise ledger for the routing layer (Frame) | opus | xhigh | `ENGINEERING_PERSONA.opus.md`, `ai-prompting.opus.md` |
| 4 | Recover the missing half of SYSTEM.md | opus | high | opus persona, `ai-prompting.opus.md` |
| 5 | Platform findings for the blackboard substrate | sonnet | medium | sonnet persona, `ai-prompting`, `python.sonnet.md` |
| 6 | B0 and the tasks the floor cannot clear | opus | high (xhigh for a hardening round) | opus persona, `ai-prompting.opus.md` |
| 7 | The Controller in code, quick mode | sonnet | high (opus high on a failed review) | sonnet persona, `ai-prompting`, `python.sonnet.md` |
| 8 | Fleet versus baseline | opus | high | opus persona, `ai-prompting.opus.md` |
| 9 | Wire the result into routing | opus | high | opus persona, `ai-prompting.opus.md` |
| 10 | Two-stage classifier: design | opus | xhigh | opus persona, `ai-prompting.opus.md` |
| 11 | Two-stage classifier: implement and measure | sonnet | high | sonnet persona, `ai-prompting`, `python.sonnet.md` |
| 12 | Close-out | sonnet | medium | sonnet persona, `ai-prompting.sonnet.md` |

The switch is made with `/model`, choosing the effort level from the same
picker where the installed version offers it. `CLAUDE_CODE_EFFORT_LEVEL` is
never used for this: invariant 3 says it overrides every worker's frontmatter
effort, so setting it for the session would silently flatten the very cells
this repository exists to keep distinct.

## State at handover, 2026-09-10

- `main` is at `125ce43` (D34). Four files arrived with this plan, all
  uncommitted at the time of writing: `docs/PLAN.md`, `docs/REVIEW.md`, the
  amended `CLAUDE.md`, and `src/System/SYSTEM.md`. Jeb said he would create
  the branch and commit them by hand before the first Claude Code session.
  Stage 0 checks `git log` rather than assuming either happened.
- `src/System/SYSTEM.md` was repaired on 2026-09-10 in the same session that
  wrote this plan: CRLF converted to LF, trailing newline added, and the
  fourteen characters a code-page conversion had turned into `?` restored
  as Unicode (twelve `←` and one `≤` in section 3's pseudocode, one `→` in
  section 7), matching the `×` and `÷` that had survived. The seven
  remaining question marks (section 1's Critic row, the six question
  headings at the end) are genuine. It passes the PROSE rules as repaired.
- The last routing evidence is `test/results/2026-09-08-routing-opus-af94deb-5a7585d-summary.md`
  (18 fixtures, 3 runs) and the F05-only batch after D33. The last benchmark
  evidence is T8 (D30). All of it is steering-grade on the routing side; see
  Stage 2.
- Bundle installed in `orchestrator-scratch`: `2026-09-07-af94deb`. Nothing
  since D28 has touched `ROUTING.md`, so no rebuild is pending.

## Proposed acceptance criteria for the integration

`SYSTEM.md` requires acceptance criteria to be fixed before any generation.
These are proposed here and fixed at Gate A (end of Stage 3), where Jeb may
change them. After Gate A they are not revised in the light of results.

1. A benchmark task set exists on which `worker-sonnet-low`'s confirmed pass
   rate fails the reporting bar (nine runs, 95 percent Wilson lower bound
   above 0.7) and some higher cell, or the fleet, clears it. Without this,
   nothing above the floor is measured and Stages 8 and 9 have no subject.
2. On that set, the fleet in quick mode beats B0 (one cell running the
   eight steps as a single prompt) at the reporting bar, at a cost per
   solved task no more than three times B0's. The multiplier is Jeb's to
   set at Gate A; three is the proposal.
3. Every routing row above the floor is either backed by a measured
   frontier or removed. Judgement fixtures alone no longer back a row that
   routes above `worker-sonnet-low`.
4. The harness stays green at every commit and no invariant is weakened.
   A charter amendment (Stage 7 names one) is a decision entry, not a quiet
   edit.
5. No routing-table change is described as confirmed below nine runs per
   affected fixture. Below that it is steering.

If criterion 2 fails, the integration's deliverable is the B0 brief as a
handover template for the top rows, and that outcome is recorded as a result,
not a failure. `SYSTEM.md`'s own words: "if it does not beat it by a margin
that pays for itself, you have a prompt, not a system."

## Human gates

Beyond the per-stage approval `CLAUDE.md` requires:

- **Gate A**, end of Stage 3: Jeb fixes the acceptance criteria and the goal
  ladder. Cheap, high leverage, the gate `SYSTEM.md` puts first.
- **Gate B**, start of Stage 8: Jeb approves the spend before the fleet runs.
  The pre-registration is presented with the cost estimate attached.
- **Gate C**, end of Stage 9: Jeb accepts or rejects the wiring into
  `ROUTING.md` on the before-and-after evidence.

No gate sits inside generation. A session that wants approval mid-stage for
something the stage did not anticipate records the question as a decision
entry and stops, rather than improvising.

---

## Stage 0. Migration and repair

Status: **not started**
Model: sonnet, low. Mechanical git and file work; nothing here needs judgement.

Purpose: confirm the plan landed on the branch as Jeb committed it, record
its adoption in the ledger, and leave a clean, green tree for Stage 1.

Entry: a Claude Code session in this repository, on any branch.

Tasks:

- [ ] 0.1 Run `git branch --show-current`. If it is not `the-system`, and
      the branch exists, check it out; if it does not exist, create it with
      `git checkout -b the-system` from `main` at `125ce43` or later. Then
      `git status --short`: if `CLAUDE.md`, `docs/PLAN.md`, `docs/REVIEW.md`
      or `src/System/SYSTEM.md` are still uncommitted, commit them now as
      one change ("adopt the staged plan; add SYSTEM.md, repaired") before
      going further. Note in this task's tick which of the two happened.
- [ ] 0.2 Run `python3 test/harness/check.py`. PROSE must pass with
      `SYSTEM.md` included (it is under `src/**/*.md`, which the check
      globs) and with `PLAN.md` and `REVIEW.md` under `docs/*.md`. All
      three were checked against a replica of the PROSE rules before they
      were written; this task confirms it against the real harness. Fix
      any finding in the same task.
- [ ] 0.3 D35, a decision entry recording: the branch and its purpose; that
      `CLAUDE.md` gained an "Active plan" section and this is a charter
      amendment; the approval protocol; that the plan and review were
      authored by Claude on 2026-09-10 and approved by Jeb; the commit in
      which Jeb landed the four files; the `SYSTEM.md` repair (what was
      restored and that Unicode was chosen); and that `SYSTEM.md` is the
      second half of an exchange whose first half (the eight-step sequence
      and the forty techniques) is not in the repository, which Stage 4
      addresses.
- [ ] 0.4 Update this stage's status line and commit it.

Exit criteria: on `the-system`, tree clean, all four files committed,
`check.py` reports 0 failing, D35 present.

Cost: no model calls beyond the session.

## Stage 1. Documentation and harness hygiene

Status: **not started**
Model: sonnet, medium. Load `python.sonnet.md` for task 1.3.

Purpose: the stale statements and the one remaining evidence-loss defect
`REVIEW.md` lists under "Smaller and concrete". Each task is its own commit.

Tasks:

- [ ] 1.1 `test/fixtures/README.md`: eighteen fixtures, not seventeen; F17's
      gap was closed by D9 and the "Coverage" paragraph is rewritten from the
      current table (F18 backs the `worker-fable-xhigh` row; F19 was removed
      by D27); the review-status line names F18's `assigned_by` date.
- [ ] 1.2 `test/fixtures/benchmark/README.md`: T1 to T8 exist; two sentences
      on the open-task grader convention and the three grader defects found
      so far (D16, D17, D30) and what each taught.
- [ ] 1.3 `test/harness/benchmark.py`: the docstring says six tasks; say
      eight and that new tasks are discovered from the directory. Then the
      filename defect: result files are keyed by date and bundle only, so a
      `--tasks T7` run overwrote the six-task result under the same name
      (`docs/DECISIONS.md` D20's pre-registration outcome records where each
      version survives in git). Fix it exactly as D34 fixed
      `score_routing.py`: fold the task subset into the filename, and fall
      back to `-2`, `-3` suffixes for anything that still collides. Recover
      the overwritten six-task original and its replication from git history
      into distinctly named files under `test/results/`, using the commits
      `git log --oneline -- test/results/2026-09-07-benchmark-04d2acc.md`
      lists. Record as D36.
- [ ] 1.4 `docs/COST.md`: recompute against the installed bundle
      (`2026-09-07-af94deb`; the commands are in the file), and add one
      measured line the file lacks: the cost of a routing verdict against
      the cost of the work it routes. Mean opus verdict cost per fixture
      comes from the `-summary.md` routing files (total cost divided by
      fixtures times runs); mean `worker-sonnet-low` cost per run comes from
      the benchmark result files. State both and their ratio. This is the
      "classification may cost more than the work" point in `REVIEW.md`,
      made into a number.
- [ ] 1.5 `CLAUDE.md` "Open questions worth developing": add the three
      `REVIEW.md` found missing: no benchmark task yet fails the cheapest
      cell, so nothing above the floor is measured; the router's own cost
      is not on the ledger; horizon is the least reliable axis and the
      table has been adapting to that without saying so. Keep the existing
      entries untouched.
- [ ] 1.6 Update this stage's status line and commit it.

Exit criteria: harness green after every commit; D36 present; the recovered
six-task result files exist under distinct names; `COST.md` carries the
verdict-versus-work line.

Cost: no model calls beyond the session.

## Stage 2. A reporting bar for routing runs

Status: **not started**
Model: sonnet, high. Load `python.sonnet.md`.

Purpose: `REVIEW.md`, "The routing side has no reporting bar". The benchmark
refuses to claim anything below nine runs; the routing side has changed the
table on three. Give `score_routing.py` the same two-threshold discipline and
record the policy.

Tasks:

- [ ] 2.1 `score_routing.py`: label every rendered file and summary with its
      grade. `steering` when runs are fewer than nine; `reporting` at nine
      or more. In the summary, add a per-fixture column stating whether that
      fixture's 95 percent Wilson lower bound exceeds 0.7, and an overall
      line stating how many fixtures clear it. The Wilson function already
      exists; this is presentation and one comparison.
- [ ] 2.2 D37, the policy: a change to `ROUTING.md`'s table or to a
      fixture's assessment is called confirmed only on a reporting-grade run
      for every fixture the change touches. Below that it is steering, and
      the ledger entry says so. Retroactively, without editing them, note
      that D23 through D33 rest on steering-grade runs. This entry also
      records the reason for the asymmetry until now: routing runs cost
      about USD 3 per pass on opus, so nine passes is about USD 27, and
      that was judged too much per decision during calibration. It is not
      too much per table change.
- [ ] 2.3 Optional, Jeb's call at this stage's approval: one reporting-grade
      opus run against the current table, `--runs 9 --record`, about USD 27,
      to establish the branch's baseline. Recommended, because Stages 9 and
      11 need a before-measurement at the bar and would otherwise pay for it
      then.
- [ ] 2.4 Update this stage's status line and commit it.

Exit criteria: a `--runs 9 --dry-run` prints the run plan; a `--runs 3
--record` against a scratch project renders `steering` in the header and the
new column; D37 present; harness green.

Cost: session only, plus about USD 27 if 2.3 is taken.

Gate: at this stage's approval Jeb also decides whether Stages 10 and 11
are pulled forward.

## Stage 3. Premise ledger for the routing layer (Frame)

Status: **not started**
Model: opus, xhigh. This is `SYSTEM.md`'s Framer role, "highest value per
token in the system; a wrong ledger wastes everything after it". Fable at
xhigh is the deep-mode alternative if Jeb wants a second, independent pass;
one pass at opus xhigh is the recommendation.

Purpose: run the framework's first step on the orchestrator itself, and fix
the acceptance criteria before anything is generated. `REVIEW.md`'s five-row
sketch under "The premise ledger, turned on the routing table" is the seed.

Tasks:

- [ ] 3.1 `docs/PREMISES.md`: a ledger of every premise the routing layer
      rests on. One row per premise: id, statement, class (law, maths,
      policy, habit, unverified), source (a decision entry, a file, a run),
      confidence, cheapest verification, status. Cover `ROUTING.md` section
      1's axis definitions, section 2's table and constraints, each
      fixture's assessment (three premises per fixture), `CLAUDE.md`'s
      seven invariants (laws by measurement where FINDINGS verifies them),
      and the assumptions `BENCHMARK-DESIGN.md` names. Cap the ledger at
      forty rows by merging, as `SYSTEM.md` requires; if it will not fit,
      the merging itself is a finding.
- [ ] 3.2 Goal ladder for the project, three rungs: route each task to the
      cheapest sufficient cell; get the same quality for less money than one
      capable cell; and the rung above that, which the Framer states rather
      than this plan. Dissolution check: does the routing problem dissolve
      if the floor does everything? State B0 for the project explicitly
      ("route everything to `worker-sonnet-low`, escalate on failure") and
      what evidence would show the table beats it.
- [ ] 3.3 Metric interrogation: fixture agreement measures agreement with a
      human label, not with a measured frontier. State the metric the
      project should be optimising (cost per task solved at the reporting
      bar) and how far the current instruments are from measuring it.
- [ ] 3.4 Present the acceptance criteria from this plan's "Proposed
      acceptance criteria" to Jeb with any amendments the ledger suggests.
      This is Gate A. Record the fixed criteria verbatim in D38.
- [ ] 3.5 List the platform questions the ledger exposes for Stage 5,
      appended to `test/harness/empirical-checklist.md` as E15 onward, each
      with what to run and what it settles.
- [ ] 3.6 D38: the ledger's adoption, the fixed criteria, the goal ladder,
      the dissolution verdict, and B0 for the project.
- [ ] 3.7 Update this stage's status line and commit it.

Exit criteria: `PREMISES.md` committed and PROSE-clean; every premise has a
class and a cheapest verification; Gate A passed with the criteria recorded;
E15 onward listed; harness green.

Cost: session only.

## Stage 4. Recover the missing half of SYSTEM.md

Status: **not started**
Model: opus, high. Authoring technique briefs is judgement work; the record
schemas that follow are structured and could be done at sonnet high, but one
stage at opus high avoids a switch for a small saving.

Purpose: `SYSTEM.md` refers to "the eight-step sequence from the previous
answer" and "the forty techniques from the previous answer"; neither is in
the repository. Nothing in Stages 6 to 8 can be built without at least the
tier-1 technique families and the record schemas.

Tasks:

- [ ] 4.1 Ask Jeb for the first half of the exchange. If he supplies it,
      commit it as `src/System/TECHNIQUES.md` (the forty briefs) and
      `src/System/STEPS.md` (the eight steps) with provenance in the header.
      If he does not have it, reconstruct the minimum: the eight steps are
      recoverable from section 4's phase table (Intake, Frame, Verify,
      Generate, Critique, Select, Instantiate, Close); the tier-1 families
      are named in section 5 (subtract, re-represent, abduce) and the
      premise operations in section 1 name the rest. Write each tier-1
      family as a brief with the four parts `SYSTEM.md` specifies: trigger
      question, premise operation, output schema, and worked examples in
      relational-form language (one example each is enough to start; three
      is the target). Mark every brief `supplied` or `reconstructed`.
- [ ] 4.2 `src/System/schemas/`: one JSON Schema per record type in section
      4's table: ProblemRecord, PremiseRecord, MeasurementRecord,
      CandidateRecord, CritiqueRecord, SelectionRecord, EvaluationRecord,
      SolutionRecord, GapReport, plus PhaseDigest and BudgetEntry from
      sections 6 and 7. Each schema's description names its single writer
      role. Every free-text field carries a length cap, per section 6.
      Every record carries `id`, `ledger_version` and `references`.
- [ ] 4.3 `tools/validate_records.py`: validates a JSONL file against the
      schemas, standard library only (no dependency beyond what
      `score_routing.py` already uses; if JSON Schema validation without a
      dependency is too much, a hand-written validator over the eleven
      types is acceptable and simpler). `check.py` gains a SCHEMA check
      that example records under `test/fixtures/system/` validate, and that
      a deliberately broken example is rejected.
- [ ] 4.4 `src/System/ROLES.md`: one brief per role (Framer, Verifier,
      Generator template with the technique family as a parameter, Critic,
      Selector, Librarian), each stating its input slice, its output
      schema, and the rule that it emits new records referencing old ids
      and never edits another role's record. The cell assignment per role
      is configuration, given as `SYSTEM.md` section 5's quick-mode column
      and marked in the file as a prior to be measured in Stage 8.
- [ ] 4.5 D39.
- [ ] 4.6 Update this stage's status line and commit it.

Exit criteria: briefs for at least the three tier-1 families; eleven
schemas; validator passing on examples and rejecting a broken one; ROLES.md
committed; harness green with the SCHEMA check counted.

Cost: session only.

## Stage 5. Platform findings for the blackboard substrate

Status: **not started**
Model: sonnet, medium. Load `python.sonnet.md`. Empirical work in
`orchestrator-scratch`, recorded in `docs/FINDINGS.md`.

Purpose: `REVIEW.md`, "The substrate has no blackboard". Four questions the
Controller's design depends on, answered by observation before any design
commits to them. Each is unverified as of 2026-09-10.

Tasks:

- [ ] 5.1 Cache prefix sharing. Run three `claude -p --output-format json`
      invocations in parallel from one Python process, each with an
      identical static prefix of several thousand tokens followed by a
      different short task. Compare `cache_read_input_tokens` across the
      three. Settles whether `SYSTEM.md` section 5's cache layout (static
      block, ledger block, role brief) can be realised with per-role
      invocations.
- [ ] 5.2 Schema rejection before a model sees a record. Test whether a
      PreToolUse hook on Write, configured in the scratch project, can
      reject a file that fails validation when the writer is a worker
      spawned inside a `claude -p` session. If hooks do not reach workers,
      record that; the Scribe then validates after the fact and the
      Controller discards, which is weaker but sufficient.
- [ ] 5.3 Concurrency. N parallel `claude -p` processes from one parent:
      rate-limit behaviour, any shared-state interference, and the largest
      N observed to work. Quick mode needs three; deep mode up to twelve.
- [ ] 5.4 Per-role cost. One Frame call at the Stage 4 default cell, one
      Verify, one Generate, one Critique, on a toy problem, each with its
      brief; record cost, tokens and wall clock. These are the parameters
      Stage 8's pre-registration needs.
- [ ] 5.5 Record every result in `docs/FINDINGS.md` with the installed
      version, mark E15 onward done in the checklist, and log the session
      in `test/results/<date>-empirical-system.md`.
- [ ] 5.6 Update this stage's status line and commit it.

Exit criteria: four FINDINGS rows with a version and evidence each; no
change to `src/`.

Cost: about USD 2 to 5 in `claude -p` calls, a guess with the assumption
stated: fewer than twenty short calls, most at sonnet.

## Stage 6. B0 and the tasks the floor cannot clear

Status: **not started**
Model: opus, high. Move to opus xhigh only for a hardening round (task 6.3's
rule), and record the switch.

Purpose: two things `REVIEW.md` says are missing and `SYSTEM.md` says come
first. The single-model baseline the fleet must beat, and a benchmark task
that `worker-sonnet-low` measurably fails, without which nothing above the
floor is evidence.

Tasks:

- [ ] 6.1 `src/System/B0_BRIEF.md`: one handover prompt that runs all eight
      steps in a single worker. Output contract: a `ledger.jsonl` of records
      conforming to the Stage 4 schemas, and a `REPORT.md` carrying the
      answer, B0 for the problem, and the non-negotiable from `SYSTEM.md`
      section 8: which premises are unverified and load-bearing.
- [ ] 6.2 Benchmark tasks T9, T10, T11, a new shape. Each is a small
      repository plus a `PROBLEM.md` whose stated constraints include one or
      more planted false premises: a habit or policy presented as a law. The
      intended solution is reachable only by reclassifying that premise. The
      grader stays an exit code, in three checks: the report names the
      planted premise as reclassified; it cites an artefact file that exists
      and contains the measurement output the Verifier must have produced by
      actually running the check; and the chosen solution matches the
      expected shape by string match, T5 to T8 style. Test each grader
      against a correct report in two phrasings, two plausible wrong ones,
      and one adversarial one before any run (the D16 and D30 lesson), and
      record the results in the pre-registration.
- [ ] 6.3 Pre-register in `test/results/<date>-T9-T11-preregistration.md`
      on the T7 template, with this prediction stated outright:
      `worker-sonnet-low` fails at least one of T10 and T11 at the reporting
      bar. Hardening rule: if all three clear at the floor, harden once
      (a second false premise and one red herring each), re-run; if they
      clear again, stop hardening, record "the floor keeps winning" as a
      finding, and proceed with the hardest task. Two rounds is the cap,
      matching `SYSTEM.md`'s reframe cap.
- [ ] 6.4 `benchmark.py` gains `--brief <file>`: prepends a brief to the
      handover so the same task can be run raw and with B0. Own commit.
- [ ] 6.5 Run the ladder raw: `python3 test/harness/benchmark.py --project
      "C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch" --tasks
      T9,T10,T11 --confirm --record --fresh`. This is each task's raw
      frontier. Then run with `--brief src/System/B0_BRIEF.md` for B0's
      frontier. Jeb runs both; the session prepares and analyses.
- [ ] 6.6 D40: the results, whether criterion 1 is met, and B0's frontier
      per task.
- [ ] 6.7 Update this stage's status line and commit it.

Exit criteria: three tasks with graders tested five ways; pre-registration
committed before the run; both runs recorded; D40; criterion 1 either met or
recorded as unmet after two hardening rounds.

Cost: the guess, with assumptions: three tasks, each climbing at least two
rungs before clearing (the prediction), search and confirmation at two cells,
per-run cost rising from about USD 0.2 at the floor to an unmeasured figure
at opus (the only data point above the floor is one fable-xhigh run at 103k
tokens). USD 30 to 150 for the raw ladder, similar again for B0. The upper
half of that range is uncertainty, not expectation.

## Stage 7. The Controller in code, quick mode

Status: **not started**
Model: sonnet, high. Load `python.sonnet.md`. The design decisions were made
in Stages 3 and 4 and `SYSTEM.md` section 3 is the specification; this is
implementation from a good brief, which is what `SYSTEM.md` says mid-size
models do well. If the first review of the state machine finds structural
problems, switch to opus high for the rework and record it.

Purpose: the integration shape `REVIEW.md` proposes. Not the orchestrator
persona running the framework; a deterministic Python Controller in
`benchmark.py`'s lineage that spawns the orchestrator's cells via `claude -p`
with role briefs and a file-based blackboard. The persona stays out of this
loop.

Tasks:

- [ ] 7.1 Factor the `claude -p` invocation, permission arguments, checkpoint
      and reset code that `benchmark.py` and `score_routing.py` share into
      `tools/claudep.py`, and make both harnesses import it. Behaviour
      unchanged; harness green; own commit. This is the one refactor in the
      plan and it exists so the Controller does not copy a third version.
- [ ] 7.2 `tools/system_controller.py`, command line: `--problem <file>
      --project <consumer> --mode quick --record`, plus `--dry-run` printing
      the phase plan and `--selftest` (task 7.6). Every run gets a directory
      `runs/<id>/` inside `--project` holding `ledger.jsonl`, a `records/`
      directory, `budget.jsonl` and `digests.md`.
- [ ] 7.3 The Scribe: validates every record against the Stage 4 schemas
      before it is appended; enforces one writer role per record type;
      rejects any candidate citing a ledger version other than the frozen
      one; assigns ids. Code only, no model calls.
- [ ] 7.4 The state machine, quick mode only: Intake, Frame, the Verify
      loop until stable or the verify budget is spent (verify ceiling one
      tool call, no code), Generate with three isolated Generators run as
      parallel `claude -p` processes each given its brief and the frozen
      ledger slice and nothing else, Critique blind (candidates, not
      generator reasoning), Select against acceptance and B0, paper
      falsification only, Close. Termination: acceptance met, dissolved,
      budget spent, or first candidate surviving critique with no unverified
      load-bearing premise, else B0. Reframe cap three. Phase digests under
      300 tokens, produced by code from the records, not by a model.
- [ ] 7.5 The two Controller model calls ("is the ledger stable enough to
      freeze"; "which technique families for this problem type") as
      schema-forced classification at `worker-sonnet-low`, using whatever
      structured-output mechanism Stage 5 found workable, validated on
      return. Everything else the Controller decides is code.
- [ ] 7.6 `--selftest`: runs the state machine over canned records from
      `test/fixtures/system/` with a fake role runner, no model calls, and
      asserts every transition, the stale-version rejection, the
      single-writer rejection, the reframe cap and each termination rule.
      `check.py` gains a SYSTEM check that invokes it.
- [ ] 7.7 Isolation rules written into `ROLES.md` and cross-referenced from
      `LIFECYCLE.md`: a Generator is never resumed, always spawned fresh; no
      role uses `SendMessage` to another; role-private state is discarded at
      phase end. This is where `LIFECYCLE.md`'s resume semantics and
      `SYSTEM.md`'s isolation rule are reconciled by rule rather than left
      to collide.
- [ ] 7.8 D41, including the charter amendment: `CLAUDE.md`'s "no runtime
      beyond Claude Code itself" gains the Controller as the one exception,
      with the reason (`REVIEW.md`, "Two Controllers"). Edit the sentence in
      `CLAUDE.md` in the same commit and cite D41 beside it.
- [ ] 7.9 Update this stage's status line and commit it.

Exit criteria: `--dry-run` prints a correct quick-mode plan; `--selftest`
passes and `check.py` counts it; one real quick-mode run on a toy problem
completes end to end in `orchestrator-scratch` and its `runs/<id>/` directory
contains valid records for every phase; D41 present; harness green.

Cost: session only, plus one toy run at about USD 1 to 3 (five to ten
model calls at cheap cells, per `SYSTEM.md` section 8).

## Stage 8. Fleet versus baseline

Status: **not started**
Model: opus, high. Most of this stage is waiting on runs, so the session's
own token cost is small; opus is here for the pre-registration and the
verdict, which are judgement.

Purpose: `SYSTEM.md`'s own falsification test, run with this repository's
instrument. Criterion 2.

Tasks:

- [ ] 8.1 Pre-register in `test/results/<date>-fleet-v-b0-preregistration.md`:
      predicted pass rate for quick mode on T9 to T11 against B0's Stage 6
      numbers; predicted cost per run from Stage 5's per-role figures;
      predicted cost per solved task for both; the decision rule with the
      Gate A multiplier; the failure shapes expected (forwarder
      confabulation per D20, Scribe rejections, budget exhaustion) and their
      predicted rates.
- [ ] 8.2 Gate B: present the pre-registration with the cost estimate to
      Jeb and wait for approval before any run.
- [ ] 8.3 Run quick mode nine times per task with `--record`. Jeb runs; the
      session prepares the commands with real paths and analyses.
- [ ] 8.4 Compare at the reporting bar: pass rate with Wilson intervals for
      fleet and B0 per task, cost per solved task, and the ratio. Score
      every prediction as held or falsified.
- [ ] 8.5 D42, the verdict, in one of two forms. "System": the fleet beats
      B0 within the multiplier, and Stage 9 wires the Controller in.
      "Prompt": it does not, and Stage 9 wires B0's brief in. Either is a
      result. Include the technique that produced each winning candidate,
      per task, logged as `SYSTEM.md`'s training signal from day one.
- [ ] 8.6 Update this stage's status line and commit it.

Exit criteria: pre-registration committed before the run; nine runs per task
recorded; D42 with an unambiguous verdict and every prediction scored.

Cost: the guess, with assumptions: quick mode at five to ten calls per run,
mostly at sonnet cells with one opus Framer call, about USD 0.5 to 2 per
run; twenty-seven runs; USD 15 to 55.

## Stage 9. Wire the result into routing

Status: **not started**
Model: opus, high. A change to `ROUTING.md`'s table with the before-and-after
fixture discipline; opus is the measured better classifier and the better
judge of what the fixtures now mean.

Purpose: the rows `REVIEW.md` identifies as backed by judgement only, open
and long and consequential, open and medium and contained, and the frontier
row, get a destination with measurement behind it. Which destination depends
on D42.

Tasks:

- [ ] 9.1 Design the destination. If D42 says "system": how the
      orchestrator persona hands a task to the Controller (a worker cell
      whose brief is "run `tools/system_controller.py` on this problem and
      return its `REPORT.md`" is the least invasive; the persona never runs
      the framework itself). If D42 says "prompt": a worker cell whose
      handover template is `B0_BRIEF.md`. Record the design in D43 before
      editing anything.
- [ ] 9.2 Before-measurement: a reporting-grade `score_routing.py` run
      against the current table if Stage 2.3 was not taken, or reuse it if
      it was.
- [ ] 9.3 Edit `ROUTING.md`'s rows and the affected fixtures' `expected_cell`
      (F10, F11, F12, F14, F18 at least). ROW-BACKED must hold; `check.py`
      green. Regenerate the worker definitions.
- [ ] 9.4 After-measurement: a reporting-grade run against the new table.
      Compare fixture by fixture. Any fixture that regressed at the bar
      reopens the change per the attractor rule in `CLAUDE.md`.
- [ ] 9.5 Rebuild `dist/`, install into `orchestrator-scratch`, and log the
      install per the dogfooding protocol.
- [ ] 9.6 Gate C: present the before-and-after to Jeb. D43 records the
      outcome either way.
- [ ] 9.7 Update this stage's status line and commit it.

Exit criteria: two reporting-grade runs recorded; ROW-BACKED green; every
row above the floor backed by a measured frontier or removed (criterion 3);
Gate C passed; `dist/` rebuilt and stamped clean.

Cost: about USD 27 per reporting-grade opus run, two runs if 2.3 was not
taken, so USD 27 to 55.

## Stage 10. Two-stage classifier: design

Status: **not started**
Model: opus, xhigh. This changes the shipped product's routing mechanism and
is the hardest reasoning in the plan.

Purpose: `REVIEW.md`, "The project's own standards prescribe the fix to its
own central defect". Assessment as schema-forced output that never sees the
table; routing applied afterwards in code. The attractor class becomes
impossible rather than detectable. Also the instrument for the horizon
question.

Tasks:

- [ ] 10.1 `docs/CLASSIFIER-DESIGN.md`: the mechanism by which the
      orchestrator persona obtains a routing decision without the table in
      its prompt. Candidates: the persona runs `tools/route.py` via Bash
      with its assessment and receives the cell; or a hook; or a dedicated
      tool. Name the one chosen and why, and what FINDINGS question it
      depends on. Section 1 of `ROUTING.md` stays as the assessment rubric;
      section 2's table moves to data (`src/routing_table.json` or similar)
      that `generate_workers.py`, `check.py` and `route.py` all read, so
      there is still one source of truth.
- [ ] 10.2 The two-axis variant as a configuration flag: assessment on
      sensitivity and blast only, horizon dropped, with escalation driven by
      the worker-side signal (`compact_boundary` in the transcript, per
      `CLAUDE.md`) rather than an orchestrator-side prediction. State the
      fixtures whose expected cells change under it and how they are
      scored.
- [ ] 10.3 Pre-register Stage 11's measurement: three configurations
      (current prose table; two-stage with three axes; two-stage with two
      axes), each at the reporting bar, with predicted agreement per
      configuration and the decision rule for shipping.
- [ ] 10.4 D44, the design.
- [ ] 10.5 Update this stage's status line and commit it.

Exit criteria: design document committed; pre-registration committed;
D44; no code yet.

Cost: session only.

## Stage 11. Two-stage classifier: implement and measure

Status: **not started**
Model: sonnet, high. Load `python.sonnet.md`.

Tasks:

- [ ] 11.1 Implement `tools/route.py` and the table-as-data move per D44;
      `generate_workers.py` and `check.py` read the data file; harness
      green; `dist/` rebuilt with the new mechanism behind a flag so the
      current behaviour is still available for the comparison.
- [ ] 11.2 `score_routing.py` gains `--classifier {prose,two-stage}` and
      `--axes {3,2}` so all three configurations run through the same
      scorer.
- [ ] 11.3 Run the three configurations at the reporting bar. Jeb runs; the
      session prepares real-path commands and analyses.
- [ ] 11.4 D45, the verdict against the Stage 10 pre-registration. If a
      two-stage configuration wins, ship it: flag removed, `dist/` rebuilt,
      `ROUTING.md` section 2 rewritten to describe the mechanism, fixtures
      updated. If not, record it and leave the flag out of `dist/`.
- [ ] 11.5 Update this stage's status line and commit it.

Exit criteria: three reporting-grade runs recorded; D45; harness green;
`dist/` in whichever state D45 selects.

Cost: three reporting-grade opus runs, about USD 80.

## Stage 12. Close-out

Status: **not started**
Model: sonnet, medium.

Tasks:

- [ ] 12.1 `CLAUDE.md`: strike through every open question this plan
      answered, with the decision or FINDINGS row that answered it, in the
      style the file already uses. Replace the "Active plan" section with a
      one-line pointer to this file marked complete.
- [ ] 12.2 `docs/COST.md`: recompute against the final bundle, including
      the Controller's per-run cost if it shipped.
- [ ] 12.3 `docs/FINDINGS.md`: consolidate; every "unverified" row either
      moved up with evidence or left with the date it was last checked.
- [ ] 12.4 This file: set the plan's status to complete with the date; every
      stage `done` or `blocked` with its pointer.
- [ ] 12.5 D46: what the branch delivered against the five acceptance
      criteria, one line each, and the merge question for Jeb. The merge
      into `main` is Jeb's action, not the session's.
- [ ] 12.6 Final `check.py` run recorded with `--record`.

Exit criteria: harness green; plan marked complete; D46 present.

Cost: session only.

---

## Cost summary

Guesses, with the assumptions stated in each stage. Session tokens are
excluded throughout.

| Stage | Model calls | Estimate |
| :--- | :--- | :--- |
| 0 to 4 | none beyond the session | USD 0, or about USD 27 if 2.3 is taken |
| 5 | probes | USD 2 to 5 |
| 6 | two ladders over three tasks | USD 60 to 300 |
| 7 | one toy run | USD 1 to 3 |
| 8 | twenty-seven quick-mode runs | USD 15 to 55 |
| 9 | one or two reporting-grade routing runs | USD 27 to 55 |
| 10 | none | USD 0 |
| 11 | three reporting-grade routing runs | about USD 80 |
| 12 | none | USD 0 |

Total: roughly USD 185 to 525, dominated by Stage 6, whose upper bound is
uncertainty about cells above the floor that nothing has yet measured. Every
run is Jeb's to start; the session prepares commands with real paths and
never starts a paid run itself.

## What this plan does not do

- It does not run deep mode. Quick mode is the smallest fleet that tests
  `SYSTEM.md`'s claim; deep mode is a later plan if D42 says "system".
- It does not build the Librarian's cross-run library beyond logging the
  training signal (which technique won, per task). Fifty runs is
  `SYSTEM.md`'s own threshold for that library to matter.
- It does not add haiku cells. Invariant 5 stands as D5's decision.
- It does not merge `the-system` into `main`. That is Jeb's call at D46.
