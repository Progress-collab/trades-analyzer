# 🛠️ Настройка cTrader FxPro API

## 📋 Шаги настройки

### 1. Получение доступа к cTrader Open API

1. **Зарегистрируйтесь** на [cTrader Developer Portal](https://openapi.ctrader.com/)
2. **Создайте приложение** в разделе "My Apps"
3. **Получите credentials:**
   - `Client ID` 
   - `Client Secret`

### 2. Настройка FxPro аккаунта

1. **Откройте аккаунт** у брокера FxPro
2. **Убедитесь**, что у вас есть доступ к cTrader платформе
3. **Получите ID аккаунта** (Account ID) из cTrader

### 3. Настройка файла .env

Создайте файл `.env` на основе `env_template.txt`:

```env
# cTrader FxPro Open API
CTRADER_CLIENT_ID=your_client_id_here
CTRADER_CLIENT_SECRET=your_client_secret_here
CTRADER_API_URL=https://api.spotware.com

# Дополнительные параметры (если необходимо)
CTRADER_ACCOUNT_ID=your_account_id_here
```

### 4. Настройка списка инструментов

Отредактируйте файл `crypto_instruments.txt`:

```
# Основные криптовалюты
BITCOIN
ETHEREUM
XRP
LITECOIN

# Дополнительные (раскомментируйте при необходимости)
#BITCOIN CASH
#CARDANO
#POLKADOT
```

## 🚀 Запуск

### Тестирование подключения
```bash
python test_ctrader.py
# или
run_ctrader_test.bat
```

### Получение котировок
```bash
python ctrader_api.py
# или
run_ctrader.bat
```

## 🔧 Устранение неполадок

### Ошибка аутентификации
- ✅ Проверьте правильность `Client ID` и `Client Secret`
- ✅ Убедитесь, что приложение активно в Developer Portal
- ✅ Проверьте права доступа приложения

### Не получается получить котировки
- ✅ Проверьте правильность названий инструментов
- ✅ Убедитесь, что инструменты доступны через FxPro
- ✅ Проверьте статус торговых сессий

### Ошибки подключения
- ✅ Проверьте интернет соединение
- ✅ Убедитесь, что cTrader Open API доступен
- ✅ Проверьте настройки файрвола

## 📚 Полезные ссылки

- [cTrader Open API Documentation](https://help.ctrader.com/open-api/)
- [FxPro cTrader](https://www.fxpro.com/trading-platforms/ctrader)
- [Developer Portal](https://openapi.ctrader.com/)

## ⚠️ Важные замечания

1. **Тестовый режим**: Начните с тестового аккаунта
2. **Лимиты API**: Соблюдайте лимиты запросов
3. **Безопасность**: Никогда не делитесь своими credentials
4. **Обновления**: Следите за обновлениями API

## 📞 Поддержка

Если возникают проблемы:
1. Проверьте логи в файле `ctrader_test.log`
2. Обратитесь к документации cTrader
3. Свяжитесь с поддержкой FxPro
