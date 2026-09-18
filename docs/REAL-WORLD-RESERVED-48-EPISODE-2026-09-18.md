# W08 48-episode reserved comparison approval package

Candidate: `99f6e7447b81054101c7ad57c4cd1bfd14b8d860aeec6f54f6f5a8d812e04fa4`.

The fixed package runs H01-H12 twice under the frozen B0 baseline and B1 adaptive candidate.
48 episode reservations cap model spend at **USD 192**. Separate calibration headroom is **USD 8**, so the requested combined ceiling is **USD 200**.

No paid call starts without an approval file matching this manifest and candidate.

## Measured cost context

The W07 policy-mean extrapolation is **USD 2.064230409**.
Applying the highest W07 episode to all 48 episodes gives **USD 8.301883200**. Reserved tasks differ
from development tasks, so both figures are planning evidence rather than
billing limits. The exact USD 200 ceiling remains authoritative.

## Outbound data and destination

Execution sends the synthetic H01-H12 fixture issues, public checks, source
files read by an agent and runtime observations to Anthropic through the local
Claude CLI. B0 and B1 remain frozen; no reserved outcome may change them.

## Scheduling

Each reserved task runs twice under both policies. Episodes run serially in
adjacent pairs and alternate which policy runs first. The full schedule is
fixed before any reserved outcome is inspected.

| # | Task | Policy | Repetition | Episode cap |
| -: | :--- | :--- | ---: | ---: |
| 57 | H01 | B0 | 1 | USD 4.00 |
| 58 | H01 | B1 | 1 | USD 4.00 |
| 59 | H02 | B1 | 1 | USD 4.00 |
| 60 | H02 | B0 | 1 | USD 4.00 |
| 61 | H03 | B0 | 1 | USD 4.00 |
| 62 | H03 | B1 | 1 | USD 4.00 |
| 63 | H04 | B1 | 1 | USD 4.00 |
| 64 | H04 | B0 | 1 | USD 4.00 |
| 65 | H05 | B0 | 1 | USD 4.00 |
| 66 | H05 | B1 | 1 | USD 4.00 |
| 67 | H06 | B1 | 1 | USD 4.00 |
| 68 | H06 | B0 | 1 | USD 4.00 |
| 69 | H07 | B0 | 1 | USD 4.00 |
| 70 | H07 | B1 | 1 | USD 4.00 |
| 71 | H08 | B1 | 1 | USD 4.00 |
| 72 | H08 | B0 | 1 | USD 4.00 |
| 73 | H09 | B0 | 1 | USD 4.00 |
| 74 | H09 | B1 | 1 | USD 4.00 |
| 75 | H10 | B1 | 1 | USD 4.00 |
| 76 | H10 | B0 | 1 | USD 4.00 |
| 77 | H11 | B0 | 1 | USD 4.00 |
| 78 | H11 | B1 | 1 | USD 4.00 |
| 79 | H12 | B1 | 1 | USD 4.00 |
| 80 | H12 | B0 | 1 | USD 4.00 |
| 81 | H01 | B0 | 2 | USD 4.00 |
| 82 | H01 | B1 | 2 | USD 4.00 |
| 83 | H02 | B1 | 2 | USD 4.00 |
| 84 | H02 | B0 | 2 | USD 4.00 |
| 85 | H03 | B0 | 2 | USD 4.00 |
| 86 | H03 | B1 | 2 | USD 4.00 |
| 87 | H04 | B1 | 2 | USD 4.00 |
| 88 | H04 | B0 | 2 | USD 4.00 |
| 89 | H05 | B0 | 2 | USD 4.00 |
| 90 | H05 | B1 | 2 | USD 4.00 |
| 91 | H06 | B1 | 2 | USD 4.00 |
| 92 | H06 | B0 | 2 | USD 4.00 |
| 93 | H07 | B0 | 2 | USD 4.00 |
| 94 | H07 | B1 | 2 | USD 4.00 |
| 95 | H08 | B1 | 2 | USD 4.00 |
| 96 | H08 | B0 | 2 | USD 4.00 |
| 97 | H09 | B0 | 2 | USD 4.00 |
| 98 | H09 | B1 | 2 | USD 4.00 |
| 99 | H10 | B1 | 2 | USD 4.00 |
| 100 | H10 | B0 | 2 | USD 4.00 |
| 101 | H11 | B0 | 2 | USD 4.00 |
| 102 | H11 | B1 | 2 | USD 4.00 |
| 103 | H12 | B1 | 2 | USD 4.00 |
| 104 | H12 | B0 | 2 | USD 4.00 |

## Stop conditions

- candidate, bundle, isolation or authorisation does not validate.
- an episode stops with unresolved provider accounting.
- a served task model does not match the exact required model.
- the event chain, external grade or protected-oracle check is invalid.
- the fixed USD 192 episode envelope or USD 200 combined ceiling would be exceeded.

## Required operator decision

Approve or reject this exact USD 200 package.
