#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест реальной задержки между временем биржи и временем получения
Тестируем на SiU5 (доллар-рубль сентябрь) - 20 секунд
"""

import sys
import os
from datetime import datetime
from time import sleep, time
import threading

# Добавляем путь к AlorPy
sys.path.append(os.path.join(os.path.dirname(__file__), 'AlorPy'))

from AlorPy import AlorPy


def load_token():
    """Загружает токен"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('ALOR_API_TOKEN='):
                    return line.split('=', 1)[1].strip().strip("'\"")
    return None


def main():
    print("⏱️  ТЕСТ РЕАЛЬНОЙ ЗАДЕРЖКИ - SiU5 - 20 СЕКУНД")
    print("=" * 60)
    
    measurements = []
    running = [True]
    
    def on_update(response):
        """Обработчик с измерением реальной задержки"""
        if not running[0]:
            return
            
        try:
            receive_time = datetime.now()
            data = response.get('data', {})
            
            if data.get('bids') and data.get('asks'):
                bid = data['bids'][0]['price']
                ask = data['asks'][0]['price']
                
                # Ищем timestamp от биржи в разных полях
                exchange_timestamp = None
                
                # Возможные поля с временем от биржи
                timestamp_fields = ['timestamp', 'time', 'exchange_time', 'server_time']
                
                for field in timestamp_fields:
                    if field in data and data[field]:
                        exchange_timestamp = data[field]
                        break
                
                # Если не нашли в data, ищем в корне response
                if not exchange_timestamp:
                    for field in timestamp_fields:
                        if field in response and response[field]:
                            exchange_timestamp = response[field]
                            break
                
                latency_ms = None
                exchange_time_str = "NO_TIMESTAMP"
                
                if exchange_timestamp:
                    try:
                        # Конвертируем timestamp биржи
                        if isinstance(exchange_timestamp, (int, float)):
                            # Unix timestamp
                            if exchange_timestamp > 1e12:  # Миллисекунды
                                exchange_time = datetime.fromtimestamp(exchange_timestamp / 1000)
                            else:  # Секунды
                                exchange_time = datetime.fromtimestamp(exchange_timestamp)
                        else:
                            # ISO строка
                            exchange_time = datetime.fromisoformat(str(exchange_timestamp).replace('Z', '+00:00'))
                            exchange_time = exchange_time.replace(tzinfo=None)
                        
                        # Рассчитываем задержку в миллисекундах
                        latency_ms = (receive_time - exchange_time).total_seconds() * 1000
                        exchange_time_str = exchange_time.strftime('%H:%M:%S.%f')[:-3]
                        
                    except Exception as e:
                        exchange_time_str = f"ERROR: {e}"
                
                measurements.append({
                    'receive_time': receive_time,
                    'exchange_time': exchange_timestamp,
                    'latency_ms': latency_ms,
                    'bid': bid,
                    'ask': ask
                })
                
                # Показываем каждое 3-е обновление
                if len(measurements) % 3 == 0:
                    receive_str = receive_time.strftime('%H:%M:%S.%f')[:-3]
                    
                    if latency_ms is not None:
                        print(f"📊 #{len(measurements):2d} | Получено: {receive_str} | "
                              f"Биржа: {exchange_time_str} | "
                              f"Задержка: {latency_ms:+7.1f}мс | Bid: {bid:.2f}")
                    else:
                        print(f"📊 #{len(measurements):2d} | Получено: {receive_str} | "
                              f"Биржа: {exchange_time_str} | Bid: {bid:.2f}")
                    
        except Exception as e:
            print(f"❌ Ошибка обработки: {e}")
    
    def stop_timer():
        """Останавливает через 20 секунд"""
        sleep(20)
        running[0] = False
        print("\n⏰ 20 секунд - автостоп!")
    
    try:
        # Подключение
        token = load_token()
        ap = AlorPy(refresh_token=token)
        print("✅ Подключено к AlorPy")
        
        # Подписка на SiU5 (доллар-рубль)
        ap.on_change_order_book = on_update
        guid = ap.order_book_get_and_subscribe('MOEX', 'SiU5')
        print(f"✅ Подписка на SiU5: {guid[:8]}...")
        print("-" * 60)
        
        # Запускаем таймер
        timer = threading.Thread(target=stop_timer)
        timer.daemon = True
        timer.start()
        
        start_time = time()
        
        # Ждем 20 секунд
        while running[0] and (time() - start_time) < 21:
            sleep(0.1)
        
        running[0] = False
        
        # Анализ результатов
        if measurements:
            print(f"\n📈 АНАЛИЗ ЗАДЕРЖКИ:")
            
            # Фильтруем измерения с валидной задержкой
            valid_latencies = [m['latency_ms'] for m in measurements if m['latency_ms'] is not None]
            
            if valid_latencies:
                avg_latency = sum(valid_latencies) / len(valid_latencies)
                min_latency = min(valid_latencies)
                max_latency = max(valid_latencies)
                
                print(f"   Измерений с timestamp: {len(valid_latencies)}/{len(measurements)}")
                print(f"   Средняя задержка: {avg_latency:6.1f} мс")
                print(f"   Мин задержка:    {min_latency:6.1f} мс")
                print(f"   Макс задержка:   {max_latency:6.1f} мс")
                
                if avg_latency < 100:
                    print("   ✅ ОТЛИЧНО: Задержка < 100мс")
                elif avg_latency < 500:
                    print("   ✅ ХОРОШО: Задержка < 500мс")
                else:
                    print("   ⚠️ МЕДЛЕННО: Задержка > 500мс")
            else:
                print("   ❌ Нет timestamp от биржи для расчета задержки")
                
            total_time = (measurements[-1]['receive_time'] - measurements[0]['receive_time']).total_seconds()
            frequency = len(measurements) / total_time
            print(f"   Частота обновлений: {frequency:.1f} раз/сек")
        
        print("\n🎯 Тест завершен")
        os._exit(0)
        
    except KeyboardInterrupt:
        print("\n🛑 Остановлено пользователем")
        os._exit(0)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        os._exit(1)


if __name__ == "__main__":
    main()
