# Full-project freshness repair, 2026-10-14

The repaired full-project checks completed under simultaneous Windows and native
WSL load, while the previous checks exceeded 180 seconds. The evidence establishes
three Graft causes of excessive work. It identifies Defender callback delays in the captured Graft process, while
the unique cause of the entire Windows/WSL stall remains unproven.

## Observed failure and source repair

The tested Windows installation changed compiled output and package metadata
while retaining the 0.21.1 lineage. Its extractor identity no longer matched the
saved core fingerprint. Graft rejected that fingerprint's scope together with
its hashes, then enumerated excluded fixtures. Scope filtering also happened
after Git/filesystem walking and metadata calls. A full check independently
parsed every unchanged source again. Linux was observed waiting in Git's mounted
filesystem request path; that wait alone does not identify the Windows service
or driver responsible.

The source repair prunes scoped Git pathspecs and filesystem descent before
metadata work, preserves validated unanimous foreign fingerprint scope policy,
and reads/hashes current source before reusing matching-extractor parse entries.
Foreign cached hashes or parses are never accepted. Missing/malformed entries
fall back to extraction. New, edited and removed files still produce drift.
`GRAFT_CHECK_REPARSE=1` preserves an independent parser audit. Local parse reuse
trusts a matching extractor's cache and is not protection against deliberate
cache tampering. Binary documents retain their existing rendering check path.
The initial full build walk is unchanged; pruning applies to scoped source
checks/probes rather than every Graft traversal.

The package probes actual runtime features and extractor identity, and refuses
a foreign fingerprint on an older runtime before launching an expensive check.
The bundled nine-file source patch includes fail-first regressions, an exact
source-base manifest, backups on application and a separate MIT licence.
The patch helper does not edit installed compiled output or host registration.
Use the [source repair reference](graft-setup/references/freshness.md) to apply it
to a matching checkout; other source bases require review or a port.

## Concurrent full-project results

Both hosts used the physical Windows project drive, with Linux `/mnt/d` reporting
VirtioFS. The source scope was `src`, `tools`, `test/harness`: 346 Python files,
3,948 nodes and 12,453 edges. Four disposable filesystem workers per host used
1 ms pacing for 300 seconds. Check bounds remained 180 seconds. Provider calls
were zero; the qualification checks did not rebuild their caches.

| Runtime/helper | Windows check | Native Linux check | Outcome |
| --- | ---: | ---: | --- |
| Original CLI under four-worker load | 180.215 s timeout | 180.238 s timeout | Retained failure |
| Scope repair, CLI only | 175.757 s | 158.190 s | Passed with little margin |
| Scope repair, complete helper | 180.224 s timeout | 171.824 s | Insufficient repair |
| Scope and hash-verified memo, complete helper | 6.646 s | 22.800 s | Both passed |

The final complete helpers took 48.537 and 48.359 seconds respectively, including
runtime capability and graph diagnostics. Both reused 346 parses and parsed zero
files, while still reading and hashing current source. Serial checks after
building these caches took 3.270 and 3.002 seconds. These are observed runs,
not a universal latency bound. Runtime placement, package metadata, cold imports,
background applications and profiler overhead are recorded confounders; no
isolated percentage improvement or Windows filter causal estimate is claimed.
The final candidate helpers reported prerelease metadata `0.21.1-nishadherath`;
this is distinct from the plain-version metadata used for the source test gate.
The CLI digest alone cannot identify the full compiled build.

## Windows attribution and profiler limits

The first WPR CPU/file/minifilter capture produced an oversized, unfinished
16.6 GB merge. Only that task-owned merge was stopped after explicit approval.
A memory fallback did not start successfully. A bounded CPU/thread-wait capture
lost 1,199,599 events, preventing reliable aggregate attribution. A prior minimal
capture ended before the actual Graft workload and therefore provides no causal
Graft evidence.

The final handshaken minifilter capture overlapped unrepaired Graft PID 10892
and sixteen workers on each host. Graft timed out again at 180.265 seconds.
The recorder reported zero lost events/buffers, but its raw file reached the
512 MiB circular cap. Early workload and driver metadata were overwritten.
All-process Node totals cannot establish a unique blocker. Combining image
metadata from the prior same-boot capture resolved driver names in retained
events. Exact matching of Graft PID 10892's init/completion records by phase,
IRP, operation, module, file object and callback pointer produced 640 callbacks
with no unmatched own init. Exported microsecond timestamps were paired; raw
QPC values in completion payloads were not subtracted from them.

The largest retained callback delays were in `WdFilter.sys`: 138.763 ms on
CREATE, 30.381 ms on READ of `src/preflight.py`, and 38.566 ms on READ of an
excluded benchmark fixture. `bfs.sys` also had a 16.322 ms callback; the captured
`SbieDrv.sys` callbacks reached only 0.049 ms. These samples identify a specific
Windows component delaying this Graft process, rather than mere driver presence.
[Microsoft identifies WdFilter as Defender's antivirus minifilter](https://learn.microsoft.com/en-us/defender-endpoint/troubleshoot-service-startup-problems).
Callback elapsed includes thread descheduling. Missing early events and thread
wait evidence still prevent attributing the entire 180-second timeout or WSL
multi-second stalls uniquely to Defender. The portable `filter_trace.py` reproduces
the paired-callback summary without publishing file paths or request pointers.
Raw traces and whole-machine exports remain ignored and local. Reviewed task
records retain the failed attempts and raw digests. No protection settings,
antivirus exclusions or unrelated processes/services were changed.

VirtioFS still exhibited multi-second operations under heavier load. The Graft
repair reduces avoidable work; it is not a Windows filesystem driver repair.
Exact component attribution remains an open requirement. A future capture must
avoid circular overwrite, retain module metadata and correlate the request's
actual PID, operation and thread scheduling before naming a culprit. See the
[portable trace guidance](graft-setup/references/hosts.md#windows-kernel-trace-evidence).

## Verification and reproducibility

`tests/full_project_worker.py` runs the actual complete helper against an existing
explicit cache with owned load and unchanged bounds. `tests/compare_hosts.py`
coordinates native Windows/Linux fixture acceptance. Evidence files beginning
`freshness-105-`, `freshness-full-helper-` and `freshness-final-105-` preserve source
regressions, failed repairs, stage timings and final qualification. The release
verification record lists the final build/test gate, active runtime, source patch
checks, package tests, real MCP acceptance and archive/installed parity separately.
Raw traces are excluded from the redistributable archive and Git.

The source build/test gate passed on native Windows Node 26.7.0: 1,556 tests,
1,551 passed, five skipped and zero failures, with two test-file workers and no
changed test assertions/deadlines. A preceding prerelease-metadata run had one
inherited plain-version regex failure; the final gate used version metadata
0.21.1. The active install retains its existing 0.21.1-nishadherath metadata.
Twenty-one compiler-generated outputs were copied after before/after hash checks
and backups. The external fork checkout and unrelated work were preserved.
Its future rebuild/sync can overwrite this repair; apply the included source patch
to that matching checkout before the next sync. The original Windows core cache
was refreshed with backup and checked fresh in 3.530 seconds. Long-lived MCP
processes retain previously loaded modules until their host reloads them.

The first final mounted Linux offline run failed at existing deadlines during
background verification. With heavy jobs finished, all 26 then-current tests
passed in 26.323 seconds. Real MCP initially refused unfamiliar prerelease labels,
as designed. Fixture acceptance now queries the chosen runtime's actual wiring
policy and acknowledges startup only after verifying no hosts are configured;
the installed helper's review guard is unchanged. Subsequent release records
include the added callback review tests and final acceptance outcomes.

The final 28-test skill suite passed on Windows in 39.485 seconds and mounted
native Linux in 27.576 seconds. Both real fork runtimes passed 14 acceptance
steps, including all six MCP tools, edit/add/remove refresh, retained scope and
structured Markdown. The paced-load pair used four workers per host at 50 ms
for 120 seconds. Windows acceptance took 203.201 seconds and Linux 128.521;
load overlapped the run but did not cover every final step. The separate
full-project freshness qualification used 1 ms pacing for its entire checks.
The initial unfamiliar-build MCP refusals remain recorded.

A second pair verified the active global Windows runtime and original `graft/`
cache against native Linux with four workers per host at 1 ms pacing for 120
seconds. Both checks remained within the load window: 11.017 seconds on Windows
and 16.982 on Linux. Both reused all 346 parses. An independent Windows full
re-extraction check passed in 31.116 seconds, reusing zero and parsing 346 files,
with identical fresh structural results. The relevant project offline checks
passed; the consumer bundle was unchanged. The release archive contains 22
allowlisted files and matches the installed skill and native Linux rebuild.
