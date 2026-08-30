#Requires -Version 5.1
param(
  [string]$Path = ""
)

$ErrorActionPreference = "Stop"
$SkillRoot = Split-Path $PSScriptRoot -Parent

$ReminderTemplate = Join-Path $SkillRoot "templates\reminder-block.md"
$UserRuleTemplate = Join-Path $SkillRoot "templates\cursor-user-rule.txt"

function Get-SecondBrainPath {
  param([string]$Override)
  if ($Override) { return $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Override) }
  $fromSession = $env:SECOND_BRAIN_PATH
  if ($fromSession) { return $fromSession.TrimEnd('\') }
  $fromUser = [Environment]::GetEnvironmentVariable("SECOND_BRAIN_PATH", "User")
  if ($fromUser) { return $fromUser.TrimEnd('\') }
  return $null
}

function Merge-MarkedBlock {
  param(
    [string]$FilePath,
    [string]$BlockContent
  )

  $dir = Split-Path $FilePath -Parent
  if (-not (Test-Path $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
  }

  $begin = "<!-- feed-second-brain:begin -->"
  $end = "<!-- feed-second-brain:end -->"
  $block = $BlockContent.TrimEnd() + "`r`n"

  if (Test-Path $FilePath) {
    $existing = Get-Content -LiteralPath $FilePath -Raw
    if ($existing -match '(?s)<!-- feed-second-brain:begin -->.*?<!-- feed-second-brain:end -->') {
      $updated = [regex]::Replace($existing, '(?s)<!-- feed-second-brain:begin -->.*?<!-- feed-second-brain:end -->', $block.TrimEnd())
      Set-Content -LiteralPath $FilePath -Value $updated -NoNewline
      Write-Host "Updated markers in $FilePath"
      return
    }
    if (-not $existing.EndsWith("`n")) { $existing += "`r`n" }
    Set-Content -LiteralPath $FilePath -Value ($existing + "`r`n" + $block) -NoNewline
    Write-Host "Appended block to $FilePath"
    return
  }

  Set-Content -LiteralPath $FilePath -Value $block
  Write-Host "Created $FilePath"
}

$brainPath = Get-SecondBrainPath -Override $Path
if (-not $brainPath -or -not (Test-Path -LiteralPath $brainPath -PathType Container)) {
  Write-Error "SECOND_BRAIN_PATH is missing or not a directory. Pass -Path or run set-second-brain-path.ps1 first."
  exit 1
}

$reminder = Get-Content -LiteralPath $ReminderTemplate -Raw
$userRule = Get-Content -LiteralPath $UserRuleTemplate -Raw

# Claude
$claudeMd = Join-Path $env:USERPROFILE ".claude\CLAUDE.md"
Merge-MarkedBlock -FilePath $claudeMd -BlockContent $reminder

# Cursor support files
$cursorDir = Join-Path $env:USERPROFILE ".cursor\feed-second-brain"
New-Item -ItemType Directory -Path $cursorDir -Force | Out-Null
Set-Content -LiteralPath (Join-Path $cursorDir "reminder.md") -Value $reminder.TrimEnd()
Set-Content -LiteralPath (Join-Path $cursorDir "user-rule.txt") -Value $userRule.TrimEnd()
Write-Host "Wrote $cursorDir\reminder.md and user-rule.txt"

# Cursor sessionStart hook (env inject)
$cursorRoot = Join-Path $env:USERPROFILE ".cursor"
$hooksDir = Join-Path $cursorRoot "hooks"
New-Item -ItemType Directory -Path $hooksDir -Force | Out-Null

$hookScript = Join-Path $hooksDir "inject-second-brain-path.ps1"
@'
param()
$path = $env:SECOND_BRAIN_PATH
if (-not $path) {
  $path = [Environment]::GetEnvironmentVariable('SECOND_BRAIN_PATH', 'User')
}
if (-not $path) {
  Write-Output '{}'
  exit 0
}
$escaped = $path -replace '\\', '\\' -replace '"', '\"'
Write-Output "{`"env`":{`"SECOND_BRAIN_PATH`":`"$escaped`"}}"
exit 0
'@ | Set-Content -LiteralPath $hookScript -Encoding UTF8

$hooksJsonPath = Join-Path $cursorRoot "hooks.json"
$hookEntry = @{
  command = "./hooks/inject-second-brain-path.ps1"
}
$desired = @{
  version = 1
  hooks = @{
    sessionStart = @($hookEntry)
  }
}

if (Test-Path $hooksJsonPath) {
  $raw = Get-Content -LiteralPath $hooksJsonPath -Raw
  try {
    $existing = $raw | ConvertFrom-Json
  } catch {
    Write-Warning "Could not parse hooks.json; skipping hook merge."
    $existing = $null
  }
  if ($existing) {
    if (-not $existing.hooks) { $existing | Add-Member -NotePropertyName hooks -NotePropertyValue @{} }
    if (-not $existing.hooks.sessionStart) {
      $existing.hooks | Add-Member -NotePropertyName sessionStart -NotePropertyValue @() -Force
    }
    $already = @($existing.hooks.sessionStart) | Where-Object { $_.command -match 'inject-second-brain-path' }
    if (-not $already) {
      $existing.hooks.sessionStart = @($existing.hooks.sessionStart) + @($hookEntry)
    }
    if (-not $existing.version) { $existing | Add-Member -NotePropertyName version -NotePropertyValue 1 -Force }
    ($existing | ConvertTo-Json -Depth 10) | Set-Content -LiteralPath $hooksJsonPath
    Write-Host "Merged sessionStart hook in $hooksJsonPath"
  }
} else {
  ($desired | ConvertTo-Json -Depth 10) | Set-Content -LiteralPath $hooksJsonPath
  Write-Host "Created $hooksJsonPath"
}

# Manifest
$manifest = @{
  skill = "feed-second-brain"
  version = "0.2.1"
  secondBrainPath = $brainPath
  installedAt = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
  targets = @("claude-claude.md", "cursor-reminder", "cursor-user-rule-snippet", "cursor-sessionStart-hook")
} | ConvertTo-Json -Depth 5
Set-Content -LiteralPath (Join-Path $cursorDir "installed.json") -Value $manifest

Write-Host ""
Write-Host "feed-second-brain init complete."
Write-Host "  SECOND_BRAIN_PATH=$brainPath"
Write-Host "  Claude: $claudeMd"
Write-Host "  Cursor: paste ~/.cursor/feed-second-brain/user-rule.txt into Settings -> Rules -> User Rules (once)."
Write-Host "  Restart Cursor so sessionStart hook and user env apply."
