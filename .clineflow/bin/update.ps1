[CmdletBinding()]
param([switch]$Yes, [switch]$DryRun)

$ErrorActionPreference = 'Stop'
$baseUrl = if ($env:CLINEFLOW_BASE_URL) { $env:CLINEFLOW_BASE_URL } else { 'https://raw.githubusercontent.com/hassanvfx/clineflow/main/template' }
$bashCommand = Get-Command bash -ErrorAction SilentlyContinue
$bashPath = if ($bashCommand) { $bashCommand.Source } else { $null }
if (-not $bashPath) {
  $gitBash = Join-Path ${env:ProgramFiles} 'Git\bin\bash.exe'
  if (Test-Path $gitBash) { $bashPath = $gitBash }
}
if (-not $bashPath) { throw 'Git Bash is required. Install Git for Windows, then rerun the updater.' }
$updateUrl = "$baseUrl/.clineflow/bin/update"
$updateUri = [Uri]$updateUrl
$script = if ($updateUri.IsFile) { Get-Content -Raw -LiteralPath $updateUri.LocalPath } else { (Invoke-WebRequest -UseBasicParsing -Uri $updateUrl).Content }
$arguments = @()
if ($Yes) { $arguments += '--yes' }
if ($DryRun) { $arguments += '--dry-run' }
$script | & $bashPath -s -- @arguments
if ($LASTEXITCODE -ne 0) { throw "ClineFlow update failed with exit code $LASTEXITCODE" }
