# X5 v2 canary prelaunch proof and accounting status

Date: 2026-09-28 Australia/Sydney. The read-only
[audit result](../../test/results/2026-09-28-controller-x5-v2-prelaunch-audit.json)
is reproducible with its adjacent `-audit.py` script on the WSL root host.
It binds the frozen v2 manifest, archived adapter and canary source, the
installed Q3 launcher and the signed Q1 actor record. It reads no credential
bytes and does not modify the ledger.

The installed Q3 launcher SHA-256 matches the frozen source
(`9da08e0d450c3d102b56ef69002cc9d8b5d47807b5d895560bcf212b6e190941`)
and its modification time precedes the signed actor record. The v2 request
selected Sonnet High, while that launcher accepts only Sonnet Low and Opus
High. Its rejecting guard precedes both subscription credential issuance
and `worker_wsl_q1.py start`. The signed actor stage record exists, but no
Q1 `start`, Q1 `stop` or actor auth session exists. **Inference from the
frozen control flow and root-owned records:** this canary made zero Claude
provider invocations. There is no provider-reported cost receipt, so no
provider price is asserted for the rejected attempt.

The task-local ledger still marks the invocation `uncertain` and holds
**USD 1.00**. It was not changed because the current generic budget API
documents final settlement only with terminal provider evidence. A future
prelaunch-zero release path should validate equivalent signed boundary
evidence explicitly, retain the prior uncertain resolution and record the
zero-invocation rationale before releasing a hold. Until that path exists,
the historical hold remains visible; it is not a paid-call estimate or a
reason to replay this single-use actor.
