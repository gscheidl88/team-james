# close-session.ps1
# Session Closing Checklist — runs automatically after every agent session.
# Called from Invoke-James finally block. Direct file I/O only — no Obsidian dependency.

param(
    [string]$VaultRoot = "<WORKSPACE_ROOT>",
    [string]$SessionStateRoot = "",
    [string]$SessionStateBase = "~\.copilot\session-state",
    [switch]$SkipGraph   # skip graph rebuild when no wiki pages were changed
)

. (Join-Path $PSScriptRoot "session-lifecycle.ps1")

$uv      = Get-UvPath
$notePath = Ensure-DailyNote -VaultRoot $VaultRoot
$agentTrace = Invoke-AgentTraceStatus -VaultRoot $VaultRoot
$delegationAudit = Invoke-DelegationAudit -VaultRoot $VaultRoot
$mutationProfile = Get-LifecycleMutationProfile -VaultRoot $VaultRoot

Set-Location $VaultRoot

Write-Host ""
Write-Host "  ─────────────────────────────────────────" -ForegroundColor DarkCyan
Write-Host "  Session Closing Checklist" -ForegroundColor Cyan
Write-Host "  ─────────────────────────────────────────" -ForegroundColor DarkCyan
Write-MutationSummary -MutationProfile $mutationProfile

# ── 2. Wiki Lint ───────────────────────────────────────────
Write-Host "  [2/3] Running wiki lint..." -ForegroundColor Yellow
$lintResult = & $uv run "$VaultRoot\tools\wiki\wiki_lint.py" 2>&1
$lintLines  = $lintResult | Where-Object { $_ -match "issues|✓|✗|WARNING|ERROR" }
if ($LASTEXITCODE -eq 0) {
    Write-Host "        ✓ Wiki lint clean" -ForegroundColor Green
} else {
    Write-Host "        ⚠ Wiki lint issues found — fix before closing!" -ForegroundColor Red
    $lintLines | ForEach-Object { Write-Host "        $_" -ForegroundColor Red }
}

# ── 3. Dream Consolidation ────────────────────────────────
Write-Host "  [3/3] Running dream consolidation..." -ForegroundColor Yellow
$dreamResult = & $uv run "$VaultRoot\tools\notes\notes_summarizer.py" --dream 2>&1
$newEntries  = ($dreamResult | Select-String "new entries|mem_").Count
if ($newEntries -gt 0) {
    Write-Host "        ✓ Dream: $newEntries new memory entries extracted" -ForegroundColor Green
} else {
    Write-Host "        ✓ Dream: no new entries (dedup clean)" -ForegroundColor Green
}

if (Finalize-SessionScratchpad -VaultRoot $VaultRoot -SessionStateRoot $SessionStateRoot -NotePath $notePath) {
    Invoke-MemoryReview -VaultRoot $VaultRoot -SessionStateRoot $SessionStateRoot
}

Invoke-MemoryCompoundSummary -VaultRoot $VaultRoot
$agentReview = Invoke-AgentReview -VaultRoot $VaultRoot
Invoke-MemoryQA -VaultRoot $VaultRoot
$guardStatus = Invoke-MemoryGuard -VaultRoot $VaultRoot -SessionStateRoot $SessionStateRoot -SessionStateBase $SessionStateBase

# ── 4. Knowledge Rebuild (mutation-aware) ─────────────────
$knowledgeReviewPath = Join-Path $VaultRoot "wiki\reviews\knowledge-performance-review.json"
if ($SkipGraph) {
    Write-Host "  [4/5] Knowledge rebuild skipped by explicit flag." -ForegroundColor DarkYellow
} elseif ($mutationProfile.wiki_rebuild_required -or -not $mutationProfile.detection_available) {
    Invoke-WikiGraphBuild -VaultRoot $VaultRoot | Out-Null
    Invoke-WikiSearchIndex -VaultRoot $VaultRoot | Out-Null
} else {
    Write-Host "  [4/5] No wiki/search mutations detected — skipping graph and index rebuild." -ForegroundColor DarkYellow
}

$knowledgeStatus = if ($SkipGraph) {
    Get-ExistingJsonStatus -Path $knowledgeReviewPath -Default "unknown"
} elseif ($mutationProfile.knowledge_review_required -or -not $mutationProfile.detection_available) {
    Invoke-KnowledgeReview -VaultRoot $VaultRoot
} else {
    $existing = Get-ExistingJsonStatus -Path $knowledgeReviewPath -Default "unknown"
    Write-Host "  [knowledge] No relevant mutations detected; reusing existing review status ($existing)." -ForegroundColor DarkYellow
    $existing
}

# ── 5. Live Wiki Pages ────────────────────────────────────
Invoke-LiveWikiPages -VaultRoot $VaultRoot

# ── 5b. Skills Curator ────────────────────────────────────
Invoke-SkillsCurator -VaultRoot $VaultRoot

# ── 5c. Mnemosyne Consolidation ───────────────────────────
Write-Host "  [5c] Mnemosyne sleep (consolidation)..." -ForegroundColor Yellow
$mnemoExe = "~\.local\bin\mnemosyne.exe"
if (Test-Path $mnemoExe) {
    $mnemoEnv = $env:MNEMOSYNE_DATA_DIR
    $env:MNEMOSYNE_DATA_DIR = "$VaultRoot\.mnemosyne"
    $env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"
    & $mnemoExe sleep 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "        ✓ Mnemosyne consolidation complete" -ForegroundColor Green
    } else {
        Write-Host "        ⚠ Mnemosyne sleep returned non-zero (non-fatal)" -ForegroundColor DarkYellow
    }
    $env:MNEMOSYNE_DATA_DIR = $mnemoEnv
} else {
    Write-Host "        — Mnemosyne not installed, skipping" -ForegroundColor DarkGray
}

# ── 6. Git Sync ───────────────────────────────────────────
Invoke-GitSync -VaultRoot $VaultRoot -Label "close"

if ($guardStatus -in @("degraded", "blocked")) {
    Write-Host "  [close] Memory guard reports a degraded state. Review memory\reviews before next session." -ForegroundColor Red
}
if ($knowledgeStatus -in @("warn", "degraded")) {
    Write-Host "  [close] Knowledge review found issues in RAG/graph effectiveness. Review wiki\reviews before next session." -ForegroundColor Yellow
}
if ($agentTrace.open_task_count -gt 0) {
    Write-Host "  [close] Agent trace shows open delegated tasks. Close only after logging completion, cancellation, or escalation." -ForegroundColor Yellow
}
if ($delegationAudit.classification -eq "warn") {
    Write-Host "  [close] Delegation audit still shows routing/coverage gaps. Review .agent-trace.jsonl before relying on the handoff." -ForegroundColor Yellow
}
if ($agentReview -in @("warn", "degraded")) {
    Write-Host "  [close] Agent review found delegation or verification follow-up. Review memory\reviews\agent-performance-review.md before the next session." -ForegroundColor Yellow
}

Write-LifecycleHistory -VaultRoot $VaultRoot -SessionStateRoot $SessionStateRoot -EventType "close_complete" -SafeHandover:$true -Status $guardStatus -Note "Session close completed." -Artifacts @{ daily_note = $notePath; mutation_groups = $mutationProfile.changed_groups; wiki_rebuild_required = $mutationProfile.wiki_rebuild_required; knowledge_review_required = $mutationProfile.knowledge_review_required }

Write-Host "  ─────────────────────────────────────────" -ForegroundColor DarkCyan
Write-Host "  Session closed cleanly. Auf Wiedersehen!" -ForegroundColor Cyan
Write-Host ""
