# N4 WSL worker host

Status, 2026-09-24: local isolation and unauthenticated Claude startup passed.
This is a host qualification component, not a paid campaign runner. The
[N4 result](stage-results/worker-n4.md) states the remaining gate.

## Boundary

`tools/setup_worker_wsl.sh` installs pinned Node 22.22.0 and Graft 0.18.0
under `/opt/orchestrator-worker-runtime` on the Linux filesystem. The actor
does not execute Windows Node/Graft via `/mnt/c`. The official native Claude
2.1.273 binary is copied there by `tools/worker_wsl_stage.sh`. All runtime
files are root-owned; a generated MCP JSON names only Graft and binds its
index root to the actor's `CLAUDE_PROJECT_DIR`.

The stage helper creates separate actor and evaluator directories under
`/var/lib/orchestrator-worker-n4`. The evaluator is root-only (mode 700). The
actor owns only its materialized package. `tools/worker_wsl_namespace.sh`
starts a private mount and PID namespace, mounts a new `/proc`, removes the
Windows C/D and WSL drivers mounts, covers WSL interop sockets and other host
integration mounts, and replaces `/init` with `/dev/null`. It then clears the
inherited environment and drops to UID/GID 65534 with no capabilities and
`no_new_privs`. DNS is copied into a private mount so the eventual provider
client can still connect. The actor cannot remount host drives.

The actor probe attempts direct and symlink reads, recursive search,
`/proc/1/root` traversal, Windows mount access, and Graft retrieval of a
root-only sentinel. It also verifies actor writes and the native Claude CLI.
The attestation then starts the actual Claude CLI with restricted file tools,
explicit strict MCP configuration and a six-tool Graft allowlist. Its actor
home has no credential; the expected terminal event is authentication failure
with zero input/output tokens and zero cost. The startup event must show Graft
connected and no shell, web or delegation tool. This confirms the launch
configuration is parsed and loaded by Claude, rather than merely constructing
an argument list.

## Reproduce and check

On this WSL instance, Kali's 2025.1 image initially lacked its rotated archive
signing key. Refresh the keyring using [Kali's documented procedure](https://www.kali.org/blog/new-kali-archive-signing-key/)
and verify the published SHA-1 before `apt-get update`. Install
`build-essential` and `python3-dev`; Graft's tree-sitter dependencies require
native compilation. The pinned Node archive is verified against the matching
[Node release checksums](https://nodejs.org/en/download/archive/v22.22.0).

From the repository root in PowerShell, after installing the official native
[Claude Code Linux/WSL build](https://code.claude.com/docs/en/setup) as WSL
user `wsl` at version 2.1.273:

```powershell
wsl.exe -u root -- bash /mnt/c/Users/Bob/Desktop/Code/Claude/Orchestrator/tools/setup_worker_wsl.sh
python tools/worker_wsl_attestation.py
python tools/worker_wsl_attestation.py --check
```

The first command uses this checkout's current Windows path; on another
checkout, translate its absolute path with `wslpath` and pass that path. The
attestation computes the translated path automatically. It stages fresh
random sentinels, launches the actor probe and unauthenticated Claude startup,
then writes `test/results/2026-09-24-worker-n4-wsl-host.json`. `--check`
rejects a changed frozen N4 manifest, source file, runtime binary or evidence
digest. Its checks are pure validation; N5 must rerun the full probe, not rely
on a previously recorded pass.

## Limits and next integration

The native Claude actor has no login or API key. The zero-cost startup test
does not establish that an authenticated worker can complete or safely stop an
edit. `WorkerAdapter` still uses its generic local transport and explicitly
reports `enforcement_proven: false`; the WSL wrapper is not wired to
`TaskExecutor`. The N4 offline campaign remains fake-only. No N5 payment was
incurred or enabled by this work.

Before N5, add a WSL transport that stages only the selected actor package,
passes an admitted invocation through the wrapper, parses a matched receipt,
handles cancellation/unknown charges without replay, and runs the independent
grader only after the writer is stopped. Handle provider credentials without
copying host secrets into the actor package. Freeze that transport and its
configuration into the N5 manifest, rerun the same sentinel attacks through
the exact live launch path, and require the resulting attestation to match the
manifest at dispatch time. Authentication or budget authorisation cannot waive
a failed host check.
