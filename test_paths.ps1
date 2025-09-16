# Test script to check available paths
# Safe approach using standard Windows variables

Write-Host "Testing available paths:" -ForegroundColor Cyan
Write-Host ""

# Test USERPROFILE
Write-Host "USERPROFILE: $env:USERPROFILE" -ForegroundColor Yellow
Write-Host "Exists: $(Test-Path $env:USERPROFILE)" -ForegroundColor $(if (Test-Path $env:USERPROFILE) {'Green'} else {'Red'})
Write-Host ""

# Test Desktop variants
$desktopPaths = @(
    "$env:USERPROFILE\Desktop",
    "$env:USERPROFILE\OneDrive\Desktop", 
    "$env:USERPROFILE\OneDrive\Рабочий стол",
    "$env:USERPROFILE\Рабочий стол"
)

Write-Host "Desktop variants:" -ForegroundColor Cyan
foreach ($path in $desktopPaths) {
    $exists = Test-Path $path
    $status = if ($exists) {"✅"} else {"❌"}
    Write-Host "$status $path" -ForegroundColor $(if ($exists) {'Green'} else {'Red'})
}

Write-Host ""

# Test Kas path
$kasPath = "C:\Sandbox\glaze\Kas\user\current\OneDrive\Рабочий стол"
$kasExists = Test-Path $kasPath
Write-Host "Kas path:" -ForegroundColor Cyan
Write-Host "$(if ($kasExists) {'✅'} else {'❌'}) $kasPath" -ForegroundColor $(if ($kasExists) {'Green'} else {'Red'})

Write-Host ""
Write-Host "Test completed!" -ForegroundColor Green
