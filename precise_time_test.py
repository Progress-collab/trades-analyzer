#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Точный тест времени - сравнение с миллисекундами
"""

import os
import sys
import requests
from datetime import datetime
import time

def test_time_precision():
    """Тестируем точность времени"""
    print("🕐 ТОЧНЫЙ ТЕСТ ВРЕМЕНИ")
    print("=" * 60)
    
    # Делаем несколько запросов для анализа
    for i in range(5):
        try:
            # Время ДО запроса
            before_request = datetime.now()
            
            # Запрос к серверу Alor
            response = requests.get('https://api.alor.ru/md/v2/time')
            
            # Время ПОСЛЕ запроса  
            after_request = datetime.now()
            
            if response.status_code == 200:
                server_timestamp = response.json()
                server_time = datetime.fromtimestamp(server_timestamp)
                
                # Время запроса (среднее между до и после)
                request_time = before_request + (after_request - before_request) / 2
                
                print(f"\n📊 Измерение #{i+1}:")
                print(f"   🕐 До запроса:     {before_request.strftime('%H:%M:%S.%f')}")
                print(f"   🕐 После запроса:  {after_request.strftime('%H:%M:%S.%f')}")
                print(f"   🕐 Среднее время:  {request_time.strftime('%H:%M:%S.%f')}")
                print(f"   🕐 Сервер Alor:    {server_time.strftime('%H:%M:%S.000000')} (без миллисекунд)")
                
                # Разница с учетом того что сервер округляет до секунд
                diff_ms = (request_time.timestamp() - server_timestamp) * 1000
                print(f"   ⚡ Разница:        {diff_ms:+7.1f} мс")
                
                # Время запроса к серверу
                request_duration = (after_request - before_request).total_seconds() * 1000
                print(f"   📡 Время запроса:  {request_duration:6.1f} мс")
                
            else:
                print(f"❌ Ошибка запроса: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        if i < 4:  # Пауза между измерениями
            time.sleep(1)
    
    print("\n💡 ОБЪЯСНЕНИЕ:")
    print("   • Сервер Alor возвращает время только до СЕКУНД (без миллисекунд)")
    print("   • Поэтому точное сравнение миллисекунд невозможно")
    print("   • Отрицательная задержка = ваши часы отстают от биржи")
    print("   • Положительная задержка = ваши часы спешат")

def test_websocket_timestamp():
    """Тестируем timestamp в WebSocket данных"""
    print("\n🔍 АНАЛИЗ TIMESTAMP В WEBSOCKET")
    print("=" * 60)
    
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), 'AlorPy'))
    
    from AlorPy import AlorPy
    
    def load_token():
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('ALOR_API_TOKEN='):
                        return line.split('=', 1)[1].strip().strip("'\"")
        return None
    
    measurements = []
    
    def on_update(response):
        if len(measurements) >= 3:  # Ограничиваем 3 измерениями
            return
            
        try:
            receive_time = datetime.now()
            data = response.get('data', {})
            
            print(f"\n📊 WebSocket сообщение #{len(measurements)+1}:")
            print(f"   🕐 Время получения: {receive_time.strftime('%H:%M:%S.%f')}")
            
            # Ищем все поля с временем
            time_fields = ['timestamp', 'time', 'server_time', 'exchange_time']
            
            for field in time_fields:
                if field in data and data[field]:
                    ts = data[field]
                    print(f"   🕐 {field}: {ts}")
                    
                    # Пробуем конвертировать
                    try:
                        if isinstance(ts, (int, float)):
                            if ts > 1e12:  # Миллисекунды
                                dt = datetime.fromtimestamp(ts / 1000)
                                print(f"      → {dt.strftime('%H:%M:%S.%f')} (из миллисекунд)")
                            else:  # Секунды
                                dt = datetime.fromtimestamp(ts)
                                print(f"      → {dt.strftime('%H:%M:%S.%f')} (из секунд)")
                    except:
                        pass
            
            # Ищем время в корне response
            for field in time_fields:
                if field in response and response[field]:
                    ts = response[field]
                    print(f"   🕐 response.{field}: {ts}")
            
            measurements.append(receive_time)
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    try:
        token = load_token()
        ap = AlorPy(refresh_token=token)
        print("✅ Подключено")
        
        ap.on_change_order_book = on_update
        guid = ap.order_book_get_and_subscribe('MOEX', 'SiU5')
        print(f"✅ Подписка на SiU5: {guid[:8]}...")
        
        # Ждем 3 сообщения
        while len(measurements) < 3:
            time.sleep(0.1)
        
        print(f"\n✅ Получено {len(measurements)} сообщений")
        
        # Быстро завершаем
        os._exit(0)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        os._exit(1)

if __name__ == "__main__":
    test_time_precision()
    test_websocket_timestamp()
