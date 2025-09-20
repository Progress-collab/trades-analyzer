# Анализатор торговых сделок

Комплексная система для анализа торговых сделок и мониторинга позиций в реальном времени.

## 🚀 Быстрый старт

### Анализ сделок
```bash
# Запуск через .bat файл (рекомендуется)
run_analyzer.bat

# Или через PowerShell
.\run_analyzer.ps1

# Или напрямую Python
python trades_analyzer.py
```

### API мониторинг
```bash
# Alor API (российские инструменты)
python alor_api.py

# cTrader FxPro API (криптовалюты) - НОВОЕ!
python ctrader_api.py

# Тестирование cTrader API
python test_ctrader.py
```

## 📊 Возможности

### Анализатор сделок
- ✅ **4 источника данных**: Рабочий стол, Kas (Ваня), LiteRuslan, Все источники
- ✅ **Автоматическое копирование** файлов с метками источников
- ✅ **Excel отчеты** с 5 листами и автошириной столбцов
- ✅ **VWAP расчеты** - средневзвешенные цены
- ✅ **Анализ по тикерам** с чистыми позициями (Buy-Sell)
- ✅ **Разделение сессий** - переносы vs активная торговля

### API мониторинг
- ✅ **Alor API**: котировки российских инструментов (акции, фьючерсы)
- ✅ **cTrader FxPro API**: котировки криптовалют (BITCOIN, ETHEREUM, XRP, LITECOIN)
- ✅ **Список инструментов** из файлов (instruments.txt, crypto_instruments.txt)
- ✅ **Безопасное хранение** токенов и credentials
- ✅ **Автоматическое обновление** токенов доступа

## ⚙️ Настройка API

### 1. Создайте файл .env
```bash
cp .env.example .env
```

### 2. Заполните токены и credentials
```env
# Alor API
ALOR_API_TOKEN=ваш_токен_alor
ALOR_PORTFOLIO=ваш_портфель

# cTrader FxPro API
CTRADER_CLIENT_ID=ваш_client_id_ctrader
CTRADER_CLIENT_SECRET=ваш_client_secret_ctrader
```

### 3. Настройте списки инструментов

**Для Alor API** (российские инструменты) - файл `instruments.txt`:
```
PDU5
PTZ5
KCX5
```

**Для cTrader FxPro** (криптовалюты) - файл `crypto_instruments.txt`:
```
BITCOIN
ETHEREUM
XRP
LITECOIN
```

## 🔒 Безопасность

- ❌ **Никогда не коммитьте** файл `.env` в Git
- ✅ **Используйте .env.example** как шаблон
- ✅ **Токены хранятся локально** и не попадают в репозиторий

## 📁 Структура проекта

```
trades-analyzer/
├── trades_analyzer.py         # Основной анализатор
├── alor_api.py               # API модуль Alor
├── ctrader_api.py            # API модуль cTrader FxPro
├── test_ctrader.py           # Тестирование cTrader API
├── instruments.txt           # Российские инструменты
├── crypto_instruments.txt    # Криптовалюты
├── run_analyzer.bat          # Запуск анализатора
├── run_ctrader.bat          # Запуск cTrader API
├── run_ctrader_test.bat     # Тестирование cTrader
├── env_template.txt         # Шаблон настроек
├── requirements.txt         # Зависимости
└── input/                   # Результаты анализа
```

## 🎯 Планы развития

- 📊 **Комплексный анализ** позиций в реальном времени
- 🔄 **Автоматический мониторинг** котировок (Alor + cTrader)
- 📈 **Расчет финрезов** по открытым позициям
- 🌐 **Мультиплатформенная интеграция** (российский рынок + криптовалюты)
- 📱 **Уведомления** о важных изменениях цен
- 🤖 **Автоматизация торговых стратегий**
