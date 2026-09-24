# N5 worker-cell screen contract

Status, 2026-09-24: **provider-free inventory and driver validation only**.
The live screen driver has not been enabled and no provider call has run. The
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
the registry ID, the WSL attestation digest, the screen planner and driver sources, the
ordered calls, the credential method and the spend-notice digest. Its default
credential method is `unconfigured` and its notice digest is absent, so it
cannot pass the approval validator. `validate_authorisation` re-derives the
manifest and requires an exact USD 48.75 approval for that digest, credential
method and notice. On a live host it also revalidates the WSL attestation.
This validation is a prerequisite for a future live launch, not an authority to
run calls by itself.

The [saved provisional manifest](../test/results/2026-09-24-worker-n5-screen-plan.json)
has digest `a7f25d1cd839d4a4c84acde7890f599b8cffa0bc55a4b72d6593b2e45412e089`.
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

`tools/worker_n5_live_screen.py` implements the provider-free driver contract.
It materialises only the four public actor files, persists a budget reservation
and intent before each call, commits the receipt before settling cost, and
resumes grading a durable terminal receipt without repeating the call. An
absent or incomplete receipt retains its budget hold and blocks the campaign.
An identity mismatch skips the rest of that cell's tranche; a failed microtask
with matching identity still gets an objective grade. Protected-file changes
and row-cap overruns block the campaign. The driver uses the isolated WSL
grader only after a terminal, stopped-writer receipt and checks the grade's
oracle and actor digests. Its default production constructor rejects dispatch
until credential delivery is qualified, even with an approval file. Eight
driver tests inject a fake adapter and send no
provider traffic.

The screen needs a separate one-call driver because `TaskExecutor` owns B0's
fixed three-cell ladder. N5 development episodes still use `TaskExecutor` and
remain to be implemented as a live campaign.

Provider-free inspection:

```text
python tools/worker_n5_screen.py
python -m unittest test.harness.worker_n5_screen_tests
python test/harness/worker_n5_live_screen_tests.py
```

The [N5 host record](stage-results/worker-n5-host.md) distinguishes this
preparation from live qualification.
