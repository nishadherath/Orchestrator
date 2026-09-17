# Real-world corpus qualification

**Result:** PASS

The complete 12-task development split and 12-task reserved split were
validated offline. This run made zero model calls.

- Task fixtures: 24
- Original/solution/adversarial states: 144
- Protected-boundary attack checks: 72
- Isolation evidence: PASS

## Tasks

| Split | IDs | Result |
| :--- | :--- | :--- |
| Development | D01, D02, D03, D04, D05, D06, D07, D08, D09, D10, D11, D12 | PASS |
| Reserved | H01, H02, H03, H04, H05, H06, H07, H08, H09, H10, H11, H12 | PASS |

## Reserved-authoring limitation

The authoring session had access to pilot outcomes; fixtures were constrained to the pre-pilot blueprints and were not adapted to policy-specific failures.

This is a reserved evaluation corpus, not proof of uncontaminated model testing.
