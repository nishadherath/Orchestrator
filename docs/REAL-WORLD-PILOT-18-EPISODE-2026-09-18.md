# Remaining eighteen-episode paid pilot approval package

Candidate: `ce6cf4467b0ec462202f5cf419c5845aac471d30a9956fe3382b620b60660bec`.

The fixed package runs D03, D05 and D07-D10 once under each policy B0, B1 and B2.
18 episode reservations cap model spend at **USD 72**. Separate calibration headroom is **USD 2**, so the requested combined ceiling is **USD 74**.

No paid call starts without an approval file matching this manifest and candidate.

## Measured cost context

The completed six-episode checkpoint averaged USD 0.0232061 per first-rung
episode. A floor-only extrapolation for these 18 episodes is USD 0.417710.
The planning range is **USD 1-22** because these harder tasks can invoke Opus
fallbacks or the approximately USD 2.99 historical quick Controller path.
The USD 74 ceiling remains authoritative; the range is not a billing limit.

## Outbound data and destination

Execution sends the synthetic D03, D05 and D07-D10 fixture issue prompts,
public checks, source files read by an agent and runtime observations to
Anthropic through the local Claude CLI. Task calls request Claude Sonnet 5 or
Claude Opus 5. B2 can also invoke the frozen read-only Controller roles.

| # | Task | Policy | Episode cap |
| -: | :--- | :--- | ---: |
| 7 | D03 | B0 | USD 4.00 |
| 8 | D03 | B1 | USD 4.00 |
| 9 | D03 | B2 | USD 4.00 |
| 10 | D05 | B0 | USD 4.00 |
| 11 | D05 | B1 | USD 4.00 |
| 12 | D05 | B2 | USD 4.00 |
| 13 | D07 | B0 | USD 4.00 |
| 14 | D07 | B1 | USD 4.00 |
| 15 | D07 | B2 | USD 4.00 |
| 16 | D08 | B0 | USD 4.00 |
| 17 | D08 | B1 | USD 4.00 |
| 18 | D08 | B2 | USD 4.00 |
| 19 | D09 | B0 | USD 4.00 |
| 20 | D09 | B1 | USD 4.00 |
| 21 | D09 | B2 | USD 4.00 |
| 22 | D10 | B0 | USD 4.00 |
| 23 | D10 | B1 | USD 4.00 |
| 24 | D10 | B2 | USD 4.00 |

## Stop conditions

- candidate, bundle, isolation or authorisation does not validate.
- an episode stops with unresolved provider accounting.
- a served task model does not match the exact required model.
- the event chain, external grade or protected-oracle check is invalid.
- the fixed USD 72 episode envelope or USD 74 combined ceiling would be exceeded.

## Required operator decision

Approve or reject this exact USD 74 package.
