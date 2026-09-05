# Decision ledger

Append-only. One entry per decision, newest last. An entry records what was
decided, why, and what would reverse it. Do not edit earlier entries; add a
superseding entry instead.

## 2026-09-05 D1. Adopt the CLAUDE.md layout on disk

Decision: move the deliverables under `src/`, add `docs/`, `test/`, `tools/`
and `dist/`, and rename the consumer install guide from `README.md` (briefly
`PERSONA.md`) to `src/README.md`.

Why: `CLAUDE.md` described this layout while the tree was flat, so every path
in the charter was wrong. Moving `.claude/agents/` out of the repository root
also stops the fifteen workers loading into development sessions, which the
charter forbids outside the dogfooding protocol.

Reversal: none expected. `tools/` is an addition to the charter layout because
the generator and the bundle builder are neither deliverables nor tests.

## 2026-09-05 D2. Generated persona files stay at the root, without their generator

Decision: `ENGINEERING_PERSONA.*.md` and `ENGINEERING_PERSONA_LANGUAGES/` remain
at the repository root as copied-in generated artefacts. Their source
(`source/core.source.md`, `source/languages.source.md`) and builder
(`build_persona.py`) live in another repository and are not vendored here.

Why: the persona documents locate themselves at the root and the loading matrix
in section 3.2 depends on that. Vendoring the generator would duplicate a
build that has one owner elsewhere.

Guard: `test/harness/persona.sha256` records a hash of each file with carriage
returns stripped. The harness fails if a hash changes, so a hand edit of a
generated file is caught. To update: rebuild from source, copy in, run
`python3 test/harness/check.py --update-persona-manifest`, commit both.

Reversal: vendor the generator if the persona starts changing in step with this
repository.

## 2026-09-05 D3. Worker definitions are generated with the persona inlined

Decision: `src/agents/*.md` are produced by `tools/generate_workers.py` from
`src/WORKER_PERSONA.md` and the routing table in `src/ROUTING.md`. The shared
persona is inlined into each definition. A cell's `model-specific-*` section is
inlined only when non-empty. Each description states the cell, the assessments
that route to it (or that none do), and the instruction never to pass `model`.

Why: the hand-written definitions told each worker to read `WORKER_PERSONA.md`
by bare relative name, which fails when the definitions are installed globally,
and cost a tool call at startup to load an empty section. Descriptions are the
one field the orchestrator sees in the Agent tool listing without reading the
rubric; identical descriptions carried no information. Deriving the routed
assessments from the table keeps one source of truth.

Kept: all fifteen cells, because CLAUDE.md fixes the count. Six are not in the
routing table and their descriptions say so. Dropping them is a charter change.

Reversal: if the empirical checklist shows a worker benefits from knowing its
cell, fill the sections in; no generator change is needed.

## 2026-09-05 D4. dist/ is committed and built only on a green harness

Decision: `tools/build_dist.py` runs `test/harness/check.py` and refuses to
build on any FAIL. The bundle is committed, stamped in
`.claude/ORCHESTRATOR_VERSION` with the date and the source commit it was
built from, and `-dirty` if the tree was not clean. The bundle carries
`ORCHESTRATOR.md` (ROUTING.md and LIFECYCLE.md concatenated) rather than the two
files separately, so a consumer installs one file beside `CLAUDE.md`.

Why: the charter says nothing ships from `dist/` until the harness passes and
that dogfooding must name the bundle version. A build step that can be
bypassed would make both unenforceable.

Reversal: split `ORCHESTRATOR.md` back into two files if a consumer needs to
adopt routing without lifecycle management.

## 2026-09-05 D5. Haiku is permanently excluded from the worker matrix

Decision: haiku is not, and will not become, a worker cell. Invariant 5 in
CLAUDE.md stands as a decision, not a carry-over pending review.

Why: Jeb's call, made after E8 (`docs/FINDINGS.md`) disproved the invariant's
original justification (a defined `effort: high` haiku worker showed "Haiku 4.5
(high)" on its `/tasks` row, so haiku does honour effort). The justification
was wrong; the exclusion stands anyway. This forgoes the cell most likely to
undercut `worker-sonnet-low` on cost for mechanical, short, contained work, a
trade-off recorded here rather than left implicit.

Reversal: none. Reopening this needs a new decision entry, not an edit to this
one.

## 2026-09-05 D6. The calibration instruction assumes referenced artefacts exist

Decision: score_routing.py's VERDICT_INSTRUCTION now tells the orchestrator
under test to assume every artefact a fixture task refers to exists, even
though orchestrator-scratch (the consumer project used for calibration, see
D8) has none of them: no ticket for F01, no pull request for F09, no gateway
logs for F11, no theme.css for F15, and more generally no existing codebase
for the fixtures that assume one (docs/duration.md and duration.spec.ts in
F04, RateLimiter's doc comment in F05, src/legacy/ in F07, and others).

Why: without the instruction, an orchestrator that checks its inputs before
spawning is correct to answer action: clarify on any of these, which is
indistinguishable in score_routing.py's output from an orchestrator that
cannot judge the task. The fixtures test routing judgement, not whether the
orchestrator notices a scratch project is empty; the instruction removes the
second effect so the score measures the first.

Impact: the results in test/results/2026-09-05-routing-sonnet.md and
test/results/2026-09-05-routing-opus.md (empirical-checklist.md item E12) were
recorded before this sentence existed and are not comparable with any run made
after it. Re-run E12 before drawing further conclusions from routing scores.

Reversal: seed orchestrator-scratch with the actual artefacts instead, and drop
the sentence, if a future stage wants the orchestrator scored on noticing
missing context as well as on axis judgement.

## 2026-09-05 D7. Clarify is a first-class routing outcome

Decision: `action: clarify` stands alongside `action: spawn` as a legitimate
orchestrator response, not a failure to route. `test/harness/score_routing.py`
already scores it and fixture F16 already expects it; `src/ROUTING.md` itself
states no rule for when clarify is the correct answer.

Why: Jeb's call, made after E12 showed a sonnet orchestrator and an opus
orchestrator disagreeing sharply on how often to clarify (3 of 17 verdicts
against 9 of 17, `docs/FINDINGS.md`) with no rule in `ROUTING.md` to referee
the disagreement. Leaving clarify unruled treats every clarify verdict as
unscoreable uncertainty instead of a defined choice.

Deferred: the rule itself, when clarify is correct as distinct from a
low-confidence spawn, is judgement work scoped for a later stage of the
improvement plan. This entry records only that clarify is in scope, not what
the rule says.

Reversal: drop clarify from `score_routing.py` and retire fixture F16 if a
future review decides the orchestrator should always spawn and let the worker
report underspecification instead (`ROUTING.md` section 4 already covers that
path).

## 2026-09-05 D8. orchestrator-scratch is the consumer project

Decision: `orchestrator-scratch` is the consumer project for fixture
calibration (`score_routing.py`), any cost or quality benchmark built later,
and dogfooding (`test/harness/empirical-checklist.md` item E13's protocol). It
is not this repository; `CLAUDE.md`'s Dogfooding section already forbids
running from here.

Why: Jeb's call. The project already has the `dist/` bundle installed and
carries the E1 to E13 empirical history and the two dogfood runs recorded in
`test/results/2026-09-05-dogfood.md`, so it continues existing work rather than
starting fresh in one of the six unconnected sibling directories (Book,
Provenance, TealElephant, Tsunami, WikiSkills, Wuxing).

Reversal: name a different project here if orchestrator-scratch's synthetic,
no-other-codebase nature becomes a problem for a specific measurement; D6
already works around this for fixture calibration.

## 2026-09-05 D9. The routing table names all eighteen triples; one documented tie-break

Decision: `src/ROUTING.md`'s table is total over the three axes it defines.
Five combinations that previously had no row now do: mechanical-short-
consequential (`worker-sonnet-medium`, closing the exact gap fixture F17 had
already worked around), mechanical-long-contained and mechanical-long-
consequential (one new row, "Mechanical, long horizon", at `worker-sonnet-high`,
mirroring structured's own long-horizon row in not splitting by blast),
structured-short-consequential (widened into the existing medium-consequential
row, now `worker-sonnet-high` for short or medium), and open-short-
consequential (widened into the existing medium-or-long-consequential row, now
any horizon, `worker-opus-xhigh`). The one remaining double match, open-long-
consequential (`worker-opus-xhigh` and `worker-fable-xhigh`), is not closed by
picking a winner; it is documented as a tie-break in the table's constraints:
prefer `worker-opus-xhigh`, and reach for `worker-fable-xhigh` only when the
task itself demands sustained, self-directed investigation, not merely because
it is long and consequential. Fixture F12 (open, long, consequential, no such
demand, confirmed `worker-opus-xhigh`) is cited as the worked example.
`test/harness/check.py`'s new ROUTE-TOTAL check enforces both: zero gaps, and
any remaining double match must name both workers in a tie-break sentence
still present in the file, or the check fails.

Why: Jeb asked for the fix and the check together so the tree is never red
between them (2026-09-05 conversation). Every new row uses a rule already
established and confirmed elsewhere rather than a fresh judgement call: the
mechanical-short-consequential fill is fixture F17's own rationale, made into
a table row instead of a worked-around gap; the mechanical-long row mirrors
structured's existing blast-agnostic long-horizon row, one model-effort step
below it; the two widened rows extend an adjacent row's horizon range rather
than inventing a new cell; the open-long-consequential tie-break's default
(`worker-opus-xhigh`) is fixture F12's own confirmed answer, not a new one.

Verified: ROUTE-TOTAL added to `test/harness/check.py`, passes (18 triples, 0
gaps, 1 documented tie-break). Checked it actually catches regressions, not
just the current state: removing the tie-break sentence and deleting the new
mechanical-long row each independently produced the expected FAIL, both
reverted before this commit. `tools/generate_workers.py` regenerated the three
affected worker definitions (`sonnet-medium`, `sonnet-high`, `opus-xhigh`) with
0 drift after. Fixture F17's rationale and note updated to describe a closed
gap rather than an open one; its `assessment`, `expected_cell` and
`assigned_by` are unchanged, so it did not need re-review.

Reversal: remove a row and its ROUTE_TOTAL_ALLOWED_CONFLICTS entry together;
the check will immediately say which triple lost coverage.
