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
the same login method and subscription. No token value was displayed.

## Important limitation

The N5 test worker uses `tools/worker_wsl_namespace.sh`, which deliberately
sets a separate actor `HOME` with `env -i`. The interactive `wsl` account's
login therefore **does not authenticate that isolated worker**. Do not copy
this file into an actor directory or weaken the namespace. N5 live dispatch
remains closed until a separate, attested credential-delivery path is built
and the manifest-bound spend gate is satisfied. See
[the N5 screen contract](WORKER-N5-SCREEN.md).
