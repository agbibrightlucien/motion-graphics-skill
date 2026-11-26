<#
.SYNOPSIS
  Install the clean-motion-video skill into one or more AI coding agents (Windows).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File install\install.ps1 -Agent claude,codex,antigravity -Scope global
  powershell -ExecutionPolicy Bypass -File install\install.ps1 -Agent all -Scope project -ProjectPath C:\videos
#>
param(
  [string[]]$Agent = @("claude"),
  [ValidateSet("global", "project")][string]$Scope = "global",
  [string]$ProjectPath = (Get-Location).Path,
  [switch]$SkipHyperFrames,
  [switch]$Yes
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$src = Join-Path $repo "skills\clean-motion-video"
if (-not (Test-Path (Join-Path $src "SKILL.md"))) { throw "Can't find skills\clean-motion-video\SKILL.md next to this script." }

$global = @{
  claude      = "$HOME\.claude\skills"
  codex       = "$HOME\.agents\skills"
  antigravity = "$HOME\.gemini\config\skills"
  gemini      = "$HOME\.gemini\skills"
  cursor      = "$HOME\.cursor\skills"
  copilot     = "$HOME\.copilot\skills"
  opencode    = "$HOME\.config\opencode\skills"
  windsurf    = "$HOME\.codeium\windsurf\skills"
}
$project = @{
  claude = ".claude\skills"; codex = ".agents\skills"; antigravity = ".agents\skills"; gemini = ".agents\skills"
  cursor = ".agents\skills"; copilot = ".agents\skills"; opencode = ".agents\skills"; windsurf = ".windsurf\skills"
}
$cliName = @{ claude = "claude-code"; codex = "codex"; antigravity = "antigravity"; gemini = "gemini-cli"; cursor = "cursor"
              copilot = "github-copilot"; opencode = "opencode"; windsurf = "windsurf" }

$agents = @()
foreach ($a in $Agent) { $agents += ($a -split ",") | ForEach-Object { $_.Trim().ToLower() } | Where-Object { $_ } }
if ($agents -contains "all") { $agents = @($global.Keys) }

$targets = @()
foreach ($a in $agents) {
  if (-not $global.ContainsKey($a)) { Write-Warning "Unknown agent '$a' (use: $($global.Keys -join ', '), all)"; continue }
  $base = if ($Scope -eq "global") { $global[$a] } else { Join-Path $ProjectPath $project[$a] }
  if ($targets -notcontains $base) { $targets += $base }
}

foreach ($base in $targets) {
  $dst = Join-Path $base "clean-motion-video"
  New-Item -ItemType Directory -Force $base | Out-Null
  if (Test-Path $dst) {
    $bak = "$dst.bak-" + (Get-Date -Format "yyyyMMdd-HHmmss")
    Move-Item $dst $bak
    Write-Host "  previous version moved to $bak"
  }
  Copy-Item $src $dst -Recurse
  Write-Host "installed -> $dst"
}

if (-not $SkipHyperFrames) {
  $doIt = $Yes
  if (-not $Yes) { $doIt = (Read-Host "Install the HyperFrames skills too (recommended)? [Y/n]") -notmatch "^[nN]" }
  if ($doIt) {
    $flags = @("--yes", "skills", "add", "heygen-com/hyperframes")
    if ($Scope -eq "global") { $flags += "-g" }
    foreach ($a in $agents) { if ($cliName.ContainsKey($a)) { $flags += @("-a", $cliName[$a]) } }
    if ($Yes) { $flags += "-y" }
    Write-Host "npx $($flags -join ' ')"
    if ($Scope -eq "project") { Push-Location $ProjectPath }
    try { & npx @flags } catch { Write-Warning "HyperFrames skills install failed: $_ (the skill still works through npx)" }
    if ($Scope -eq "project") { Pop-Location }
  }
}

$py = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $py) { $py = (Get-Command py -ErrorAction SilentlyContinue) }
if ($py -and $targets.Count -gt 0) {
  & $py.Source -I -u (Join-Path (Join-Path $targets[0] "clean-motion-video") "scripts\cmv.py") setup
} else {
  Write-Warning "Python not found: install Python 3.9+, then run: python -I -u <skill>\scripts\cmv.py setup"
}
Write-Host "`nDone. Start a new agent session and ask for a video (or call the skill: /clean-motion-video, `$clean-motion-video)."
