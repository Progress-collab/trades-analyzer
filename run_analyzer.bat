@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo 🚀 АНАЛИЗАТОР ТОРГОВЫХ СДЕЛОК
echo ============================================================
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python для работы скрипта.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo ✅ Python найден: !PYTHON_VERSION!
)

REM Проверяем наличие основного файла
if not exist "trades_analyzer.py" (
    echo ❌ Файл trades_analyzer.py не найден!
    pause
    exit /b 1
)

REM Проверяем наличие папки input
if not exist "input" (
    echo 📁 Создаю папку input...
    mkdir input
)

echo 🔍 Запускаю анализ торговых сделок...
echo.

REM Запускаем анализатор
python trades_analyzer.py

if %errorlevel% equ 0 (
    echo.
    echo ✅ Анализ завершен успешно!
    echo 📊 Excel файл с результатами открыт автоматически
    echo 📂 Все файлы сохранены в папке input/
    echo 🎯 Активный лист: Сессия_по_тикерам
) else (
    echo.
    echo ❌ Ошибка при выполнении анализа!
)

echo.
echo ============================================================
pause
