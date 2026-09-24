# N5 worker-cell screen contract

Status, 2026-09-24: **provider-free inventory and approval validation only**.
The live screen launcher is not present and no provider call has run. The
shipping B0 policy remains unchanged. This contract implements the screen
portion of the [worker plan](WORKER-ROUTING-ACTION-PLAN-2026-09-19.md) and
uses the [attested WSL host](WORKER-N4-WSL-HOST.md).

`tools/worker_n5_screen.py` derives the fifteen cells from the validated model
registry in model and effort order. Each cell has one I00 identity call capped
at USD 0.25, followed by S01, S02 and S03 capped at USD 1 each. The schedule
contains exactly 60 calls and USD 48.75 in **local admission allocations**.
Those caps are not a bill prediction. The identity task asks for no edit; the
three separate microtasks cover configuration parsing, atomic inventory
changes and a correct implementation that should be left untouched. Their
oracles are outside the public actor directories. None of the twelve D-series
development tasks or twelve R-series reserved tasks is part of this screen.

The manifest binds every screen file, the complete N4 frozen corpus digest,
the registry ID, the WSL attestation digest, the screen planner source, the
ordered calls, the credential method and the spend-notice digest. Its default
credential method is `unconfigured` and its notice digest is absent, so it
cannot pass the approval validator. `validate_authorisation` re-derives the
manifest and requires an exact USD 48.75 approval for that digest, credential
method and notice. On a live host it also revalidates the WSL attestation.
This validation is a prerequisite for a future launcher, not an authority to
run calls by itself.

The [saved provisional manifest](../test/results/2026-09-24-worker-n5-screen-plan.json)
has digest `3ed3d3ab7ec732bd33fe5d4d107c8ee0926aa01832bb49226ffdd5f15c5d2b6f`.
It records `unconfigured` credentials and no spend notice, so it is an
inspection artefact and cannot authorise a paid call. Any fixture, planner,
host or credential change requires a newly derived manifest.

Before the first paid call, choose and safely configure either a project-scoped
API key or subscription login, verify current pricing, create a dated direct
API cost and elapsed-time projection, and freeze that spend notice into a new
manifest. The live runner must persist intent before each call, use the
attested WSL adapter, retain unknown charges without replay, stop a cell's
tranche on unsupported or mismatched identity, and use the isolated WSL grader
only after the worker has stopped. It must record requested effort separately
from any independently observed served effort, all usage and cache counters,
wall time, objective quality and incomplete outcomes. The screen output may
guide N5 development selection; it cannot change B0 or expose N6 reserved
grades.

Provider-free inspection:

```text
python tools/worker_n5_screen.py
python -m unittest test.harness.worker_n5_screen_tests
```

The [N5 host record](stage-results/worker-n5-host.md) distinguishes this
preparation from live qualification.
