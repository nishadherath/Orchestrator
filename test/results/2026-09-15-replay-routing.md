# Routing replay, 2026-09-15 10:43 at 81b0d99

Every recorded routing verdict (test/results/*routing*.md) replayed through tools/route.py's plan() with an empty ledger (docs/ROUTING-2-DESIGN.md section 4, docs/PLAN-2.md Stage 2.3, D65). No live claude -p call.

**Gate**: pooled agreement on `2026-09-11-routing-opus-d65b476-two-stage-3axis-run*-of-9.md` (D40's measured two-stage opus batch, 153 verdicts) at or above 92.2%, **excluding rows where the policy dial fired** (D65: that is a deliberate divergence from the floor-only table `expected_cell` was fixed against, D45, not a classifier error), and zero `first: controller` on any contained fixture, pooled across every batch below.

Gate result: PASS. Gating batch agreement 125/125 (100.0%) after excluding 27 policy-fired row(s). Controller-on-contained violations: 0.

| Batch | Scored | Agree (excl. policy) | Rate | 95% Wilson | Unparsed/skipped | Policy fires | Other controller fires |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-09-05-routing-opus | 14 | 14 | 100.0% | [78.5%, 100.0%] | 0 | 3 | 0 |
| 2026-09-05-routing-sonnet | 14 | 14 | 100.0% | [78.5%, 100.0%] | 0 | 3 | 0 |
| 2026-09-06-routing-opus | 42 | 42 | 100.0% | [91.6%, 100.0%] | 0 | 9 | 0 |
| 2026-09-06-routing-sonnet | 42 | 42 | 100.0% | [91.6%, 100.0%] | 0 | 9 | 0 |
| 2026-09-06-routing-sonnet-04d2acc | 43 | 43 | 100.0% | [91.8%, 100.0%] | 1 | 7 | 0 |
| 2026-09-06-routing-sonnet-04d2acc-assessonly | 0 | 0 | n/a | [0.0%, 0.0%] | 51 | 0 | 0 |
| 2026-09-07-routing-default-681f8d8 | 13 | 12 | 92.3% | [66.7%, 98.6%] | 1 | 5 | 0 |
| 2026-09-07-routing-opus-2f1651a | 15 | 15 | 100.0% | [79.6%, 100.0%] | 1 | 3 | 0 |
| 2026-09-07-routing-opus-2f1651a-run2 | 15 | 15 | 100.0% | [79.6%, 100.0%] | 1 | 3 | 0 |
| 2026-09-07-routing-opus-681f8d8-run1 | 14 | 14 | 100.0% | [78.5%, 100.0%] | 1 | 4 | 0 |
| 2026-09-07-routing-opus-681f8d8-run2 | 14 | 14 | 100.0% | [78.5%, 100.0%] | 1 | 4 | 0 |
| 2026-09-07-routing-opus-70b2eed | 15 | 15 | 100.0% | [79.6%, 100.0%] | 1 | 3 | 0 |
| 2026-09-07-routing-opus-ccd6350 | 14 | 14 | 100.0% | [78.5%, 100.0%] | 0 | 4 | 0 |
| 2026-09-08-routing-opus-2f1651a | 15 | 15 | 100.0% | [79.6%, 100.0%] | 1 | 3 | 0 |
| 2026-09-08-routing-opus-af94deb | 48 | 48 | 100.0% | [92.6%, 100.0%] | 0 | 6 | 0 |
| 2026-09-08-routing-opus-af94deb-5a7585d | 45 | 45 | 100.0% | [92.1%, 100.0%] | 0 | 9 | 0 |
| 2026-09-08-routing-opus-af94deb-b86c53d-F05only | 3 | 3 | 100.0% | [43.8%, 100.0%] | 0 | 0 | 0 |
| 2026-09-11-routing-opus-af94deb | 132 | 132 | 100.0% | [97.2%, 100.0%] | 0 | 27 | 0 |
| 2026-09-11-routing-opus-af94deb-only-F01 | 4 | 4 | 100.0% | [51.0%, 100.0%] | 0 | 0 | 0 |
| 2026-09-11-routing-opus-af94deb-only-F01-2 | 1 | 1 | 100.0% | [20.7%, 100.0%] | 0 | 0 | 0 |
| 2026-09-11-routing-opus-d65b476-two-stage-3axis | 165 | 165 | 100.0% | [97.7%, 100.0%] | 0 | 38 | 0 |
| 2026-09-11-routing-sonnet-d65b476-two-stage-2axis | 0 | 0 | n/a | [0.0%, 0.0%] | 51 | 0 | 0 |
| 2026-09-11-routing-sonnet-d65b476-two-stage-3axis | 158 | 158 | 100.0% | [97.6%, 100.0%] | 1 | 45 | 0 |
| 2026-09-14-routing-opus-282981f-only-F14+F16 | 18 | 18 | 100.0% | [82.4%, 100.0%] | 0 | 0 | 0 |
| 2026-09-14-routing-opus-b6605f4 | 135 | 135 | 100.0% | [97.2%, 100.0%] | 0 | 27 | 0 |
| 2026-09-15-routing-opus-9b5f64b | 135 | 135 | 100.0% | [97.2%, 100.0%] | 0 | 27 | 0 |
