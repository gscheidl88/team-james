# checkpoint-session.ps1
# Mid-session flush for crash resistance.

param(
    [string]$VaultRoot = "<WORKSPACE_ROOT>",
    [string]$SessionStateRoot = "",
    [string]$SessionStateBase = "~\.copilot\session-state"
)

. (Join-Path $PSScriptRoot "session-lifecycle.ps1")

Set-Location $VaultRoot

Write-Host ""
Write-Host "  ─────────────────────────────────────────" -ForegroundColor DarkCyan
Write-Host "  Session Checkpoint" -ForegroundColor Cyan
Write-Host "  ─────────────────────────────────────────" -ForegroundColor DarkCyan

$notePath = Ensure-DailyNote -VaultRoot $VaultRoot
$finalized = Finalize-SessionScratchpad -VaultRoot $VaultRoot -SessionStateRoot $SessionStateRoot -NotePath $notePath
$agentTrace = Invoke-AgentTraceStatus -VaultRoot $VaultRoot
$delegationAudit = Invoke-DelegationAudit -VaultRoot $VaultRoot
$mutationProfile = Get-LifecycleMutationProfile -VaultRoot $VaultRoot
Write-MutationSummary -MutationProfile $mutationProfile
if ($finalized) {
    Invoke-MemoryReview -VaultRoot $VaultRoot -SessionStateRoot $SessionStateRoot
}
$agentReview = Invoke-AgentReview -VaultRoot $VaultRoot
Invoke-MemoryQA -VaultRoot $VaultRoot
$guardStatus = Invoke-MemoryGuard -VaultRoot $VaultRoot -SessionStateRoot $SessionStateRoot -SessionStateBase $SessionStateBase
if ($mutationProfile.wiki_rebuild_required) {
    Invoke-WikiGraphBuild -VaultRoot $VaultRoot | Out-Null
    Invoke-WikiSearchIndex -VaultRoot $VaultRoot | Out-Null
}
$knowledgeReviewPath = Join-Path $VaultRoot "wiki\reviews\knowledge-performance-review.json"
$knowledgeStatus = if ($mutationProfile.knowledge_review_required -or -not $mutationProfile.detection_available) {
    Invoke-KnowledgeReview -VaultRoot $VaultRoot
} else {
    $existing = Get-ExistingJsonStatus -Path $knowledgeReviewPath -Default "unknown"
    Write-Host "  [knowledge] No relevant mutations detected; reusing existing review status ($existing)." -ForegroundColor DarkYellow
    $existing
}
Write-LifecycleHistory -VaultRoot $VaultRoot -SessionStateRoot $SessionStateRoot -EventType "checkpoint_complete" -SafeHandover:$true -Status $guardStatus -Note "Session checkpoint completed." -Artifacts @{ daily_note = $notePath; candidates_json = $(if ($SessionStateRoot) { Join-Path $SessionStateRoot "files\memory-candidates.json" } else { $null }); mutation_groups = $mutationProfile.changed_groups; wiki_rebuild_required = $mutationProfile.wiki_rebuild_required; knowledge_review_required = $mutationProfile.knowledge_review_required }

if ($guardStatus -in @("degraded", "blocked")) {
    Write-Host "  [checkpoint] Guard requires review before further durable writes." -ForegroundColor Red
} elseif ($guardStatus -eq "warn") {
    Write-Host "  [checkpoint] Guard warnings recorded. Continue with retrieval + review discipline." -ForegroundColor Yellow
} else {
    Write-Host "  [checkpoint] Checkpoint persisted cleanly." -ForegroundColor Green
}

if ($knowledgeStatus -in @("warn", "degraded")) {
    Write-Host "  [checkpoint] Knowledge review found search/graph issues worth addressing before handover." -ForegroundColor Yellow
}
if ($agentTrace.open_task_count -gt 0) {
    Write-Host "  [checkpoint] Agent trace still shows open delegated tasks. Confirm they are progressing before ending the session." -ForegroundColor Yellow
}
if ($delegationAudit.classification -eq "warn") {
    Write-Host "  [checkpoint] Delegation audit found unresolved routing or coverage gaps. Close them before handoff." -ForegroundColor Yellow
}
if ($agentReview -in @("warn", "degraded")) {
    Write-Host "  [checkpoint] Agent review found follow-up work in delegation or verification discipline." -ForegroundColor Yellow
}
Write-CheckpointSummary -AgentTrace $agentTrace -NextTest "Confirm next action or handoff entry before leaving the checkpoint"

# ── Git Sync ──────────────────────────────────────────────
Invoke-GitSync -VaultRoot $VaultRoot -Label "checkpoint"

Write-Host "  ─────────────────────────────────────────" -ForegroundColor DarkCyan
Write-Host "  Session checkpoint complete." -ForegroundColor Cyan
Write-Host ""
