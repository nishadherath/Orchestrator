# Routing score summary, steering, two-stage, 2 axes, 3 runs, 2026-09-11 16:36 at e776fe3

Orchestrator model: sonnet. Bundle: 2026-09-11-d65b476-dirty-rubric-only. Project: `C:\Users\Bob\Desktop\Code\Claude\orchestrator-scratch-rubric-only`. Fixtures reviewed by a human: yes.

Grade: steering (fewer than 9 runs; steering only, not a basis for a table or fixture change, D37).

All-fields agreement (primary) 31/51 (60.8%, 95% Wilson [47.1%, 73.0%]). Mean cost per run: USD 0.2523; total across 3 costed of 3 runs: USD 0.7570.

Cell agreement (derived, reported for context) 26/51 (51.0%, 95% Wilson [37.7%, 64.1%]).

Two-axis configuration: cell agreement above is NOT valid evidence either way (docs/CLASSIFIER-DESIGN.md's pre-registration fixes this in advance). Dropping horizon changes what the correct cell is for four fixtures by construction (F03, F05, F07, F10), so a low cell-agreement figure here reflects the axis change, not classifier error.

0 of 17 fixtures clear the 70% Wilson lower bound on all-fields agreement, but this is steering grade: not yet reporting-grade confirmation.

| Fixture | Fields agree | Runs | Rate | 95% Wilson interval | Cell agree rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F01 | 3 | 3 | 100% | [44%, 100%] | 3/3 |
| F02 | 3 | 3 | 100% | [44%, 100%] | 3/3 |
| F03 | 3 | 3 | 100% | [44%, 100%] | 0/3 |
| F04 | 3 | 3 | 100% | [44%, 100%] | 3/3 |
| F05 | 2 | 3 | 67% | [21%, 94%] | 0/3 |
| F06 | 3 | 3 | 100% | [44%, 100%] | 3/3 |
| F07 | 1 | 3 | 33% | [6%, 79%] | 0/3 |
| F08 | 3 | 3 | 100% | [44%, 100%] | 3/3 |
| F09 | 0 | 3 | 0% | [0%, 56%] | 0/3 |
| F10 | 3 | 3 | 100% | [44%, 100%] | 0/3 |
| F11 | 0 | 3 | 0% | [0%, 56%] | 3/3 |
| F12 | 0 | 3 | 0% | [0%, 56%] | 0/3 |
| F13 | 0 | 3 | 0% | [0%, 56%] | 0/3 |
| F14 | 0 | 3 | 0% | [0%, 56%] | 3/3 |
| F15 | 2 | 3 | 67% | [21%, 94%] | 2/3 |
| F17 | 3 | 3 | 100% | [44%, 100%] | 3/3 |
| F18 | 2 | 3 | 67% | [21%, 94%] | 0/3 |

A wide interval on a fixture run only a few times is sample noise, not necessarily a wrong rule; widen --runs before drawing a conclusion. All-fields agreement, not cell agreement, is what this summary's grade is computed from, per docs/CLASSIFIER-DESIGN.md.
