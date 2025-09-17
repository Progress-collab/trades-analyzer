#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрый тест задержки - 20 секунд без зависаний
"""

import sys
import os
from datetime import datetime
from time import sleep, time

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
    print("⚡ БЫСТРЫЙ ТЕСТ - 20 СЕКУНД")
    print("=" * 40)
    
    measurements = []
    
    def on_update(response):
        """Простой обработчик"""
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
    
    try:
        # Подключение
        token = load_token()
        ap = AlorPy(refresh_token=token)
        print("✅ Подключено")
        
        # Подписка
        ap.on_change_order_book = on_update
        guid = ap.order_book_get_and_subscribe('MOEX', 'PDU5')
        print(f"✅ Подписка: {guid[:8]}...")
        print("-" * 40)
        
        # Тест 20 секунд
        start_time = time()
        while (time() - start_time) < 20:
            sleep(0.1)
        
        print("\n⏰ 20 секунд прошло!")
        
        # Результаты
        if measurements:
            total_time = (measurements[-1]['time'] - measurements[0]['time']).total_seconds()
            frequency = len(measurements) / total_time if total_time > 0 else 0
            
            print("\n📊 РЕЗУЛЬТАТЫ:")
            print(f"   Обновлений: {len(measurements)}")
            print(f"   Время: {total_time:.1f}с")
            print(f"   Частота: {frequency:.1f} обновлений/сек")
            
            # Интервалы
            if len(measurements) > 1:
                intervals = []
                for i in range(1, len(measurements)):
                    interval_ms = (measurements[i]['time'] - measurements[i-1]['time']).total_seconds() * 1000
                    intervals.append(interval_ms)
                
                avg_interval = sum(intervals) / len(intervals)
                print(f"   Средний интервал: {avg_interval:.0f}мс")
        
        print("\n✅ Тест завершен успешно")
        
    except KeyboardInterrupt:
        print("\n🛑 Остановлено")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
