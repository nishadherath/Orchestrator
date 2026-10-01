# X5 H02 first B0 attempt stopped before provider launch, 2026-09-30

The first H02 B0 root `f1192b5708e3d0da8b85d359` became uncertain during
pre-launch graph creation. Q4U had staged the 159-file actor, but there was no
start or stop receipt, no auth session and no active process for invocation
`e9d9708b893c79590a77ff3e22537b6c`. The [reconciliation](../../test/results/2026-09-30-controller-x5-h02-producer-run/reconciliation.json)
settled the USD 5 reservation at **USD 0** API-equivalent and left the root
blocked with no unresolved budget. Do not replay it. No worker result or H02
protected score exists for that root.

A provider-free fresh actor reproduced `EFBIG` in the isolated Graft build.
`build_actor_graph` inherited the 1,000,000-byte ordinary actor file-size cap;
the H02 graph's largest file is 6,299,575 bytes. The graph step now has its
own 16,000,000-byte cap, while ordinary actor output retains the 1,000,000-byte
cap. A disposable actor then built the graph and passed the credential-free
Q4U launcher. These observations support a new manifest and root. They do not
establish a paid worker outcome or Controller uplift.
