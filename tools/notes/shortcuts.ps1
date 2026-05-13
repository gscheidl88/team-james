# Notes Summarizer — PowerShell Shortcuts
# Source this file or call functions directly.
# Usage: . .\tools\notes\shortcuts.ps1

$ScriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent
$VaultRoot  = (Resolve-Path "$ScriptDir\..\.." ).Path
$Summarizer = "$ScriptDir\notes_summarizer.py"

function New-WeeklySummary {
    param([string]$Date = (Get-Date -Format "yyyy-MM-dd"), [switch]$Overwrite)
    $args = @("--weekly", "--date", $Date)
    if ($Overwrite) { $args += "--overwrite" }
    Set-Location $VaultRoot
    uv run $Summarizer @args
}

function New-MonthlySummary {
    param([string]$Date = (Get-Date -Format "yyyy-MM-dd"), [switch]$Overwrite)
    $args = @("--monthly", "--date", $Date)
    if ($Overwrite) { $args += "--overwrite" }
    Set-Location $VaultRoot
    uv run $Summarizer @args
}

function New-AnnualSummary {
    param([string]$Date = (Get-Date -Format "yyyy-MM-dd"), [switch]$Overwrite)
    $args = @("--annual", "--date", $Date)
    if ($Overwrite) { $args += "--overwrite" }
    Set-Location $VaultRoot
    uv run $Summarizer @args
}
