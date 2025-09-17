#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ФИНАЛЬНЫЙ REAL-TIME МОНИТОРИНГ ВСЕХ ФЬЮЧЕРСОВ
WebSocket подписка на все инструменты с красивым выводом
"""

import os
import sys
from datetime import datetime
from time import sleep
import threading

# Добавляем путь к AlorPy
sys.path.append(os.path.join(os.path.dirname(__file__), 'AlorPy'))

from AlorPy import AlorPy


class FinalRealTimeMonitor:
    """Финальный real-time мониторинг всех фьючерсов"""
    
    def __init__(self):
        self.refresh_token = self._load_token()
        if not self.refresh_token:
            raise ValueError("Токен не найден в .env файле!")
        
        self.ap = AlorPy(refresh_token=self.refresh_token)
        self.instruments_data = {}
        self.subscriptions = []
        self.running = False
        self.update_count = 0
        self.start_time = None
        
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
    
    def load_instruments_list(self):
        """Загружает список инструментов"""
        instruments = []
        filepath = os.path.join(os.path.dirname(__file__), 'instruments.txt')
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        instruments.append(line.upper())
            return instruments
        except Exception as e:
            print(f"❌ Ошибка загрузки инструментов: {e}")
            return []
    
    def clear_screen(self):
        """Очищает экран"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def format_change_indicator(self, current, previous):
        """Форматирует индикатор изменения"""
        if previous is None or current is None:
            return " "
        
        if current > previous:
            return "↑"
        elif current < previous:
            return "↓"
        else:
            return "="
    
    def on_orderbook_update(self, response):
        """Обработчик обновления стакана"""
        if not self.running:
            return
            
        try:
            data = response.get('data', {})
            guid = response.get('guid')
            
            # Получаем символ из подписки
            symbol = 'UNKNOWN'
            if guid and guid in self.ap.subscriptions:
                subscription = self.ap.subscriptions[guid]
                symbol = subscription.get('code', 'UNKNOWN')
            
            if data.get('bids') and data.get('asks') and symbol != 'UNKNOWN':
                receive_time = datetime.now()
                bid = data['bids'][0]['price']
                ask = data['asks'][0]['price']
                spread = ask - bid
                
                # Сохраняем предыдущие данные
                prev_data = self.instruments_data.get(symbol, {})
                
                # Обновляем данные
                self.instruments_data[symbol] = {
                    'bid': bid,
                    'ask': ask,
                    'spread': spread,
                    'prev_bid': prev_data.get('bid'),
                    'prev_ask': prev_data.get('ask'),
                    'last_update': receive_time,
                    'update_count': prev_data.get('update_count', 0) + 1
                }
                
                self.update_count += 1
                
                # Обновляем дисплей каждые 5 обновлений (чтобы не мигало сильно)
                if self.update_count % 5 == 0:
                    self.display_table()
                    
        except Exception as e:
            print(f"❌ Ошибка обработки: {e}")
    
    def display_table(self):
        """Отображает таблицу котировок"""
        if not self.instruments_data:
            return
            
        self.clear_screen()
        
        print("=" * 90)
        print("🔥 ФИНАЛЬНЫЙ REAL-TIME МОНИТОРИНГ ФЬЮЧЕРСОВ ALOR")
        print("=" * 90)
        
        # Время работы
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
            print(f"⏰ Время работы: {uptime:.0f}с | 📊 Всего обновлений: {self.update_count}")
        
        print(f"{'Фьючерс':<8} {'Bid':<12} {'Ask':<12} {'Спред':<10} {'Обновлений':<12} {'Последнее':<12}")
        print("-" * 90)
        
        # Сортируем по названию инструмента
        sorted_instruments = sorted(self.instruments_data.items())
        
        for symbol, data in sorted_instruments:
            bid = data.get('bid', 0)
            ask = data.get('ask', 0)
            spread = data.get('spread', 0)
            update_count = data.get('update_count', 0)
            last_update = data.get('last_update', datetime.now())
            
            # Индикаторы изменения
            bid_ind = self.format_change_indicator(bid, data.get('prev_bid'))
            ask_ind = self.format_change_indicator(ask, data.get('prev_ask'))
            
            # Время последнего обновления
            time_str = last_update.strftime("%H:%M:%S.%f")[:-3]
            
            # Цветовое кодирование активности
            if update_count > 50:
                activity = "🔥"  # Очень активный
            elif update_count > 20:
                activity = "⚡"  # Активный
            elif update_count > 5:
                activity = "📊"  # Умеренный
            else:
                activity = "💤"  # Спокойный
            
            print(f"{symbol:<8} {bid_ind}{bid:<11.4f} {ask_ind}{ask:<11.4f} {spread:<10.4f} "
                  f"{activity}{update_count:<11d} {time_str:<12}")
        
        print("-" * 90)
        current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"🔄 Обновлено: {current_time} | 🌐 WebSocket Real-time | ❌ Ctrl+C для выхода")
        print("=" * 90)
    
    def start_monitoring(self):
        """Запускает финальный мониторинг"""
        instruments = self.load_instruments_list()
        
        if not instruments:
            print("❌ Список инструментов пуст")
            return
        
        print("🚀 ФИНАЛЬНЫЙ REAL-TIME МОНИТОРИНГ")
        print("=" * 50)
        print(f"📊 Инструменты: {', '.join(instruments)}")
        print(f"🔌 WebSocket: {self.ap.ws_server}")
        print("⚡ Подписываемся на real-time обновления...")
        
        try:
            # Устанавливаем обработчик
            self.ap.on_change_order_book = self.on_orderbook_update
            
            # Подписываемся на все инструменты
            for i, symbol in enumerate(instruments):
                print(f"📡 {i+1}/{len(instruments)} Подписка на {symbol}...")
                guid = self.ap.order_book_get_and_subscribe('MOEX', symbol)
                self.subscriptions.append(guid)
                sleep(0.3)  # Пауза между подписками
            
            print(f"✅ Все подписки созданы: {len(self.subscriptions)}")
            print("🔥 Получение real-time данных...")
            print("-" * 50)
            
            self.start_time = datetime.now()
            self.running = True
            
            # Ждем обновления
            while self.running:
                sleep(0.5)  # Проверяем каждые 0.5 сек
                
        except KeyboardInterrupt:
            print(f"\n🛑 Остановка мониторинга...")
            self.stop_monitoring()
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Останавливает мониторинг"""
        self.running = False
        
        print("📤 Отписка от обновлений...")
        for i, guid in enumerate(self.subscriptions):
            try:
                self.ap.unsubscribe(guid)
                print(f"✅ Отписка {i+1}/{len(self.subscriptions)}")
            except:
                pass
        
        # Показываем финальную статистику
        if self.instruments_data:
            print(f"\n📈 ФИНАЛЬНАЯ СТАТИСТИКА:")
            total_updates = sum(data.get('update_count', 0) for data in self.instruments_data.values())
            uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 1
            
            print(f"   Время работы: {uptime:.0f} секунд")
            print(f"   Всего обновлений: {total_updates}")
            print(f"   Частота: {total_updates/uptime:.1f} обновлений/сек")
            
            print(f"\n📊 По инструментам:")
            for symbol, data in sorted(self.instruments_data.items()):
                updates = data.get('update_count', 0)
                freq = updates / uptime
                print(f"   {symbol}: {updates} обновлений ({freq:.1f}/сек)")
        
        try:
            self.ap.close_web_socket()
            print("\n✅ WebSocket закрыт")
        except:
            pass
        
        print("🎯 Мониторинг завершен")


def main():
    print("🔥 ФИНАЛЬНЫЙ REAL-TIME МОНИТОРИНГ ФЬЮЧЕРСОВ")
    print("=" * 60)
    print("🌐 WebSocket подписка на все ваши инструменты")
    print("⚡ Обновления в реальном времени (~100-500мс задержка)")
    print("❌ Ctrl+C для остановки")
    print("-" * 60)
    
    try:
        monitor = FinalRealTimeMonitor()
        monitor.start_monitoring()
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")


if __name__ == "__main__":
    main()
