# Скрипт для запуска анализатора торговых сделок
# Автор: Glaze
# Дата создания: 16.09.2025

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🚀 АНАЛИЗАТОР ТОРГОВЫХ СДЕЛОК" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Проверяем наличие Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python найден: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python не найден! Установите Python для работы скрипта." -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Проверяем наличие основного файла
if (-not (Test-Path "trades_analyzer.py")) {
    Write-Host "❌ Файл trades_analyzer.py не найден!" -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Проверяем наличие папки input
if (-not (Test-Path "input")) {
    Write-Host "📁 Создаю папку input..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "input" -Force | Out-Null
}

Write-Host "🔍 Запускаю анализ торговых сделок..." -ForegroundColor Yellow
Write-Host ""

# Запускаем анализатор
try {
    python trades_analyzer.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Анализ завершен успешно!" -ForegroundColor Green
        Write-Host "📊 Excel файл с результатами открыт автоматически" -ForegroundColor Green
        Write-Host "📂 Все файлы сохранены в папке input/" -ForegroundColor Green
        Write-Host "🎯 Активный лист: Сессия_по_тикерам" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "❌ Ошибка при выполнении анализа!" -ForegroundColor Red
    }
} catch {
    Write-Host ""
    Write-Host "❌ Критическая ошибка: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Read-Host "Нажмите Enter для выхода"