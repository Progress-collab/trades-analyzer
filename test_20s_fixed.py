#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Фиксированный тест задержки - строго 20 секунд с принудительной остановкой
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
    print("⚡ ТЕСТ ЗАДЕРЖКИ - СТРОГО 20 СЕКУНД")
    print("=" * 50)
    
    measurements = []
    running = [True]  # Используем список для изменения из других функций
    
    def on_update(response):
        """Обработчик обновлений"""
        if not running[0]:
            return
            
        try:
            now = datetime.now()
            data = response.get('data', {})
            
            if data.get('bids') and data.get('asks'):
                bid = data['bids'][0]['price']
                ask = data['asks'][0]['price']
                
                measurements.append({
                    'time': now,
                    'bid': bid,
                    'ask': ask
                })
                
                # Показываем каждое 5-е
                if len(measurements) % 5 == 0:
                    print(f"📊 #{len(measurements):2d} | {now.strftime('%H:%M:%S.%f')[:-3]} | Bid: {bid:.4f}")
                    
        except:
            pass
    
    def stop_timer():
        """Останавливает тест через 20 секунд"""
        sleep(20)
        running[0] = False
        print("\n⏰ 20 секунд - СТОП!")
    
    try:
        # Подключение
        token = load_token()
        ap = AlorPy(refresh_token=token)
        print("✅ Подключено")
        
        # Подписка
        ap.on_change_order_book = on_update
        guid = ap.order_book_get_and_subscribe('MOEX', 'PDU5')
        print(f"✅ Подписка: {guid[:8]}...")
        print("-" * 50)
        
        # Запускаем таймер в отдельном потоке
        timer = threading.Thread(target=stop_timer)
        timer.daemon = True
        timer.start()
        
        start_time = time()
        
        # Ждем 20 секунд или остановки
        while running[0] and (time() - start_time) < 21:  # +1 секунда запас
            sleep(0.1)
        
        # Принудительная остановка
        running[0] = False
        
        # Результаты
        if measurements:
            total_time = (measurements[-1]['time'] - measurements[0]['time']).total_seconds()
            frequency = len(measurements) / total_time if total_time > 0 else 0
            
            print("\n📊 ИТОГИ:")
            print(f"   Обновлений: {len(measurements)}")
            print(f"   Время: {total_time:.1f}с") 
            print(f"   Частота: {frequency:.1f} обновлений/сек")
            
            if len(measurements) > 1:
                intervals = []
                for i in range(1, len(measurements)):
                    interval_ms = (measurements[i]['time'] - measurements[i-1]['time']).total_seconds() * 1000
                    intervals.append(interval_ms)
                
                avg_interval = sum(intervals) / len(intervals)
                min_interval = min(intervals)
                max_interval = max(intervals)
                
                print(f"   Средний интервал: {avg_interval:.0f}мс")
                print(f"   Мин-Макс: {min_interval:.0f}-{max_interval:.0f}мс")
                
                if avg_interval < 500:
                    print("   ✅ ОТЛИЧНО: Очень быстро!")
                elif avg_interval < 1000:
                    print("   ✅ ХОРОШО: Быстро")
                else:
                    print("   ⚠️ МЕДЛЕННО")
        
        print("\n🎯 Тест завершен - процесс завершается")
        
        # Быстрый выход без закрытия WebSocket (избегаем зависания)
        os._exit(0)
        
    except KeyboardInterrupt:
        print("\n🛑 Остановлено")
        os._exit(0)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        os._exit(1)


if __name__ == "__main__":
    main()
