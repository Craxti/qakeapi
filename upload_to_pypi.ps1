# Script to upload package to PyPI
# Usage: .\upload_to_pypi.ps1

$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "YOUR_PYPI_TOKEN_HERE"

Write-Host "Uploading package to PyPI..." -ForegroundColor Green
Write-Host "Files to upload:" -ForegroundColor Yellow
Get-ChildItem dist\*.whl, dist\*.tar.gz | ForEach-Object { Write-Host "  - $($_.Name) ($([math]::Round($_.Length/1KB, 2)) KB)" }

py -m twine upload dist/*

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nPackage successfully uploaded to PyPI!" -ForegroundColor Green
    Write-Host "Check: https://pypi.org/project/qakeapi/" -ForegroundColor Cyan
} else {
    Write-Host "`nUpload error. Possible causes:" -ForegroundColor Red
    Write-Host "  - Network/internet connection issues" -ForegroundColor Yellow
    Write-Host "  - Firewall blocking connection" -ForegroundColor Yellow
    Write-Host "  - Issues on PyPI side" -ForegroundColor Yellow
    Write-Host "`nTry:" -ForegroundColor Yellow
    Write-Host "  1. Check internet connection" -ForegroundColor White
    Write-Host "  2. Temporarily disable firewall/antivirus" -ForegroundColor White
    Write-Host "  3. Try again later" -ForegroundColor White
    Write-Host "  4. Use GitHub Actions for automatic publishing" -ForegroundColor White
}
