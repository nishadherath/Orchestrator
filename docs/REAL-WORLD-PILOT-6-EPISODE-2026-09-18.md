# Six-episode paid pilot approval package

Candidate: `4fd79c1577ef97ccae9430d9b5f666edf72172d0973135baa3808642e6d08dcd`.

The fixed checkpoint runs D01 and D11 once under each policy B0, B1 and B2.
Six episode reservations cap model spend at **USD 24**. Separate calibration
headroom is **USD 2**, so the requested combined ceiling is **USD 26**.

No paid call starts without an approval file matching this manifest and candidate.

| # | Task | Policy | Episode cap |
| -: | :--- | :--- | ---: |
| 1 | D01 | B0 | USD 4.00 |
| 2 | D01 | B1 | USD 4.00 |
| 3 | D01 | B2 | USD 4.00 |
| 4 | D11 | B0 | USD 4.00 |
| 5 | D11 | B1 | USD 4.00 |
| 6 | D11 | B2 | USD 4.00 |

## Stop conditions

- candidate, bundle, isolation or authorisation does not validate.
- an episode stops with unresolved provider accounting.
- a served task model does not match the exact required model.
- the event chain, external grade or protected-oracle check is invalid.
- the fixed USD 24 episode envelope or USD 26 combined ceiling would be exceeded.

## Required operator decision

Choose the project licence, then approve or reject this exact USD 26 package.
