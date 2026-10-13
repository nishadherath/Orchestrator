[CmdletBinding()]
param(
    # Evaluation actors and result copies have a separate, opt-in index.
    [switch]$Corpus
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$graftCommand = (Get-Command graft.cmd -CommandType Application -ErrorAction Stop |
    Select-Object -First 1).Source

if ($Corpus) {
    $contextDir = Join-Path $repoRoot '.graft/corpus'
    $scope = @('--only-dir', 'test/fixtures', '--only-dir', 'test/results')
    # The parent directory is already ignored; do not re-admit local backups
    # or corpus cards to broad ripgrep searches through an .ignore override.
    $ignoreFlags = @('--no-gitignore', '--no-ignore')
} else {
    $contextDir = Join-Path $repoRoot 'graft'
    $scope = @('--only-dir', 'src', '--only-dir', 'tools', '--only-dir', 'test/harness')
    $ignoreFlags = @()
}

# Explicit scope is required for manual builds. Graft 0.21.1 retains it for
# automatic query refreshes, but a bare manual build can widen the index.
& $graftCommand --dir $contextDir build @scope @ignoreFlags $repoRoot
if ($LASTEXITCODE -ne 0) {
    throw "Graft structural refresh failed with exit code $LASTEXITCODE."
}
