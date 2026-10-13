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
