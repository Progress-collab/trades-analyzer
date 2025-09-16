# Setup short paths for trades analyzer project
# Creates environment variables for long paths with Russian characters

$env:TRADES_KAS = "C:\Sandbox\glaze\Kas\user\current\OneDrive\Рабочий стол"
$env:TRADES_DESKTOP = "$env:USERPROFILE\OneDrive\Рабочий стол"
$env:TRADES_PROJECT = "C:\cursorC\trades_today"

Write-Host "Environment variables configured:" -ForegroundColor Green
Write-Host "TRADES_KAS = $env:TRADES_KAS" -ForegroundColor Yellow
Write-Host "TRADES_DESKTOP = $env:TRADES_DESKTOP" -ForegroundColor Yellow  
Write-Host "TRADES_PROJECT = $env:TRADES_PROJECT" -ForegroundColor Yellow

# Save to PowerShell profile for permanent use
$profilePath = $PROFILE
if (-not (Test-Path $profilePath)) {
    New-Item -Path $profilePath -ItemType File -Force | Out-Null
}

$envVars = @"
# Trades Analyzer Environment Variables
`$env:TRADES_KAS = "C:\Sandbox\glaze\Kas\user\current\OneDrive\Рабочий стол"
`$env:TRADES_DESKTOP = "`$env:USERPROFILE\OneDrive\Рабочий стол"  
`$env:TRADES_PROJECT = "C:\cursorC\trades_today"
"@

Add-Content -Path $profilePath -Value $envVars
Write-Host "Variables added to PowerShell profile" -ForegroundColor Green
Write-Host "Restart PowerShell to use variables permanently" -ForegroundColor Cyan