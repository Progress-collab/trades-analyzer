# Trades Analyzer Launcher
# Simple PowerShell script for Windows PowerShell compatibility

# Change to script directory
Set-Location -Path $PSScriptRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "TRADES ANALYZER" -ForegroundColor Yellow  
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Working directory: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

try {
    $version = python --version 2>&1
    Write-Host "Python found: $version" -ForegroundColor Green
} catch {
    Write-Host "Python not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path "trades_analyzer.py")) {
    Write-Host "trades_analyzer.py not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path "input")) {
    Write-Host "Creating input folder..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "input" -Force | Out-Null
}

Write-Host "Starting trades analysis..." -ForegroundColor Yellow
Write-Host ""

try {
    python trades_analyzer.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Analysis completed successfully!" -ForegroundColor Green
        Write-Host "Excel file opened automatically" -ForegroundColor Green
        Write-Host "Files saved in input/ folder" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "Error during analysis!" -ForegroundColor Red
    }
} catch {
    Write-Host ""
    Write-Host "Critical error: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Read-Host "Press Enter to exit"
