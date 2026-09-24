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
`/var/lib/orchestrator-worker-n4`. The evaluator is root-only (mode 700).
`tools/worker_wsl_materialize.py` copies exactly `app.py`, `public_check.py`,
`ISSUE.md` and `acceptance.json` into a root-owned actor directory. Only the
existing `app.py` and private cache/scratch directories are writable by the
actor. Executor state and oracle files are never staged.
`tools/worker_wsl_namespace.sh`
starts a private mount and PID namespace, mounts a new `/proc`, removes the
Windows C/D and WSL drivers mounts, covers WSL interop sockets and other host
integration mounts, and replaces `/init` with `/dev/null`. It then clears the
inherited environment and drops to UID/GID 65534 with no capabilities and
`no_new_privs`. DNS is copied into a private mount so the eventual provider
client can still connect. The actor cannot remount host drives.

The actor probe attempts direct and symlink reads, recursive search,
`/proc/1/root` traversal, Windows mount access, and Graft retrieval of a
root-only sentinel. It also verifies that the actor can edit `app.py` but
cannot write the acceptance file or create a new root-level file. A separate
transport probe checks materialization, stopped-writer collection, protected
file tampering and source-race rejection.
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
then writes `test/results/2026-09-24-worker-n4-wsl-host.json`. The 40 checks
include a Windows-to-WSL launch through `tools/worker_wsl_transport.py`, with
Graft registered by Claude and a zero-token authentication failure. A second
Windows actor round trip verifies that an allowed `app.py` edit is collected
while the protected acceptance file remains unchanged.
`--check`
rejects a changed frozen N4 manifest, source file, runtime binary or evidence
digest. Its checks are pure validation; N5 must rerun the full probe, not rely
on a previously recorded pass.

`python tools/worker_wsl_adapter_probe.py` additionally invokes the
`TaskExecutor`-compatible `WslWorkerAdapter`. It verifies the matched receipt,
stopped writer, unchanged source and zero provider charge. This test also has
no credentials and cannot measure an authenticated model response.

## Limits and next integration

The native Claude actor has no login or API key. The zero-cost startup test
does not establish that an authenticated worker can complete or safely stop an
edit. The generic `WorkerAdapter` still reports `enforcement_proven: false`.
The project-side `WslWorkerAdapter` reports the attested host capability and
can be passed to `TaskExecutor`, but the N4 campaign remains fake-only. No N5
payment was incurred or enabled by this work.

Before paid N5 execution, finish the campaign runner and its spend gate, choose
and configure the provider credential method without copying host secrets into
the actor package, and freeze the final N5 manifest. The runner must use
`TaskExecutor`, reconcile cancellation and unknown charges without replay, and
grade only after a stopped writer. Repeat the sentinel probe through that
final launch path and require its attestation at dispatch time. Authentication
or budget authorisation cannot waive a failed host check.
