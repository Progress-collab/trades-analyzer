#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест задержки WebSocket данных Alor API - 20 секунд
"""

import sys
import os
import logging
from datetime import datetime
from time import sleep, time
import threading

# Добавляем путь к AlorPy
sys.path.append(os.path.join(os.path.dirname(__file__), 'AlorPy'))

from AlorPy import AlorPy

# Настройка логирования
logging.basicConfig(level=logging.ERROR)


class LatencyTest20s:
    """Тест задержки на 20 секунд"""
    
    def __init__(self):
        # Загружаем токен
        self.refresh_token = self._load_token()
        if not self.refresh_token:
            raise ValueError("Refresh Token не найден!")
        
        self.ap = AlorPy(refresh_token=self.refresh_token)
        self.measurements = []
        self.start_time = None
        self.running = False
        
    def _load_token(self):
        """Загружает токен из .env"""
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('ALOR_API_TOKEN='):
                        return line.split('=', 1)[1].strip().strip("'\"")
        return None
    
    def on_orderbook_update(self, response):
        """Обработчик для измерения задержки"""
        if not self.running:
            return
            
        try:
            receive_time = datetime.now()
            data = response.get('data', {})
            
            if data.get('bids') and data.get('asks'):
                bid = data['bids'][0]['price']
                ask = data['asks'][0]['price']
                
                # Простое измерение - время получения vs текущее время
                measurement = {
                    'receive_time': receive_time,
                    'bid': bid,
                    'ask': ask,
                    'measurement_number': len(self.measurements) + 1
                }
                
                self.measurements.append(measurement)
                
                # Выводим каждое 5-е измерение чтобы не засорять консоль
                if len(self.measurements) % 5 == 0:
                    elapsed = (receive_time - self.start_time).total_seconds()
                    print(f"📊 #{len(self.measurements):2d} | {receive_time.strftime('%H:%M:%S.%f')[:-3]} | "
                          f"Bid: {bid:8.4f} | Ask: {ask:8.4f} | {elapsed:4.1f}с")
                    
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    def calculate_frequency_stats(self):
        """Рассчитывает статистику частоты обновлений"""
        if len(self.measurements) < 2:
            return
        
        intervals = []
        for i in range(1, len(self.measurements)):
            interval = (self.measurements[i]['receive_time'] - self.measurements[i-1]['receive_time']).total_seconds() * 1000
            intervals.append(interval)
        
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            min_interval = min(intervals)
            max_interval = max(intervals)
            frequency = 1000 / avg_interval if avg_interval > 0 else 0
            
            print("\n" + "="*70)
            print("📈 СТАТИСТИКА ЧАСТОТЫ ОБНОВЛЕНИЙ")
            print("="*70)
            print(f"📊 Всего обновлений:    {len(self.measurements)}")
            print(f"📊 Средний интервал:    {avg_interval:6.1f} мс")
            print(f"📊 Мин интервал:       {min_interval:6.1f} мс")
            print(f"📊 Макс интервал:      {max_interval:6.1f} мс")
            print(f"📊 Частота обновлений: {frequency:6.1f} раз/сек")
            print("="*70)
    
    def auto_stop_timer(self):
        """Таймер автоматической остановки через 20 секунд"""
        sleep(20)
        self.running = False
        print(f"\n⏰ 20 секунд прошло - автоматическая остановка")
    
    def start_test(self):
        """Запускает тест на 20 секунд"""
        print("⏱️  ТЕСТ ЗАДЕРЖКИ WEBSOCKET - 20 СЕКУНД")
        print("=" * 60)
        print("🎯 Подписываемся на PDU5...")
        
        try:
            # Устанавливаем обработчик
            self.ap.on_change_order_book = self.on_orderbook_update
            
            # Подписываемся
            guid = self.ap.order_book_get_and_subscribe('MOEX', 'PDU5')
            print(f"✅ Подписка создана: {guid}")
            print("⚡ Измеряем частоту обновлений...")
            print("-" * 60)
            
            self.start_time = datetime.now()
            self.running = True
            
            # Запускаем таймер автоостановки в отдельном потоке
            timer_thread = threading.Thread(target=self.auto_stop_timer)
            timer_thread.daemon = True
            timer_thread.start()
            
            # Ждем обновления или остановки
            while self.running:
                sleep(0.1)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Тест остановлен пользователем")
            self.running = False
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.running = False
        
        finally:
            # Показываем финальную статистику
            total_time = (datetime.now() - self.start_time).total_seconds()
            print(f"\n📊 РЕЗУЛЬТАТЫ ТЕСТА:")
            print(f"   Время теста: {total_time:.1f} секунд")
            print(f"   Обновлений: {len(self.measurements)}")
            
            if len(self.measurements) > 0:
                avg_per_sec = len(self.measurements) / total_time
                print(f"   Частота: {avg_per_sec:.1f} обновлений/сек")
                
                self.calculate_frequency_stats()
            
            # Закрываем соединения
            try:
                self.ap.unsubscribe(guid)
                self.ap.close_web_socket()
                print("✅ WebSocket закрыт")
            except:
                pass


def main():
    try:
        test = LatencyTest20s()
        test.start_test()
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")


if __name__ == "__main__":
    main()
