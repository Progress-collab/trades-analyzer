#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простой тест задержки - 20 секунд с таймером
"""

import sys
import os
import logging
from datetime import datetime
from time import sleep
import signal

# Добавляем путь к AlorPy
sys.path.append(os.path.join(os.path.dirname(__file__), 'AlorPy'))

from AlorPy import AlorPy

# Отключаем все логи
logging.basicConfig(level=logging.CRITICAL)


class SimpleLatencyTest:
    """Простой тест задержки с таймером"""
    
    def __init__(self):
        self.refresh_token = self._load_token()
        self.ap = None
        self.measurements = []
        self.start_time = None
        self.running = False
        self.guid = None
        
    def _load_token(self):
        """Загружает токен"""
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('ALOR_API_TOKEN='):
                        return line.split('=', 1)[1].strip().strip("'\"")
        return None
    
    def on_update(self, response):
        """Простой обработчик"""
        if not self.running:
            return
            
        try:
            now = datetime.now()
            data = response.get('data', {})
            
            if data.get('bids') and data.get('asks'):
                bid = data['bids'][0]['price']
                ask = data['asks'][0]['price']
                
                self.measurements.append({
                    'time': now,
                    'bid': bid,
                    'ask': ask
                })
                
                # Показываем каждое 3-е обновление
                if len(self.measurements) % 3 == 0:
                    elapsed = (now - self.start_time).total_seconds()
                    remaining = 20 - elapsed
                    print(f"📊 #{len(self.measurements):2d} | {now.strftime('%H:%M:%S.%f')[:-3]} | "
                          f"Bid: {bid:8.4f} | Ask: {ask:8.4f} | Осталось: {remaining:4.1f}с")
                    
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    def timeout_handler(self, signum, frame):
        """Обработчик таймаута"""
        self.running = False
        print("\n⏰ 20 секунд прошло - автостоп")
    
    def run_test(self):
        """Запускает тест"""
        print("⏱️  ТЕСТ ЗАДЕРЖКИ - 20 СЕКУНД")
        print("=" * 50)
        
        try:
            print("🔌 Подключение к AlorPy...")
            self.ap = AlorPy(refresh_token=self.refresh_token)
            print("✅ Подключено!")
            
            print("📡 Подписка на PDU5...")
            self.ap.on_change_order_book = self.on_update
            
            self.start_time = datetime.now()
            self.running = True
            
            # Устанавливаем таймер на 20 секунд (только для Unix/Linux)
            # Для Windows используем простой цикл
            if os.name != 'nt':
                signal.signal(signal.SIGALRM, self.timeout_handler)
                signal.alarm(20)
            
            self.guid = self.ap.order_book_get_and_subscribe('MOEX', 'PDU5')
            print(f"✅ Подписка: {self.guid}")
            print("-" * 50)
            
            # Для Windows - простой цикл с проверкой времени
            if os.name == 'nt':
                while self.running:
                    elapsed = (datetime.now() - self.start_time).total_seconds()
                    if elapsed >= 20:
                        self.running = False
                        print("\n⏰ 20 секунд прошло - автостоп")
                        break
                    sleep(0.1)
            else:
                # Для Unix - ждем сигнал
                while self.running:
                    sleep(0.1)
            
        except KeyboardInterrupt:
            print("\n🛑 Остановлено пользователем")
            self.running = False
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.running = False
        
        finally:
            # Сначала отписываемся
            print("\n🔄 Завершение теста...")
            try:
                if self.guid and self.ap:
                    print("📤 Отписка от обновлений...")
                    self.ap.unsubscribe(self.guid)
                    sleep(0.5)  # Даем время на отписку
            except Exception as e:
                print(f"⚠️ Ошибка отписки: {e}")
            
            # Показываем результаты
            self.show_results()
            
            # Закрываем WebSocket
            try:
                if self.ap:
                    print("🔌 Закрытие WebSocket...")
                    self.ap.close_web_socket()
                    print("✅ WebSocket закрыт")
            except Exception as e:
                print(f"⚠️ Ошибка закрытия: {e}")
            
            print("✅ Тест завершен")
    
    def show_results(self):
        """Показывает результаты теста"""
        if not self.measurements:
            print("❌ Нет измерений")
            return
        
        total_time = (self.measurements[-1]['time'] - self.measurements[0]['time']).total_seconds()
        updates_count = len(self.measurements)
        frequency = updates_count / total_time if total_time > 0 else 0
        
        # Рассчитываем интервалы между обновлениями
        intervals = []
        for i in range(1, len(self.measurements)):
            interval_ms = (self.measurements[i]['time'] - self.measurements[i-1]['time']).total_seconds() * 1000
            intervals.append(interval_ms)
        
        print("\n" + "="*60)
        print("🎯 РЕЗУЛЬТАТЫ ТЕСТА ЗАДЕРЖКИ")
        print("="*60)
        print(f"⏱️  Время теста:         {total_time:.1f} секунд")
        print(f"📊 Всего обновлений:     {updates_count}")
        print(f"🔄 Частота обновлений:   {frequency:.1f} раз/секунду")
        
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            min_interval = min(intervals)
            max_interval = max(intervals)
            
            print(f"📈 Средний интервал:     {avg_interval:.0f} мс")
            print(f"📈 Мин интервал:        {min_interval:.0f} мс") 
            print(f"📈 Макс интервал:       {max_interval:.0f} мс")
            
            # Оценка качества
            if avg_interval < 500:
                print("✅ ОТЛИЧНО: Очень быстрые обновления!")
            elif avg_interval < 1000:
                print("✅ ХОРОШО: Быстрые обновления")
            else:
                print("⚠️  МЕДЛЕННО: Редкие обновления")
        
        print("="*60)


def main():
    try:
        test = SimpleLatencyTest()
        test.run_test()
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
