function Get-UvPath {
    return "uv"
}

function Get-GitExecutable {
    $gitPath = (Get-Command git -ErrorAction SilentlyContinue)?.Source
    if (-not $gitPath) {
        $candidates = @(
            "C:\Program Files\Git\cmd\git.exe",
            "C:\Program Files (x86)\Git\cmd\git.exe"
        )
        $gitPath = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    }
    return $gitPath
}

function Get-SessionId {
    param(
        [string]$SessionStateRoot = ""
    )

    if ($SessionStateRoot) {
        return Split-Path $SessionStateRoot -Leaf
    }
    return "no-session-state"
}

function Write-LifecycleHistory {
    param(
        [string]$VaultRoot,
        [string]$SessionStateRoot = "",
        [string]$EventType,
        [bool]$SafeHandover = $false,
        [string]$Status = "",
        [string]$Note = "",
        [hashtable]$Artifacts = @{}
    )

    $historyPath = Join-Path $VaultRoot "memory\reviews\memory-guard-history.jsonl"
    $entry = [ordered]@{
        timestamp = (Get-Date -Format "o")
        event_type = $EventType
        session_id = Get-SessionId -SessionStateRoot $SessionStateRoot
        session_root = $(if ($SessionStateRoot) { $SessionStateRoot } else { $null })
        safe_handover = $SafeHandover
        status = $(if ($Status) { $Status } else { $null })
        note = $(if ($Note) { $Note } else { $null })
        artifacts = $Artifacts
    }

    $json = $entry | ConvertTo-Json -Compress -Depth 5
    Add-Content -Path $historyPath -Value $json -Encoding UTF8
}

function Get-ExistingJsonStatus {
    param(
        [string]$Path,
        [string]$Default = "unknown"
    )

    if (!(Test-Path $Path)) { return $Default }
    try {
        $payload = Get-Content -Path $Path -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($payload.status) {
            return [string]$payload.status
        }
    } catch {
        return $Default
    }
    return $Default
}

function Get-ChangedPaths {
    param(
        [string]$VaultRoot
    )

    $gitPath = Get-GitExecutable
    if (-not $gitPath) { return @() }

    Set-Location $VaultRoot
    $result = & $gitPath status --porcelain=v1 --untracked-files=all 2>&1
    if ($LASTEXITCODE -ne 0) { return @() }

    $paths = @()
    foreach ($line in $result) {
        $text = $line.ToString()
        if ([string]::IsNullOrWhiteSpace($text)) { continue }
        $pathText = if ($text.Length -ge 4) { $text.Substring(3).Trim() } else { $text.Trim() }
        if ($pathText -match "\s->\s") {
            $parts = $pathText -split "\s->\s"
            $pathText = $parts[-1].Trim()
        }
        $normalized = $pathText.Trim('"') -replace '/', '\'
        if ($normalized) {
            $paths += $normalized
        }
    }
    return $paths | Sort-Object -Unique
}

function Test-ChangedPathPrefix {
    param(
        [string[]]$Paths,
        [string[]]$Prefixes
    )

    foreach ($path in $Paths) {
        foreach ($prefix in $Prefixes) {
            if ($path.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
                return $true
            }
        }
    }
    return $false
}

function Get-LifecycleMutationProfile {
    param(
        [string]$VaultRoot
    )

    $gitPath = Get-GitExecutable
    if (-not $gitPath) {
        return @{
            detection_available = $false
            changed_paths = @()
            changed_groups = @()
            total_changed_paths = 0
            wiki_rebuild_required = $true
            knowledge_review_required = $true
        }
    }

    $changedPaths = @(Get-ChangedPaths -VaultRoot $VaultRoot)
    $changedGroups = @()

    $wikiChanged = Test-ChangedPathPrefix -Paths $changedPaths -Prefixes @("wiki\", "tools\wiki\")
    $memoryChanged = Test-ChangedPathPrefix -Paths $changedPaths -Prefixes @("memory\", "tools\memory\", "tools\notes\")
    $agentChanged = Test-ChangedPathPrefix -Paths $changedPaths -Prefixes @("agents\", "tools\agents\", "skills\", "AGENTS.md", ".agent-trace.jsonl")
    $sessionChanged = Test-ChangedPathPrefix -Paths $changedPaths -Prefixes @("tools\session\")
    $issueChanged = Test-ChangedPathPrefix -Paths $changedPaths -Prefixes @("tools\github\", "sources\agent-ecosystem\")

    if ($wikiChanged) { $changedGroups += "wiki" }
    if ($memoryChanged) { $changedGroups += "memory" }
    if ($agentChanged) { $changedGroups += "agents" }
    if ($sessionChanged) { $changedGroups += "session" }
    if ($issueChanged) { $changedGroups += "issues" }

    return @{
        detection_available = $true
        changed_paths = $changedPaths
        changed_groups = $changedGroups
        total_changed_paths = $changedPaths.Count
        wiki_rebuild_required = $wikiChanged
        knowledge_review_required = ($wikiChanged -or $sessionChanged)
    }
}

function Write-MutationSummary {
    param(
        [hashtable]$MutationProfile
    )

    if (-not $MutationProfile.detection_available) {
        Write-Host "  [mutation] Git-based mutation detection unavailable; using safe fallback behavior." -ForegroundColor DarkYellow
        return
    }

    Write-Host "  [mutation] Changed paths: $($MutationProfile.total_changed_paths)" -ForegroundColor Cyan
    if ($MutationProfile.changed_groups.Count -gt 0) {
        Write-Host "  [mutation] Changed groups: $($MutationProfile.changed_groups -join ', ')" -ForegroundColor Cyan
    } else {
        Write-Host "  [mutation] No tracked path mutations detected." -ForegroundColor Cyan
    }
    Write-Host "  [mutation] Wiki rebuild required: $($MutationProfile.wiki_rebuild_required)" -ForegroundColor Cyan
    Write-Host "  [mutation] Knowledge review required: $($MutationProfile.knowledge_review_required)" -ForegroundColor Cyan
}

function Ensure-DailyNote {
    param(
        [string]$VaultRoot
    )

    $today = Get-Date -Format "yyyy-MM-dd"
    $noteDir = Join-Path $VaultRoot "PersonalNotes\Daily"
    $notePath = Join-Path $noteDir "$today.md"

    if (!(Test-Path $notePath)) {
        $now = Get-Date
        $isoWeekYear = [System.Globalization.ISOWeek]::GetYear($now)
        $isoWeekNum = [System.Globalization.ISOWeek]::GetWeekOfYear($now)
        $isoWeek  = "{0}-W{1:00}" -f $isoWeekYear, $isoWeekNum
        $dayName  = $now.ToString("dddd, dd. MMMM yyyy")
        $yesterday = $now.AddDays(-1).ToString("yyyy-MM-dd")
        $tomorrow  = $now.AddDays(1).ToString("yyyy-MM-dd")
        $yearMonth = $now.ToString("yyyy-MM")
        $year      = $now.ToString("yyyy")

        $template = @"
---
created: $today
week: $isoWeek
tags: [daily-note, $year]
agent-session: true
---

# $dayName

← [[$yesterday|Yesterday]] · [[$tomorrow|Tomorrow]] →
[[$isoWeek|This Week]] · [[$yearMonth|This Month]]

---

## 🌅 Morning Focus

**Main goal today:**

**Top 3 priorities:**
- [ ] 
- [ ] 
- [ ] 

**Energy level:** 

---

## 📋 Tasks

### Must Do
- [ ] 

### Should Do
- [ ] 

### Could Do
- [ ] 

---

## 💬 Notes & Captures

*(Quick thoughts, ideas, links, fleeting notes)*
*(Use ⚠️ PERMANENT / 🔥 HIGH / 📌 PIN markers for important entries)*

---

## 🤖 Agent Sessions

*(James logs here automatically after each work session)*

---

## 📖 Wiki Pages Today

| Aktion | Seite |
|--------|-------|

---

## 🏆 Achievements

- 

---

## 📚 Learnings

- 

---

## 🔁 Reflections

**What went well:**

**What could improve:**

**One thing I'm grateful for:**

---

## 🌙 Plan for Tomorrow

- [ ] 
"@
        New-Item -ItemType File -Path $notePath -Force | Out-Null
        Set-Content -Path $notePath -Value $template -Encoding UTF8
        Write-Host "  [note] Daily note created: $today.md" -ForegroundColor Green
    } else {
        Write-Host "  [note] Daily note exists: $today.md" -ForegroundColor Green
    }

    return $notePath
}

function Initialize-SessionScratchpad {
    param(
        [string]$VaultRoot,
        [string]$SessionStateRoot,
        [string]$Task = ""
    )

    if (-not $SessionStateRoot) { return }
    $scratchpadScript = Join-Path $VaultRoot "tools\session\memory_scratchpad.py"
    if (!(Test-Path $scratchpadScript) -or !(Test-Path $SessionStateRoot)) { return }

    $uv = Get-UvPath
    $result = if ($Task) {
        & $uv run $scratchpadScript init --session-root $SessionStateRoot --task $Task 2>&1
    } else {
        & $uv run $scratchpadScript init --session-root $SessionStateRoot 2>&1
    }

    if ($LASTEXITCODE -eq 0) {
        $result | ForEach-Object { Write-Host "  [scratchpad] $_" -ForegroundColor Green }
        Write-LifecycleHistory -VaultRoot $VaultRoot -SessionStateRoot $SessionStateRoot -EventType "scratchpad_init" -SafeHandover:$false -Note "Session scratchpad initialized."
    } else {
        Write-Host "  [scratchpad] Initialization failed" -ForegroundColor Red
        $result | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
    }
}

function Finalize-SessionScratchpad {
    param(
        [string]$VaultRoot,
        [string]$SessionStateRoot,
        [string]$NotePath
    )

    if (-not $SessionStateRoot) { return $false }
    $scratchpadScript = Join-Path $VaultRoot "tools\session\memory_scratchpad.py"
    $scratchpadPath = Join-Path $SessionStateRoot "files\memory-scratchpad.md"
    if (!(Test-Path $scratchpadScript) -or !(Test-Path $scratchpadPath)) { return $false }

    $uv = Get-UvPath
    Write-Host "  [scratchpad] Finalizing session scratchpad..." -ForegroundColor Yellow
    $result = & $uv run $scratchpadScript finalize --session-root $SessionStateRoot --daily-note $NotePath 2>&1
    if ($LASTEXITCODE -eq 0) {
        $result | ForEach-Object { Write-Host "    $_" -ForegroundColor Green }
        Write-LifecycleHistory -VaultRoot $VaultRoot -SessionStateRoot $SessionStateRoot -EventType "scratchpad_finalize" -SafeHandover:$false -Note "Scratchpad finalized into candidates." -Artifacts @{ daily_note = $NotePath; candidates_json = (Join-Path $SessionStateRoot "files\memory-candidates.json") }
        return $true
    }

    Write-Host "    Scratchpad finalization failed" -ForegroundColor Red
    $result | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
    return $false
}

function Invoke-MemoryReview {
    param(
        [string]$VaultRoot,
        [string]$SessionStateRoot
    )

    if (-not $SessionStateRoot) { return }
    $candidateJsonPath = Join-Path $SessionStateRoot "files\memory-candidates.json"
    $reconcileScript = Join-Path $VaultRoot "tools\memory\memory_reconcile.py"
    if (!(Test-Path $candidateJsonPath) -or !(Test-Path $reconcileScript)) { return }

    $uv = Get-UvPath
    $reviewMarkdown = Join-Path $VaultRoot "memory\reviews\latest-memory-review.md"
    $reviewJson = Join-Path $VaultRoot "memory\reviews\latest-memory-review.json"
    Write-Host "  [review] Reconciling memory candidates..." -ForegroundColor Yellow
    $result = & $uv run $reconcileScript --candidate-file $candidateJsonPath --markdown-out $reviewMarkdown --json-out $reviewJson 2>&1
    if ($LASTEXITCODE -eq 0) {
        $result | ForEach-Object { Write-Host "    $_" -ForegroundColor Green }
    } else {
        Write-Host "    Memory reconciliation failed" -ForegroundColor Red
        $result | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
    }
}

function Invoke-MemoryQA {
    param(
        [string]$VaultRoot
    )

    $qaScript = Join-Path $VaultRoot "tools\memory\memory_qa.py"
    if (!(Test-Path $qaScript)) { return }

    $uv = Get-UvPath
    Write-Host "  [qa] Running memory QA..." -ForegroundColor Yellow
    $result = & $uv run $qaScript 2>&1
    if ($LASTEXITCODE -eq 0) {
        $result | ForEach-Object { Write-Host "    $_" -ForegroundColor Green }
    } else {
        Write-Host "    Memory QA failed" -ForegroundColor Red
        $result | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
    }
}

function Invoke-MemoryGuard {
    param(
        [string]$VaultRoot,
        [string]$SessionStateRoot = "",
        [string]$SessionStateBase = ""
    )

    $guardScript = Join-Path $VaultRoot "tools\memory\memory_guard.py"
    if (!(Test-Path $guardScript)) { return "unknown" }

    $uv = Get-UvPath
    Write-Host "  [guard] Evaluating memory guard..." -ForegroundColor Yellow
    $args = @("run", $guardScript)
    if ($SessionStateBase) {
        $args += @("--session-state-base", $SessionStateBase)
    }
    if ($SessionStateRoot) {
        $args += @("--current-session-root", $SessionStateRoot)
        $args += @("--session-id", (Get-SessionId -SessionStateRoot $SessionStateRoot))
    }
    $result = & $uv @args 2>&1

    $statusLine = $result | Where-Object { $_ -like "STATUS:*" } | Select-Object -Last 1
    $status = if ($statusLine) { $statusLine.ToString().Split(":", 2)[1].Trim() } else { "unknown" }
    $color = switch ($status) {
        "ok" { "Green" }
        "warn" { "Yellow" }
        "degraded" { "Red" }
        "blocked" { "Red" }
        default { "DarkYellow" }
    }
    $result | ForEach-Object { Write-Host "    $_" -ForegroundColor $color }
    return $status
}

function Invoke-WikiSearchIndex {
    param(
        [string]$VaultRoot
    )

    $script = Join-Path $VaultRoot "tools\wiki\wiki_search.py"
    if (!(Test-Path $script)) { return $false }

    $uv = Get-UvPath
    Write-Host "  [wiki] Rebuilding wiki search index..." -ForegroundColor Yellow
    $result = & $uv run --python 3.12 $script --index 2>&1
    if ($LASTEXITCODE -eq 0) {
        $result | ForEach-Object { Write-Host "    $_" -ForegroundColor Green }
        return $true
    }

    Write-Host "    Wiki search index rebuild failed" -ForegroundColor Red
    $result | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
    return $false
}

function Invoke-WikiGraphBuild {
    param(
        [string]$VaultRoot
    )

    $script = Join-Path $VaultRoot "tools\wiki\wiki_graph.py"
    if (!(Test-Path $script)) { return $false }

    $uv = Get-UvPath
    Write-Host "  [wiki] Rebuilding wiki graph..." -ForegroundColor Yellow
    $result = & $uv run --python 3.12 $script --build 2>&1
    if ($LASTEXITCODE -eq 0) {
        $result | ForEach-Object { Write-Host "    $_" -ForegroundColor Green }
        return $true
    }

    Write-Host "    Wiki graph rebuild failed" -ForegroundColor Red
    $result | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
    return $false
}

function Invoke-KnowledgeReview {
    param(
        [string]$VaultRoot
    )

    $script = Join-Path $VaultRoot "tools\wiki\knowledge_refresh.py"
    if (!(Test-Path $script)) { return "unknown" }

    $uv = Get-UvPath
    Write-Host "  [knowledge] Running self-healing knowledge refresh..." -ForegroundColor Yellow
    $result = & $uv run --python 3.12 $script --mode apply 2>&1
    $statusLine = $result | Where-Object { $_ -like "KNOWLEDGE_STATUS:*" } | Select-Object -Last 1
    $status = if ($statusLine) { $statusLine.ToString().Split(":", 2)[1].Trim() } else { "unknown" }
    $color = switch ($status) {
        "ok" { "Green" }
        "warn" { "Yellow" }
        "degraded" { "Red" }
        default { "DarkYellow" }
    }
    $result | ForEach-Object { Write-Host "    $_" -ForegroundColor $color }
    return $status
}

function Invoke-AgentTraceStatus {
    param(
        [string]$VaultRoot
    )

    $script = Join-Path $VaultRoot "tools\agents\agent_trace.py"
    if (!(Test-Path $script)) {
        return @{
            status = "unknown"
            open_task_count = 0
            open_hypothesis_count = 0
            open_failure_classes = @{}
        }
    }

    $uv = Get-UvPath
    Write-Host "  [agents] Checking sub-agent trace..." -ForegroundColor Yellow
    $result = & $uv run $script status --json 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "    Agent trace status failed" -ForegroundColor Red
        $result | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
        return @{
            status = "unknown"
            open_task_count = 0
            open_hypothesis_count = 0
            open_failure_classes = @{}
        }
    }

    $payload = ($result | Select-Object -Last 1) | ConvertFrom-Json
    $color = if ($payload.status -eq "ok") { "Green" } else { "Yellow" }
    Write-Host "    STATUS: $($payload.status)" -ForegroundColor $color
    Write-Host "    OPEN_TASKS: $($payload.open_task_count)" -ForegroundColor $color
    Write-Host "    OPEN_HYPOTHESES: $($payload.open_hypothesis_count)" -ForegroundColor $color
    if ($payload.open_failure_classes.PSObject.Properties.Count -gt 0) {
        Write-Host "    OPEN_FAILURE_CLASSES: $($payload.open_failure_classes | ConvertTo-Json -Compress)" -ForegroundColor $color
    }
    return @{
        status = $payload.status
        open_task_count = [int]$payload.open_task_count
        open_hypothesis_count = [int]$payload.open_hypothesis_count
        open_failure_classes = $payload.open_failure_classes
    }
}

function Invoke-AgentReview {
    param(
        [string]$VaultRoot
    )

    $script = Join-Path $VaultRoot "tools\agents\agent_review.py"
    if (!(Test-Path $script)) { return "unknown" }

    $uv = Get-UvPath
    Write-Host "  [agents] Running agent performance review..." -ForegroundColor Yellow
    $result = & $uv run $script 2>&1
    $statusLine = $result | Where-Object { $_ -like "STATUS:*" } | Select-Object -Last 1
    $status = if ($statusLine) { $statusLine.ToString().Split(":", 2)[1].Trim() } else { "unknown" }
    $color = switch ($status) {
        "ok" { "Green" }
        "warn" { "Yellow" }
        "degraded" { "Red" }
        default { "DarkYellow" }
    }
    $result | ForEach-Object { Write-Host "    $_" -ForegroundColor $color }
    return $status
}

function Get-DelegationTracePath {
    param(
        [string]$VaultRoot,
        [string]$TracePath = ""
    )

    if ($TracePath) {
        return $TracePath
    }
    return Join-Path $VaultRoot ".agent-trace.jsonl"
}

function Normalize-StringList {
    param(
        [string[]]$Values
    )

    $normalized = @()
    foreach ($value in $Values) {
        if ([string]::IsNullOrWhiteSpace($value)) { continue }
        foreach ($part in ($value -split ",")) {
            $trimmed = $part.Trim()
            if ($trimmed) {
                $normalized += $trimmed
            }
        }
    }
    return $normalized
}

function Get-DelegationTraceState {
    param(
        [string]$VaultRoot,
        [string]$TracePath = ""
    )

    $resolvedTracePath = Get-DelegationTracePath -VaultRoot $VaultRoot -TracePath $TracePath
    $entries = @()
    if (Test-Path $resolvedTracePath) {
        foreach ($line in (Get-Content -Path $resolvedTracePath -Encoding UTF8)) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            try {
                $entries += ($line | ConvertFrom-Json -Depth 8)
            } catch {
                continue
            }
        }
    }

    $sessionEvents = @($entries | Where-Object { $_.event -eq "session_expectation" })
    $taskEntries = @($entries | Where-Object { $_.event -ne "session_expectation" })
    $spawnCount = @($taskEntries | Where-Object { $_.event -eq "spawn" }).Count
    $latestExpected = $null
    if ($sessionEvents.Count -gt 0) {
        $rawExpected = $sessionEvents[-1].metadata.expected_delegations
        $parsedExpected = 0
        if ([int]::TryParse([string]$rawExpected, [ref]$parsedExpected)) {
            $latestExpected = $parsedExpected
        }
    }

    return @{
        trace_path = $resolvedTracePath
        entry_count = $entries.Count
        spawn_count = $spawnCount
        latest_expected_delegations = $latestExpected
    }
}

function Set-DelegationExpectationFloor {
    param(
        [string]$VaultRoot,
        [string]$TracePath = "",
        [string]$Note = "auto-raised by request-delegation.ps1",
        [switch]$Quiet
    )

    $state = Get-DelegationTraceState -VaultRoot $VaultRoot -TracePath $TracePath
    $requiredExpectation = [int]$state.spawn_count + 1
    $latestExpected = $state.latest_expected_delegations
    if ($null -ne $latestExpected -and [int]$latestExpected -ge $requiredExpectation) {
        return @{
            changed = $false
            trace_path = $state.trace_path
            expected_delegations = [int]$latestExpected
        }
    }

    $uv = Get-UvPath
    $delegateScript = Join-Path $VaultRoot "tools\agents\delegate.py"
    $result = & $uv run --python 3.12 $delegateScript session-expectation --trace-path $state.trace_path --expected-delegations $requiredExpectation --note $Note 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to set delegation expectation floor.`n$($result -join "`n")"
    }
    if (-not $Quiet) {
        $result | ForEach-Object { Write-Host "  [delegation] $_" -ForegroundColor Green }
    }
    return @{
        changed = $true
        trace_path = $state.trace_path
        expected_delegations = $requiredExpectation
    }
}

function Invoke-DelegationAudit {
    param(
        [string]$VaultRoot,
        [string]$TracePath = ""
    )

    $uv = Get-UvPath
    $delegateScript = Join-Path $VaultRoot "tools\agents\delegate.py"
    $resolvedTracePath = Get-DelegationTracePath -VaultRoot $VaultRoot -TracePath $TracePath
    $result = & $uv run --python 3.12 $delegateScript audit --trace-path $resolvedTracePath 2>&1
    $lines = @($result | ForEach-Object { $_.ToString() })
    $summary = if ($lines.Count -gt 0) { $lines[0] } else { "" }
    $classification = if ($summary -like "AUDIT: no_trace_file*") {
        "no_trace_file"
    } elseif ($summary -like "AUDIT: ok — no task events*") {
        "undeclared_empty"
    } elseif ($summary -like "AUDIT: ok*") {
        "ok"
    } else {
        "warn"
    }
    $color = switch ($classification) {
        "ok" { "Green" }
        "warn" { "Yellow" }
        default { "DarkYellow" }
    }

    Write-Host "  [delegation] Auditing routed delegation trace..." -ForegroundColor Yellow
    if ($lines.Count -eq 0) {
        Write-Host "    No audit output produced." -ForegroundColor $color
    } else {
        $lines | ForEach-Object { Write-Host "    $_" -ForegroundColor $color }
    }

    return @{
        classification = $classification
        exit_code = $LASTEXITCODE
        trace_path = $resolvedTracePath
        output = $lines
    }
}

function Invoke-RoutedDelegationRequest {
    param(
        [string]$VaultRoot,
        [string]$TracePath = "",
        [string]$TaskId,
        [string]$Goal,
        [string]$Dod,
        [string]$VerificationPlan,
        [string]$AgentRole,
        [string[]]$RequestedTools,
        [string]$Complexity,
        [string]$TaskType,
        [string]$Risk,
        [string]$CostProfile = "normal",
        [string]$TaskAgentType = "",
        [string]$ModelOverride = "",
        [string]$ModelOverrideReason = "",
        [string]$TimeoutHint = "",
        [string]$PlanPath = "",
        [string]$Assumptions = "",
        [string]$ValidationPlan = "",
        [string]$ReplanRule = "",
        [string]$HandoffState = "",
        [string]$Hypothesis = "",
        [string]$Confidence = "",
        [string]$Evidence = "",
        [string]$Contradiction = "",
        [string]$NextTest = "",
        [Nullable[int]]$OpenHypotheses = $null,
        [string]$FailureClass = "",
        [string]$FallbackAction = "",
        [string]$EscalateWhen = "",
        [string]$TaskBody = "",
        [string[]]$SkillContextFile = @(),
        [string]$AgentId = "",
        [string]$AgentName = "",
        [string]$Note = "",
        [switch]$SkipLifecycleHistory,
        [switch]$Json
    )

    $normalizedRequestedTools = Normalize-StringList -Values $RequestedTools
    $expectation = Set-DelegationExpectationFloor -VaultRoot $VaultRoot -TracePath $TracePath -Quiet:$Json
    if (-not $Json) {
        Write-Host "  [delegation] Expectation floor: $($expectation.expected_delegations)" -ForegroundColor Cyan
    }

    $uv = Get-UvPath
    $helperScript = Join-Path $VaultRoot "tools\agents\cao_helper.py"
    $args = @(
        "run",
        "--python",
        "3.12",
        $helperScript,
        "spawn",
        "--trace-path",
        $expectation.trace_path,
        "--task-id",
        $TaskId,
        "--goal",
        $Goal,
        "--dod",
        $Dod,
        "--verification-plan",
        $VerificationPlan,
        "--agent-role",
        $AgentRole,
        "--requested-tools"
    )
    $args += $normalizedRequestedTools
    $args += @(
        "--complexity",
        $Complexity,
        "--task-type",
        $TaskType,
        "--risk",
        $Risk,
        "--cost-profile",
        $CostProfile
    )

    if ($TaskAgentType) { $args += @("--task-agent-type", $TaskAgentType) }
    if ($ModelOverride) { $args += @("--model-override", $ModelOverride) }
    if ($ModelOverrideReason) { $args += @("--model-override-reason", $ModelOverrideReason) }
    if ($TimeoutHint) { $args += @("--timeout-hint", $TimeoutHint) }
    if ($PlanPath) { $args += @("--plan-path", $PlanPath) }
    if ($Assumptions) { $args += @("--assumptions", $Assumptions) }
    if ($ValidationPlan) { $args += @("--validation-plan", $ValidationPlan) }
    if ($ReplanRule) { $args += @("--replan-rule", $ReplanRule) }
    if ($HandoffState) { $args += @("--handoff-state", $HandoffState) }
    if ($Hypothesis) { $args += @("--hypothesis", $Hypothesis) }
    if ($Confidence) { $args += @("--confidence", $Confidence) }
    if ($Evidence) { $args += @("--evidence", $Evidence) }
    if ($Contradiction) { $args += @("--contradiction", $Contradiction) }
    if ($NextTest) { $args += @("--next-test", $NextTest) }
    if ($null -ne $OpenHypotheses) { $args += @("--open-hypotheses", [string]$OpenHypotheses) }
    if ($FailureClass) { $args += @("--failure-class", $FailureClass) }
    if ($FallbackAction) { $args += @("--fallback-action", $FallbackAction) }
    if ($EscalateWhen) { $args += @("--escalate-when", $EscalateWhen) }
    if ($TaskBody) { $args += @("--task-body", $TaskBody) }
    foreach ($path in $SkillContextFile) {
        if ($path) {
            $args += @("--skill-context-file", $path)
        }
    }
    if ($AgentId) { $args += @("--agent-id", $AgentId) }
    if ($AgentName) { $args += @("--agent-name", $AgentName) }
    if ($Note) { $args += @("--note", $Note) }
    if ($Json) { $args += "--json" }

    $result = & $uv @args 2>&1
    $exitCode = $LASTEXITCODE
    if ($Json) {
        $result | ForEach-Object { Write-Output $_ }
    } else {
        $color = if ($exitCode -eq 0) { "Green" } else { "Red" }
        $result | ForEach-Object { Write-Host $_ -ForegroundColor $color }
    }
    if ($exitCode -ne 0) {
        return @{
            status = "failed"
            exit_code = $exitCode
            trace_path = $expectation.trace_path
            expected_delegations = $expectation.expected_delegations
        }
    }

    if (-not $SkipLifecycleHistory) {
        Write-LifecycleHistory -VaultRoot $VaultRoot -EventType "delegation_request" -SafeHandover:$false -Status "ok" -Note "Routed delegation request logged for $TaskId." -Artifacts @{
            trace_path = $expectation.trace_path
            task_id = $TaskId
            expected_delegations = $expectation.expected_delegations
            agent_role = $AgentRole
            requested_tools = $normalizedRequestedTools
        }
    }
    return @{
        status = "ok"
        exit_code = 0
        trace_path = $expectation.trace_path
        expected_delegations = $expectation.expected_delegations
    }
}

function Invoke-GitSync {
    param(
        [string]$VaultRoot,
        [string]$Label = "checkpoint"   # "checkpoint" or "close"
    )

    $gitPath = Get-GitExecutable
    if (-not $gitPath) {
        Write-Host "  [git] git not found — skipping sync" -ForegroundColor DarkYellow
        return
    }

    Set-Location $VaultRoot
    Write-Host "  [git] Syncing repository..." -ForegroundColor Yellow

    # Stage all changes
    & $gitPath add -A 2>&1 | Out-Null

    # Check if there is anything to commit
    $staged = & $gitPath status --porcelain 2>&1
    if (-not $staged) {
        Write-Host "        ✓ Nothing to commit — repo already up to date" -ForegroundColor Green
        return
    }

    # Commit
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    $msg = "chore: session $Label [$timestamp]`n`nAuto-commit from session lifecycle ($Label).`n`nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
    $commitResult = & $gitPath commit -m $msg 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "        ⚠ Git commit failed — check manually" -ForegroundColor Red
        $commitResult | ForEach-Object { Write-Host "          $_" -ForegroundColor Red }
        return
    }

    # Push
    $pushResult = & $gitPath push origin main 2>&1
    if ($LASTEXITCODE -eq 0) {
        $changed = ($staged | Measure-Object -Line).Lines
        Write-Host "        ✓ Pushed $changed changed file(s) to origin/main" -ForegroundColor Green
    } else {
        Write-Host "        ⚠ Git push failed — changes committed locally, push manually" -ForegroundColor Red
        $pushResult | ForEach-Object { Write-Host "          $_" -ForegroundColor Red }
    }
}

function Invoke-MemoryWarmup {
    param(
        [string]$VaultRoot
    )

    Write-Host "  [memory-warmup] Seeding access log with benchmark queries..." -ForegroundColor Cyan
    $uv = Get-UvPath
    $script = Join-Path $VaultRoot "tools\memory\memory_retrieval.py"
    & $uv run $script --warmup 2>&1 | ForEach-Object { Write-Host "    $_" }
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [memory-warmup] Done — access-log seeded." -ForegroundColor Green
    } else {
        Write-Host "  [memory-warmup] WARNING: warmup exited with code $LASTEXITCODE" -ForegroundColor Yellow
    }
}

function Invoke-MemoryCompoundSummary {
    param(
        [string]$VaultRoot
    )

    Write-Host "  [memory-compound] Running maintenance + surfacing compounding memories..." -ForegroundColor Cyan
    $uv = Get-UvPath
    $script = Join-Path $VaultRoot "tools\memory\memory_maintenance.py"
    $output = & $uv run $script --output json 2>&1
    if ($LASTEXITCODE -eq 0) {
        try {
            $data = $output | ConvertFrom-Json -Depth 10
            $topItems = $data.top_reinforcement
            if ($topItems -and $topItems.Count -gt 0) {
                Write-Host "  [memory-compound] Top compounding memories:" -ForegroundColor Green
                foreach ($item in ($topItems | Select-Object -First 3)) {
                    $refs = $item.references
                    $text = [string]$item.text
                    if ($text.Length -gt 80) { $text = $text.Substring(0, 80) + "..." }
                    Write-Host "    refs=$refs — $text" -ForegroundColor Green
                }
            } else {
                Write-Host "  [memory-compound] No reinforcement candidates yet." -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  [memory-compound] Output (non-JSON):" -ForegroundColor Yellow
            $output | ForEach-Object { Write-Host "    $_" }
        }
    } else {
        Write-Host "  [memory-compound] WARNING: maintenance exited with code $LASTEXITCODE" -ForegroundColor Yellow
        $output | Select-Object -First 5 | ForEach-Object { Write-Host "    $_" }
    }
}

function Invoke-LiveWikiPages {
    param(
        [string]$VaultRoot
    )

    Write-Host "  [live-wiki] Refreshing live wiki pages..." -ForegroundColor Cyan
    $uv = Get-UvPath
    $script = Join-Path $VaultRoot "tools\wiki\wiki_live_pages.py"
    $env:PYTHONIOENCODING = "utf-8"
    & $uv run $script --apply 2>&1 | ForEach-Object { Write-Host "    $_" }
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [live-wiki] Done." -ForegroundColor Green
    } else {
        Write-Host "  [live-wiki] WARNING: wiki_live_pages exited with code $LASTEXITCODE" -ForegroundColor Yellow
    }
}

function Invoke-SkillsCurator {
    param(
        [string]$VaultRoot,
        [switch]$Apply
    )

    $mode = if ($Apply) { "apply" } else { "check" }
    Write-Host "  [skills-curator] Running skills lifecycle check (--mode $mode)..." -ForegroundColor Cyan
    $uv = Get-UvPath
    $script = Join-Path $VaultRoot "tools\skills\skills_curator.py"
    $env:PYTHONIOENCODING = "utf-8"
    & $uv run $script --mode $mode 2>&1 | ForEach-Object { Write-Host "    $_" }
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [skills-curator] Done." -ForegroundColor Green
    } else {
        Write-Host "  [skills-curator] WARNING: skills_curator exited with code $LASTEXITCODE" -ForegroundColor Yellow
    }
}

function Write-CheckpointSummary {
    param(
        [hashtable]$AgentTrace,
        [string[]]$Blockers = @(),
        [string]$NextTest = "Manual follow-up required",
        [string]$OpenHypotheses = "none recorded in runtime trace"
    )

    $openWip = if ($AgentTrace -and $AgentTrace.open_task_count -gt 0) {
        "$($AgentTrace.open_task_count) delegated task(s) still open"
    } else {
        "no delegated runtime WIP detected"
    }
    $openHypothesisText = if ($AgentTrace -and $AgentTrace.open_hypothesis_count -gt 0) {
        "$($AgentTrace.open_hypothesis_count) open hypothesis/hypotheses in runtime trace"
    } else {
        $OpenHypotheses
    }
    $blockerText = if ($Blockers -and $Blockers.Count -gt 0) {
        ($Blockers -join "; ")
    } else {
        "none recorded"
    }

    Write-Host "  [checkpoint-summary]" -ForegroundColor Cyan
    Write-Host "    OPEN_WIP: $openWip" -ForegroundColor Cyan
    Write-Host "    OPEN_HYPOTHESES: $openHypothesisText" -ForegroundColor Cyan
    Write-Host "    BLOCKERS: $blockerText" -ForegroundColor Cyan
    Write-Host "    NEXT_TEST: $NextTest" -ForegroundColor Cyan
}
