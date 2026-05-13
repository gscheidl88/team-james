param(
    [string]$VaultRoot = "<WORKSPACE_ROOT>",
    [string]$TracePath = "",
    [Parameter(Mandatory = $true)][string]$TaskId,
    [Parameter(Mandatory = $true)][string]$Goal,
    [Parameter(Mandatory = $true)][string]$Dod,
    [Parameter(Mandatory = $true)][string]$VerificationPlan,
    [Parameter(Mandatory = $true)][string]$AgentRole,
    [Parameter(Mandatory = $true)][string[]]$RequestedTools,
    [Parameter(Mandatory = $true)][ValidateSet("trivial", "standard", "complex", "critical")][string]$Complexity,
    [Parameter(Mandatory = $true)][ValidateSet("lookup", "code", "analysis", "synthesis", "decision")][string]$TaskType,
    [Parameter(Mandatory = $true)][ValidateSet("low", "medium", "high")][string]$Risk,
    [ValidateSet("budget", "normal", "unlimited")][string]$CostProfile = "normal",
    [ValidateSet("explore", "general-purpose", "code-review", "task")][string]$TaskAgentType = "",
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

. (Join-Path $PSScriptRoot "session-lifecycle.ps1")

Set-Location $VaultRoot

$result = Invoke-RoutedDelegationRequest `
    -VaultRoot $VaultRoot `
    -TracePath $TracePath `
    -TaskId $TaskId `
    -Goal $Goal `
    -Dod $Dod `
    -VerificationPlan $VerificationPlan `
    -AgentRole $AgentRole `
    -RequestedTools $RequestedTools `
    -Complexity $Complexity `
    -TaskType $TaskType `
    -Risk $Risk `
    -CostProfile $CostProfile `
    -TaskAgentType $TaskAgentType `
    -ModelOverride $ModelOverride `
    -ModelOverrideReason $ModelOverrideReason `
    -TimeoutHint $TimeoutHint `
    -PlanPath $PlanPath `
    -Assumptions $Assumptions `
    -ValidationPlan $ValidationPlan `
    -ReplanRule $ReplanRule `
    -HandoffState $HandoffState `
    -Hypothesis $Hypothesis `
    -Confidence $Confidence `
    -Evidence $Evidence `
    -Contradiction $Contradiction `
    -NextTest $NextTest `
    -OpenHypotheses $OpenHypotheses `
    -FailureClass $FailureClass `
    -FallbackAction $FallbackAction `
    -EscalateWhen $EscalateWhen `
    -TaskBody $TaskBody `
    -SkillContextFile $SkillContextFile `
    -AgentId $AgentId `
    -AgentName $AgentName `
    -Note $Note `
    -SkipLifecycleHistory:$SkipLifecycleHistory `
    -Json:$Json

exit $result.exit_code
