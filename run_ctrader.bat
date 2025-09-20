@echo off
chcp 65001 > nul
echo =====================================
echo 🚀 cTrader FxPro API - Котировки
echo =====================================
echo.

REM Активируем виртуальное окружение если оно есть
if exist "..\..\..\venv\Scripts\activate.bat" (
    echo 🔄 Активация виртуального окружения...
    call "..\..\..\venv\Scripts\activate.bat"
)

REM Запускаем cTrader API модуль
echo 📊 Запуск получения котировок криптовалют...
echo.
python ctrader_api.py

echo.
echo ⏸️  Нажмите любую клавишу для выхода...
pause > nul
