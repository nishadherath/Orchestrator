# X5 v3 prospective screen stopped at its second task

Date: 2026-09-28 Australia/Sydney. Frozen manifest:
`bf5c768724b2207e6701190a69bb6264e3e0a2b721de59fb405ca01bf6192d72`.
The [v3 predeclaration](controller-x5-screen-v3-predeclare-2026-09-28.md)
required four of four proposed suitable tasks to auto-select Controller,
one ordinary worker decision and one clarification. The first miss stopped
the sequential runner. No worker or Controller pilot episode was launched;
C04-D1, C06-D1, N01-D1 and C08-D2 remain unassessed in v3.

| Operation | Observed result | API-equivalent USD |
| --- | --- | ---: |
| Q4R Sonnet High host canary, C03-D1 | Served `claude-sonnet-5`, terminal Q1 collection, completed, public check passed, no unresolved hold | 0.272499400 |
| Public assessment, C03-D1 | Automatic Controller, `consequential_unresolved_material_alternatives`, Sonnet High | 0.043493601 |
| Public assessment, C03-D2 | Worker, `clear_worker_frame` and `implementation_failure_worker_repair`, Sonnet High | 0.050661400 |
| **V3 settled subtotal** | Three provider calls; two assessments | **0.366654401** |

The v1 settled assessment adds USD 0.0330442 across X5 attempts, making
reported settled X5 use USD 0.399698601. The v2 canary has an unreported
cost and an independent USD 1.00 uncertain local hold. It is **not** included
as zero or folded into the settled subtotal. V3's canary and both assessment
ledgers are settled; the four remaining assessment caps were never used.
The later [v2 prelaunch audit]
(controller-x5-v2-prelaunch-proof-2026-09-28.md) supports zero provider
invocations for that rejected canary, but does not supply a provider receipt
or release its historical local hold.

C03-D2's issue already states that the local trace identifies a lease race,
names the stale-owner acknowledgement, specifies the fencing-token repair,
and asks for a patch. It supplies no `trace.json` and no unresolved competing
diagnosis. The assessor recorded `premise_uncertainty=none`,
`alternatives=one-established`, `constraint_coupling=local`, and an
implementation failure. **Inference:** routing this task to a worker is
consistent with the current policy. The failed gate exposes a weak proposed
"Controller-suitable" task label; it does not show that the router missed a
rigorous task. C03-D1, with a reproduced contradictory retry trace, received
the intended automatic Controller decision. These two assessments alone do
not establish routing accuracy, quality uplift, or an economic case for
default promotion.

The next prospective screen should not relax this frozen gate or reinterpret
C03-D2 after seeing its decision. For a new development attempt, independently
audit all candidate public tasks **before** model assessment: require a
concrete observable contradiction or multiple live material causes, a reason
why the choice changes the repair, available discriminating evidence, and
consequential failure if the premise is wrong. Keep a visible exclusion table
for clear worker tasks such as C03-D2. Build any new public overlay from
reproducible baseline observations, leave X3 code/oracles unchanged, freeze
the overlay and task list prospectively, and keep ordinary and clarification
controls. One screen of six assessments has a USD 3.00 local allocation and
roughly USD 0.15-0.60 expected API-equivalent usage based on v1/v3 receipts;
the already-settled v3 Sonnet High identity can be reused only if host,
launcher, schema, auth method and source remain unchanged. Estimated design
and offline audit time is 2-4 hours, screen time 1-2 hours. The later
18-episode pilot retains its separate USD 144 local ceiling and prior
USD 5-30 API-equivalent, 2-8 hour projection. A new screen is development
tuning only; X6 reserved evidence and independent X7 review remain mandatory.

Raw v3 canary and assessment summaries are under `test/results/`; source
snapshots with `-v3-source.py` suffixes preserve the exact stopped driver.
The B0 shipping default remains unchanged.
