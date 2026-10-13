# Preserve host configuration and checkout identity

Install `@nanonets/graft` only when needed and authorised; confirm `graft
--version` and the actual executable path. On Windows, direct Node plus Graft's
`dist/cli.js` is reliable across shells. The helpers resolve ordinary npm shims
or accept an explicit launcher array. They do not use `npx` to download tools
implicitly or issue shell-composed process commands.

For instruction wiring, preview `graft init --dry-run` before any write. Choose
only the hosts the operator uses, and keep machine-global changes out of a
project-only setup. For an AGENTS.md-only setup on the tested version:

```sh
graft init --agents agents --no-mcp --no-hooks --no-global --no-build --dry-run /absolute/project
graft init --agents agents --no-mcp --no-hooks --no-global --no-build /absolute/project
```

Do not rerun `init` just to repair a slow index when host wiring already works.
Do not hand-edit Graft's fenced `<!-- graft:start -->` managed section. Keep
project-specific retrieval guidance outside that section and respect existing
instructions. Inspect a prior wiring stamp when upgrading or cleaning a cache:
MCP upkeep can replay its selected global/host options at startup.

## Project-local registrations

Read the existing config, then merge only the Graft server. Use the host's
current supported schema. Below, executable and CLI paths are placeholders to
resolve on that machine; they are not literal installation destinations.

Codex project `.codex/config.toml`, following the locally verified stdio shape:

```toml
[mcp_servers.graft]
command = "/absolute/path/to/node"
args = ["/absolute/path/to/graft/dist/cli.js", "mcp", "/absolute/project"]
cwd = "/absolute/project"
enabled = true
startup_timeout_sec = 30
tool_timeout_sec = 180
```

These timeouts are example bounds, not prescribed universal values. Choose
them from observed startup/freshness costs. Preserve any existing `required`
policy and unrelated fields rather than forcing all users into required startup.
Project trust and a host restart may be needed before changed settings load.

Claude project `.mcp.json` can use an explicit project root or its supported
`${CLAUDE_PROJECT_DIR:-.}` expansion:

```json
{
  "mcpServers": {
    "graft": {
      "type": "stdio",
      "command": "/absolute/path/to/node",
      "args": ["/absolute/path/to/graft/dist/cli.js", "mcp", "${CLAUDE_PROJECT_DIR:-.}"]
    }
  }
}
```

Review the host's project-server approval and narrow retrieval permissions.
Do not grant blanket permission to unrelated future servers/tools.

For ZCode, merge the server under `.zcode/config.json` → `mcp.servers` using
the installed host's schema. Use a directly resolved Node/CLI launcher on
Windows, or an executable `graft` on Unix. Verify the target host actually
loads this entry; a generic stdio smoke is a different piece of evidence.

## Global registrations and worktrees

A machine-global registration must follow the active session's project root.
Omit a fixed project argument when the host launches the server in the correct
checkout, and verify that behaviour with two distinct roots. If the host does
not supply a trustworthy cwd, use its supported per-project registration or
explicit root mechanism instead. Never make every project query one fixed repo.

Each worktree needs an index for its own current source. Graft can seed worktree
caches, but the receiving checkout's freshness and source spans must still pass.
Only index a broad workspace parent when multi-project federation was actually
requested; do not initialise Graft over a home directory or unrelated projects.

After wiring, prove host tool access, selected root and a real scoped source
query in that host. `probe_mcp.py` proves a fresh local MCP process; it does not
prove that a new editor/chat has loaded the intended configuration or that a
worker is confined to the repository filesystem.

## WSL startup and native POSIX verification

Separate the Windows VM boundary from the Linux launcher. A
`Wsl/Service/CreateInstance/CreateVm/ERROR_TIMEOUT` occurs before Graft starts;
changing a Graft tool timeout cannot repair that failure. From Windows, inspect
`wsl --list --verbose`, then run a bounded direct probe such as
`wsl -d <distro> --exec /usr/bin/python3 --version`. Use an actual Linux
interpreter path, avoiding a login shell's inherited aliases and startup files.

If the boundary is stuck, review active distro workloads before stopping them.
`wsl --terminate <distro>` stops that distro; `wsl --shutdown` stops every distro
and the shared VM, including Docker's distro. Use shutdown only when all affected
workloads can stop. Bound both the reset and the next startup attempt; stop and
retain the error if recovery fails. Do not kill unrelated services, remove a
distro or change VM settings merely to obtain a passing test.

After recovery, verify more than a warm command. Repeat cold starts when the
host is idle, recording reset/startup times and errors. If an intermittent error
has already disappeared, report recovery and its observed limits; a successful
retry does not establish a root cause or a permanent fix.

Inside WSL, inspect `command -v node` and `command -v graft`, then prove
`node -p 'JSON.stringify({platform:process.platform,execPath:process.execPath})'`.
It must report `linux` for native WSL verification. Windows PATH entries can
select `.exe` files or shell shims under `/mnt/c`; Linux Python alone does not
prove that Graft also ran on Linux. Use a separately installed native Node and
Graft, with an explicit Node/CLI launcher array and the native Node directory
first on the child PATH. Preserve the Windows installation and host settings.

The source package's acceptance runner accepts `--node /native/path/to/node`
alongside `--launcher-json '["/native/path/to/node","/native/path/to/graft/dist/cli.js"]'`.
It rejects a Python/Node platform mismatch and records the runtime identity.
Run it in isolated roots; its source and MCP addition/removal checks must pass
before claiming real POSIX acceptance. Archive `--check` should also pass on
that native interpreter. These checks qualify the recorded platform and Graft
version, not every Unix host.

Primary host references: [Microsoft WSL commands](https://learn.microsoft.com/en-us/windows/wsl/basic-commands)
and [WSL troubleshooting](https://learn.microsoft.com/en-us/windows/wsl/troubleshooting-guide).

## WSL mounted projects

`diagnose.py` reports the Linux filesystem type and mount point containing the
resolved project. Use that evidence rather than assuming every `/mnt/` path
uses the same transport. Windows junctions can give one checkout several paths;
prefer its actual physical drive path when comparing measurements.

Separate cold WSL startup, Python/Node startup, file metadata, file reads and
Graft work. Compare repeated operations with a native temporary-file control.
Keep test deadlines unchanged. A serial passing rerun does not explain earlier
intermittent stalls, and faster averages do not establish bounded tail latency.
Preserve failures and record whether source, fixtures and caches were mounted.

On the tested WSL 3.0.3 x64 host, the legacy 9P/DrvFs boundary had slower metadata
and reads. An authorised, backed-up `[wsl2]` `virtiofs=true` trial switched the
same Windows drives to VirtioFS. This is an experimental, user-wide WSL 2
setting, not a portable default or an automatic action of these helpers. Check
the installed version's documented prerequisites and active distro workloads.
Do not change antivirus protection, filesystem permissions or unrelated storage
settings to make a test pass.

When a transport change is in scope, save the exact existing `.wslconfig`, merge
only the reviewed setting and reset WSL when affected workloads can stop.
Finish inspections before resetting; do not overlap a reset with another WSL
request. Use an explicit Linux startup cwd such as `--cd /`. A platform boot
bound should cover its configured startup interval; keep separate 3/20-second
test bounds intact. Confirm the actual mount type with `findmnt --json -T
/absolute/project`; a setting or warning containing "virtiofs" is insufficient.
Restore the saved configuration if boot, mount or filesystem checks fail.

Verify Windows-to-Linux and Linux-to-Windows edit visibility, atomic replacement
and removal, then run real scoped refresh and MCP addition/removal from the
mounted project. The package integration runner's `--parent` must point to that
mount so fixtures and caches stay there. Its offline suite accepts
`GRAFT_TEST_PARENT` for the same purpose. Passing tests on native copies alone
does not qualify a Windows-mounted project. Inspect Git ownership checks and
symlink behaviour too; retain platform-specific skips and errors explicitly.

Primary references: [Microsoft filesystem considerations](https://learn.microsoft.com/en-us/windows/wsl/filesystems)
and [WSL configuration](https://learn.microsoft.com/en-us/windows/wsl/wsl-config).

### Concurrent Windows and WSL load

VirtioFS did not eliminate the tested concurrent-load slowdown. A native
Windows helper exceeded its unchanged 20-second deadline with VirtioFS active;
Linux helpers waited for filesystem replies on both transports. Treat this as
a host/load investigation when Windows is affected too, rather than assuming
one Linux transport is defective. Keep each host's test repositories and caches
separate so shared-cache races do not contaminate the experiment.

Run the portable probe in an existing, approved, ignored scratch directory:

```sh
python scripts/fs_probe.py --parent /project/.graft/probes --seconds 20 --workers 1 --output /project/.graft/fs-latency.json
python scripts/trace.py diagnose --repo /project --check 2> /project/.graft/diagnose.trace.jsonl
```

The probe creates 16 small files per worker in its own temporary subdirectory,
then measures stat, read, path resolution, write/replace, create/remove and bare
native Python startup. It removes only its owned scratch tree on normal exit.
It never changes a mount, antivirus policy, Graft cache or provider setting.
Start with its conservative defaults; higher worker counts and shorter pauses
deliberately create load and can reproduce the problem. The requested duration
limits work scheduling; an individual filesystem call or cleanup can take
longer. Use a separate process supervisor when a hard execution bound matters.
Inspect any owned leftovers after forced termination before removing them.
Linux pressure data is absent on other hosts, not evidence of zero pressure.

The trace wrapper accepts only this skill's diagnose, refresh and probe_mcp
helpers. It retains their arguments, JSON stdout, exit status and safety checks,
and writes stage timings plus Python frame locations to stderr. It does not
log argument values, environment values or source bodies. Capture/drain stderr
when embedding it. Stage timings nest, and wrapper process CPU excludes child
CPU; neither should be summed as independent work. Tracing adds overhead.

The bootstrap marker precedes filesystem-backed imports. If import metadata
appears in slow samples, `trace.py diagnose --isolate-imports <arguments>` is an
optional control: it removes this helper directory from normal import search
and loads the trusted common module explicitly. Other configured paths remain.
It preserves helper cwd, source/cache selection and safety checks. The tested
control improved some timings but still hit a Linux deadline under high load;
do not present it as sufficient prevention or a security isolation boundary.

Compare serial and simultaneous runs on the same source/fixture placement,
then repeat with byte-verified native source and fixtures. Record operation
counts, median and tail latency, mount type, startup times and failures. A
changed worker pause is a load intervention, not a timeout increase. Pacing
file churn reduced the measured slowdown while protection remained enabled;
serialise heavy refreshes or reduce competing metadata work when practical.
Native copies are diagnostic controls, not an instruction to relocate a project.

On Windows, inspect CPU, paging, disk queues and process CPU counters. Defender
was a substantial CPU consumer here, but CPU correlation alone does not prove
a specific scan blocked a helper. Its supported performance recorder requires
Windows administrator elevation, distinct from a tool sandbox permission.
An authorised `New-MpPerformanceRecording -RecordTo <local.etl> -Seconds 20`
can be analysed with `Get-MpPerformanceReport`. Preserve another active
recording instead of cancelling it. Record actual trace start/end times:
collection/stop overhead can exceed the requested interval. Scan durations can
overlap and are not application I/O latency or CPU time. Entries ending at the
recording boundary need particular care. Do not infer causation from those
entries or disable protection to make a benchmark pass. Raw ETL may include
unrelated file paths; keep it local and share only reviewed, scoped evidence.

Use public `/proc` wait state when permitted. Repeated protected stack/syscall
reads from a sibling can cause ptrace denials and audit work; do not weaken
security policy to remove that measurement limitation. One periodic C traceback
experiment crashed the tested Python runtime, so the package uses Python frame
sampling and timing instead. That crash is not evidence of a Graft timeout.

See [Microsoft's Defender analyzer guidance](https://learn.microsoft.com/en-us/defender-endpoint/tune-performance-defender-antivirus)
for the optional Windows recording. The package's outer concurrency report
contains the tested host, exact outcomes and remaining causal uncertainty.
