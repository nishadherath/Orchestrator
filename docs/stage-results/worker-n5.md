# N5: diverse corpus, cell screen and development comparison

Date: 2026-09-25. Gate: **N5 development complete; no new shipping policy
qualified**. The default B0 worker ladder is unchanged. Stop for operator
review before N6. This result covers the approved 15-cell
[screen](worker-n5-screen-2026-09-25.md) and the separate development campaign;
it makes no claim about the 12 reserved R tasks.

## Corpus and execution boundary

The older N4 corpus assessed every task as `moderate`, so it could not exercise
complexity-sensitive selection. N5 added a deterministic, fully synthetic
[24-task corpus](../../test/fixtures/worker_n5_realworld/catalogue.json): 12
development and 12 sealed reserved tasks. Each split has four routine, four
moderate and four complex tasks, with two distinct mechanisms in each of six
families. Every task has two public examples and three independent hidden
cases. The reference implementations passed all 24 oracles; a public-example
lookup failed every hidden oracle. The actor receives only public files, and
the grader runs after the worker stops in the attested WSL boundary.

The corpus adds variation in behaviour, state and failure modes, but every
task is a bounded single-file Python edit. It does not measure multi-file
integration, dependency maintenance, large-context retrieval, open-source
issue resolution or human review quality. Complexity is a predeclared public
assessment, not a hidden answer supplied to the worker.

The [frozen manifest](../../test/results/2026-09-25-worker-n5-development-manifest.json)
has SHA-256 `cd88664ef034fc982e27fc99386ca140e32127f78ab65d6982d91232555ddc09`.
The operator approved that exact manifest and [spend notice](worker-n5-development-spend-notice-2026-09-25.md).
The campaign used 12 D tasks, each once under B0, candidate and alternative,
with balanced arm order and a shared USD 3 root allocation. The actual first
cells were:

| Assessment | B0 | Candidate | Alternative |
| :--- | :--- | :--- | :--- |
| Routine | Sonnet low | Sonnet low | Sonnet medium |
| Moderate | Sonnet low | Sonnet high | Sonnet xhigh |
| Complex | Sonnet low | Opus high | Fable high |

The experimental selections were real manifest-bound `TaskExecutor`
dispatches, not shadow labels. All arms had the same public task materials,
acceptance contract and bounded repair ladder. Fable's model identity was
observed in the screen; only requested effort, conveyed by CLI argument, is
evidenced. Served effort was not independently reported by the provider.

## Reconciled development outcome

The [analysis](../../test/results/2026-09-25-worker-n5-development-analysis.json)
is reproducible with [worker_n5_analysis.py](../../tools/worker_n5_analysis.py).
It checks the manifest, 36 frozen rows, campaign and budget digests, all root
records, terminal receipts, model identity, actor hashes and hidden-grade
bindings. Its digest is
`8bd4cf0b88f6bed37d780b5206826c757cad996fc832859222cba540d4f7ba14`.
The [checkpoint](../../test/results/2026-09-25-worker-n5-development-run/campaign.json)
is complete and the [budget ledger](../../test/results/2026-09-25-worker-n5-development-run/budget.json)
has 36 settled episode allocations, no unresolved calls and no budget breach.
No call was automatically replayed.

From the repository root, rerun the provider-free reconciliation with:

```text
python tools/worker_n5_analysis.py --manifest test/results/2026-09-25-worker-n5-development-manifest.json --run test/results/2026-09-25-worker-n5-development-run --output test/results/2026-09-25-worker-n5-development-analysis.json
```

| Arm | Hidden acceptance | Mean quality /100 | False success | Critical errors | Calls | Reported USD |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| B0 | 11/12 | 97.2225 | 1 | 0 | 19 | 0.974192 |
| Candidate | 12/12 | 100 | 0 | 0 | 15 | 0.923656 |
| Alternative | 12/12 | 100 | 0 | 0 | 16 | 1.463923 |

The one B0 miss, D03, was a public-acceptance false success: its hidden
quality was 66.67/100. Candidate and alternative reached 100/100 on D03, but
the candidate and B0 used the same Sonnet-low first cell and repair policy for
routine work. That difference may be run variation; it does not demonstrate
that complexity-sensitive selection improved D03.

| Complexity, four tasks each | B0 accepted / USD | Candidate accepted / USD | Alternative accepted / USD |
| :--- | :--- | :--- | :--- |
| Routine | 3/4 / 0.633438 | 4/4 / 0.251045 | 4/4 / 0.368659 |
| Moderate | 4/4 / 0.142471 | 4/4 / 0.215742 | 4/4 / 0.230860 |
| Complex | 4/4 / 0.198284 | 4/4 / 0.456869 | 4/4 / 0.864403 |

On moderate tasks, candidate cost about 51% more than B0; on complex tasks,
about 130% more. Both achieved the same 4/4 hidden acceptance and 100/100
quality. Fable-high alternative cost still more without a measured quality
gain. The overall candidate total is slightly lower only because the routine
runs used fewer repairs. One run per task-arm and near-ceiling grades cannot
separate policy effects from sampling variation or support a general cost
ranking.

The 36 episodes used 50 provider calls: 37 Sonnet, nine Opus and four Fable.
Requested efforts were low 22, medium seven, high 17 and xhigh four. The
receipts sum to **USD 3.36177041 provider-reported API-equivalent usage**, not
an incremental Claude Code subscription invoice. They report 758 ordinary
input, 205,416 cache-creation input, 1,999,183 cache-read input and 69,368
output tokens. Summed call wall time was 1,305.298 seconds; elapsed campaign
time was about 98 minutes including staging and grading. The approved USD 108
was local admission allocation, not a provider charge or hard cap. The dated
USD 10–60, 2–8 hour forecast was conservative for these short tasks. The
[spend notice](worker-n5-development-spend-notice-2026-09-25.md) records the
pricing source and assumptions; this outcome is not a measured savings claim.

## Decision and limits

Keep **B0 as the shipping default**. Retain the tested candidate rule table as
an experimental, unpromoted comparator: Sonnet low for routine, Sonnet high
for moderate and Opus high for complex. Do not tune it on the reserved split.
Reject the Fable-high alternative as a default candidate on this development
evidence: its cost was higher with no measured acceptance or quality gain.

This is a completed N5 comparison, including its negative economic finding,
not a qualification of broader task-sensitive routing. The 15-cell screen had
only three tiny microtasks per cell; the D corpus remains synthetic and small;
the ceiling effect masks possible gains on harder work. The predeclared N6
12-task two-repetition design is statistically weak for modest differences, as
the [N4 preflight](worker-n4.md) established. Before spending on N6, review
whether its unchanged reserved corpus can answer a useful decision question or
whether a separately frozen, harder multi-file evaluation should be designed.
The N6 R actor outputs and grades were not run or inspected in N5.
The provider-free [N5-to-N6 gate review](worker-n5-n6-gate-review-2026-09-25.md)
derives the current 12-task bound's minimum observable effects and recommends
deferring the original N6 spend pending an operator decision.

The normal-host full offline pre-build gate and distribution build passed
before the campaign, followed by source-equivalence release checks. Graft's
structural graph was in sync at preflight. Two DeepSeek semantic refreshes
failed on an unparseable tool-call response, leaving eight stale summaries;
their exact usage and cost are unknown. This does not alter the local test or
receipt results, but semantic freshness remains an open maintenance item.
After reconciliation, the focused corpus, experimental-dispatch and
development-driver tests passed (two, five and two tests respectively), as
did `git diff --check`. The package check found 75 source-equivalent
distributed files and no sensitive material. Its clean-build stamp and
publication actions remain open because the work is uncommitted.
