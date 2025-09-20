#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки работы cTrader API модуля
"""

import logging
import sys
import os
from datetime import datetime

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(__file__))

try:
    from ctrader_api import CTraderAPI
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что файл ctrader_api.py находится в той же директории")
    sys.exit(1)


def test_ctrader_api():
    """Тестирует работу cTrader API"""
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('ctrader_test.log', encoding='utf-8')
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    print("="*60)
    print("🧪 ТЕСТИРОВАНИЕ cTrader FxPro API")
    print("="*60)
    
    try:
        # Инициализация API клиента
        print("\n1️⃣ Инициализация API клиента...")
        ctrader = CTraderAPI()
        print("✅ API клиент создан успешно")
        
        # Загрузка списка инструментов
        print("\n2️⃣ Загрузка списка криптоинструментов...")
        instruments = ctrader.load_instruments_list()
        
        if not instruments:
            print("❌ Список инструментов пуст")
            print("💡 Проверьте файл crypto_instruments.txt")
            return False
        
        print(f"✅ Загружено {len(instruments)} инструментов: {instruments}")
        
        # Тестирование аутентификации
        print("\n3️⃣ Тестирование аутентификации...")
        if ctrader._ensure_authenticated():
            print("✅ Аутентификация успешна")
        else:
            print("❌ Ошибка аутентификации")
            print("💡 Проверьте credentials в файле .env:")
            print("   - CTRADER_CLIENT_ID")
            print("   - CTRADER_CLIENT_SECRET")
            return False
        
        # Тестирование получения одной котировки
        print("\n4️⃣ Тестирование получения одной котировки...")
        test_symbol = instruments[0] if instruments else 'BITCOIN'
        print(f"Тестируем получение котировки для: {test_symbol}")
        
        quote = ctrader.get_quote(test_symbol)
        if quote:
            print("✅ Котировка получена успешно")
            print(f"   Данные: {quote}")
        else:
            print("❌ Не удалось получить котировку")
            print("💡 Возможные причины:")
            print("   - Неправильные endpoints API")
            print("   - Инструмент не найден")
            print("   - Проблемы с доступом к API")
        
        # Тестирование получения множественных котировок
        print("\n5️⃣ Тестирование получения множественных котировок...")
        test_instruments = instruments[:3] if len(instruments) >= 3 else instruments
        print(f"Тестируем получение котировок для: {test_instruments}")
        
        quotes = ctrader.get_multiple_quotes(test_instruments)
        
        successful_quotes = sum(1 for data in quotes.values() if 'error' not in data)
        failed_quotes = len(quotes) - successful_quotes
        
        print(f"✅ Результат: {successful_quotes} успешно, {failed_quotes} с ошибками")
        
        # Вывод результатов
        print("\n6️⃣ Отображение результатов...")
        ctrader.print_quotes(quotes)
        
        # Итоговая оценка
        print("\n" + "="*60)
        print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
        print("="*60)
        
        if successful_quotes > 0:
            print("✅ Тестирование частично успешно")
            print(f"   - Получено {successful_quotes} котировок")
            print(f"   - Не удалось получить {failed_quotes} котировок")
            
            if failed_quotes > 0:
                print("\n💡 Рекомендации:")
                print("   - Проверьте правильность названий инструментов")
                print("   - Уточните доступные endpoints в документации cTrader")
                print("   - Проверьте права доступа вашего аккаунта")
            
            return True
        else:
            print("❌ Тестирование неуспешно")
            print("   - Ни одной котировки не получено")
            print("\n💡 Что проверить:")
            print("   1. Правильность credentials в .env файле")
            print("   2. Доступность cTrader Open API")
            print("   3. Корректность endpoints в коде")
            print("   4. Права доступа вашего аккаунта FxPro")
            return False
    
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        logger.error(f"Критическая ошибка в тестировании: {e}", exc_info=True)
        return False


def check_requirements():
    """Проверяет наличие необходимых файлов и зависимостей"""
    print("🔍 Проверка требований...")
    
    # Проверяем наличие файлов
    required_files = [
        'ctrader_api.py',
        'crypto_instruments.txt',
        'env_template.txt'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Отсутствуют файлы: {missing_files}")
        return False
    
    # Проверяем наличие .env файла
    if not os.path.exists('.env'):
        print("⚠️  Файл .env не найден")
        print("💡 Создайте файл .env на основе env_template.txt")
        print("   и заполните ваши cTrader credentials")
        return False
    
    print("✅ Все требования выполнены")
    return True


def main():
    """Основная функция"""
    print(f"🚀 Запуск тестирования cTrader API - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Проверка требований
    if not check_requirements():
        print("\n❌ Тестирование прервано из-за невыполненных требований")
        return
    
    # Запуск тестирования
    success = test_ctrader_api()
    
    if success:
        print("\n🎉 Тестирование завершено успешно!")
    else:
        print("\n💥 Тестирование завершено с ошибками")
        print("📋 Проверьте лог файл: ctrader_test.log")


if __name__ == "__main__":
    main()
