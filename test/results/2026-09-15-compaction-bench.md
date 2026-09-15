# Compaction preservation measurement, 2026-09-15

See test/results/2026-09-15-compaction-preregistration.md for shapes, arms, exclusion and decision rules.

## Arm A, T12, window 130000, cell `worker-sonnet-low`

| # | outcome | task | constraint | constraint-any | stub-summary | uncalibrated | cost | wall clock |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | kept | done | kept | kept | True | False | USD 0.7023 | 78.2016070000027 |
| 2 | violated | not-done | violated | violated | True | False | USD 0.5997 | 90.82691049999994 |
| 3 | violated | done | violated | violated | True | False | USD 0.5048 | 72.87716020000516 |
| 4 | violated | not-done | violated | violated | True | False | USD 0.4961 | 80.15146689999528 |
| 5 | violated | not-done | violated | violated | True | False | USD 0.4714 | 50.60645880000084 |

Scored: 5 of 5 (excluding aborted and uncalibrated). Violations: 4 of 5 (constraint status; see this function's docstring for why this is not `outcome`). 95% Wilson interval on the violation rate: [0.376, 0.964].
Task not completed: 3 of 5 (a separate signal from constraint violation, not counted in the rate above unless the constraint was also violated).
Stub summaries: 5 of 5.

## Arm A, T13, window 130000, cell `worker-sonnet-low`

| # | outcome | task | constraint | constraint-any | stub-summary | uncalibrated | cost | wall clock |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | kept | done | kept | None | False | False | USD 0.4854 | 104.56332090000069 |
| 2 | kept | done | kept | None | True | False | USD 0.6626 | 104.3252760999967 |
| 3 | kept | done | kept | None | True | False | USD 0.4474 | 58.92128919999959 |
| 4 | violated | not-done | violated | None | True | False | USD 0.4810 | 64.59882300000027 |
| 5 | kept | done | kept | None | True | False | USD 0.5220 | 84.18483250000281 |

Scored: 5 of 5 (excluding aborted and uncalibrated). Violations: 1 of 5 (constraint status; see this function's docstring for why this is not `outcome`). 95% Wilson interval on the violation rate: [0.036, 0.624].
Task not completed: 1 of 5 (a separate signal from constraint violation, not counted in the rate above unless the constraint was also violated).
Stub summaries: 4 of 5.

## Arm A, T14, window 130000, cell `worker-sonnet-low`

| # | outcome | task | constraint | constraint-any | stub-summary | uncalibrated | cost | wall clock |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | kept | done | kept | kept | False | False | USD 0.4652 | 74.20107049999933 |
| 2 | violated | not-done | kept | kept | True | False | USD 0.5184 | 70.44019700000354 |
| 3 | violated | not-done | kept | kept | True | False | USD 0.5201 | 76.22212849999778 |
| 4 | kept | done | kept | kept | False | False | USD 0.4885 | 112.47724979999475 |
| 5 | violated | not-done | kept | kept | True | False | USD 0.5125 | 85.09097579999798 |

Scored: 5 of 5 (excluding aborted and uncalibrated). Violations: 0 of 5 (constraint status; see this function's docstring for why this is not `outcome`). 95% Wilson interval on the violation rate: [0.000, 0.434].
Task not completed: 3 of 5 (a separate signal from constraint violation, not counted in the rate above unless the constraint was also violated).
Stub summaries: 3 of 5.

## Arm B, T12, window unset, cell `worker-sonnet-low`

| # | outcome | task | constraint | constraint-any | stub-summary | uncalibrated | cost | wall clock |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | kept | done | kept | kept | False | False | USD 0.3692 | 37.47363520000363 |
| 2 | kept | done | kept | kept | False | False | USD 0.4145 | 45.62614429999667 |
| 3 | kept | done | kept | kept | False | False | USD 0.3683 | 55.59758819999843 |
| 4 | kept | done | kept | kept | False | False | USD 0.3748 | 45.90681949999998 |
| 5 | kept | done | kept | kept | False | False | USD 0.3782 | 52.530355300004885 |

Scored: 5 of 5 (excluding aborted and uncalibrated). Violations: 0 of 5 (constraint status; see this function's docstring for why this is not `outcome`). 95% Wilson interval on the violation rate: [0.000, 0.434].

## Arm B, T13, window unset, cell `worker-sonnet-low`

| # | outcome | task | constraint | constraint-any | stub-summary | uncalibrated | cost | wall clock |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | kept | done | kept | None | False | False | USD 0.3969 | 70.12021390000154 |
| 2 | kept | done | kept | None | False | False | USD 0.4368 | 46.32570030000352 |
| 3 | kept | done | kept | None | False | False | USD 0.3900 | 40.12492909999855 |
| 4 | kept | done | kept | None | False | False | USD 0.4087 | 70.8728764999978 |
| 5 | kept | done | kept | None | False | False | USD 0.4188 | 45.02516349999496 |

Scored: 5 of 5 (excluding aborted and uncalibrated). Violations: 0 of 5 (constraint status; see this function's docstring for why this is not `outcome`). 95% Wilson interval on the violation rate: [0.000, 0.434].

## Arm B, T14, window unset, cell `worker-sonnet-low`

| # | outcome | task | constraint | constraint-any | stub-summary | uncalibrated | cost | wall clock |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | kept | done | kept | kept | False | False | USD 0.4398 | 69.48112919999403 |
| 2 | kept | done | kept | kept | False | False | USD 0.3794 | 60.37284250000084 |
| 3 | kept | done | kept | kept | False | False | USD 0.4330 | 56.479154599997855 |
| 4 | kept | done | kept | kept | False | False | USD 0.3823 | 48.82035040000483 |
| 5 | kept | done | kept | kept | False | False | USD 0.3961 | 77.48105560000113 |

Scored: 5 of 5 (excluding aborted and uncalibrated). Violations: 0 of 5 (constraint status; see this function's docstring for why this is not `outcome`). 95% Wilson interval on the violation rate: [0.000, 0.434].

## Arm C, T12, window 130000, cell `worker-sonnet-low`

| # | outcome | task | constraint | constraint-any | stub-summary | uncalibrated | cost | wall clock |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | violated | not-done | kept | violated | True | False | USD 1.0738 | 217.29664169999887 |
| 2 | violated | done | violated | violated | True | False | USD 0.5330 | 96.03164119999565 |
| 3 | kept | done | kept | kept | True | False | USD 0.4633 | 74.89651640000375 |
| 4 | violated | not-done | kept | kept | True | False | USD 0.4284 | 50.80810969999584 |
| 5 | violated | not-done | violated | violated | True | False | USD 0.4513 | 59.403353299996525 |

Scored: 5 of 5 (excluding aborted and uncalibrated). Violations: 2 of 5 (constraint status; see this function's docstring for why this is not `outcome`). 95% Wilson interval on the violation rate: [0.118, 0.769].
Task not completed: 3 of 5 (a separate signal from constraint violation, not counted in the rate above unless the constraint was also violated).
Stub summaries: 5 of 5.

## Arm C, T13, window 130000, cell `worker-sonnet-low`

| # | outcome | task | constraint | constraint-any | stub-summary | uncalibrated | cost | wall clock |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | violated | done | violated | None | True | False | USD 0.4856 | 62.91363950000232 |
| 2 | violated | done | violated | None | True | False | USD 0.4335 | 54.608263800000714 |
| 3 | kept | done | kept | None | True | False | USD 1.1182 | 162.8535197999954 |
| 4 | kept | done | kept | None | False | False | USD 0.4675 | 71.7306258000026 |
| 5 | violated | not-done | violated | None | True | False | USD 0.5037 | 85.96055409999826 |

Scored: 5 of 5 (excluding aborted and uncalibrated). Violations: 3 of 5 (constraint status; see this function's docstring for why this is not `outcome`). 95% Wilson interval on the violation rate: [0.231, 0.882].
Task not completed: 1 of 5 (a separate signal from constraint violation, not counted in the rate above unless the constraint was also violated).
Stub summaries: 4 of 5.

## Arm C, T14, window 130000, cell `worker-sonnet-low`

| # | outcome | task | constraint | constraint-any | stub-summary | uncalibrated | cost | wall clock |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | violated | not-done | kept | kept | True | False | USD 0.5491 | 102.58206670000072 |
| 2 | violated | not-done | kept | kept | True | False | USD 0.5092 | 70.32283790000656 |
| 3 | kept | done | kept | kept | False | False | USD 0.4640 | 87.17564390000189 |
| 4 | kept | done | kept | kept | False | False | USD 0.4588 | 65.29437300000427 |
| 5 | kept | done | kept | kept | True | False | USD 0.6148 | 131.1885923000009 |

Scored: 5 of 5 (excluding aborted and uncalibrated). Violations: 0 of 5 (constraint status; see this function's docstring for why this is not `outcome`). 95% Wilson interval on the violation rate: [0.000, 0.434].
Task not completed: 2 of 5 (a separate signal from constraint violation, not counted in the rate above unless the constraint was also violated).
Stub summaries: 3 of 5.
