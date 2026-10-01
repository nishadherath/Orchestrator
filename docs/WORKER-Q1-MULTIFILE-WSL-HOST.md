# Q1 multi-file WSL actor boundary

Status: experimental host qualification, 2026-09-25. The [Q1 result](stage-results/worker-q1.md)
and [machine-readable attestation](../test/results/2026-09-25-worker-q1-wsl-host.json)
record the observed checks. This path makes no provider request and does not
replace the frozen N5 single-file transport.

## Contract

Q1 accepts a root-owned, private package directly under
`/var/lib/orchestrator-worker-n4/seed`. Its separate root-owned manifest has
schema version 1 and lists **every** public file with its relative path,
SHA-256 and `editable` boolean. It must name 2-8 existing editable files,
at most 200 total files and at most 5 MB of source bytes. An individual file
is limited to 1 MB. Paths are relative, use portable path components and
cannot enter `.home`, `.cache`, `.scratch`, `graft` or `.gitignore`. Symlinks,
hardlinks, special files, undeclared files and a changed source digest fail
staging. This first version does not permit new source files or preserve
executable modes.

`tools/worker_wsl_q1.py` stages the enumerated files under a fresh `q1-`
actor. Parent directories and protected files remain root-owned; only the
named existing files belong to UID 65534. The actor can edit their content
but cannot create files in the source tree. Private scratch, cache and Graft
directories remain writable. The root-owned manifest is outside the actor.

`tools/worker_wsl_namespace_q1.sh` is a versioned copy of the N4 namespace
launcher. It retains mount and PID isolation, the private actor-parent
overlay, hidden Windows mounts and interop sockets, a cleared environment and
the UID/capability drop. It rejects the subscription flag. The launcher
writes a root-owned start record before `unshare` and a stop record only after
the namespace exits. Q1 uses a separate installed binary, so the N5 launcher
and its historical hashes stay unchanged.

Collection rechecks actor and source inventory, ownership, hashes, protected
content, file limits and the matching stop record. It writes a new private
snapshot at `qualification-collected/<actor-name>` and reports every changed
editable path and final hash. It refuses a duplicate output. The source
package is never overwritten. If the launcher stops ambiguously, there is
no stop record and collection fails closed. A real paid transport must also
bind its terminal provider receipt before it may grade or release a budget
hold; Q1 does not claim that paid path is qualified.

The actor receives only its staged package. Graft builds inside the actor
namespace against that root; the Q1 probe verifies both editable modules are
findable while the root-only evaluator marker and a parent escape are absent.
The existing N4 hidden grader remains outside this actor. Q2 must build a
multi-file public verifier and hidden grader before pilot material is scored.

## Reproduce

Run from the repository root in PowerShell. The installer writes only new Q1
files to the root-owned WSL runtime and leaves the N5 binaries alone.

```powershell
wsl.exe -u root -- bash /mnt/c/Users/Bob/Desktop/Code/Claude/Orchestrator/tools/worker_wsl_q1_install.sh
python tools/worker_wsl_q1_attestation.py
python tools/worker_wsl_q1_attestation.py --check
wsl.exe -u root -- python3 /opt/orchestrator-worker-runtime/transport-probe.py
```

On a different checkout, translate its absolute path for the first command.
The attestation requires the existing N4 host evidence to remain current,
compares installed Q1 hashes with source, executes 38 real WSL checks, and
exercises the durable root budget with reserve-before-launch, zero-cost
settlement, duplicate-launch denial and an uncertain-charge hold. It records
zero provider calls. The last command independently retests the N5
single-file transport. The WSL probe's temporary seed, actor and collected
directories are removed after each run; a failed or ambiguous launcher is
never treated as evidence of a safe collection.

The attestation proves this provider-free boundary on the named local host.
It does not prove Claude's multi-file Edit behaviour, end-to-end paid charge
reconciliation, public acceptance or hidden grading for the new package.
