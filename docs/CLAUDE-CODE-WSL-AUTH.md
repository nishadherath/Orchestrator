# Local Claude Code login in Kali WSL

Verified on 2026-09-25 with Claude Code 2.1.273. This is a machine-local
operator procedure for using the existing **Claude.ai Max subscription** in
the default `wsl` account of the `kali-linux` WSL distribution. It does not
use an Anthropic API key or make a model request.

## Locations and boundaries

| Purpose | Path |
| --- | --- |
| Windows Claude Code source | `C:\Users\Bob\.claude\.credentials.json` |
| Git-ignored project backup | `local-auth/claude-code/.credentials.json` |
| WSL `wsl` account destination | `/home/wsl/.claude/.credentials.json` |

The backup is a **live OAuth secret**, including refresh material. It is
excluded by this repository's `.gitignore` and `.ignore`. Keep it out of
commits, patches, Graft queries, screenshots, transcripts and the
redistributable. Git ignore alone does not restrict local file reads; the
Windows copy must retain a restrictive ACL, and the WSL copy must be owned by
`wsl` with mode `0600`. The backup is a snapshot, not a synchronised login:
refresh it from the Windows source before repeating the transfer.

Claude Code's [authentication documentation](https://code.claude.com/docs/en/authentication)
places the Windows and Linux credentials at these respective paths. Its
[environment variable reference](https://code.claude.com/docs/en/env-vars)
states that `ANTHROPIC_API_KEY` overrides the subscription in `-p` mode.

## Repeat the transfer

Run these commands from PowerShell on this machine, at the repository root.
Do not print or open the credential file. Stop if the source login is not
`claude.ai`, if the source file is missing, or if any command fails.

```powershell
$status = claude auth status --json | ConvertFrom-Json
if (-not $status.loggedIn -or $status.authMethod -ne 'claude.ai') {
    throw 'Windows Claude Code subscription login is unavailable'
}
$source = 'C:\Users\Bob\.claude\.credentials.json'
$backupDir = Join-Path (Get-Location) 'local-auth\claude-code'
$backup = Join-Path $backupDir '.credentials.json'
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw 'Windows Claude Code credential file is missing'
}
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
Copy-Item -LiteralPath $source -Destination $backup -Force
$aclArgs = @(
    'BOBS-X1\Bob:(OI)(CI)(F)',
    'BOBS-X1\CodexSandboxUsers:(OI)(CI)(RX)',
    'NT AUTHORITY\SYSTEM:(OI)(CI)(F)',
    'BUILTIN\Administrators:(OI)(CI)(F)'
)
icacls (Join-Path (Get-Location) 'local-auth') /inheritance:r /grant:r $aclArgs
if ($LASTEXITCODE -ne 0) { throw 'Backup directory ACL failed' }
icacls $backupDir /inheritance:r /grant:r $aclArgs
if ($LASTEXITCODE -ne 0) { throw 'Credential directory ACL failed' }
icacls $backup /inheritance:r /grant:r @(
    'BOBS-X1\Bob:(F)',
    'BOBS-X1\CodexSandboxUsers:(RX)',
    'NT AUTHORITY\SYSTEM:(F)',
    'BUILTIN\Administrators:(F)'
)
if ($LASTEXITCODE -ne 0) { throw 'Credential file ACL failed' }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash -ne
    (Get-FileHash -Algorithm SHA256 -LiteralPath $backup).Hash) {
    throw 'Project backup differs from Windows source'
}
```

Check that the project backup is ignored and that its ACL grants access only
to the same local principals as the Windows source. The verification commands
show paths, permissions and status, never credential contents:

```powershell
git check-ignore -v local-auth/claude-code/.credentials.json
if (git ls-files local-auth) { throw 'A credential backup path is tracked by Git' }
icacls local-auth\claude-code\.credentials.json
wsl.exe -d kali-linux -u root -- install -d -m 700 -o wsl -g wsl /home/wsl/.claude
wsl.exe -d kali-linux -u root -- install -m 600 -o wsl -g wsl /mnt/c/Users/Bob/Desktop/Code/Claude/Orchestrator/local-auth/claude-code/.credentials.json /home/wsl/.claude/.credentials.json
wsl.exe -d kali-linux -u root -- cmp -s /mnt/c/Users/Bob/Desktop/Code/Claude/Orchestrator/local-auth/claude-code/.credentials.json /home/wsl/.claude/.credentials.json
if ($LASTEXITCODE -ne 0) { throw 'WSL credential copy differs from project backup' }
$ownership = wsl.exe -d kali-linux -u root -- stat -c '%U:%a' /home/wsl/.claude/.credentials.json
if ($LASTEXITCODE -ne 0 -or $ownership.Trim() -ne 'wsl:600') {
    throw 'WSL credential ownership or permissions are wrong'
}
$wslStatus = wsl.exe -d kali-linux -u wsl -- env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN -u CLAUDE_CODE_OAUTH_TOKEN /opt/orchestrator-worker-runtime/bin/claude auth status --json | ConvertFrom-Json
if (-not $wslStatus.loggedIn -or $wslStatus.authMethod -ne 'claude.ai') {
    throw 'WSL Claude Code subscription login was not recognised'
}
$wslStatus | Select-Object loggedIn, authMethod, subscriptionType
```

On 2026-09-25, the Windows status was `loggedIn=true`,
`authMethod=claude.ai`, `subscriptionType=max`. The source had a
`claudeAiOauth` section with access and refresh tokens. The copy to WSL
matched byte-for-byte, had owner `wsl` and mode `600`, and WSL status reported
the same login method and subscription. No token value was displayed. **Auth
status does not prove that the access token is still usable.** Check its
`expiresAt` field against the current epoch time before starting a worker.

## Isolated worker credential handoff

The N5 worker has a separate actor `HOME` and a cleared environment. Its
launcher takes a private copy from a **root-owned master** at
`/var/lib/orchestrator-worker-n4/auth/.credentials.json`, binds that copy at
`/run/claude-auth` inside one UID 65534 mount namespace, and points
`CLAUDE_CONFIG_DIR` there. The credential is outside the actor package, Graft
index and Windows mounts. Claude Code runs with `--restricted`, no shell tool,
and explicit Read/Edit denies for the auth mount. The root launcher serialises
invocations and commits a refreshed private copy only after the process stops
and validates the master has not changed. An interrupted or malformed copy
blocks further work until reconciled. Never copy a credential into an actor
directory or weaken the namespace.

The root store rejects an access or refresh token with less than five minutes
of stated validity, even when `claude auth status` says logged in. If WSL login
needs renewal, run `wsl.exe -d kali-linux -u wsl -- /opt/orchestrator-worker-runtime/bin/claude auth login --claudeai`
from PowerShell and complete the browser flow. On this host the pending login
emptied the WSL user's two token fields before sign-in finished. Do not copy
that intermediate file or run a worker until login completes. The root master
and ignored backup retained their earlier values. The fresh Claude.ai email
login and checked helper completed successfully on 2026-09-25; the new WSL
login, root master and ignored backup later matched by digest, with the backup
ACL unchanged. The seven-check paid Read-denial sentinel passed afterward.
The ordinary WSL user's `PATH` does not include this Claude binary, so use
the absolute path above. `claude auth status` on Windows can report logged in
while the saved token is too close to expiry for the isolated worker.

After sign-in, run the checked helper from the repository root. It stages the
current WSL runtime, validates and promotes the fresh login, then updates the
existing ignored backup without changing its ACL. It prints no credential:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/worker_wsl_sync_login.ps1
```

The equivalent manual operations are below for diagnosis. None prints a token:

```powershell
wsl.exe -d kali-linux -u root -- bash /mnt/c/Users/Bob/Desktop/Code/Claude/Orchestrator/tools/worker_wsl_stage.sh
if ($LASTEXITCODE -ne 0) { throw 'WSL runtime staging failed' }
wsl.exe -d kali-linux -u root -- python3 /opt/orchestrator-worker-runtime/worker_wsl_auth.py sync
if ($LASTEXITCODE -ne 0) { throw 'Fresh WSL login was not promoted to the root store' }
wsl.exe -d kali-linux -u root -- python3 /opt/orchestrator-worker-runtime/worker_wsl_auth.py inspect
if ($LASTEXITCODE -ne 0) { throw 'Private credential store is not ready' }
```

For the first setup, `provision` creates the root store from the valid WSL
login:

```powershell
wsl.exe -d kali-linux -u root -- python3 /opt/orchestrator-worker-runtime/worker_wsl_auth.py provision
if ($LASTEXITCODE -ne 0) { throw 'Initial root credential provision failed' }
```

Use `sync` only after the store already exists. If performing the manual path
after WSL reauthentication, refresh the existing git-ignored project backup
from the new WSL user login, preserving its Windows ACL. This is a binary copy;
do not print either file:

```powershell
$wslCredential = '\\wsl.localhost\kali-linux\home\wsl\.claude\.credentials.json'
$backup = Join-Path (Get-Location) 'local-auth\claude-code\.credentials.json'
if (-not (Test-Path -LiteralPath $wslCredential -PathType Leaf) -or
    -not (Test-Path -LiteralPath $backup -PathType Leaf)) {
    throw 'Credential source or existing ignored backup is unavailable'
}
[IO.File]::WriteAllBytes($backup, [IO.File]::ReadAllBytes($wslCredential))
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $wslCredential).Hash -ne
    (Get-FileHash -Algorithm SHA256 -LiteralPath $backup).Hash) {
    throw 'Ignored backup differs from WSL login'
}
git check-ignore -v local-auth/claude-code/.credentials.json
if (git ls-files local-auth) { throw 'Credential backup path became tracked' }
icacls $backup
```

Do not use the backup to overwrite a newer WSL login or root master.
`tools/worker_wsl_subscription_attestation.py` then performs a
provider-free status check inside the actual actor namespace and binds it to
the N4 host attestation. This verifies login visibility, not a served model.

On 2026-09-25, a one-call Sonnet-low denial sentinel reached Claude Code with
an **expired** access token. Claude Code returned a synthetic result with zero
tokens and USD 0 reported API-equivalent cost, then emptied both token fields
in its private copy. The root store rejected that copy and kept the master and
WSL user login unchanged. The failed copy was removed only with
`worker_wsl_auth.py discard-empty inv-<32-hex>`, which verifies both fields
are empty and the master is unchanged. This command must never be used on a
partially refreshed or usable copy. The result does not establish paid worker
read denial or model identity; those checks must be repeated after fresh
sign-in. See [the N5 screen contract](WORKER-N5-SCREEN.md).
