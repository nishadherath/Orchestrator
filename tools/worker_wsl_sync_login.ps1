# Promote a fresh Claude.ai WSL login and refresh its git-ignored local backup.
# This sends no model request and never writes credential bytes to the console.
param(
    [string]$Distro = 'kali-linux'
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$backup = Join-Path $root 'local-auth\claude-code\.credentials.json'
$relative = 'local-auth/claude-code/.credentials.json'
$source = "\\wsl.localhost\$Distro\home\wsl\.claude\.credentials.json"
$auth = '/opt/orchestrator-worker-runtime/worker_wsl_auth.py'

if (-not (Test-Path -LiteralPath $backup -PathType Leaf)) {
    throw 'Existing git-ignored credential backup is required; see docs/CLAUDE-CODE-WSL-AUTH.md'
}
& git -c "safe.directory=$root" check-ignore --quiet -- $relative
if ($LASTEXITCODE -ne 0) { throw 'Credential backup is not git-ignored' }
if (@(& git -c "safe.directory=$root" ls-files -- $relative).Count -ne 0) {
    throw 'Credential backup is tracked by Git'
}
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw 'WSL user credential is unavailable through the WSL filesystem share'
}
$linuxRoot = & wsl.exe -d $Distro -u root -- wslpath -a ($root -replace '\\', '/')
if ($LASTEXITCODE -ne 0 -or -not $linuxRoot) {
    throw 'Repository path is unavailable from WSL'
}
$stage = $linuxRoot.Trim().TrimEnd('/') + '/tools/worker_wsl_stage.sh'

# Stage the current, root-owned helper before asking it to inspect the login.
& wsl.exe -d $Distro -u root -- bash $stage *> $null
if ($LASTEXITCODE -ne 0) { throw 'WSL runtime staging failed' }
& wsl.exe -d $Distro -u root -- python3 $auth sync
if ($LASTEXITCODE -ne 0) {
    throw 'Fresh WSL login was not promoted; authenticate with claude auth login --claudeai'
}
& wsl.exe -d $Distro -u root -- python3 $auth inspect
if ($LASTEXITCODE -ne 0) { throw 'Private WSL credential store did not validate' }

$aclBefore = (Get-Acl -LiteralPath $backup).Sddl
[IO.File]::WriteAllBytes($backup, [IO.File]::ReadAllBytes($source))
if ((Get-Acl -LiteralPath $backup).Sddl -ne $aclBefore) {
    throw 'Credential backup ACL changed; inspect it before proceeding'
}
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $source).Hash -ne
    (Get-FileHash -Algorithm SHA256 -LiteralPath $backup).Hash) {
    throw 'Credential backup differs from the fresh WSL login'
}
& git -c "safe.directory=$root" check-ignore --quiet -- $relative
if ($LASTEXITCODE -ne 0) { throw 'Credential backup became visible to Git' }
Write-Output 'PASS: fresh WSL subscription login promoted; ignored backup matches; ACL unchanged'
