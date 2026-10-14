# Concurrent Windows and WSL investigation, 2026-10-14


The later [full-project freshness repair](FRESHNESS.md) adds source scope pruning
and content-hash-verified parse reuse. Its larger project checks passed under
concurrent load. This report retains the earlier 1.0.4 experiments and limits.

VirtioFS does **not** eliminate the intermittent timeout class. Concurrent file
churn reproduced a native Windows helper's original 20-second timeout with
VirtioFS active. A focused 16-worker replay then reproduced three Linux
20-second failures in four attempts on that same transport. The evidence
establishes load-sensitive filesystem and process/bootstrap delays, rather than
a defect unique to Graft's graph algorithm or Linux 9P. The precise Windows
component responsible for the earlier historical failures remains unproven.

## Observations and causal limits

The 22 existing offline cases kept their original 3/20-second bounds. Source,
fixtures and caches stayed on the physical Windows NTFS project drive, reached
as `/mnt/d/Code/Claude/Orchestrator`. Each host used distinct owned repositories
and caches. Windows used native Python 3.14.7; WSL used native Linux Python
3.14.7 and, for real Graft, native Node 22.23.0. Windows Node was 26.7.0.
Graft installations were retained; each real acceptance report records its CLI
digest and capabilities. Their intentional fork snapshots differ, so equal
version labels are not evidence of identical code.

Four probe threads on each host repeatedly stat/read/resolve, write/replace and
create/remove 16 owned files per thread for 120 seconds. The initial pause was
1 millisecond after each iteration. A native ext4 probe ran alongside Linux.
These are deliberate synthetic workloads, not a measured distribution of
ordinary editing activity. A worker's probe interval does not guarantee fixed
throughput: filesystem latency and host scheduling affect completed counts.

| Scenario | Windows suite seconds | Linux suite seconds | Outcome |
| --- | ---: | ---: | --- |
| 9P, serial | 27.748 | 30.915 | 22/22 each |
| 9P, four-worker simultaneous load | 75.900 | 131.462 | 22/22 each |
| VirtioFS, serial | 34.638 | 55.083 | 22/22 each |
| VirtioFS, four-worker simultaneous load | 142.883 | 134.021 | Windows: one 20-second error; Linux: 22/22 |
| 9P reverse replay, stage tracing | 63.696 | 91.924 | 22/22 each |
| VirtioFS replay, stage tracing | 81.335 | 107.113 | 22/22 each |
| VirtioFS, same tracing/workers, 50 ms pause | 46.275 | 45.409 | 22/22 each |

The higher-pressure replay selected the original failing backup/refresh case,
not the newly added diagnostic tests. Sixteen threads per host caused three
Linux helper timeouts in four attempts; all four Windows attempts completed.
Case totals can exceed 20 seconds without failure because the 20-second bound
applies to each helper invocation. The preserved partial traces show path
resolution and subprocess startup/communication for fake CLI version/help.
Some deadlines expired before Graft build work began. This fixture uses no
Graft/Node implementation, so Graft's extractor cannot be a necessary cause of
those failures. Real Graft acceptance is separate evidence below.

An additional warmed-VM replay failed both Linux attempts and also reproduced
Windows deadlines. Its early markers show roughly 0.5-0.9 seconds before script
entry and 2.0-2.4 seconds loading trace/common imports; subsequent samples show
import-path metadata and build/check subprocess waits consuming the remainder
of the same budget. It does not require a single filesystem call to block for
20 seconds. The warm native-Python probe itself took 59.790 seconds before load,
so cold startup remains a separate variable, not a claimed permanent repair.

The optional import-search control removes the helper script directory from
normal module search and loads the trusted local common module explicitly.
Its fake CLI control also uses Python `-P`. Two Windows focused attempts passed
in 26.919 seconds total; Linux still had one deadline failure in two attempts
(60.794 seconds total). This is a diagnostic control, not sufficient prevention
or proof that every slow import came from the script directory. Configured
import paths remain; the option is not a security isolation boundary.

Linux wait samples found `p9_client_rpc` on 9P and `request_wait_answer` on
VirtioFS. Traced path/link/graph operations had much more wall time than wrapper
CPU time. These locate filesystem waits, without identifying the Windows
service or filter handling each request. The 9P client source describes its
request/response wait; it does not prove a deadlock in this installed kernel.
[Microsoft kernel source](https://raw.githubusercontent.com/microsoft/WSL2-Linux-Kernel/linux-msft-wsl-6.6.y/net/9p/client.c).

Byte-verified copies of the then-current helper/test source, with fixtures on
native ext4, passed all 22 tests during concurrent load: 33.465 seconds alongside
the VirtioFS trial and 24.887 alongside the reverse 9P trial. This isolates a
substantial mounted-source/fixture contribution. Native storage still had a
2.247-second write/replace tail in an earlier control; it is not immune to host
pressure. The source digest sets are preserved in the control reports.

CPU snapshots during fast churn were 98.6-100% busy. In a traced sample Defender
used about 3.53 logical CPUs; the process counter is summed across processors,
not a percentage of the whole machine. Paging was low in that sample. After
pacing the same threads to 50 ms, the snapshot was 47.8% busy and Defender about
0.97 logical CPU. The lower suite times support contention and file-churn rate
as contributors. These are point samples on a live host, not controlled CPU
averages, and do not uniquely attribute an individual 20-second wait.

## Defender evidence, without disabling protection

The initial recorder attempt failed with Windows access denied, `0x80070005`.
An elevated read-only recording succeeded. Protection, exclusions, permissions
and power settings were unchanged, and no existing recorder was cancelled.
Although 20 seconds was requested, the report spans 45.463 seconds including
recording/stop overhead. It reports 21,402 real-time scans and substantial
activity on the owned probe files. A background ZCode updater signature check
also appears in the reviewed evidence.

The longest reported scan entries end at the recording boundary. Two probe
scan durations exceed 23 seconds, while that probe's measured Windows
write/replace maximum is only 0.088571 seconds. Those records therefore cannot
be treated as synchronous application I/O stalls. They establish activity;
they do not prove Defender blocked the failing helper, nor that the updater
caused the earlier failures. Summed scan durations overlap and are not CPU time.
The raw ETL remains local because it contains unrelated file paths; a scoped,
reviewed extract and the raw digest are tracked in
[concurrency-defender-evidence.json](test-results/concurrency-defender-evidence.json).
[Microsoft analyzer guidance](https://learn.microsoft.com/en-us/defender-endpoint/tune-performance-defender-antivirus).

## Retained experimental failures

A periodic C traceback dumper crashed one Linux test process with SIGSEGV at
11.053 seconds while printing an invalid frame. Its log and kernel report are
retained. The package now uses ordinary Python frame sampling and per-test
timing; this instrumentation crash is separate from the helper deadline errors.
The first proc sampler also encountered protected stack/syscall reads and Yama
denials. The final sampler reads public wait state without changing ptrace
policy or provoking repeated protected-read failures.

The warmed Windows replay exposed a test recorder assumption that timeout
stderr was always bytes. Windows returned text; the original timeout remained
visible but its partial log capture failed. That recorder now handles both
representations and has a regression. A descendant also briefly held its owned
fixture cwd after the parent timeout, producing a retained cleanup error. Do
not interpret parent termination as proof a whole process tree has stopped.

The initial coordinator's 360-second aggregate bound interrupted the first
VirtioFS pair after its real Windows unit timeout had already been captured.
The owned Windows integration child was inspected and allowed to finish; its
14-step result passed. The incomplete coordinator record is retained, not
presented as a completed matrix. The later pair runner gives the experiment a
separate aggregate bound while retaining existing per-helper/test bounds.
Killing a `wsl.exe` client is not proof its Linux children stopped; resets were
sequenced after owned requests completed. The reverse trial restored the exact
prior VirtioFS configuration and verified the actual mount with `findmnt`.

## Package changes and reproduction

Version 1.0.4 adds portable `fs_probe.py` and `trace.py`. The latter records an
early bootstrap marker before filesystem-backed imports, then stage wall/CPU
timing and Python frame locations. This matters because late instrumentation
can miss time consumed before helper logic starts. Helper stdout and exit
status are preserved; argument values, environment values and source bodies
are not logged. The default diagnostic probe is conservative; stress settings
are explicit. Its work duration is not a hard bound on a blocked filesystem
call or cleanup.

The outer source package includes `tests/compare_hosts.py`, `concurrent_worker.py`,
`timed_unittest.py`, `native_control.py` and `proc_waits.py`. The two-host runner
uses the existing mount and **never changes WSL settings**. Supply a Windows
runtime JSON and a Linux runtime JSON containing a `launcher` array, approved
scratch parents, and the physical Windows/Linux spellings of the same package
and output directories. Use `--serial --workers 0` for baseline, `--workers 4
--unit-only --trace` for the diagnostic pair, and `--interval-ms 50` for the
paced control. `--unit-case test_helpers.Helpers.test_backups_and_clean_meaning_fallback_preserve_wiring
--repeat 4` focuses the original failing case. `--warm` runs a bounded native
Python probe before load to separate cold VM startup. Preserve the emitted
commands, logs, source hashes and actual mount identity.

Use `trace.py refresh --isolate-imports <helper arguments>` or pair-runner
`--trace --isolate-imports` only for that import-search control. Normal helper
safety checks, cwd and cache/source scope still apply.

Transport A/B changes require the existing skill's explicit backup, workload
review, sequential reset and actual-mount verification procedure. They are not
automatic actions of the redistributable scripts. Compare repeated runs and
reverse order; do not lengthen acceptance bounds or discard stress failures.
Real Graft reports collected on both transports each passed all 14 acceptance
steps, including scoped MCP and actual automatic addition/removal. Some of
those steps occurred after the 120-second synthetic load ended; they do not
constitute an all-steps-under-load guarantee. Binary document rendering, Docker
workloads and other host versions remain untested.

The practical mitigation supported here is to reduce overlapping metadata and
refresh churn, retain a focused index and use native controls for diagnosis.
VirtioFS may change individual costs but is not sufficient prevention. The
historical 3-second MCP timeout and the unique Windows wait/scan mechanism
still require a capture at the failure itself; no permanent OS fix is claimed.

The [verification record](verification.json) and
[machine-readable summary](test-results/concurrency-summary.json) retain
successful, failed and incomplete runs separately. No provider calls were made.

Final qualification passed all 25 expanded offline cases on Windows and native
Linux with source and fixtures still Windows-mounted. The existing prose,
context, distribution-parity and diagnostics gates passed. A traced check of
the full mounted project also exceeded the existing 180-second Graft-command
bound; its actionable failure and trace are retained. Passing small fixtures
does not qualify bounded freshness latency on the full project.
