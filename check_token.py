#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка токена Alor API
"""

import os
import requests
from alor_api import AlorAPI

def check_token():
    """Проверяем токен через HTTP API"""
    try:
        # Создаем API клиент
        alor = AlorAPI()
        print(f"✅ Токен загружен: {len(alor.token)} символов")
        print(f"🔍 Первые 10 символов: {alor.token[:10]}...")
        print(f"🔍 Последние 10 символов: ...{alor.token[-10:]}")
        
        # Проверяем работу через HTTP API
        print("\n📡 Тестирую HTTP API...")
        instruments = alor.load_instruments_list()
        if instruments:
            symbol = instruments[0]
            print(f"🎯 Тестирую получение котировки {symbol}...")
            
            quote = alor.get_quote(symbol)
            if quote and 'error' not in quote:
                print(f"✅ HTTP API работает! Bid: {quote.get('bid')}, Ask: {quote.get('ask')}")
                print("💡 Это значит, что токен правильный для HTTP API")
                print("⚠️  Но для WebSocket может потребоваться JWT токен")
                
                # Показываем заголовки запроса
                print(f"\n🔧 Заголовок авторизации: Authorization: Bearer {alor.token[:20]}...")
                
            else:
                print("❌ HTTP API не работает - проблема с токеном")
        else:
            print("❌ Не удалось загрузить список инструментов")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def check_token_format():
    """Анализируем формат токена"""
    try:
        # Загружаем токен
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('ALOR_API_TOKEN='):
                        token = line.split('=', 1)[1].strip()
                        
                        print(f"\n🔍 АНАЛИЗ ТОКЕНА:")
                        print(f"Длина: {len(token)} символов")
                        
                        # Проверяем, похож ли на JWT
                        if '.' in token and token.count('.') >= 2:
                            print("🎯 Похож на JWT токен (содержит точки)")
                            parts = token.split('.')
                            print(f"   Частей JWT: {len(parts)}")
                        else:
                            print("⚠️  НЕ похож на JWT токен (нет точек)")
                            print("💡 Возможно, это API ключ для HTTP запросов")
                        
                        # Проверяем символы
                        if token.isalnum():
                            print("🔤 Содержит только буквы и цифры")
                        else:
                            print("🔤 Содержит специальные символы")
                            
                        break
        else:
            print("❌ Файл .env не найден")
            
    except Exception as e:
        print(f"❌ Ошибка анализа токена: {e}")

if __name__ == "__main__":
    print("🔍 ПРОВЕРКА ТОКЕНА ALOR API")
    print("=" * 50)
    
    check_token_format()
    print("\n" + "=" * 50)
    check_token()
    
    print("\n💡 РЕКОМЕНДАЦИИ:")
    print("1. Если HTTP API работает, токен правильный")
    print("2. Для WebSocket может потребоваться JWT токен")  
    print("3. Проверьте документацию Alor по получению JWT токена")
    print("4. Возможно, нужно обменять API ключ на JWT токен")
