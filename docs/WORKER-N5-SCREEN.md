# N5 worker-cell screen contract

Status, 2026-09-25: **subscription screen complete; development comparison pending**.
The WSL host and isolated subscription login passed provider-free attestations.
After a fresh login, one bounded Sonnet-low sentinel observed the required
Read denial and a served model at USD 0.053081 reported API-equivalent cost.
The [completed screen record](stage-results/worker-n5-screen-2026-09-25.md)
reconciles all 60 calls and USD 7.410898 of provider-reported API-equivalent
usage. The shipping B0 policy remains unchanged. This contract implements the screen
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
The [dated pricing snapshot](WORKER-N5-PRICING-SNAPSHOT-2026-09-24.md) gives
API-equivalent token scenarios and the current Opus version caveat; it is not
the manifest-bound spend notice.

The manifest binds every screen file, the complete N4 frozen corpus digest,
the registry ID, the WSL and subscription attestation digests, the passing
single-call Read sentinel digest, the screen planner and driver sources, the
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

The [subscription manifest](../test/results/2026-09-25-worker-n5-screen-manifest.json)
binds the passing sentinel and the [dated spend notice](stage-results/worker-n5-screen-spend-notice-2026-09-25.md).
Its digest is `1dbb33f603f756998e30c48346b89b3359de0330b78c70c4a49bc33b9e065e94`.
The operator's [exact approval](../test/results/2026-09-25-worker-n5-screen-approval.json)
validated against the live host. The [campaign checkpoint](../test/results/2026-09-25-worker-n5-screen-run/campaign.json)
records the completed screen and needs no resume.

For this host, the operator requires the Claude Code subscription login, not
an API key. The [WSL login and private handoff](CLAUDE-CODE-WSL-AUTH.md)
describe delivery to the isolated worker. Its provider-free status attestation
does not establish token freshness or paid model behaviour on its own. The
freshness check, access-control sentinel and current pricing check passed;
the dated cost/time notice is frozen into the manifest. The live runner must persist intent before each
call, use the attested WSL adapter, retain unknown charges without replay, stop a cell's
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
oracle and actor digests. Its production constructor selects the private WSL
subscription adapter only after the current host, subscription and passing
sentinel evidence and exact approval validate. An injected fake adapter is
accepted only for offline tests. Eight driver tests send no provider traffic.

The screen needs a separate one-call driver because `TaskExecutor` owns B0's
fixed three-cell ladder. N5 development episodes use `TaskExecutor` through the
[explicit experimental path](WORKER-N5-DEVELOPMENT.md).

For those development episodes, `TaskExecutor` now accepts an injected
acceptance command runner. The N5 host implementation only accepts the frozen
`python3 public_check.py` command and executes it in a fresh WSL actor copy,
under UID 65534 with no credential or hidden evaluator mount. Its sealed proof
binds the host attestation, four public file hashes and the acceptance
snapshots. Local command evidence cannot be reused as isolated evidence.
The public check is a development feedback and acceptance signal; the
independent hidden grader remains the objective quality measure. The live
development driver now instantiates this runner and persists episode and
grade records. It remains provider-free until its separate host, notice and
exact manifest gate pass.

`TaskExecutor.shadow_select()` remains observational on B0 roots. Its new,
explicitly admitted experimental path dispatches the candidate or predeclared
alternative cell and freezes the policy in each root and attempt. This has
passed provider-free dispatch and uncertain-call tests. The shipping B0
default remains unchanged.

Provider-free inspection:

```text
python tools/worker_n5_screen.py
python -m unittest test.harness.worker_n5_screen_tests
python test/harness/worker_n5_live_screen_tests.py
```

The [N5 host record](stage-results/worker-n5-host.md) distinguishes this
preparation from live qualification.
