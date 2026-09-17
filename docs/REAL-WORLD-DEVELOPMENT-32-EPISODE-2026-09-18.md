# W07 32-episode development comparison approval package

Candidate: `6f89533045ac2a6abe29e989f5a8ba69666a8f50bab6e58b334ab467a6638f28`.

The fixed package runs D01-D12 once under B0 and B1, then the predeclared D03, D05, D07 and D11 repeats under both policies.
32 episode reservations cap model spend at **USD 128**. Separate calibration headroom is **USD 12**, so the requested combined ceiling is **USD 140**.

No paid call starts without an approval file matching this manifest and candidate.

## Measured cost context

The policy-mean pilot extrapolation is **USD 2.084651012**.
Applying the highest single pilot episode to all 32 episodes gives **USD 13.122006400**. The pilot is small, so both
figures are planning evidence rather than billing limits. The exact USD 140
ceiling remains authoritative because every episode retains its USD 4
failure-path allowance and USD 12 remains separate campaign headroom.

## Outbound data and destination

Execution sends the synthetic D01-D12 fixture issues, public checks, source
files read by an agent and runtime observations to Anthropic through the local
Claude CLI. Task calls request Claude Sonnet 5 or Claude Opus 5. B1 can invoke
the frozen read-only Controller roles when its observable trigger fires.

## Scheduling

Episodes run serially in adjacent task pairs. The first policy alternates by
pair to reduce time-order bias. D03, D05, D07 and D11 repeats are fixed before
execution and cannot be selected from favourable first-run outcomes.

| # | Task | Policy | Repetition | Episode cap |
| -: | :--- | :--- | ---: | ---: |
| 25 | D01 | B0 | 1 | USD 4.00 |
| 26 | D01 | B1 | 1 | USD 4.00 |
| 27 | D02 | B1 | 1 | USD 4.00 |
| 28 | D02 | B0 | 1 | USD 4.00 |
| 29 | D03 | B0 | 1 | USD 4.00 |
| 30 | D03 | B1 | 1 | USD 4.00 |
| 31 | D04 | B1 | 1 | USD 4.00 |
| 32 | D04 | B0 | 1 | USD 4.00 |
| 33 | D05 | B0 | 1 | USD 4.00 |
| 34 | D05 | B1 | 1 | USD 4.00 |
| 35 | D06 | B1 | 1 | USD 4.00 |
| 36 | D06 | B0 | 1 | USD 4.00 |
| 37 | D07 | B0 | 1 | USD 4.00 |
| 38 | D07 | B1 | 1 | USD 4.00 |
| 39 | D08 | B1 | 1 | USD 4.00 |
| 40 | D08 | B0 | 1 | USD 4.00 |
| 41 | D09 | B0 | 1 | USD 4.00 |
| 42 | D09 | B1 | 1 | USD 4.00 |
| 43 | D10 | B1 | 1 | USD 4.00 |
| 44 | D10 | B0 | 1 | USD 4.00 |
| 45 | D11 | B0 | 1 | USD 4.00 |
| 46 | D11 | B1 | 1 | USD 4.00 |
| 47 | D12 | B1 | 1 | USD 4.00 |
| 48 | D12 | B0 | 1 | USD 4.00 |
| 49 | D03 | B0 | 2 | USD 4.00 |
| 50 | D03 | B1 | 2 | USD 4.00 |
| 51 | D05 | B1 | 2 | USD 4.00 |
| 52 | D05 | B0 | 2 | USD 4.00 |
| 53 | D07 | B0 | 2 | USD 4.00 |
| 54 | D07 | B1 | 2 | USD 4.00 |
| 55 | D11 | B1 | 2 | USD 4.00 |
| 56 | D11 | B0 | 2 | USD 4.00 |

## Stop conditions

- candidate, bundle, isolation or authorisation does not validate.
- an episode stops with unresolved provider accounting.
- a served task model does not match the exact required model.
- the event chain, external grade or protected-oracle check is invalid.
- the fixed USD 128 episode envelope or USD 140 combined ceiling would be exceeded.

## Required operator decision

Approve or reject this exact USD 140 package.
