# Q4S S2 independent corpus and prospective screen freeze

Date: 2026-09-26 Australia/Sydney. The six-family corpus, public trigger
assessments, evaluator-only oracles, quality rubric, two-call canary and
18-episode screen manifest are built and frozen **before any Q4S model call**.
The focused Q4S checks pass. The repository-wide offline gate was red for
historical/environmental checks described below at the time of the first
sandbox run. It subsequently passed with normal host access before S3.
B0 and `dist/` are unchanged.

## Frozen task units

All six public issues are authored regressions on exact, permissively
licensed upstream pre-fix source, not claims that an upstream issue used our
wording. Their provenance records link the corresponding upstream fix commit.
The reference overlay bytes match that fix; the actor sees neither the
reference nor the evaluator-only cases. Source inventories and licence bytes
were checked against Git objects from the six pinned public repositories.

| Unit | Repository and fix | Licence | Python source lines | Trigger | Baseline / partial / reference oracle score |
| :--- | :--- | :--- | ---: | :--- | :--- |
| S01 | [attrs](https://github.com/python-attrs/attrs/commit/4b5b295bb815bf845fa3570bf63781a88212db40), generator assignment hooks | MIT | 6,264 | Positive | 20 / 80 / 100 |
| S02 | [pluggy](https://github.com/pytest-dev/pluggy/commit/a031c1c91fdd5e4c684f97c2a0e96cbc7e18835f), hookspec defaults | MIT | 1,833 | Positive | 0 / 25 / 100 |
| S03 | [h11](https://github.com/python-hyper/h11/commit/ce515c5a9a5113646754bdb7aee3625821c9fd50), header casing | MIT | 2,167 | Positive | 0 / 50 / 100 |
| S04 | [Sorted Containers](https://github.com/grantjenks/python-sortedcontainers/commit/b5395b553d1fe3aa2f2668436a005aeedb5f6259), pickle reduction | Apache-2.0 | 4,234 | Positive | 0 / 50 / 100 |
| S05 | [more-itertools](https://github.com/more-itertools/more-itertools/commit/3eb4053e1aacac53853f6e0abae556f280726f01), zero-cache lookahead | MIT | 7,268 | Negative | 45 / 80 / 100 |
| S06 | [idna](https://github.com/kjd/idna/commit/9067b803a55441805934410b11c0899209b66785), joiner exceptions | BSD-3-Clause | 19,876 | Negative | 50 / 75 / 100 |

Each family has a distinct repository and issue, two to four existing
editable modules, an actor-visible `ISSUE.md` and smoke check, root-only
oracle, full upstream reference and incomplete partial overlay. The actor
package remains within 200 files and 5 MB. The six repositories differ from
Q3/Q4/Q4R's cachetools, ItsDangerous, Click, urllib3, Tenacity, PyJWT,
packaging and platformdirs families and from the N5 synthetic tasks.
Blinker was screened out before fixture construction because its pinned
package had 589 Python source lines, below the 1,000-line floor. idna replaced
it before any Q4S outcome existed. The selected mechanisms cover API
compatibility, state and memory, protocol serialisation and error typing;
there is no separate platform-specific family.

The [public-only trigger record](../WORKER-Q4S-PUBLIC-TRIGGERS-2026-09-26.json)
binds each judgement to the issue hash, cited line, editable module list and
module hashes. S01-S04 meet the predeclared cross-module rule; S05-S06 are
confined to at most two editable modules. The [corpus calibration](../../test/results/2026-09-26-worker-q4s-public-calibration.json)
records zero provider calls and exact baseline/partial/reference outcomes.
The [canary](../../test/fixtures/worker_q4s_canary/actor/ISSUE.md) is a
separate small synthetic multi-file task; its baseline public check fails and
its reference passes. It is excluded from the six-family and reserved sets.

## Screen contract and cost

The [manifest](../../test/results/2026-09-26-worker-q4s-screen-manifest.json)
records manifest digest `c8e5b7e6370eb46011551d48d56a8bc9905eb13b50ac3798f8ab414ac50bd8b1`.
It binds all actor inventories, oracle and rubric hashes, the public trigger,
canary, Claude Code 2.1.273 binary and Q4S launcher/schema hashes, prompt,
registry, cyclic Latin-square order, first cells, common repair tail, cost
and stop rules. The policy uses Sonnet-medium only on four positives and B0
on two negatives; negative-family medium calls are diagnostic. Comparison is
against each of two B0 repetitions at the independent family level, with
precommitted acceptance, quality, reporting, critical-error and cost guards.

The [dated spend notice](worker-q4s-spend-notice-2026-09-26.md) reserves USD 6
locally for the S3 two-call canary and USD 72 for S4's 18 episodes, at most
56 provider calls combined. Direct API-equivalent usage is projected at
USD 6.5-33 and elapsed time at 2.25-8 hours; Claude Code subscription invoice
impact is unknown. The operator's standing paid-call authorisation is bound
to this exact scope, and the staged review gate remains before S3. No paid
call, campaign directory or provider-call intent was made in S2.

## Verification and correction

- Final Git-object source and licence audit: six of six passed, including the
  reduced h11 inventory. The h11 actor omits 12 upstream tests whose old
  expectations contradict the new public issue; all retained source bytes
  match the pinned Git objects.
  Partial regeneration audit: six of six passed. Frozen catalogue and trigger
  checks passed. The final manifest was regenerated after the inventory
  guards were tightened.
- Provider-free calibration: all six reference overlays scored 100; each
  baseline failed a meaningful oracle case; each partial improved over its
  baseline and stayed below 100. Four focused S2 unit tests, all six frozen
  catalogue checks, the public-trigger check and the 722-file prose check
  passed after the final h11 correction. Static manifest reproduction passed
  using the saved runtime hashes; this is not a live host check.
- A local probe accidentally created `__pycache__` in S04's actor before the
  first draft task digest. The exact-byte audit caught it. Only those generated
  bytecode files were removed; S04's task digest, calibration and manifest
  were recomputed before review or model calls. The final actor inventory is
  eight files and matches upstream exactly.
- h11's old tests were inside its importable package and asserted lowercase
  output, contradicting the new public issue. Before any model call, the 12
  `h11/tests/` files were removed from the actor inventory. A byte-for-byte
  comparison against the prior Git-audited inventory confirmed that all 15
  retained actor files were unchanged. The S03 task digest, calibration and
  manifest were regenerated; Windows provider-free grading retained scores
  0 / 50 / 100. A final WSL Git-object audit passed after host access was
  restored. The manifest's CLI and launcher hashes were carried from the
  earlier S1-attested runtime snapshot during the offline re-freeze; the
  subsequent live Q4S host attestation and manifest check both passed.
- Graft freshness reports the committed graph stale with four changed
  indexed files and new unindexed Q4S sources. No measured token saving is
  claimed and no semantic rebuild was run for this evaluation-only freeze.

An earlier full repository harness completed with exit 1. A shorter sandbox
diagnostic run identified `WORKER-Q4-SCREEN` (historical Q4 host evidence reported stale),
`WORKER-Q4-RESULT` (sandbox could not read a historical root-owned campaign),
and `COMPACT-BENCH-SELFTEST` (child-process permission denied). The diagnostic
skipped four long legacy checks, so it is not a substitute for a green full
run. Local Q4 source hashes match their saved attestation; the exact reason
for its host validation failure was access-dependent: the same host check
passed with normal WSL access. The historical Q4 result and compaction
self-test likewise passed with normal host access. A separate Q4 screen test
was tied to the current date while replaying a sealed prior-day campaign;
its test now supplies the historical freeze date to that one validation and
asserts that production validation still rejects the expired manifest. All
four Q4 screen tests pass. Historical Q4/Q4R evidence and paid-dispatch code
were not changed. The full repository harness subsequently passed with normal
host access, including the corrected Q4 screen test. The S3 transport canary
was then run under its separate source-bound stage manifest.

## Next action

The [S3 result](worker-q4s-s3.md) records the completed two-call canary.
Before S4, bind its paid driver and recheck the S2 source, catalogue,
trigger, calibration, manifest and live host. A scope, CLI, launcher, schema
or corpus change requires a new manifest and review.
