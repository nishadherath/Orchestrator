# Controller run, 2026-09-28 10:00, 20260928T093635-40ec0e99

Outcome: gap. Calls: 17. Cost: USD 3.2275. Run directory: `/mnt/c/Users/Bob/Desktop/Code/Claude/Orchestrator/test/results/2026-09-28-controller-x4-role-probe-4/runs/20260928T093635-40ec0e99`.

```json
{
  "type": "GapReport",
  "best_candidate_id": null,
  "unmet_criteria": [
    "Each of the three competing explanations has at least one check that names an observable artefact and states the outcome pattern that confirms it while disconfirming the other two.",
    "Exactly one containment step is proposed, with its reversal stated and its effect on the pending diagnosis noted, including any evidence it would destroy.",
    "The implementation direction is stated conditionally, naming the specific check result that would authorise it.",
    "No check is described as having been run; every result is prospective.",
    "Only the supplied statement is used; no system detail, tool, log name or metric is asserted as existing without being flagged as an assumption.",
    "Load-bearing unverified premises are named, including the assumption that the cause lies among the three listed explanations."
  ],
  "unverified_load_bearing": [
    "prem-002",
    "prem-003",
    "prem-005",
    "prem-006",
    "prem-008"
  ],
  "next_cheapest_test": "Verify or replace every ineligible candidate premise.",
  "termination": "no_improvement",
  "ledger_version": 2,
  "references": [
    "frame-002"
  ],
  "id": "gap-001"
}
```
