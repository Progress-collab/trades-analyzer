@echo off
chcp 65001 > nul
echo =====================================
echo 🧪 Тестирование cTrader FxPro API
echo =====================================
echo.

REM Активируем виртуальное окружение если оно есть
if exist "..\..\..\venv\Scripts\activate.bat" (
    echo 🔄 Активация виртуального окружения...
    call "..\..\..\venv\Scripts\activate.bat"
)

REM Запускаем тестирование
echo 🔍 Запуск тестирования cTrader API...
echo.
python test_ctrader.py

echo.
echo ⏸️  Нажмите любую клавишу для выхода...
pause > nul
