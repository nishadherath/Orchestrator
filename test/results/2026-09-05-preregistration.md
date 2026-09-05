# Pre-registration: the next routing run

Written and committed before the run it describes. The commit that adds this
file is the proof of precedence; if the numbers below were adjusted after
seeing results, the history would show it.

Purpose: the routing table fill (D9), the clarify rule (D10), the fixed
calibration instruction (D6) and `--runs N` have all been verified by hand and
against stubs. None has faced a live session. This states what each should do,
with numbers, before the data exists, so the run is a test rather than a
collection exercise (persona section 6.2: predict before measuring).

## What is being tested

Bundle `2026-09-05-4cf35f7`, installed into `orchestrator-scratch` (D8).
Changes since the baseline bundle `2026-09-05-1708054`:

- The routing table names all eighteen assessment triples; five previously had
  no row (D9).
- One documented tie-break for open, long, consequential (D9).
- `ROUTING.md` section 1.1 defines when to ask instead of routing (D10).
- The calibration instruction tells the orchestrator to assume referenced
  artefacts exist (D6).

## Baseline

E12, one run per model, bundle `2026-09-05-1708054`, counts taken from
`grep -c "action: clarify"` on the two recorded files in this directory.

| Metric | Sonnet | Opus |
| :--- | :--- | :--- |
| Agreement | 11/17 | 8/17 |
| Clarify verdicts | 4/17 (F10, F13, F16, F17) | 10/17 (F01, F04, F05, F07, F08, F09, F11, F15, F16, F17) |
| Spurious clarify (excluding F16) | 3 | 9 |
| Under-provisioned | 4 | 1 |
| Cost per run | USD 0.7623 | USD 3.5808 |

The baseline is a single run per model with no error bar. Any change smaller
than a few fixtures is not distinguishable from run-to-run variation.

## Predictions

Three runs per model. Point estimate first, then the value that would falsify
the change rather than merely disappoint.

| Prediction | Sonnet | Opus | Falsified if |
| :--- | :--- | :--- | :--- |
| Clarify verdicts per run | 1/17, at most 2 | 1/17, at most 2 | Either model clarifies on more than 3 of 17 in any run |
| Agreement | 13/17 (range 12 to 14) | 16/17 (range 14 to 17) | Opus below 12/17, or sonnet below 11/17 |
| Spurious clarify | 0 | 0 to 1 | Opus above 2 |
| Cost per run | USD 0.78 to 0.85 | USD 3.65 to 3.95 | More than 10 percent above the top of the range |

The opus prediction is the sharp one: 8/17 to 16/17, driven entirely by
clarify verdicts converting to spawns that were already correctly assessed.

## Per-fixture predictions

Fixtures the changes should fix, with the mechanism:

| Fixture | Model | Baseline | Predicted | Mechanism |
| :--- | :--- | :--- | :--- | :--- |
| F17 | both | clarify | spawn `worker-sonnet-medium` | Mechanical, short, consequential is now an explicit row (D9), and section 1.1 names irreversible-but-clear as a non-reason to ask |
| F10 | sonnet | clarify | spawn `worker-opus-high` | Axes were already 3/3; only the action was wrong |
| F01, F15 | opus | clarify | spawn `worker-sonnet-low` | Axes already 3/3; F15 is the urgency trap, named as a non-reason |
| F04, F09 | opus | clarify | spawn `worker-sonnet-medium`, `worker-opus-high` | Axes already 3/3 |
| F05, F07 | opus | clarify | spawn `worker-sonnet-medium`, `worker-sonnet-xhigh` | Axes imperfect, but the table maps their stated axes to the expected cell anyway |
| F11 | opus | clarify | spawn `worker-opus-xhigh` | Cell was already right; only the action was wrong |

Fixtures predicted to stay wrong, so a fix here is a surprise worth noting:

| Fixture | Model | Why it should not improve |
| :--- | :--- | :--- |
| F05, F08, F09 | sonnet | Axis misjudgment, not an action or coverage problem. Nothing in these changes addresses assessment quality |
| F08 | opus | Called the horizon medium rather than long. Unaffected by coverage or the clarify rule |

## The watch item: a harm this change could cause

D9's tie-break tells the orchestrator to prefer `worker-opus-xhigh` over
`worker-fable-xhigh` for open, long, consequential work. F13 is open, long,
**contained**, so the tie-break does not apply to it and its confirmed answer
remains `worker-fable-xhigh`. Opus already answered F13 correctly at baseline.

If opus now answers F13 with `worker-opus-xhigh`, the tie-break wording is
leaking beyond the triple it was written for, and the constraint bullet needs
narrowing. This is a possible regression introduced by D9 and is the single
result most worth reading carefully, because nothing else in this run would
reveal it.

## Protocol

From `orchestrator-scratch`, with `CLAUDE_CODE_EFFORT_LEVEL`,
`CLAUDE_CODE_SUBAGENT_MODEL_FORCE` and `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`
unset:

```
python3 preflight.py
```

Then, from this repository:

```
python3 test/harness/score_routing.py --project <orchestrator-scratch> --model sonnet --runs 3 --record
python3 test/harness/score_routing.py --project <orchestrator-scratch> --model opus   --runs 3 --record
```

Predicted total spend, three runs per model: about USD 2.40 for sonnet and
USD 11.30 for opus, USD 13.70 together.

## What each outcome means

- Predictions hold: the clarify rule and the table fill are validated on this
  fixture set, and the next question is the cost and quality benchmark, which
  is the only remaining way to test this repository's actual claim.
- Clarify rate does not fall: D10 is wrong. Reopen it rather than defending it,
  and diagnose before building anything further.
- Agreement rises but clarify stays high: the rule is being read as advice
  rather than as a rule, which is a wording problem in section 1.1 rather than
  a design problem.
- F13 flips to `worker-opus-xhigh` on opus: narrow the D9 tie-break bullet.
