# Action plan: the-system

Adopted 2026-09-10 on branch `the-system`. Authored by Claude (Fable 5.1, the
Cowork session that produced `docs/REVIEW.md`), reviewed and approved by Jeb.
Revised 2026-09-11 by Claude (Fable 5.1, the first Claude Code session on this
machine) at Jeb's request, after a full read of the repository and a harness
run; what changed and why is under "Revision of 2026-09-11" and is recorded in
D35. Status of the plan as a whole: **in progress (since 2026-09-11)**.

This plan does two things, in a fixed order. First it repairs, instruments and
measures the orchestrator as it stands, and replaces the routing mechanism
whose structural defect `REVIEW.md` names. Then, only if the measurements show
there is anything above the cheapest cell to route to, it integrates the
problem-solving framework in `src/System/SYSTEM.md` with the orchestrator, on
the terms `REVIEW.md` sets out. Read `REVIEW.md` first; every stage below
cites it rather than restating its evidence.

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

Stages are ordered by priority and by dependency, and the order is part of
the plan. A later stage is not started before every earlier stage is `done`
or `blocked`. The one structural exception is Gate D, before Stage 9, which
can close Stages 9 to 12 as a group.

Model and effort per stage are the session's recommendation to Jeb at step 3
of the protocol, and Jeb's confirmation is what sets them for the session.
They are grounded in this project's own evidence (`REVIEW.md`: eight of eight
benchmark tasks cleared at the cheapest cell) and in `SYSTEM.md` section 5's
role assignments. Where a stage names a fallback, the fallback is used only
after the recommended model has demonstrably failed the stage's exit criteria
once, and the switch is recorded in the stage's status line.

Decision numbers below are the expected sequence. If an unplanned entry
intervenes, later numbers shift, and the affected stage text is corrected in
the commit that writes the entry.

## Revision of 2026-09-11

What changed from the adopted plan, and why. The evidence is the 2026-09-11
read of the repository and `docs/REVIEW.md`; the ordering principle is what
each finding costs to leave unaddressed while later work is built on it.

- **The two-stage classifier moves ahead of the framework integration**,
  from Stages 10 and 11 to Stages 5 and 6. It is session work plus routing
  runs, it makes the attractor class of defect impossible rather than
  detectable, and every later table change is cheaper once it ships. The
  adopted plan allowed this at the Stage 2 gate; the revision makes it the
  default rather than an option.
- **The experiment that finds a task the cheapest cell fails** is separated
  from the B0 brief and moves to Stage 7, before any framework work. It
  decides whether the table's upper half has anything to measure, and by
  extension whether the framework track has a subject.
- **A platform re-verification stage is added** (Stage 2). `docs/FINDINGS.md`
  was verified on Claude Code 2.1.245; the installed version is 2.1.263. The
  project's own rule (`ai-prompting`) treats a version bump as a code change.
  The platform question the classifier design depends on, and the substrate
  questions the Controller depends on, are asked in the same stage because
  all of them are cheap probes in the scratch project.
- **Stage 0 gains a repair.** `check.py`'s PERSONA check fails on Windows:
  the manifest stores forward-slash paths and the check compares
  backslash paths, so all fifty-six language-profile files report as
  changed. Content is unchanged (sixty of sixty hashes match after
  separator normalisation, checked 2026-09-11). Every earlier green run came
  from a Linux session; this is the first run on the machine the plan will
  execute on, and Stage 0's exit criterion cannot be met until the check is
  portable.
- **The framework track (Stages 9 to 12) is gated on acceptance criterion
  1.** If no benchmark task fails the floor after two hardening rounds, the
  fleet has nothing to beat the floor on inside this repository's grader
  boundary, and the track closes with a decision entry rather than being
  built anyway.
- **A sixth acceptance criterion** puts the router's own cost on the ledger
  and makes it part of the shipping decision for the classifier.
- **The branch.** The four plan files landed on `main` in `3f25243`, not on
  `the-system`. Stage 0.1 already anticipated this and needs no change.

Nothing in the adopted plan's task detail was discarded. Tasks moved between
stages keep their wording where the stage's purpose is unchanged.

## Model and effort by stage

| Stage | Title | Model | Effort | Persona files to load |
| :--- | :--- | :--- | :--- | :--- |
| 0 | Migration and repair | sonnet | low | `ENGINEERING_PERSONA.sonnet.md`, `ai-prompting.sonnet.md`, `python.sonnet.md` for 0.2 |
| 1 | Documentation and harness hygiene | sonnet | medium | sonnet persona, `ai-prompting`, `python.sonnet.md` |
| 2 | Platform re-verification and mechanism probes | sonnet | medium | sonnet persona, `ai-prompting`, `python.sonnet.md` |
| 3 | A reporting bar for routing runs | sonnet | high | sonnet persona, `ai-prompting`, `python.sonnet.md` |
| 4 | Premise ledger and acceptance criteria (Frame) | opus | xhigh | `ENGINEERING_PERSONA.opus.md`, `ai-prompting.opus.md` |
| 5 | Two-stage classifier: design | opus | xhigh | opus persona, `ai-prompting.opus.md` |
| 6 | Two-stage classifier: implement and measure | sonnet | high | sonnet persona, `ai-prompting`, `python.sonnet.md` |
| 7 | A task the floor cannot clear | opus | high (xhigh for a hardening round) | opus persona, `ai-prompting.opus.md` |
| 8 | Wire the floor evidence into routing | opus | high | opus persona, `ai-prompting.opus.md` |
| 9 | Recover the missing half of SYSTEM.md, schemas, roles, B0 | opus | high | opus persona, `ai-prompting.opus.md` |
| 10 | The Controller in code, quick mode | sonnet | high (opus high on a failed review) | sonnet persona, `ai-prompting`, `python.sonnet.md` |
| 11 | Fleet versus baseline | opus | high | opus persona, `ai-prompting.opus.md` |
| 12 | Wire the fleet verdict into routing | opus | high | opus persona, `ai-prompting.opus.md` |
| 13 | Close-out | sonnet | medium | sonnet persona, `ai-prompting.sonnet.md` |

Consecutive stages on the same class and effort (4 and 5, 7 and 8, 11 and
12) still begin with a fresh confirmation, because the protocol confirms per
stage, not per class. The switch is made with `/model`, choosing the effort
level from the same picker where the installed version offers it.
`CLAUDE_CODE_EFFORT_LEVEL` is never used for this: invariant 3 says it
overrides every worker's frontmatter effort, so setting it for the session
would silently flatten the very cells this repository exists to keep
distinct.

## State at handover, 2026-09-11

- `main` is at `3f25243`, tree clean before this revision. The four files
  the adopted plan listed as uncommitted (`docs/PLAN.md`, `docs/REVIEW.md`,
  the amended `CLAUDE.md`, `src/System/SYSTEM.md`) are committed on `main`
  in that commit. `the-system` does not exist yet. This revision of
  `PLAN.md` is on disk and uncommitted; Stage 0.1 commits it.
- `python3 test/harness/check.py` on this machine (Windows 11, Git Bash):
  16 pass, 1 skip (INV7, needs a live session), 1 fail (PERSONA, path
  separators; see Stage 0.2). PROSE passes with `SYSTEM.md`, `PLAN.md` and
  `REVIEW.md` included, 107 files clean.
- Installed Claude Code: 2.1.263. Last empirical verification of platform
  behaviour: 2.1.245, 2026-09-05 (`docs/FINDINGS.md`).
- `src/System/SYSTEM.md` was repaired on 2026-09-10 in the session that
  wrote the adopted plan: CRLF converted to LF, trailing newline added, and
  the fourteen characters a code-page conversion had turned into `?`
  restored as Unicode (twelve `←` and one `≤` in section 3's pseudocode, one
  `→` in section 7), matching the `×` and `÷` that had survived. The seven
  remaining question marks (section 1's Critic row, the six question
  headings at the end) are genuine.
- The last routing evidence is
  `test/results/2026-09-08-routing-opus-af94deb-5a7585d-summary.md` (18
  fixtures, 3 runs, 49 of 54) and the F05-only batch after D33. All of it is
  steering-grade; see Stage 3.
- The last benchmark evidence is T8 (D30): 9 of 9 at `worker-sonnet-low`
  after the re-grade. Every task built so far, T1 to T8, confirmed at the
  floor.
- Bundle installed in `orchestrator-scratch`: `2026-09-07-af94deb`, current
  with `src/`. Nothing since D28 has touched `ROUTING.md`, and `SYSTEM.md`
  is not part of the bundle, so no rebuild is pending.
- Session load: a stage session reads roughly 140 KB before its first task
  (the charter, one persona file, its `ai-prompting` profile, this plan and
  the review), about 35k tokens at four characters per token. It is cached
  within a session and paid once per stage. Stage 1.4 puts the number on
  `COST.md` so it is on the ledger with everything else.

## Acceptance criteria, fixed at Gate A on 2026-09-11

`SYSTEM.md` requires acceptance criteria to be fixed before any generation.
These were proposed when this plan was written, amended by the premise ledger
(`docs/PREMISES.md`, Stage 4), and fixed by Jeb at Gate A on 2026-09-11. They
are recorded verbatim in D38. **After Gate A they are not revised in the light
of results.**

1. A benchmark task set exists on which `worker-sonnet-low`'s confirmed pass
   rate fails the reporting bar (nine runs, 95 percent Wilson lower bound
   above 0.7) and some higher cell clears it. Without this, nothing above
   the floor is measured, and Stages 9 to 12 have no subject. Existence is
   the gate; the cost case additionally needs the rate at which tasks fail
   at the floor, which Stage 8 estimates from whatever sample exists, with
   the sample's limits stated.
2. If the framework track runs: on that set, the fleet in quick mode beats
   B0 (one cell running the eight steps as a single prompt) at the reporting
   bar, at a cost per solved task no more than three times B0's.
3. Every routing row above the floor is either backed by a measured
   frontier or removed, with one documented exception: a row whose only
   justification is blast radius is a policy row, and it is labelled as such
   in `src/ROUTING.md` itself, not only in the premise ledger, so a consumer
   reading the shipped table can tell a capability claim from a risk-appetite
   choice. Judgement fixtures alone no longer back a row that routes above
   `worker-sonnet-low`.
4. The harness stays green at every commit and no invariant is weakened.
   A charter amendment (Stage 10 names one) is a decision entry, not a
   quiet edit.
5. No routing-table change is described as confirmed below nine runs per
   affected fixture. Below that it is steering.
6. The cost of a routing verdict is on the ledger beside the cost of the
   work it routes, and the shipped routing mechanism is chosen on measured
   agreement and cost per verdict together, never on agreement alone. The
   comparison baseline includes zero router cost, which is B0: a mechanism
   cheaper than another router but still losing to not routing at all does
   not satisfy this criterion.
7. At close-out, the table's remaining case is stated in one sentence as
   either a measured cost saving or an accepted risk-appetite policy, and
   `src/ROUTING.md` says which.

If criterion 2 fails, the framework track's deliverable is the B0 brief as a
handover template for the top rows, and that outcome is recorded as a result,
not a failure. `SYSTEM.md`'s own words: "if it does not beat it by a margin
that pays for itself, you have a prompt, not a system."

**The caveat that qualifies all seven, recorded at Gate A.** The benchmark
gives B0 a free and perfect failure detector, because a deterministic grader
runs on every attempt; real use has no such detector. Every comparison these
criteria describe is therefore biased in B0's favour by an unknown amount,
and the size of that bias is precisely the value of the routing table
(`docs/PREMISES.md`, metric interrogation). The criteria cannot correct for
this. A result that goes against the table by a narrow margin should be read
with it in mind.

## Human gates

Beyond the per-stage approval `CLAUDE.md` requires:

- **Gate A**, end of Stage 4: Jeb fixes the acceptance criteria, the goal
  ladder, and the decision rule Gate D will apply. Cheap, high leverage, the
  gate `SYSTEM.md` puts first. **Passed 2026-09-11**, D38: seven criteria
  fixed, three amended from the proposal and one added, the multiplier in
  criterion 2 set at three, and the Gate D rule fixed as below.
- **Gate B**, start of Stage 7: Jeb approves the spend before the floor
  ladder runs. The pre-registration is presented with the cost estimate
  attached.
- **Gate C**, end of Stage 8: Jeb accepts or rejects the wiring of the floor
  evidence into the routing table on the before-and-after evidence.
- **Gate D**, before Stage 9: Jeb decides whether the framework track runs,
  by the rule fixed at Gate A on 2026-09-11: Stages 9 to 12 run only if
  criterion 1 holds, meaning at least one benchmark task where
  `worker-sonnet-low` fails the reporting bar and a higher cell clears it.
  If criterion 1 fails after the two hardening rounds Stage 7 allows, the
  framework track closes with a decision entry, and the same failure
  triggers the question of whether the routing table should collapse toward
  B0, which criterion 3 handles at Stage 8. Jeb may open the track despite
  the rule; the reason is recorded.
- **Gate E**, start of Stage 11: Jeb approves the spend before the fleet
  runs.
- **Gate F**, end of Stage 12: Jeb accepts or rejects the wiring of the
  fleet verdict into `ROUTING.md`.

The routing runs in Stages 3 and 6 are approved at those stages' own
approval, with their cost stated there. No gate sits inside generation. A
session that wants approval mid-stage for something the stage did not
anticipate records the question as a decision entry and stops, rather than
improvising.

---

## Stage 0. Migration and repair

Status: **done (2026-09-11, 7690ec4)**
Model: sonnet, low. Mechanical git and file work plus one small, fully
specified code fix; nothing here needs judgement.

Purpose: confirm the plan landed on the branch as Jeb committed it, make the
harness pass on the machine the plan will execute on, record the adoption
and this revision in the ledger, and leave a clean, green tree for Stage 1.

Entry: a Claude Code session in this repository, on any branch.

Tasks:

- [x] 0.1 Run `git branch --show-current`. If it is not `the-system`, and
      the branch exists, check it out; if it does not exist, create it with
      `git checkout -b the-system` from `main` at `3f25243` or later. Then
      `git status --short`: commit the revised `docs/PLAN.md` as one change
      ("adopt the staged plan, revised 2026-09-11"), together with anything
      else from the adopted plan's four files that is still uncommitted.
      Note in this task's tick which of the two branch cases happened.
      Done 2026-09-11 (`d10cf4d`): the branch did not exist, created from
      `main` at `3f25243`. The four adopted-plan files were already
      committed on `main` in that commit; only the 2026-09-11 revision of
      `docs/PLAN.md` was uncommitted, and this commit lands it.
- [x] 0.2 Make `check.py`'s PERSONA check portable. Build the current-file
      map from `path.relative_to(REPO_ROOT).as_posix()`, normalise recorded
      names the same way when the manifest is read, and write the manifest
      with `as_posix()` so a Linux run and a Windows run produce the same
      file. Do not regenerate the hashes: the content is unchanged. Then run
      `python3 test/harness/check.py`; expected 16 pass, 1 skip, 0 fail.
      PROSE must pass with `SYSTEM.md` included (it is under `src/**/*.md`,
      which the check globs) and with `PLAN.md` and `REVIEW.md` under
      `docs/*.md`; it did on 2026-09-11 and this task confirms it after the
      edit. Fix any other finding in the same task. Own commit.
      Done 2026-09-11 (`7e7a8cb`): current-file keys and recorded-manifest
      names both normalised to forward slashes; no hash regenerated.
      `check.py` reports 16 pass, 1 skip (INV7), 0 fail on this machine.
- [x] 0.3 D35, a decision entry recording: the branch and its purpose; that
      `CLAUDE.md` gained an "Active plan" section and this is a charter
      amendment; the approval protocol; that the plan and review were
      authored by Claude on 2026-09-10 and approved by Jeb; the commit in
      which Jeb landed the four files (`3f25243`, on `main`); the
      `SYSTEM.md` repair (what was restored and that Unicode was chosen);
      that `SYSTEM.md` is the second half of an exchange whose first half
      (the eight-step sequence and the forty techniques) is not in the
      repository, which Stage 9 addresses; and the 2026-09-11 revision, what
      moved, why, and that the version gap and the Windows harness defect
      were found on the first Claude Code session.
      Done 2026-09-11 (`7690ec4`).
- [x] 0.4 Update this stage's status line and commit it.

Exit criteria: on `the-system`, tree clean, all files committed, `check.py`
reports 0 failing on this machine, D35 present.

Cost: no model calls beyond the session.

## Stage 1. Documentation and harness hygiene

Status: **done (2026-09-11, 16c3e49)**
Model: sonnet, medium. Load `python.sonnet.md` for task 1.3.

Purpose: the stale statements and the one remaining evidence-loss defect
`REVIEW.md` lists under "Smaller and concrete". Each task is its own commit.

Tasks:

- [x] 1.1 `test/fixtures/README.md`: eighteen fixtures, not seventeen; F17's
      gap was closed by D9 and the "Coverage" paragraph is rewritten from the
      current table (F18 backs the `worker-fable-xhigh` row; F19 was removed
      by D27); the review-status line names F18's `assigned_by` date.
      Done 2026-09-11 (`446fea1`).
- [x] 1.2 `test/fixtures/benchmark/README.md`: T1 to T8 exist; two sentences
      on the open-task grader convention and the three grader defects found
      so far (D16, D17, D30) and what each taught.
      Done 2026-09-11 (`e9638bb`).
- [x] 1.3 `test/harness/benchmark.py`: the docstring says six tasks; say
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
      Done 2026-09-11 (`359dc2f`, D36). Recovering the original also
      reopened a PROSE defect a6b7426's own commit message had flagged and
      left unresolved (a worker's verbatim US spelling); resolved in the
      same commit by exempting benchmark.py's own relay markers from the
      word-level checks, not by filename.
- [x] 1.4 `docs/COST.md`: recompute against the installed bundle
      (`2026-09-07-af94deb`; the commands are in the file), and add two
      measured lines the file lacks. First, the cost of a routing verdict
      against the cost of the work it routes: mean opus verdict cost per
      fixture from the `-summary.md` routing files (total cost divided by
      fixtures times runs) against mean `worker-sonnet-low` cost per run
      from the benchmark result files, both stated with their ratio. This is
      the "classification may cost more than the work" point in
      `REVIEW.md`, made into a number, and the baseline criterion 6 is
      judged against. Second, the fixed load of a stage session in this
      repository (the files "State at handover" lists), in bytes and
      estimated tokens, so the development side's overhead is on the same
      ledger as the product's.
      Done 2026-09-11 (`27d6943`). Ratio 1.003: at the floor, the router
      costs essentially the same as the work it routes.
- [x] 1.5 `CLAUDE.md` "Open questions worth developing": add the three
      `REVIEW.md` found missing: no benchmark task yet fails the cheapest
      cell, so nothing above the floor is measured; the router's own cost
      is not on the ledger; horizon is the least reliable axis and the
      table has been adapting to that without saying so. Keep the existing
      entries untouched.
      Done 2026-09-11 (`16c3e49`). The router-cost question is added
      already resolved, since task 1.4 in this same stage answered it;
      listing it as open would have been stale on arrival.
- [x] 1.6 Update this stage's status line and commit it.

Exit criteria: harness green after every commit; D36 present; the recovered
six-task result files exist under distinct names; `COST.md` carries the
verdict-versus-work line and the session-load line.

Cost: no model calls beyond the session.

## Stage 2. Platform re-verification and mechanism probes

Status: **done (2026-09-11, 9ee0afa)**
Model: sonnet, medium. Load `python.sonnet.md`. Empirical work in
`orchestrator-scratch`, recorded in `docs/FINDINGS.md`.

Purpose: two things. `FINDINGS.md` is pinned to 2.1.245 and every later run
in this plan happens on 2.1.263 or later; the invariants the static harness
cannot check live in those rows. And Stage 5 and Stage 10 each depend on a
platform question nobody has asked, all of which are cheap probes.

Tasks:

- [x] 2.1 Re-run E1, E2, E4, E5 and E7 from
      `test/harness/empirical-checklist.md` on the installed version, plus
      the parse half of E12 (`score_routing.py --dry-run`, then one
      `--only F01` pass, checking the `claude -p --output-format json` field
      names still parse). Record each row as re-verified on the version
      seen, with the evidence, or as changed. A changed result that touches
      an invariant blocks the plan: decision entry, `blocked`, stop.
      Done 2026-09-11. E1, E4, E5, E7 and E12's parse half all re-verified
      unchanged on 2.1.263, no invariant affected. E2 could not be
      re-verified: no callable equivalent of `/tasks` exists for an agent
      session (E19, a new finding, `docs/FINDINGS.md`), so the check needs
      a human watching the panel live, which this round did not do.
- [x] 2.2 E15, the classifier mechanism Stage 5 depends on. Can an
      orchestrator obtain a routing verdict from code and act on it without
      the table in its prompt? Try each candidate in the scratch project:
      the persona runs `python3 tools/route.py` via Bash with its axis
      assessment and receives the cell name; a hook (`UserPromptSubmit` or
      `PreToolUse` on the Agent tool) that computes the cell from the
      assessment and either injects it or refuses a spawn whose
      `subagent_type` disagrees; and a small custom tool served over MCP.
      For each: does it work headless under `claude -p` (the mode
      `score_routing.py` runs in), does the persona reliably act on the
      returned cell, and what does it add to the cost of a verdict. Record
      which are workable. Stage 5 chooses among the workable ones; if none
      is, Stage 5 designs the fallback (the table stays in the prompt and
      the assessment is schema-forced first) and says so.
      Done 2026-09-11. The Bash-invoked script candidate is workable, but
      only with the same permission flags `benchmark.py` already needs for
      any headless Bash call; without them it is silently blocked, not
      merely slow. The hook and MCP-tool candidates were not separately
      live-tested this round (see `docs/FINDINGS.md`, E15); Stage 5 chooses
      with that gap stated plainly.
- [x] 2.3 E16 to E18, the substrate probes the Controller depends on, moved
      here from the adopted plan's Stage 5 because they are cheap and
      independent of any design. E16, cache prefix sharing: three
      `claude -p --output-format json` invocations in parallel from one
      Python process, each with an identical static prefix of several
      thousand tokens and a different short task; compare
      `cache_read_input_tokens`. E17, schema rejection before a model sees a
      record: whether a `PreToolUse` hook on Write, configured in the
      scratch project, rejects a failing file when the writer is a worker
      spawned inside a `claude -p` session; if hooks do not reach workers,
      record that. E18, concurrency: N parallel `claude -p` processes from
      one parent, rate-limit behaviour, shared-state interference, and the
      largest N observed to work; quick mode needs three, deep mode up to
      twelve. Per-role cost stays in Stage 9 because it needs the role
      briefs.
      Done 2026-09-11. E16: no cross-process cache sharing observed
      between three genuinely parallel calls on an identical prefix, a
      caution for Stage 10's Controller design. E17: the hook does reach a
      spawned worker's own tool calls, confirmed by the file never being
      created and zero permission denials on the blocking call. E18: 3, 6
      and 12 parallel calls all completed cleanly with the exact expected
      reply, no rate-limit failures observed at this scale.
- [x] 2.4 Record every result in `docs/FINDINGS.md` with the installed
      version at the top of the file updated; append E15 to E18 to the
      checklist and mark them done; log the session in
      `test/results/<date>-empirical.md` (the harness's `unique_path`
      convention applies if the name collides).
      Done 2026-09-11 (`test/results/2026-09-11-empirical.md`); the
      version line, E15 to E18, and E19 were recorded across the 2.1 and
      2.2-2.3 commits as each result came in, ahead of this task's own
      commit.
- [x] 2.5 Update this stage's status line and commit it.

Exit criteria: every re-run row carries 2.1.263 or later and its evidence;
E15 answered with at least one workable mechanism, or none, stated plainly;
E16 to E18 answered; no change to `src/`.

Cost: about USD 2 to 5 in `claude -p` calls, a guess with the assumption
stated: fewer than twenty short calls, most at sonnet.

## Stage 3. A reporting bar for routing runs

Status: **done (2026-09-11, b3022e3)**
Model: sonnet, high. Load `python.sonnet.md`.

Purpose: `REVIEW.md`, "The routing side has no reporting bar". The benchmark
refuses to claim anything below nine runs; the routing side has changed the
table on three. Give `score_routing.py` the same two-threshold discipline and
record the policy.

Tasks:

- [x] 3.1 `score_routing.py`: label every rendered file and summary with its
      grade. `steering` when runs are fewer than nine; `reporting` at nine
      or more. In the summary, add a per-fixture column stating whether that
      fixture's 95 percent Wilson lower bound exceeds 0.7, and an overall
      line stating how many fixtures clear it. The Wilson function already
      exists; this is presentation and one comparison.
      Done 2026-09-11, verified live with `--only F01 --runs 3 --record`
      (`test/results/2026-09-11-routing-opus-af94deb-only-F01-summary.md`):
      the header, the grade line, and the new `Clears 0.7` column all
      render correctly. Also found and corrected while writing this: below
      nine runs the bar cannot clear at all, not merely "by chance" as a
      first draft claimed; eight of eight gives a lower bound of 67.6
      percent, still short of 0.7.
- [x] 3.2 D37, the policy: a change to `ROUTING.md`'s table or to a
      fixture's assessment is called confirmed only on a reporting-grade run
      for every fixture the change touches. Below that it is steering, and
      the ledger entry says so. Retroactively, without editing them, note
      that D23 through D33 rest on steering-grade runs. This entry also
      records the reason for the asymmetry until now: routing runs cost
      about USD 3 per pass on opus, so nine passes is about USD 27, and
      that was judged too much per decision during calibration. It is not
      too much per table change.
      Done 2026-09-11 (D37).
- [x] 3.3 Jeb's call at this stage's approval: one reporting-grade opus run
      against the current table, `--runs 9 --record`, about USD 27, to
      establish the branch's baseline. Recommended, because Stage 6 needs
      the prose-table configuration at the bar and Stage 8 needs a
      before-measurement, and both would otherwise pay for it then.
      Done 2026-09-11 (`test/results/2026-09-11-routing-opus-af94deb-
      summary.md`), USD 15.9079, the first reporting-grade routing
      baseline this branch has. Overall agreement 155/162 (95.7 percent,
      95% Wilson [91.4%, 97.9%]). 16 of 18 fixtures clear the 0.7 lower
      bound cleanly at 100 percent. Two do not, and F09's result is a real
      finding, not noise: 4 of 9 (44 percent, [19%, 73%]), the orchestrator
      over-provisioning to `worker-opus-high` in 5 of 9 runs against the
      confirmed floor cell, well past ROUTING.md section 4's three-
      disagreement threshold for "the rubric is wrong for this task class".
      F07 also falls short (7/9, 78 percent, [45%, 94%], 2 disagreements),
      more likely noise at this sample size. Not acted on in this stage,
      since Stage 3's purpose is instrumentation, not table changes (D37);
      flagged here for Stage 5's classifier design and Stage 8's wiring
      work, both of which should treat F09 as a known, reporting-grade-
      confirmed weak point of the current prose classifier to test against.
- [x] 3.4 Update this stage's status line and commit it.

Exit criteria: a `--runs 9 --dry-run` prints the run plan; a `--runs 3
--record` against a scratch project renders `steering` in the header and the
new column; D37 present; harness green.

Cost: session only, plus about USD 27 if 3.3 is taken.

## Stage 4. Premise ledger and acceptance criteria (Frame)

Status: **done (2026-09-11, 255d5ff)**
Model: opus, xhigh. This is `SYSTEM.md`'s Framer role, "highest value per
token in the system; a wrong ledger wastes everything after it". Fable at
xhigh is the deep-mode alternative if Jeb wants a second, independent pass;
one pass at opus xhigh is the recommendation.

Purpose: run the framework's first step on the orchestrator itself, and fix
the acceptance criteria before anything is generated. `REVIEW.md`'s five-row
sketch under "The premise ledger, turned on the routing table" is the seed.
The ledger also decides, before any spend, what Stage 7 has to show for the
framework track to open.

Tasks:

- [x] 4.1 `docs/PREMISES.md`: a ledger of every premise the routing layer
      rests on. One row per premise: id, statement, class (law, maths,
      policy, habit, unverified), source (a decision entry, a file, a run),
      confidence, cheapest verification, status. Cover `ROUTING.md` section
      1's axis definitions, section 2's table and constraints, each
      fixture's assessment (three premises per fixture), `CLAUDE.md`'s
      seven invariants (laws by measurement where FINDINGS verifies them),
      and the assumptions `BENCHMARK-DESIGN.md` names. Cap the ledger at
      forty rows by merging, as `SYSTEM.md` requires; if it will not fit,
      the merging itself is a finding.
      Done 2026-09-11. Forty rows exactly, each with a class, a cheapest
      verification and a status. Roughly 11 laws, 11 unverified, 10
      policies, 5 falsified, 2 habits, 1 maths. Two merges did the
      compression and both are recorded as findings: the fixtures collapse
      68 premises into 2 rows, and `ROUTING.md`'s constraints paragraph
      collapses 3 unmeasured quality claims into 1. The layer rests on
      about 110 distinct premises; forty is a readable summary, not a
      complete enumeration. Two free arithmetic checks the ledger prompted
      are recorded with it: the fixture suite confounds sensitivity with
      horizon (a 35 point prediction lift), which bears directly on whether
      Stage 6's two-axis comparison can be decisive; and four of the five
      table rows with no fixture behind them are consequential, putting the
      least evidenced rows on the one axis the benchmark cannot measure.
- [x] 4.2 Goal ladder for the project, three rungs: route each task to the
      cheapest sufficient cell; get the same quality for less money than one
      capable cell; and the rung above that, which the Framer states rather
      than this plan. Dissolution check: does the routing problem dissolve
      if the floor does everything? State B0 for the project explicitly
      ("route everything to `worker-sonnet-low`, escalate on failure") and
      what evidence would show the table beats it.
      Done 2026-09-11. Rung 3 is stated as total cost, including the user's
      attention, per unit of work that can be trusted without re-checking;
      at that rung, routing competes with four levers the project has never
      compared it against, handover quality among them. The dissolution
      check is arithmetic rather than argument, from the two measured
      figures in `COST.md`: the table beats B0 only when the router costs
      less than the floor run it lets you skip, which at opus prices needs
      a floor-failure rate above 100 percent and is therefore impossible.
      The problem does not dissolve; it shrinks from a cost problem to an
      insurance problem, and the insurance case rests on P05, which the
      benchmark structurally cannot measure. A cheap classifier is not a
      defect fix but the only route by which the cost thesis can be true
      at all: at USD 0.02 a verdict the required failure rate falls to
      12 percent.
- [x] 4.3 Metric interrogation: fixture agreement measures agreement with a
      human label, not with a measured frontier. State the metric the
      project should be optimising (cost per task solved at the reporting
      bar) and how far the current instruments are from measuring it.
      Done 2026-09-11. Two of the four terms in cost per solved task are
      measured; both missing ones are about what happens above the floor.
      The sharpest finding is that the current metric has no term for the
      router's own cost, so a router could score 100 percent agreement and
      still make the system strictly more expensive than not routing. The
      deepest finding cuts against Stage 4.2's own conclusion: the
      benchmark hands B0 a free and perfect failure detector that real use
      does not supply, so any benchmark measurement of cost per solved task
      is biased in B0's favour by an unknown amount, and the size of that
      bias is exactly the value of the routing table. The ledger also ends
      with the load-bearing unverified list `SYSTEM.md` requires, eight
      premises ranked by what their falsity would cost.
- [x] 4.4 Present the acceptance criteria from this plan's "Proposed
      acceptance criteria" to Jeb with any amendments the ledger suggests,
      together with the decision rule for Gate D (what Stage 7 must show for
      Stages 9 to 12 to run) and the multiplier in criterion 2. This is
      Gate A. Record the fixed criteria and the rule verbatim in D38.
      Done 2026-09-11. Gate A passed: Jeb accepted all four ledger-driven
      changes as recommended. Criterion 1 amended (existence is the gate,
      the rate is what the cost case separately needs), criterion 3 amended
      (blast-only rows are labelled policy in `ROUTING.md` itself, not only
      in the ledger), criterion 6 amended (the comparison baseline includes
      B0 at zero router cost), criterion 7 added (the table's remaining
      case is stated at close-out as either a measured saving or an
      accepted risk-appetite policy). Multiplier fixed at three. Gate D
      rule fixed. This plan's criteria section is now the fixed set, not
      the proposal.
- [x] 4.5 List any platform questions the ledger exposes that Stage 2 did
      not answer, appended to `test/harness/empirical-checklist.md` as E20
      onward (E19 was consumed during Stage 2 by an unplanned finding, the
      `/tasks` tool question, `docs/FINDINGS.md`), each with what to run,
      what it settles, and which stage needs it.
      Done 2026-09-11, taken before 4.4 because Gate A waits on Jeb and
      this does not. Three: E20, whether `compact_boundary` is the reliable
      undersizing signal `CLAUDE.md` claims (P29), which Stage 5 needs
      before it proposes replacing an entire axis with it; E21, whether an
      escalation leaves any machine-readable trace, which is one of the two
      missing terms in cost per solved task; E22, the real cost of a
      minimal schema-forced classification call, which is the `R` term the
      whole cost thesis turns on.
- [x] 4.6 D38: the ledger's adoption, the fixed criteria, the goal ladder,
      the dissolution verdict, B0 for the project, and the Gate D rule.
      Done 2026-09-11 (D38), in the same commit as 4.4, since the entry is
      the record of what that gate decided.
- [x] 4.7 Update this stage's status line and commit it.

Exit criteria: `PREMISES.md` committed and PROSE-clean; every premise has a
class and a cheapest verification; Gate A passed with the criteria and the
Gate D rule recorded; harness green.

Cost: session only.

## Stage 5. Two-stage classifier: design

Status: **done (2026-09-11, e50cad2)**
Model: opus, xhigh. This changes the shipped product's routing mechanism and
is the hardest reasoning in the plan.

Purpose: `REVIEW.md`, "The project's own standards prescribe the fix to its
own central defect". Assessment as schema-forced output that never sees the
table; routing applied afterwards in code. The attractor class becomes
impossible rather than detectable, every later table edit stops needing a
paid before-and-after run to detect it, and the design is the instrument
for the horizon question.

Tasks:

- [x] 5.1 `docs/CLASSIFIER-DESIGN.md`: the mechanism by which the
      orchestrator persona obtains a routing decision without the table in
      its prompt, chosen from the mechanisms Stage 2.2 found workable, with
      the reason and the FINDINGS row it rests on. Section 1 of
      `ROUTING.md` stays as the assessment rubric; section 2's table moves
      to data (`src/routing_table.json` or similar) that
      `generate_workers.py`, `check.py` and `route.py` all read, so there is
      still one source of truth. If Stage 2.2 found no workable mechanism,
      design the fallback (assessment schema-forced first, the table applied
      by the persona second) and state what it does and does not remove.
      Done 2026-09-11 (`docs/CLASSIFIER-DESIGN.md`). Mechanism: the
      Bash-invoked script, the only one Stage 2.2 verified, but the design
      separates measuring the classifier from shipping it and does
      measurement first, because measuring needs no shipped mechanism at
      all and shipping adds a Bash-permission requirement with a silent
      failure mode. Table moves to `src/routing_table.json`, rendered back
      into `ORCHESTRATOR.md` at build time so consumers still read prose
      and there is still one source. Central finding, made while
      pre-flighting the TABLE-DATA check: the routing table is not a
      function of the three axes. F14 and F18 route through rows
      conditioned on prior failure and on self-directed investigation,
      neither of which the triple carries. With those two as enumerated
      fields the table is a pure function and all seventeen assessed
      fixtures resolve.
- [x] 5.2 The metric. Because the classifier never sees the table, the
      natural measure is axis agreement against each fixture's recorded
      assessment triple, and cell agreement follows from the table in code.
      State both, and specify a deterministic `check.py` check (TABLE-DATA)
      asserting that `route.py` resolves every fixture's assessment triple
      to that fixture's expected cell. That check replaces one class of paid
      fixture run with a free one.
      Done 2026-09-11. Field agreement is primary, cell agreement derived
      in code, and the gap between them reported, because the gap is what
      the current metric hides: cell agreement forgives 24 of 72 possible
      single-field errors, 33.3 percent, and horizon is the most forgiven
      axis at 42.9 percent. That gives a causal account of why horizon
      drifted across five fixtures, since it is both the least reliable
      axis and the one the metric penalises least. TABLE-DATA specified
      and pre-flighted: it fails today on F14 and F18 with three fields,
      which is how the five-field finding was made, and passes on all
      seventeen with five.
- [x] 5.3 The two-axis variant as a configuration flag: assessment on
      sensitivity and blast only, horizon dropped, with escalation driven by
      the worker-side signal (`compact_boundary` in the transcript, per
      `CLAUDE.md`) rather than an orchestrator-side prediction. State the
      fixtures whose expected cells change under it and how they are
      scored.
      Done 2026-09-11. Collapse rule is cheapest-across-horizons, which is
      P12's standing policy. Four fixtures change cell, all downward to the
      floor: F03, F05, F07, F10. Two findings. Open and contained is not
      monotonic in horizon under the current table (short to the floor,
      medium to `worker-opus-high`, long back to the floor), so horizon is
      not ordinally coherent in the band with the most measured evidence
      behind it. And the variant cannot be scored on fixture cell
      agreement at all, because dropping an axis changes the correct
      answer the fixtures encode; it would be marked wrong four times out
      of seventeen by construction. Combined with the suite's
      sensitivity-to-horizon confound, the conclusion recorded in the
      design is that this fixture suite cannot decide the two-axis
      question, and the pre-registration says so in advance.
- [x] 5.4 Pre-register Stage 6's measurement: three configurations (current
      prose table; two-stage with three axes; two-stage with two axes).
      Steer each at three runs; report at nine for the prose baseline
      (Stage 3.3's run if it was taken) and for the best two-stage
      configuration. Predicted axis and cell agreement per configuration,
      predicted cost per verdict per configuration (criterion 6), and the
      decision rule for shipping.
      Done 2026-09-11 (`test/results/2026-09-11-classifier-preregistration.md`).
      Four configurations, not three: the prose baseline is Stage 3.3's
      existing reporting-grade run and is not re-run, and the two-stage
      design is measured at both opus (isolating the mechanism against the
      baseline's model) and `worker-sonnet-low` (the shipping candidate,
      since the cost case needs a cheap router). Predictions written as
      ranges with centres, including a deliberate null prediction that the
      two-stage design will be indistinguishable from the baseline on cell
      agreement. The shipping rule's cost ceiling is derived rather than
      chosen: 0 of 8 benchmark tasks have failed at the floor, whose 95
      percent Wilson upper bound is 32.4 percent, so a router must cost
      below USD 0.0532 a verdict to pay for itself at any failure rate the
      evidence permits. The opus router exceeds that by 3.1 times. Total
      estimate USD 10 to 40, below the plan's USD 45 to 72, because the
      baseline is already measured.
- [x] 5.5 D39, the design.
      Done 2026-09-11 (D39), recording the five-input finding, the
      measurement-before-delivery split, the metric change, the two-axis
      variant's undecidability on this suite, the horizon non-monotonicity,
      and the derived cost ceiling. Reversal conditions are E20 and E22.
- [x] 5.6 Update this stage's status line and commit it.

Exit criteria: design document committed; pre-registration committed;
D39; no code yet.

Cost: session only.

## Stage 6. Two-stage classifier: implement and measure

Status: **done (2026-09-11, 022043c)**
Model: sonnet, high. Load `python.sonnet.md`.

Tasks:

- [x] 6.1 Implement `tools/route.py` and the table-as-data move per D39;
      `generate_workers.py` and `check.py` read the data file; the
      TABLE-DATA check is added and counted; ROUTE-TOTAL and ROW-BACKED keep
      their meaning; harness green; `dist/` rebuilt with the new mechanism
      behind a flag so the current behaviour is still available for the
      comparison. Own commit per component.
      Done 2026-09-11, five commits (`cc4fab7`, `d65b476`, `5890f06`,
      `5635bcc`, `f75b50b`). `src/routing_table.json`, an ordered rule list,
      first match wins; `tools/route.py` resolves and is callable both as a
      module and via CLI (the mechanism E15 verified). ROUTE-TOTAL and
      ROW-BACKED rewritten against the data and gained a check the prose
      version could not express: at most one non-frontier rule may match a
      given input, or the overlap must be the one documented, ordered
      exception, catching accidental future shadowing rather than trusting
      list order silently. TABLE-DATA added, free, replacing the class of
      drift a paid routing run used to be the only way to catch.
      `build_dist.py --rubric-only` builds `dist-rubric-only/`, gitignored,
      never touching `dist/`, with only the destination table stripped from
      `ORCHESTRATOR.md` and the constraints paragraph (self_directed's and
      prior_failure's own wording) kept intact. 18 checks, 0 failing
      throughout; `dist/` confirmed unaffected by `git status` after a
      rubric-only build.
- [x] 6.2 `score_routing.py` gains `--classifier {prose,two-stage}` and
      `--axes {3,2}` so all three configurations run through the same
      scorer, and records cost per verdict per configuration.
      Done 2026-09-11 (`92f2c97`, `5e3b0fb`). Refuses to run two-stage
      against a project whose bundle is not `dist-rubric-only/`, per the
      pre-registration's own constraint. Field agreement is the primary
      metric feeding the run's grade; cell agreement is derived through
      `tools/route.py` and reported alongside, never as the grade, since it
      forgives up to a third of single-field errors. Verified end to end
      at zero cost: dry-run against a freshly installed rubric-only scratch
      project (`orchestrator-scratch-rubric-only`, not committed to this
      repository) for both 3 and 2 axes, and synthetic verdicts covering a
      correct reply, a wrong field, F18's self_directed case, and an
      unparseable reply.
- [x] 6.3 Run the configurations per the Stage 5 pre-registration. Jeb runs;
      the session prepares real-path commands and analyses.
      Done 2026-09-11 (`e776fe3`, `594810a`, plus the two reporting-grade
      recordings). Steering then reporting for B and C; steering only for D,
      not scored on cell agreement per the pre-registration. A live bug
      surfaced during D's first attempt: `resolve_two_axis` crashed when a
      model correctly reported `prior_failure: failed_at_xhigh`, since the
      frontier rule's worker is deliberately absent from the cost ladder
      the two-axis collapse ranks against. Fixed and verified before any
      further runs; D's crashed attempt wrote no file (`score_routing.py`
      has no per-fixture checkpoint) and was re-run clean. At reporting
      grade: B (opus) cell agreement 92.2% [86.8%, 95.5%], cost per verdict
      USD 0.103. C (sonnet, effort low) cell agreement 58.2% [50.2%,
      65.7%], cost per verdict USD 0.013.
- [x] 6.4 D40, the verdict against the pre-registration, on agreement and
      cost per verdict together. If a two-stage configuration wins, ship
      it: flag removed, `dist/` rebuilt, `ROUTING.md` section 2 rewritten to
      describe the mechanism, fixtures updated, install into
      `orchestrator-scratch` logged per the dogfooding protocol. If not,
      record it and leave the flag out of `dist/`.
      Done 2026-09-11 (D40). Neither configuration clears both rules: B
      (opus) fails on cost (USD 0.1030 against a USD 0.0532 ceiling), C
      (sonnet, effort low) fails on accuracy (58.2 percent cell agreement,
      Wilson lower bound 50.2 percent, against A's 91.4 percent
      requirement). No two-stage classifier ships; `dist/` and `ROUTING.md`
      are untouched, `--rubric-only` stays in `build_dist.py` as a
      measurement tool. A live bug in `resolve_two_axis` was found and
      fixed during the run (see 6.3); `self_directed` was found to fire
      spuriously in 37.9 percent of sonnet-at-low-effort verdicts against a
      5.9 percent true rate, a concrete design defect for any future
      attempt, independent of the shipping verdict.
- [x] 6.5 Update this stage's status line and commit it.

Exit criteria: the pre-registered runs recorded with their grade labels;
D40; harness green; `dist/` in whichever state D40 selects.

Cost: about USD 9 per steering pass and USD 27 per reporting pass on opus:
two steering passes and one reporting pass for the two-stage configurations,
plus the prose baseline at the bar if Stage 3.3 was not taken. USD 45 to 72,
less if the winning classifier runs at a cheaper model, which is itself a
result criterion 6 wants.

## Stage 7. A task the floor cannot clear

Status: **done (2026-09-14, see the 7.6 commit)**
Model: opus, high. Move to opus xhigh only for a hardening round (task 7.3's
rule), and record the switch.

Purpose: `REVIEW.md`'s first recommendation and the single experiment most
likely to change the table. Every benchmark task so far cleared at
`worker-sonnet-low`, so every row above the floor is a hypothesis. Until a
task exists that the floor measurably fails, nothing above the floor is
evidence, and the framework track has no subject.

Tasks:

- [x] 7.1 Benchmark tasks T9, T10 and T11, in two shapes so the result does
      not rest on one. T9 and T10: a small repository plus a `PROBLEM.md`
      whose stated constraints include one or more planted false premises,
      a habit or policy presented as a law, where the intended solution is
      reachable only by reclassifying that premise. T11: T7's lineage at a
      larger scale, a root cause shared across more simulated services,
      reproducible only by running the code at varying sizes, with more red
      herrings that need ruling out. Every grader stays an exit code. For T9
      and T10, three checks: the report names the planted premise as
      reclassified; it cites an artefact file that exists and contains the
      measurement output a real check would produce; and the chosen
      solution matches the expected shape by string match, T5 to T8 style.
      Test each grader against a correct report in two phrasings, two
      plausible wrong ones, and one adversarial one before any run (the D16
      and D30 lesson), and record the results in the pre-registration.
      Departure, made deliberately and recorded here rather than reworded
      in place: T9's and T10's graders are behavioural, not the three
      string-match checks prescribed above. That prescription was written
      before the task shapes were concrete, and both tasks turned out to
      change code rather than only diagnose, which makes behavioural
      grading available and strictly better. Three of the four graders
      written for this benchmark before Stage 7 needed correcting for false
      negatives on phrasing (D16, D17, D30), and a behavioural check cannot
      have that defect. Both graders still compute and print the report
      string signals as diagnostics, so the analysis loses nothing; they
      just do not gate. The artefact criterion survives intact, as
      `MEASUREMENT.txt` for T9 and `IMPACT.txt` for T10, because
      `PROBLEM.md` states it as an acceptance criterion in both. T11 stays
      a string-match grader, since it is diagnose-only, and gains a third
      gating check the T5 to T8 graders do not have: the report must state
      the mechanism, without which a shotgun list of every candidate would
      pass. Each of the three graders was tested six ways, one more than
      the five prescribed, and the results are recorded in the commits
      35909b1, 9a30586 and 6a07bfd and restated in the pre-registration.
- [x] 7.2 Pre-register in `test/results/<date>-T9-T11-preregistration.md`
      on the T7 template, with this prediction stated outright:
      `worker-sonnet-low` fails at least one of T9 to T11 at the reporting
      bar. Present it with the cost estimate; this is Gate B.
- [x] 7.3 Hardening rule: if all three clear at the floor, harden once (a
      second false premise and one red herring each for T9 and T10, one
      more service and one more red herring for T11), re-run; if they clear
      again, stop hardening, record "the floor keeps winning" as a finding,
      and proceed with the hardest task. Two rounds is the cap, matching
      `SYSTEM.md`'s reframe cap.
      Not triggered, 2026-09-13: T10 did not clear the floor (D42).
- [x] 7.4 Run the ladder raw: `python3 test/harness/benchmark.py --project
      "C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch" --tasks
      T9,T10,T11 --confirm --record --fresh`. This is each task's raw
      frontier. Jeb runs; the session prepares and analyses.
      Run 2026-09-11, recorded at 6c2c62d. T9's confirmation was voided
      by a harness defect (D41, fixed at b78df2a); its fresh attempt on
      2026-09-13 confirmed the floor, 9 of 9, with no recurrence of the
      defect. Frontiers: T9 floor, T10 `worker-opus-high`, T11 floor.
- [x] 7.5 D41: the results, whether criterion 1 is met, each task's
      frontier cell with its interval, and the Gate D verdict by the rule
      fixed at Gate A.
      Done 2026-09-13 as D42; D41 went to the harness defect that preceded
      it. Criterion 1 is met on T10; the Gate D rule's condition holds.
- [x] 7.6 Update this stage's status line and commit it.

Exit criteria: three tasks with graders tested five ways; pre-registration
committed before the run; the run recorded; D41; criterion 1 either met or
recorded as unmet after two hardening rounds.

Cost: the guess, with assumptions: three tasks, each climbing at least two
rungs before clearing (the prediction), search and confirmation at two cells,
per-run cost rising from about USD 0.2 at the floor to an unmeasured figure
at opus (the only data point above the floor is one fable-xhigh run at 103k
tokens). USD 30 to 150. The upper half of that range is uncertainty, not
expectation.

## Stage 8. Wire the floor evidence into routing

Status: **done (2026-09-14, see the 8.8 commit)**
Model: opus, high. A change to the routing table with the before-and-after
fixture discipline; opus is the measured better classifier and the better
judge of what the fixtures now mean.

Purpose: criterion 3. The rows `REVIEW.md` identifies as backed by judgement
only (open and long and consequential, open and medium and contained, and
the frontier row) get a destination with measurement behind it, or go.

Tasks:

- [x] 8.1 For each row above the floor, state what Stage 7 measured for its
      task class: a frontier above the floor with its cell and interval, or
      none. Rows whose only justification is blast radius are policy rows
      (`PREMISES.md`) and are listed separately.
- [x] 8.2 Design the change and record it in D42 before editing anything.
      A row with a measured frontier stays or moves to that frontier. A row
      with none is removed or merged downward, and its fixtures' expected
      cells follow. Policy rows are presented to Jeb at Gate C with their
      class stated, to keep or drop as a risk-appetite decision, never as a
      measurement. If Stage 7 recorded "the floor keeps winning", the design
      is the dissolution outcome from Stage 4.2 made concrete: the table
      collapses to the floor plus the clarify rule plus whichever policy
      rows survive Gate C, and that is written as the result it is.
      Done 2026-09-14 as D43 (D42 was taken by Stage 7's result). The
      policy-row decision was taken before 8.4 rather than at Gate C, so
      that one after-measurement runs against the final table; Jeb
      dropped all four. Gate C still accepts or rejects the whole change.
- [x] 8.3 Before-measurement: reuse Stage 3.3's reporting-grade run, or
      Stage 6's reporting-grade run of the shipped configuration if the
      table has not changed since; otherwise run one now.
      Done 2026-09-14, no spend: `src/ROUTING.md` is byte-identical to
      `af94deb`, so Stage 3.3's run is the before-measurement
      (`test/results/2026-09-11-routing-opus-af94deb-summary.md`, 155 of
      162, 16 of 18 fixtures at the bar, USD 15.91 for nine runs).
- [x] 8.4 Edit the table (the data file if Stage 6 shipped, `ROUTING.md`'s
      prose table if not) and the affected fixtures' `expected_cell` (F10,
      F11, F12, F14, F18 at least). ROW-BACKED and TABLE-DATA must hold;
      `check.py` green. Regenerate the worker definitions.
      Done 2026-09-14 at 67c53c6; the tick landed one commit later.
- [x] 8.5 After-measurement: a reporting-grade run against the new table.
      Compare fixture by fixture. Any fixture that regressed at the bar
      reopens the change per the attractor rule in `CLAUDE.md`.
      Run 2026-09-14, bundle `b6605f4`, 134 of 162 against 155 of 162
      before; F10, F11, F12 and F18 regressed at the bar, all by horizon
      reads that moved toward the cell the orchestrator wanted. Change
      reopened, D44: the reopened design is the floor plus the escalation
      rule, with T10's evidence as a section 4 escalation trigger. The
      after-run of the reopened design, F14 and F16 only by Jeb's choice at
      Gate C, was 18 of 18 (D45).
- [x] 8.6 Rebuild `dist/`, install into `orchestrator-scratch`, and log the
      install per the dogfooding protocol.
      Done 2026-09-14, before 8.5 because the after-run needs the installed
      table: bundle `2026-09-14-b6605f4`, clean stamp, preflight green,
      `test/results/2026-09-14-dogfood-install.md`.
- [x] 8.7 Gate C: present the before-and-after to Jeb. D42 records the
      outcome either way.
      Passed 2026-09-14, D45: the reopened design (floor plus escalation
      rule) accepted on the three runs' evidence.
- [x] 8.8 Update this stage's status line and commit it.

Exit criteria: two reporting-grade runs recorded; ROW-BACKED green; every
row above the floor backed by a measured frontier, removed, or kept as a
policy row by Jeb's recorded decision (criterion 3); Gate C passed; `dist/`
rebuilt and stamped clean.

Cost: about USD 27 per reporting-grade opus run, one or two runs, so USD 27
to 55.

---

## Gate D. Whether the framework track runs

Applied after Stage 8 and before Stage 9, by the rule fixed at Gate A. The
default is: Stages 9 to 12 run only if criterion 1 holds, because the
fleet's test is beating B0 on tasks the floor fails, and inside this
repository's grader boundary no such task would exist. If the track is
closed, D43 records the verdict and the reason, Stages 9 to 12 are marked
`blocked (see D43)` without rewording, and the plan proceeds to Stage 13.
If Jeb opens the track despite the rule, D43 records that and why, and the
stages run as written.

---

## Stage 9. Recover the missing half of SYSTEM.md, schemas, roles, B0

Status: **not started**
Model: opus, high. Authoring technique briefs and the B0 brief is judgement
work; the record schemas that follow are structured and could be done at
sonnet high, but one stage at opus high avoids a switch for a small saving.

Purpose: `SYSTEM.md` refers to "the eight-step sequence from the previous
answer" and "the forty techniques from the previous answer"; neither is in
the repository, and the document names the technique library as its actual
intellectual property. Nothing in Stages 10 to 12 can be built without at
least the tier-1 technique families and the record schemas. The single-model
baseline the fleet must beat is built here too, so Stage 11 has both sides
of its comparison measured on the same tasks.

Tasks:

- [ ] 9.1 Ask Jeb for the first half of the exchange. If he supplies it,
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
- [ ] 9.2 `src/System/schemas/`: one JSON Schema per record type in section
      4's table: ProblemRecord, PremiseRecord, MeasurementRecord,
      CandidateRecord, CritiqueRecord, SelectionRecord, EvaluationRecord,
      SolutionRecord, GapReport, plus PhaseDigest and BudgetEntry from
      sections 6 and 7. Each schema's description names its single writer
      role. Every free-text field carries a length cap, per section 6.
      Every record carries `id`, `ledger_version` and `references`.
- [ ] 9.3 `tools/validate_records.py`: validates a JSONL file against the
      schemas, standard library only (no dependency beyond what
      `score_routing.py` already uses; if JSON Schema validation without a
      dependency is too much, a hand-written validator over the eleven
      types is acceptable and simpler). `check.py` gains a SCHEMA check
      that example records under `test/fixtures/system/` validate, and that
      a deliberately broken example is rejected.
- [ ] 9.4 `src/System/ROLES.md`: one brief per role (Framer, Verifier,
      Generator template with the technique family as a parameter, Critic,
      Selector, Librarian), each stating its input slice, its output
      schema, and the rule that it emits new records referencing old ids
      and never edits another role's record. The cell assignment per role
      is configuration, given as `SYSTEM.md` section 5's quick-mode column
      and marked in the file as a prior to be measured in Stage 11.
- [ ] 9.5 `src/System/B0_BRIEF.md`: one handover prompt that runs all eight
      steps in a single worker. Output contract: a `ledger.jsonl` of records
      conforming to the schemas, and a `REPORT.md` carrying the answer, B0
      for the problem, and the non-negotiable from `SYSTEM.md` section 8:
      which premises are unverified and load-bearing.
- [ ] 9.6 `benchmark.py` gains `--brief <file>`: prepends a brief to the
      handover so the same task can be run raw and with B0. Own commit.
- [ ] 9.7 Per-role cost (E19 or the next free number): one Frame call at
      the section 5 quick-mode cell, one Verify, one Generate, one
      Critique, on a toy problem, each with its brief; record cost, tokens
      and wall clock in `FINDINGS.md`. These are the parameters Stage 11's
      pre-registration needs.
- [ ] 9.8 Run B0 on the Stage 7 tasks: the Stage 7.4 command with
      `--brief src/System/B0_BRIEF.md`. This is B0's frontier per task.
      Jeb runs; the session prepares and analyses.
- [ ] 9.9 D44: the briefs' provenance, the schemas, the roles, B0's
      frontier per task beside the raw frontier from D41.
- [ ] 9.10 Update this stage's status line and commit it.

Exit criteria: briefs for at least the three tier-1 families; eleven
schemas; validator passing on examples and rejecting a broken one;
`ROLES.md` and `B0_BRIEF.md` committed; B0's run recorded; per-role costs
in `FINDINGS.md`; D44; harness green with the SCHEMA check counted.

Cost: the B0 ladder over three tasks, similar to Stage 7's raw ladder,
USD 30 to 150, plus a few dollars of per-role probes.

## Stage 10. The Controller in code, quick mode

Status: **not started**
Model: sonnet, high. Load `python.sonnet.md`. The design decisions were made
in Stages 4 and 9 and `SYSTEM.md` section 3 is the specification; this is
implementation from a good brief, which is what `SYSTEM.md` says mid-size
models do well. If the first review of the state machine finds structural
problems, switch to opus high for the rework and record it.

Purpose: the integration shape `REVIEW.md` proposes. Not the orchestrator
persona running the framework; a deterministic Python Controller in
`benchmark.py`'s lineage that spawns the orchestrator's cells via `claude -p`
with role briefs and a file-based blackboard. The persona stays out of this
loop.

Tasks:

- [ ] 10.1 Factor the `claude -p` invocation, permission arguments,
      checkpoint and reset code that `benchmark.py` and `score_routing.py`
      share into `tools/claudep.py`, and make both harnesses import it.
      Behaviour unchanged; harness green; own commit. This is the one
      refactor in the plan and it exists so the Controller does not copy a
      third version.
- [ ] 10.2 `tools/system_controller.py`, command line: `--problem <file>
      --project <consumer> --mode quick --record`, plus `--dry-run` printing
      the phase plan and `--selftest` (task 10.6). Every run gets a
      directory `runs/<id>/` inside `--project` holding `ledger.jsonl`, a
      `records/` directory, `budget.jsonl` and `digests.md`.
- [ ] 10.3 The Scribe: validates every record against the Stage 9 schemas
      before it is appended; enforces one writer role per record type;
      rejects any candidate citing a ledger version other than the frozen
      one; assigns ids. Code only, no model calls.
- [ ] 10.4 The state machine, quick mode only: Intake, Frame, the Verify
      loop until stable or the verify budget is spent (verify ceiling one
      tool call, no code), Generate with three isolated Generators run as
      parallel `claude -p` processes each given its brief and the frozen
      ledger slice and nothing else, Critique blind (candidates, not
      generator reasoning), Select against acceptance and B0, paper
      falsification only, Close. Termination: acceptance met, dissolved,
      budget spent, or first candidate surviving critique with no unverified
      load-bearing premise, else B0. Reframe cap three. Phase digests under
      300 tokens, produced by code from the records, not by a model.
- [ ] 10.5 The two Controller model calls ("is the ledger stable enough to
      freeze"; "which technique families for this problem type") as
      schema-forced classification at `worker-sonnet-low`, using whatever
      structured-output mechanism Stage 2 found workable, validated on
      return. Everything else the Controller decides is code.
- [ ] 10.6 `--selftest`: runs the state machine over canned records from
      `test/fixtures/system/` with a fake role runner, no model calls, and
      asserts every transition, the stale-version rejection, the
      single-writer rejection, the reframe cap and each termination rule.
      `check.py` gains a SYSTEM check that invokes it.
- [ ] 10.7 Isolation rules written into `ROLES.md` and cross-referenced from
      `LIFECYCLE.md`: a Generator is never resumed, always spawned fresh; no
      role uses `SendMessage` to another; role-private state is discarded at
      phase end. This is where `LIFECYCLE.md`'s resume semantics and
      `SYSTEM.md`'s isolation rule are reconciled by rule rather than left
      to collide.
- [ ] 10.8 D45, including the charter amendment: `CLAUDE.md`'s "no runtime
      beyond Claude Code itself" gains the Controller as the one exception,
      with the reason (`REVIEW.md`, "Two Controllers"). Edit the sentence in
      `CLAUDE.md` in the same commit and cite D45 beside it.
- [ ] 10.9 Update this stage's status line and commit it.

Exit criteria: `--dry-run` prints a correct quick-mode plan; `--selftest`
passes and `check.py` counts it; one real quick-mode run on a toy problem
completes end to end in `orchestrator-scratch` and its `runs/<id>/` directory
contains valid records for every phase; D45 present; harness green.

Cost: session only, plus one toy run at about USD 1 to 3 (five to ten
model calls at cheap cells, per `SYSTEM.md` section 8).

## Stage 11. Fleet versus baseline

Status: **not started**
Model: opus, high. Most of this stage is waiting on runs, so the session's
own token cost is small; opus is here for the pre-registration and the
verdict, which are judgement.

Purpose: `SYSTEM.md`'s own falsification test, run with this repository's
instrument. Criterion 2.

Tasks:

- [ ] 11.1 Pre-register in `test/results/<date>-fleet-v-b0-preregistration.md`:
      predicted pass rate for quick mode on the Stage 7 tasks against B0's
      Stage 9 numbers; predicted cost per run from Stage 9's per-role
      figures; predicted cost per solved task for both; the decision rule
      with the Gate A multiplier; the failure shapes expected (forwarder
      confabulation per D20, Scribe rejections, budget exhaustion) and their
      predicted rates.
- [ ] 11.2 Gate E: present the pre-registration with the cost estimate to
      Jeb and wait for approval before any run.
- [ ] 11.3 Run quick mode nine times per task with `--record`. Jeb runs; the
      session prepares the commands with real paths and analyses.
- [ ] 11.4 Compare at the reporting bar: pass rate with Wilson intervals for
      fleet and B0 per task, cost per solved task, and the ratio. Score
      every prediction as held or falsified.
- [ ] 11.5 D46, the verdict, in one of two forms. "System": the fleet beats
      B0 within the multiplier, and Stage 12 wires the Controller in.
      "Prompt": it does not, and Stage 12 wires B0's brief in. Either is a
      result. Include the technique that produced each winning candidate,
      per task, logged as `SYSTEM.md`'s training signal from day one.
- [ ] 11.6 Update this stage's status line and commit it.

Exit criteria: pre-registration committed before the run; nine runs per task
recorded; D46 with an unambiguous verdict and every prediction scored.

Cost: the guess, with assumptions: quick mode at five to ten calls per run,
mostly at sonnet cells with one opus Framer call, about USD 0.5 to 2 per
run; twenty-seven runs; USD 15 to 55.

## Stage 12. Wire the fleet verdict into routing

Status: **not started**
Model: opus, high. A change to the routing table with the before-and-after
fixture discipline.

Purpose: the rows Stage 8 left above the floor, if any, get a destination
that D46 measured. Which destination depends on the verdict.

Tasks:

- [ ] 12.1 Design the destination. If D46 says "system": how the
      orchestrator persona hands a task to the Controller (a worker cell
      whose brief is "run `tools/system_controller.py` on this problem and
      return its `REPORT.md`" is the least invasive; the persona never runs
      the framework itself). If D46 says "prompt": a worker cell whose
      handover template is `B0_BRIEF.md`. Record the design in D47 before
      editing anything.
- [ ] 12.2 Before-measurement: Stage 8's after-measurement, if the table has
      not changed since; otherwise a reporting-grade run now.
- [ ] 12.3 Edit the table and the affected fixtures. ROW-BACKED and
      TABLE-DATA must hold; `check.py` green. Regenerate the worker
      definitions.
- [ ] 12.4 After-measurement: a reporting-grade run against the new table,
      compared fixture by fixture; any regression at the bar reopens the
      change.
- [ ] 12.5 Rebuild `dist/`, install into `orchestrator-scratch`, and log the
      install per the dogfooding protocol.
- [ ] 12.6 Gate F: present the before-and-after to Jeb. D47 records the
      outcome either way.
- [ ] 12.7 Update this stage's status line and commit it.

Exit criteria: the two runs recorded; ROW-BACKED green; Gate F passed;
`dist/` rebuilt and stamped clean.

Cost: about USD 27 per reporting-grade opus run, one or two runs.

## Stage 13. Close-out

Status: **not started**
Model: sonnet, medium.

Tasks:

- [ ] 13.1 `CLAUDE.md`: strike through every open question this plan
      answered, with the decision or FINDINGS row that answered it, in the
      style the file already uses. Replace the "Active plan" section with a
      one-line pointer to this file marked complete.
- [ ] 13.2 `docs/COST.md`: recompute against the final bundle, including
      the cost per verdict of the shipped classifier and the Controller's
      per-run cost if it shipped.
- [ ] 13.3 `docs/FINDINGS.md`: consolidate; every "unverified" row either
      moved up with evidence or left with the date it was last checked.
- [ ] 13.4 This file: set the plan's status to complete with the date; every
      stage `done` or `blocked` with its pointer.
- [ ] 13.5 D48: what the branch delivered against the six acceptance
      criteria, one line each, and the merge question for Jeb. The merge
      into `main` is Jeb's action, not the session's.
- [ ] 13.6 Final `check.py` run recorded with `--record`.

Exit criteria: harness green; plan marked complete; D48 present.

Cost: session only.

---

## Cost summary

Guesses, with the assumptions stated in each stage. Session tokens are
excluded throughout.

| Stage | Model calls | Estimate |
| :--- | :--- | :--- |
| 0 and 1 | none beyond the session | USD 0 |
| 2 | probes | USD 2 to 5 |
| 3 | one reporting-grade routing run if 3.3 is taken | USD 0 or about 27 |
| 4 and 5 | none | USD 0 |
| 6 | two steering and one or two reporting-grade routing runs | USD 45 to 72 |
| 7 | one raw ladder over three tasks | USD 30 to 150 |
| 8 | one or two reporting-grade routing runs | USD 27 to 55 |
| 9 | one B0 ladder over three tasks, plus per-role probes | USD 35 to 155 |
| 10 | one toy run | USD 1 to 3 |
| 11 | twenty-seven quick-mode runs | USD 15 to 55 |
| 12 | one or two reporting-grade routing runs | USD 27 to 55 |
| 13 | none | USD 0 |

Total: roughly USD 130 to 340 for Stages 0 to 8, which is the routing
product measured and repaired, and a further USD 80 to 270 for Stages 9 to
12 if Gate D opens them. Stage 7's upper bound is uncertainty about cells
above the floor that nothing has yet measured. Every run is Jeb's to start;
the session prepares commands with real paths and never starts a paid run
itself.

## What this plan does not do

- It does not run deep mode. Quick mode is the smallest fleet that tests
  `SYSTEM.md`'s claim; deep mode is a later plan if D46 says "system".
- It does not build the Librarian's cross-run library beyond logging the
  training signal (which technique won, per task). Fifty runs is
  `SYSTEM.md`'s own threshold for that library to matter.
- It does not test whether a worker should know its own cell. The fifteen
  `model-specific-*` persona sections are empty, so every cell runs the
  same persona, and the question stays open until a benchmark task
  distinguishes cells at all. Once Stage 7 produces one, the test is cheap
  (fill one section, re-run that task at the bar) and belongs at the front
  of the next plan.
- It does not add haiku cells. Invariant 5 stands as D5's decision.
- It does not merge `the-system` into `main`. That is Jeb's call at D48.
