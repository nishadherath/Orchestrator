# X5 external intake B: fresh public issue screen

Date: 2026-09-30 Australia/Sydney. Status: **provider-free exploratory
screen**. No producer, Controller or S/A call was made. B0 remains the
shipping default and X6 is sealed. This is a convenience screen, not a
random sample or reserved evaluation, and its yield cannot estimate the
target population's entry rate.

After E01-E03 failed blind admission, recent open issue metadata was checked
in HTTPcore, HTTPX, Starlette, AnyIO, Werkzeug, Requests and Pydantic. E04-E07
were read from recent AnyIO issues, E08 from Werkzeug and E09-E11 from
Pydantic. Each fetched issue body was saved unchanged under
`test/fixtures/controller_x5_external/development/<id>/source-issue.md` and
SHA-256 bound in the [machine record](../../test/results/2026-09-30-controller-x5-external-intake-b.json).
The candidate choices used public titles and dates after seeing earlier X5
screens, so this batch has selection bias. Later linked PRs were consulted
only for exclusion and calibration, never for selecting a paid actor.

| Case | Natural report | Provider-free decision |
| --- | --- | --- |
| E04 [AnyIO #1364](https://github.com/agronholm/anyio/issues/1364) | A connected socket can be orphaned when an outer cancel scope expires after connect. | Reject blind paid work: the issue supplies a concrete `except BaseException` cleanup patch. |
| E05 [AnyIO #1356](https://github.com/agronholm/anyio/issues/1356) | A child's cleanup exception is lost during `TaskGroup.start()` cancellation. | Reject blind paid work: the report identifies the exact `task_done()` early return and ordering. No independent protected check was built. |
| E06 [AnyIO #1344](https://github.com/agronholm/anyio/issues/1344) | A non-daemon thread can keep the interpreter alive after a manually driven loop stops. | Reproduced as research, then reject blind paid work: the linked [PR #1346](https://github.com/agronholm/anyio/pull/1346) publishes a multi-path cleanup design under maintainer review. The correct ownership policy is not settled. |
| E07 [AnyIO #1353](https://github.com/agronholm/anyio/issues/1353) | Hypothesis tests marked for multiple backends run again on the first backend. | Reject blind paid work: the issue points to the precise pytest hook lines and missing re-wrap. |
| E08 [Werkzeug #3285](https://github.com/pallets/werkzeug/issues/3285) | Split multipart boundaries append a stray byte to upload data. | Reject blind paid work: the report identifies `_parse_data()`, the regression commits, the dropped guard and two suggested repairs. |
| E09 [Pydantic #13869](https://github.com/pydantic/pydantic/issues/13869) | `model_construct` leaks `AliasPath` input into model extras. | Reject blind paid work: the issue gives exact source lines, branch asymmetry, fix layer and control matrix. |
| E10 [Pydantic #13678](https://github.com/pydantic/pydantic/issues/13678) | Multiple inheritance field and private-attribute merges disagree with Python MRO. | Reject blind paid work: the issue diagnoses the two merge directions and suggests MRO-order merging. |
| E11 [Pydantic #13647](https://github.com/pydantic/pydantic/issues/13647) | Deferred `SerializeAsAny` models fail during JSON serialisation. | Reject blind paid work: the issue names the Rust function, gives the exact mock rebuild steps and says the author already has a tested fix. |

## E06 watchdog calibration

Pinned AnyIO 4.15.1 was staged in a disposable dependency directory. The
[process watchdog](../../test/fixtures/controller_x5_external/development/E06/repro/run_probe.py)
kills each child after three seconds. The adapted
[issue case](../../test/fixtures/controller_x5_external/development/E06/repro/exit_hang.py)
printed that `run_forever()` returned and that a non-daemon AnyIO worker
remained before the child timed out on Windows and WSL. Its fixed half-second
timer had one WSL run that stopped before the worker existed. A separate
[readiness-controlled case](../../test/fixtures/controller_x5_external/development/E06/repro/exit_hang_ready.py)
then guaranteed that the worker had started without creating a transient root
task; it printed the same state and timed out on both hosts. The
[`asyncio.run()` control](../../test/fixtures/controller_x5_external/development/E06/repro/drain_control.py)
returned with exit code 0 on both. The readiness-controlled case is an
adaptation, not a byte-for-byte replay of the issue.

These observations establish a reproducible shutdown failure in this host
mix. They do not establish a correct upstream repair, a public residual
review trigger or Controller uplift. The PR is open and its maintainer has
questioned the need for three shutdown mechanisms. No hidden oracle was
constructed and no paid E06 root exists.

## Consequence for X5

Zero of these eight screened reports qualifies for a blind paid pair. Most
contain the diagnosis or suggested patch in the natural issue body. E06 has
a real failure but a public repair proposal and unsettled lifecycle policy.
Selecting from these reports after seeing their later fixes would measure
recognition of public solutions as much as problem solving. This is a screen
outcome, not proof that all real repository work lacks Controller headroom.

The next intake needs a prospectively fixed source population and a public
symptom without a published repair, a deterministic worker-host reproduction,
an independently authored acceptance contract and a consequential public
follow-up that can remain broken after a plausible first repair. If those
conditions do not yield enough cases at a feasible cost, X5 should report
insufficient evidence for Controller uplift and keep B0.
