[CmdletBinding()]
param([switch]$Yes, [switch]$DryRun)

$ErrorActionPreference = 'Stop'
$installUrl = 'https://raw.githubusercontent.com/hassanvfx/clineflow/main/template/.clineflow/bin/install'
function Write-Plan([string]$Message) { Write-Host "  $Message" }
function Find-GitCommand { $c = Get-Command git -ErrorAction SilentlyContinue; if ($c) { return $c.Source }; $p = Join-Path ${env:ProgramFiles} 'Git\cmd\git.exe'; if (Test-Path $p) { return $p } }
function Find-GitBash { $c = Get-Command bash -ErrorAction SilentlyContinue; if ($c) { return $c.Source }; $p = Join-Path ${env:ProgramFiles} 'Git\bin\bash.exe'; if (Test-Path $p) { return $p } }
function Find-Curl { $c = Get-Command curl.exe -ErrorAction SilentlyContinue; if ($c) { return $c.Source }; $p = Join-Path ${env:ProgramFiles} 'Git\mingw64\bin\curl.exe'; if (Test-Path $p) { return $p } }

$git = Find-GitCommand; $bash = Find-GitBash; $curl = Find-Curl; $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
Write-Host 'ClineFlow prerequisite plan'
Write-Plan "OS: Windows ($(if ([Environment]::Is64BitOperatingSystem) { 'x64' } else { 'x86' }))"
Write-Plan "Git: $(if ($git) { 'available' } else { 'missing' })"
Write-Plan "Downloader: $(if ($curl) { 'curl available' } else { 'missing' })"
Write-Plan "Package manager: $(if ($winget) { 'winget' } else { 'not detected' })"
if (-not $git -or -not $bash -or -not $curl) {
  Write-Plan 'Action: install Git for Windows (includes Git Bash and curl)'
  Write-Plan 'Command: winget install --id Git.Git -e --source winget'
  if ($DryRun) { return }
  if (-not $winget) { Write-Warning 'Prerequisites are unresolved. Install Git for Windows manually, then rerun this command.'; return }
  if (-not $Yes) { $approval = Read-Host 'Approve this prerequisite installation? [y/N]'; if ($approval -notmatch '^(y|yes)$') { Write-Warning 'Prerequisites were not installed: approval declined.'; return } }
  try { & $winget.Source install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements } catch { Write-Warning "Prerequisite installation failed: $($_.Exception.Message). Install Git for Windows manually and rerun this command."; return }
  $git = Find-GitCommand; $bash = Find-GitBash; $curl = Find-Curl
}
if (-not $git -or -not $bash -or -not $curl) { Write-Warning 'Git, Git Bash, or curl is still unavailable. Install Git for Windows manually and rerun this command.'; return }
try { $installer = (Invoke-WebRequest -UseBasicParsing -Uri $installUrl).Content; $installer | & $bash -s -- --yes } catch { Write-Warning "ClineFlow prerequisite checks passed, but the core installer could not run: $($_.Exception.Message)" }
