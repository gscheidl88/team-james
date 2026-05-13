# start-session.ps1
# Session start preflight — ensures recoverability before work begins.

param(
    [string]$VaultRoot = "<WORKSPACE_ROOT>",
    [string]$SessionStateRoot = "",
    [string]$SessionStateBase = "~\.copilot\session-state",
    [string]$Task = ""
)

. (Join-Path $PSScriptRoot "session-lifecycle.ps1")

Set-Location $VaultRoot

Write-Host ""
Write-Host "  ─────────────────────────────────────────" -ForegroundColor DarkCyan
Write-Host "  Session Start Preflight" -ForegroundColor Cyan
Write-Host "  ─────────────────────────────────────────" -ForegroundColor DarkCyan

$notePath = Ensure-DailyNote -VaultRoot $VaultRoot
Initialize-SessionScratchpad -VaultRoot $VaultRoot -SessionStateRoot $SessionStateRoot -Task $Task
Invoke-MemoryWarmup -VaultRoot $VaultRoot
$agentTrace = Invoke-AgentTraceStatus -VaultRoot $VaultRoot
$delegationAudit = Invoke-DelegationAudit -VaultRoot $VaultRoot
Invoke-MemoryQA -VaultRoot $VaultRoot
$guardStatus = Invoke-MemoryGuard -VaultRoot $VaultRoot -SessionStateRoot $SessionStateRoot -SessionStateBase $SessionStateBase
$knowledgeStatus = Invoke-KnowledgeReview -VaultRoot $VaultRoot
Write-LifecycleHistory -VaultRoot $VaultRoot -SessionStateRoot $SessionStateRoot -EventType "preflight_complete" -SafeHandover:$false -Status $guardStatus -Note "Session preflight completed." -Artifacts @{ daily_note = $notePath }

if ($guardStatus -in @("degraded", "blocked")) {
    Write-Host "  [preflight] Memory guard requires attention before heavy durable writes." -ForegroundColor Red
} elseif ($guardStatus -eq "warn") {
    Write-Host "  [preflight] Memory guard reports warnings. Continue carefully and prefer checkpointing." -ForegroundColor Yellow
} else {
    Write-Host "  [preflight] Memory guard healthy. Ready to continue." -ForegroundColor Green
}

if ($knowledgeStatus -in @("warn", "degraded")) {
    Write-Host "  [preflight] Knowledge review reports follow-up work for search/graph effectiveness." -ForegroundColor Yellow
}
if ($agentTrace.open_task_count -gt 0) {
    Write-Host "  [preflight] Agent trace reports open delegated tasks from an earlier session. Review .agent-trace.jsonl before spawning duplicates." -ForegroundColor Yellow
}
if ($delegationAudit.classification -eq "warn") {
    Write-Host "  [preflight] Delegation audit found routing/coverage gaps. Prefer tools\session\request-delegation.ps1 for the next spawn." -ForegroundColor Yellow
} elseif ($delegationAudit.classification -in @("no_trace_file", "undeclared_empty")) {
    Write-Host "  [preflight] No auditable delegation request has been logged yet. If this session will delegate, start via tools\session\request-delegation.ps1." -ForegroundColor DarkYellow
}

Write-Host "  ─────────────────────────────────────────" -ForegroundColor DarkCyan
Write-Host "  Session preflight complete." -ForegroundColor Cyan
Write-Host ""
