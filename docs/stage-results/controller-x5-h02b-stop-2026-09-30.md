# X5 H02b stopped at the Q4U allowance check, 2026-09-30

H02b root `d7f201d528a9f05d15f59aa5` staged the actor and built its Graft
graph, then the Q4U subscription launcher returned exit 64 before its start
receipt or auth session. The worker stream was empty, with no model or cost
telemetry. The launcher limits a single call to USD 4 API-equivalent, while
the H02b manifest offered USD 5. The [reconciliation](../../test/results/2026-09-30-controller-x5-h02b-producer-run/reconciliation.json)
confirmed no active writer and settled the reservation at **USD 0**, leaving
the root blocked. Do not replay it.

H02c uses a distinct root and a USD 4 per-call limit under a new frozen
manifest. Its translated CLI argv must pass a provider-free check against
the launcher before any paid dispatch. H02b yielded no worker result,
protected score or Controller uplift.
