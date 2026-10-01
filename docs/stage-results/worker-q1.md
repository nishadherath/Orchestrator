# Q1: multi-file WSL boundary

Date: 2026-09-25. Status: **Q1 provider-free boundary complete for operator
review; Q2 and paid work have not started**. Branch `v1.0-rc1`, HEAD
`15ecf66`. B0, N5 frozen results and the reserved N6 R tasks are unchanged.
The existing worktree had unrelated uncommitted N5 and Q0 work, which was
preserved. The [host guide](../WORKER-Q1-MULTIFILE-WSL-HOST.md) is the
reproduction and boundary contract.

## Exit criteria and evidence

| Q1 criterion | Observed result | Limit |
| :--- | :--- | :--- |
| Manifest-bound 2-8-file edits | Two nested Python modules were editable; protected issue, acceptance and public test files and new files were denied. Path traversal, absolute/backslash paths, symlink and undeclared source files were rejected. | Existing editable files only; 200-file/5 MB package cap. |
| Actor-only Graft and evaluator isolation | Both module markers were returned by actor Graft; the evaluator marker was absent; parent escape, direct/symlink reads and a sibling actor path were denied. | This is a local synthetic probe, not a proof for every future corpus project. |
| Stopped-writer collection | Collection before stop failed. The launcher emitted a stop record after `unshare` returned; collection copied both edits into a private snapshot, rejected a second collection, source races and protected actor drift. The source package stayed unchanged. | A paid transport must additionally bind its provider terminal event and no-replay state. |
| Root accounting | A `task_dispatch` budget reserved before the WSL probe, settled a verified zero-cost run, refused duplicate start, retained an uncertain-charge hold and blocked further dispatch against that hold. | Provider calls were zero. Actual paid telemetry and a multi-file `TaskExecutor` adapter remain untested. |
| N5 compatibility | The unchanged N4 single-file transport probe passed all eight checks after Q1 installation. | The N5 path remains separate. |

The [Q1 attestation](../../test/results/2026-09-25-worker-q1-wsl-host.json)
passed **38 WSL boundary checks and five accounting checks**, with evidence
digest `4f8533e4edfe4d90c24cafa0f0cadd892d732a20046f3680c97ac1e0e3d98295`.
The Q1 actor probe ran Python and Graft only: zero Claude/provider calls and
USD 0 provider-reported cost. This is a true zero paid experiment, not an
estimate of the development session's API cost. The latter is unavailable
from this host. The staged protocol requested GPT-5.6 Sol High for bounded
implementation; this session's actual model and effort were not exposed for
verification.

Commands and observed results:

```text
wsl.exe -u root -- bash .../tools/worker_wsl_q1_install.sh
  exit 0
wsl.exe -u root -- python3 /opt/orchestrator-worker-runtime/worker_wsl_q1_probe.py
  PASS: 38/38 boundary checks, provider_calls=0
python tools/worker_wsl_q1_attestation.py
  PASS: 38 WSL checks and 5 accounting checks
wsl.exe -u root -- python3 /opt/orchestrator-worker-runtime/transport-probe.py
  PASS: 8/8 legacy transport checks
python test/harness/worker_wsl_q1_tests.py
  2 tests OK
python test/harness/check.py
  PASS: 0 failing of 64 checks at 15ecf66
python tools/worker_wsl_q1_attestation.py --check
  PASS: Q1 WSL attestation current
python tools/release_check.py
  source-equivalence, generated-workers, sensitive-material and licence checks PASS;
  clean build stamp and publication remain operator actions on the dirty branch
```

The new project-side files are `tools/worker_wsl_q1.py`,
`tools/worker_wsl_namespace_q1.sh`, `tools/worker_wsl_q1_install.sh`,
`tools/worker_wsl_q1_actor_probe.py`, `tools/worker_wsl_q1_probe.py`,
`tools/worker_wsl_q1_attestation.py` and
`test/harness/worker_wsl_q1_tests.py`. The offline harness includes the
path/evidence regression cases. No consumer `src/` or generated `dist/`
file was changed for Q1.

Graft MCP was used for scoped retrieval. Its local structural graph was
rebuilt and reports no wiring drift. Its semantic layer still reports stale
N5/Q1 summaries because the previously observed DeepSeek forced-tool parse
failure has not been repaired; no semantic rebuild charge was incurred in Q1.
The first concurrent full-harness attempt timed out in the existing N4 corpus
suite at its 150-second limit. That suite passed alone in 97.119 seconds,
and the uncontended full rerun passed 64/64. This is a host contention
observation, not a code failure.

## Next action after review

Q2 should prepare a few public Python service/CLI tasks that fit this exact
package contract, add multi-file public verification and hidden grading,
and freeze a reproducible source-project/issue sampling rule. It must not
use the sealed N6 R tasks or launch a paid Claude episode. Review Q1's
existing-file and package-size limits before expanding either.
