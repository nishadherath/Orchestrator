# WSL mounted-project remediation, 2026-10-14

The Windows project remains on its original NTFS data drive. WSL now accesses
that drive through VirtioFS instead of the legacy 9P/DrvFs transport. The
authorised change is one user-wide `.wslconfig` setting: `[wsl2]` followed by
`virtiofs=true`. This experimental WSL 3.0.3 feature was retained after mounted
source, cache, cross-host visibility and cold-start checks passed. The previous
configuration is preserved in the ignored local rollback area.

## Diagnosis and measured limits

Earlier mounted-source runs had hit 20-second subprocess and 3-second MCP
deadlines, while byte-identical native Linux source passed. At the start of
this investigation the serial mounted-source baseline passed all 20 existing
tests in 38.600 seconds. The historical multi-second spikes were therefore
intermittent and were not reproduced before the transport change.

The host's C and D volumes were healthy NTFS drives, and WSL had ample memory
with no swap use. Measurements found a slower mounted filesystem boundary:
before the change, median stat/read/list operations took 4.6/6.1/8.7 milliseconds,
while native controls were below the reporting precision. Disabling Python
bytecode writes or moving bytecode to a native cache did not materially improve
warm imports. These results support filesystem-boundary latency as a contributor;
they do not identify an internal 9P defect or explain every old spike.

After the change, median stat/read/list times were 3.3/4.1/3.5 milliseconds.
Python import timings varied and were not uniformly faster. The remediation
targets the shared-filesystem transport; no timeout in the tests was increased,
and antivirus protection, permissions and the project location were preserved.

The helper had a separate amplification bug: it resolved a file path for every
symbol, often twice, although symbols share files. It now validates each
distinct path once per graph snapshot and reuses that resolution. On the actual
346-file/3,948-node index, validation calls fell from 3,948 to 346 and measured
diagnostic time fell from 30.560 to 2.266 seconds on the same VirtioFS mount.
The regression verifies large-symbol scaling and rejects an escaping symbol
path, so the performance fix preserves path safety.

## Change and verification

The first 45-second transport trial did not complete startup and restored the
exact old configuration. An inspection was inadvertently overlapped with its
reset and was terminated by that reset. The subsequent trial ran strictly
sequentially with an explicit Linux startup cwd and a 90-second platform boot
bound, covering WSL's configured startup interval. It booted in 9.006 seconds
and `findmnt --json` confirmed `/mnt/d` was actually `virtiofs`.

Both helper code and all test repositories/caches stayed on the Windows mount.
Two final offline runs passed all 22 tests, with no skips, in 25.554 and 26.941 seconds.
Real fork Graft 0.21.1 passed all 14 acceptance steps in 46.939 seconds, including
structured Markdown, Git/non-Git layouts, separate caches, clean replacement,
scoped MCP retrieval and actual automatic addition/removal. Git ownership and
cache-link safeguards remained enabled.

An additional native check against the pre-existing Windows cache failed to
produce a usable structural result; its output named added files beyond the
intended scope. That failure is retained rather than treated as a filesystem
success. A separate native profile at `.graft/wsl-core`, explicitly scoped to
the real project source, was built and checked: 346 files, 3,948 nodes and fresh
structure, with an absent optional semantic tier. The Windows cache was retained
and the helper's redundant ignore append was removed without changing the
project's existing ignore rules.

Cross-host checks passed Windows creation/replacement observed by Linux,
Linux atomic replacement/creation observed by Windows, and removal observed
across the boundary, using a unique Unicode/metacharacter filename. Only owned
probe files were created and removed. Cold-start and archive evidence is in
[the verification record](verification.json), alongside the retained failed trial.

The package's diagnostics now report the selected project's Linux mount point,
filesystem type and host-sharing state. The tests accept `GRAFT_TEST_PARENT`
and integration `--parent` to exercise an actual mounted project; native copies
alone cannot qualify that configuration.

## Scope and rollback

This setting affects all WSL 2 distros for this Windows user. Docker was stopped
during the change; Docker workloads were not qualified. The skill documents the
experimental setting and a review/backup/verification workflow, and never applies
the setting automatically to another host. Runtime dependencies remain native
Linux; the source/project stay Windows-mounted.

To roll back here, restore the exact saved `.wslconfig` bytes after reviewing any
later local changes, stop affected workloads, then run `wsl --shutdown` and
verify the next mount. The retained backup is
`.graft/wslconfig-before-mount-fix-2026-10-14.ini`. Do not overwrite unrelated
configuration or interrupt another active distro merely to reproduce these
measurements. Passing these checks establishes the tested state; it does not
guarantee that every future filesystem request or host load will meet a bound.

Primary host references: [Microsoft WSL filesystem guidance](https://learn.microsoft.com/en-us/windows/wsl/filesystems)
and [configuration settings](https://learn.microsoft.com/en-us/windows/wsl/wsl-config).
