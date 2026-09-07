# T8 re-graded against corrected grade.sh (D30), 2026-09-08

Same checkpoint as `2026-09-08-benchmark-af94deb.md`
(`.benchmark-checkpoint.jsonl` in the consumer project, bundle
2026-09-07-af94deb). No new `claude -p` calls: every one of the twelve
stored worker reports for T8 was re-graded offline against the corrected
`test/fixtures/benchmark/T8/grade.sh`, which drops the redundant literal
`api_client.py` requirement (D30). This file records that re-grading; it
does not represent a fresh benchmark run.

## What changed

Three runs flip from FAIL to PASS. All three failed the old grader on
the same message, "FAIL: report does not name api_client.py", while
correctly identifying `create_order` and the exact planted duplicate-
order risk by content. No run flips the other way, since the fix only
removes a check and cannot turn a prior pass into a fail.

| Phase | Cell | Run | Old | New |
| :--- | :--- | :--- | :--- | :--- |
| search | worker-sonnet-low | 2 | FAIL | PASS |
| confirm | worker-sonnet-low | 8 | FAIL | PASS |
| confirm | worker-sonnet-low | 9 | FAIL | PASS |

## Corrected results

### Search (steering only, not evidence)

| Cell | Passes | Runs | Rate | Threshold met |
| :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 3 | 3 | 100% | yes |

### Confirmation (reporting threshold)

| Cell | Passes | Runs | Rate | 95% Wilson interval | Clears 0.7 lower bound |
| :--- | :--- | :--- | :--- | :--- | :--- |
| worker-sonnet-low | 9 | 9 | 100% | [70.1%, 100.0%] | yes |

Frontier confirmed: `worker-sonnet-low`, at n=9 the only score that can
clear the bound at all (8/9 gives a lower bound of 56.5%). Not a wide
margin in the usual sense, but the strongest evidence this sample size
can produce, and every one of the nine confirmation runs independently
named the correct function and the correct risk.

## What this means for F09

T8 was built specifically at F09's scale (a ~200-line PR review) to test
whether T5's worker-sonnet-low result generalises past T5's narrower,
two-file bug-report shape. It does: F09's row (open, short, contained ->
worker-sonnet-low) is confirmed rather than needing escalation. See D30
in `docs/DECISIONS.md` for the grading-defect finding this depended on.
