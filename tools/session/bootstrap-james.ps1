# bootstrap-james.ps1
# Windows Terminal bootstrap for the James alias.

param(
    [string]$Prompt = "",
    [string]$TeamDir = "<WORKSPACE_ROOT>"
)

$env:JAMES_WT_BOOTSTRAPPED = "1"

if (-not (Test-Path $TeamDir)) {
    throw "Agent team directory not found: $TeamDir"
}

Set-Location $TeamDir

if (-not (Get-Command Invoke-James -ErrorAction SilentlyContinue)) {
    $allHostsProfile = $PROFILE.CurrentUserAllHosts
    if (Test-Path $allHostsProfile) {
        . $allHostsProfile
    }
}

if (-not (Get-Command Invoke-James -ErrorAction SilentlyContinue)) {
    throw "Invoke-James is not available. Expected profile at $($PROFILE.CurrentUserAllHosts)."
}

Invoke-James -Prompt $Prompt
