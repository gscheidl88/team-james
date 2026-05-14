param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$utf8 = New-Object System.Text.UTF8Encoding($false)
$updated = 0

$targetFiles = Get-ChildItem -Path $repoRoot -Recurse -File | Where-Object {
    $_.FullName -notmatch '\\\.git(\\|$)' -and
    $_.Extension -in '.md', '.yaml', '.yml', '.py', '.ps1', '.sh'
}

foreach ($file in $targetFiles) {
    $text = [System.IO.File]::ReadAllText($file.FullName)
    if (-not $text.Contains('<WORKSPACE_ROOT>')) {
        continue
    }

    $newText = $text.Replace('<WORKSPACE_ROOT>', $WorkspaceRoot)
    if ($newText -eq $text) {
        continue
    }

    [System.IO.File]::WriteAllText($file.FullName, $newText, $utf8)
    $updated++
    Write-Host "Updated $($file.FullName.Substring($repoRoot.Length + 1))"
}

$memoryPairs = @(
    @{ Source = 'memory\USER.example.md'; Target = 'memory\USER.md' },
    @{ Source = 'memory\MEMORY.example.md'; Target = 'memory\MEMORY.md' }
)

foreach ($pair in $memoryPairs) {
    $source = Join-Path $repoRoot $pair.Source
    $target = Join-Path $repoRoot $pair.Target
    if (-not (Test-Path $target)) {
        Copy-Item -Path $source -Destination $target
        Write-Host "Created $($pair.Target)"
    }
}

Write-Host "Setup complete. Updated $updated files."
