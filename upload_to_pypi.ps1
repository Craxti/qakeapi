# Скрипт для загрузки пакета на PyPI
# Использование: .\upload_to_pypi.ps1

$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "YOUR_PYPI_TOKEN_HERE"

Write-Host "Загрузка пакета на PyPI..." -ForegroundColor Green
Write-Host "Файлы для загрузки:" -ForegroundColor Yellow
Get-ChildItem dist\*.whl, dist\*.tar.gz | ForEach-Object { Write-Host "  - $($_.Name) ($([math]::Round($_.Length/1KB, 2)) KB)" }

py -m twine upload dist/*

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nПакет успешно загружен на PyPI!" -ForegroundColor Green
    Write-Host "Проверьте: https://pypi.org/project/qakeapi/" -ForegroundColor Cyan
} else {
    Write-Host "`nОшибка при загрузке. Возможные причины:" -ForegroundColor Red
    Write-Host "  - Проблемы с сетью/интернет-соединением" -ForegroundColor Yellow
    Write-Host "  - Файрвол блокирует соединение" -ForegroundColor Yellow
    Write-Host "  - Проблемы на стороне PyPI" -ForegroundColor Yellow
    Write-Host "`nПопробуйте:" -ForegroundColor Yellow
    Write-Host "  1. Проверить интернет-соединение" -ForegroundColor White
    Write-Host "  2. Временно отключить файрвол/антивирус" -ForegroundColor White
    Write-Host "  3. Попробовать позже" -ForegroundColor White
    Write-Host "  4. Использовать GitHub Actions для автоматической публикации" -ForegroundColor White
}

