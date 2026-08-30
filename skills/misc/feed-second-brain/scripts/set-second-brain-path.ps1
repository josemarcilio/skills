#Requires -Version 5.1
param(
  [Parameter(Mandatory = $true)]
  [string]$Path
)

$resolved = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)
if (-not (Test-Path -LiteralPath $resolved -PathType Container)) {
  Write-Error "Directory does not exist: $resolved"
  exit 1
}

[Environment]::SetEnvironmentVariable("SECOND_BRAIN_PATH", $resolved, "User")
$env:SECOND_BRAIN_PATH = $resolved
Write-Host "Set user SECOND_BRAIN_PATH=$resolved"

if ($env:CLAUDE_ENV_FILE) {
  Add-Content -LiteralPath $env:CLAUDE_ENV_FILE -Value "export SECOND_BRAIN_PATH=`"$resolved`""
  Write-Host "Appended export to CLAUDE_ENV_FILE=$($env:CLAUDE_ENV_FILE)"
}

Write-Host "Restart Cursor (or open a new shell) so agents see the variable. For session inject, see setup.md (Cursor)."
