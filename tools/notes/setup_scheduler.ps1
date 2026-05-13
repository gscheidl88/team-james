# Setup Windows Task Scheduler for Periodic Notes
# Run once as Administrator to register all tasks.
# Usage: powershell -ExecutionPolicy Bypass -File tools\notes\setup_scheduler.ps1

$VaultRoot   = "<WORKSPACE_ROOT>"
$Summarizer  = "$VaultRoot\tools\notes\notes_summarizer.py"
$UVPath      = (Get-Command uv -ErrorAction Stop).Source

function Register-NoteTask {
    param(
        [string]$TaskName,
        [string]$Description,
        [string]$Argument,
        [string]$TriggerType,   # "weekly" | "monthly"
        [string]$DayOfWeek,     # e.g. "Sunday"
        [int]$DayOfMonth,       # e.g. 1
        [string]$StartTime = "20:00"
    )

    $action = New-ScheduledTaskAction `
        -Execute $UVPath `
        -Argument "run `"$Summarizer`" $Argument" `
        -WorkingDirectory $VaultRoot

    if ($TriggerType -eq "weekly") {
        $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $DayOfWeek -At $StartTime
    } else {
        # Monthly: Daily trigger + script checks if it's the 1st of the month itself
        $trigger = New-ScheduledTaskTrigger -Daily -At $StartTime
    }

    $settings = New-ScheduledTaskSettingsSet `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType Interactive `
        -RunLevel Limited

    Register-ScheduledTask `
        -TaskName $TaskName `
        -TaskPath "\GerhardsAgentTeam\" `
        -Description $Description `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Force | Out-Null

    Write-Host "  Registered: $TaskName" -ForegroundColor Green
}

Write-Host ""
Write-Host "Setting up Gerhards Agent Team — Note Scheduler" -ForegroundColor Cyan
Write-Host ""

# Weekly summary — every Sunday at 20:00
Register-NoteTask `
    -TaskName    "WeeklyNoteSummary" `
    -Description "Generate weekly summary note from daily notes (every Sunday 20:00)" `
    -Argument    "--weekly" `
    -TriggerType "weekly" `
    -DayOfWeek   "Sunday" `
    -StartTime   "20:00"

# Monthly summary — 1st of each month at 08:00
Register-NoteTask `
    -TaskName    "MonthlyNoteSummary" `
    -Description "Generate monthly summary note (1st of month 08:00)" `
    -Argument    "--monthly" `
    -TriggerType "monthly" `
    -DayOfMonth  1 `
    -StartTime   "08:00"

# Annual summary — January 1st (via monthly trigger on Jan 1)
Register-NoteTask `
    -TaskName    "AnnualNoteSummary" `
    -Description "Generate annual summary note (January 1st 08:00)" `
    -Argument    "--annual" `
    -TriggerType "monthly" `
    -DayOfMonth  1 `
    -StartTime   "09:00"

Write-Host ""
Write-Host "Done! Tasks registered under \GerhardsAgentTeam\" -ForegroundColor Green
Write-Host "View in Task Scheduler: taskschd.msc" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Manual run examples:" -ForegroundColor Yellow
Write-Host "  uv run tools\notes\notes_summarizer.py --weekly" -ForegroundColor White
Write-Host "  uv run tools\notes\notes_summarizer.py --monthly" -ForegroundColor White
Write-Host "  uv run tools\notes\notes_summarizer.py --annual" -ForegroundColor White
