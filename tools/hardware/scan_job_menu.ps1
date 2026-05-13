param(
    [string]$VaultRoot = "<WORKSPACE_ROOT>",
    [string]$WorkspaceRoot = "~\.copilot\session-state\828feeb0-4f56-4cc5-9c4d-ca7b5fd60875\files\scan-job",
    [string]$JobName = "current-job",
    [ValidateSet("menu", "status", "reset", "scan-front", "scan-back", "assemble", "simplex", "open-wia")]
    [string]$Action = "menu",
    [ValidateSet("same", "reverse")]
    [string]$BackOrder = "same",
    [string]$OutputPdf = "",
    [string]$Device = "HP LJ M282M285 (USB)",
    [ValidateSet("feeder", "flatbed", "front-only")]
    [string]$Source = "feeder",
    [int]$Resolution = 200,
    [int]$PageLimit = 10
)

$ErrorActionPreference = "Stop"

function Get-JobPaths {
    param(
        [string]$BaseRoot,
        [string]$Name,
        [string]$OutputPdfOverride
    )

    $jobRoot = Join-Path $BaseRoot $Name
    $frontDir = Join-Path $jobRoot "stack1"
    $backDir = Join-Path $jobRoot "stack2"
    $outputPdf = if ($OutputPdfOverride) { $OutputPdfOverride } else { Join-Path $jobRoot ($Name + ".pdf") }

    return [pscustomobject]@{
        JobRoot = $jobRoot
        FrontDir = $frontDir
        BackDir = $backDir
        OutputPdf = $outputPdf
    }
}

function Ensure-JobDirectories {
    param($Paths)
    New-Item -ItemType Directory -Force -Path $Paths.JobRoot, $Paths.FrontDir, $Paths.BackDir | Out-Null
}

function Get-PageFiles {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return @()
    }
    return @(Get-ChildItem $Path -File -Filter "page-*.jpg" | Sort-Object Name)
}

function Get-JobStatus {
    param($Paths)
    $frontFiles = Get-PageFiles $Paths.FrontDir
    $backFiles = Get-PageFiles $Paths.BackDir
    $pdfExists = Test-Path $Paths.OutputPdf

    return [pscustomobject]@{
        JobRoot = $Paths.JobRoot
        FrontPages = $frontFiles.Count
        BackPages = $backFiles.Count
        OutputPdf = $Paths.OutputPdf
        PdfExists = $pdfExists
    }
}

function Invoke-ScanTool {
    param(
        [string[]]$Arguments
    )

    Push-Location $VaultRoot
    try {
        $json = & "uv" run --python 3.12 tools\hardware\scan_adf_to_pdf.py @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "scan_adf_to_pdf.py exited with code $LASTEXITCODE"
        }
        return $json | ConvertFrom-Json
    }
    finally {
        Pop-Location
    }
}

function Reset-Job {
    param($Paths)
    Ensure-JobDirectories $Paths
    Get-ChildItem $Paths.FrontDir -File -ErrorAction SilentlyContinue | Remove-Item -Force
    Get-ChildItem $Paths.BackDir -File -ErrorAction SilentlyContinue | Remove-Item -Force
    if (Test-Path $Paths.OutputPdf) {
        Remove-Item $Paths.OutputPdf -Force
    }
}

function Invoke-ScanPass {
    param(
        [string]$TargetDir,
        [string]$Label
    )

    $args = @(
        "scan-pass",
        $TargetDir,
        "--device", $Device,
        "--source", $Source,
        "--resolution", $Resolution,
        "--page-limit", $PageLimit
    )
    $result = Invoke-ScanTool -Arguments $args
    Write-Host ""
    Write-Host ("{0}: {1} page(s) captured" -f $Label, $result.page_count) -ForegroundColor Green
    return $result
}

function Invoke-Assemble {
    param($Paths)

    $args = @(
        "assemble-manual-duplex",
        $Paths.FrontDir,
        $Paths.BackDir,
        $Paths.OutputPdf,
        "--back-order", $BackOrder
    )
    $result = Invoke-ScanTool -Arguments $args
    Write-Host ""
    Write-Host ("PDF built: {0}" -f $result.output_pdf) -ForegroundColor Green
    return $result
}

function Invoke-Simplex {
    param($Paths)

    $args = @(
        "simplex",
        $Paths.OutputPdf,
        "--device", $Device,
        "--source", $Source,
        "--resolution", $Resolution,
        "--page-limit", $PageLimit
    )
    $result = Invoke-ScanTool -Arguments $args
    Write-Host ""
    Write-Host ("Simplex PDF built: {0}" -f $result.output_pdf) -ForegroundColor Green
    return $result
}

function Show-Status {
    param($Paths)
    $status = Get-JobStatus $Paths
    Write-Host ""
    Write-Host "Scan job status" -ForegroundColor Cyan
    Write-Host ("Job root : {0}" -f $status.JobRoot)
    Write-Host ("Stack 1  : {0} page(s)" -f $status.FrontPages)
    Write-Host ("Stack 2  : {0} page(s)" -f $status.BackPages)
    Write-Host ("PDF      : {0}" -f $status.OutputPdf)
    Write-Host ("PDF file : {0}" -f ($(if ($status.PdfExists) { "present" } else { "missing" })))
}

function Show-Menu {
    param($Paths)

    while ($true) {
        Show-Status $Paths
        Write-Host ""
        Write-Host "1. Reset job"
        Write-Host "2. Scan Stack 1"
        Write-Host "3. Scan Stack 2"
        Write-Host "4. Build shuffled PDF"
        Write-Host "5. Build simplex PDF"
        Write-Host "6. Open Windows scan dialog"
        Write-Host "7. Refresh status"
        Write-Host "0. Exit"
        Write-Host ""

        $choice = Read-Host "Select an action"
        switch ($choice) {
            "1" {
                Reset-Job $Paths
                Write-Host "Job reset complete." -ForegroundColor Yellow
            }
            "2" {
                Invoke-ScanPass -TargetDir $Paths.FrontDir -Label "Stack 1" | Out-Null
            }
            "3" {
                Invoke-ScanPass -TargetDir $Paths.BackDir -Label "Stack 2" | Out-Null
            }
            "4" {
                Invoke-Assemble $Paths | Out-Null
            }
            "5" {
                Invoke-Simplex $Paths | Out-Null
            }
            "6" {
                Start-Process -FilePath "C:\Windows\System32\wiaacmgr.exe" | Out-Null
                Write-Host "Windows scan dialog started." -ForegroundColor Green
            }
            "7" {
                continue
            }
            "0" {
                break
            }
            default {
                Write-Host "Unknown option." -ForegroundColor Red
            }
        }
    }
}

$paths = Get-JobPaths -BaseRoot $WorkspaceRoot -Name $JobName -OutputPdfOverride $OutputPdf
Ensure-JobDirectories $paths

switch ($Action) {
    "status" {
        Show-Status $paths
    }
    "reset" {
        Reset-Job $paths
        Show-Status $paths
    }
    "scan-front" {
        Invoke-ScanPass -TargetDir $paths.FrontDir -Label "Stack 1" | Out-Null
        Show-Status $paths
    }
    "scan-back" {
        Invoke-ScanPass -TargetDir $paths.BackDir -Label "Stack 2" | Out-Null
        Show-Status $paths
    }
    "assemble" {
        Invoke-Assemble $paths | Out-Null
        Show-Status $paths
    }
    "simplex" {
        Invoke-Simplex $paths | Out-Null
        Show-Status $paths
    }
    "open-wia" {
        Start-Process -FilePath "C:\Windows\System32\wiaacmgr.exe" | Out-Null
        Write-Host "Windows scan dialog started." -ForegroundColor Green
        Show-Status $paths
    }
    default {
        Show-Menu $paths
    }
}
