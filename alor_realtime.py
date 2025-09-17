#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-time мониторинг на основе AlorPy, но адаптированный под API токен
"""

import os
import time
import logging
from datetime import datetime
from alor_api import AlorAPI

logger = logging.getLogger(__name__)


class AlorRealTimeMonitor:
    """Real-time мониторинг котировок с использованием быстрых HTTP запросов"""
    
    def __init__(self, update_interval=3.0):
        self.alor = AlorAPI()
        self.update_interval = update_interval
        self.running = False
        self.previous_data = {}
        self.update_count = 0
        
    def clear_screen(self):
        """Очищает экран"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_order_book_data(self, symbol):
        """
        Получает данные стакана через HTTP API
        Имитирует real-time через частые запросы
        """
        try:
            quote_data = self.alor.get_quote(symbol)
            if quote_data and 'error' not in quote_data:
                return {
                    'symbol': symbol,
                    'bid': quote_data.get('bid'),
                    'ask': quote_data.get('ask'),
                    'last_price': quote_data.get('last_price'),
                    'orderbook_time': quote_data.get('orderbook_time'),
                    'last_trade_time': quote_data.get('last_trade_time'),
                    'volume': quote_data.get('volume'),
                    'change_percent': quote_data.get('change_percent')
                }
            return None
        except Exception as e:
            logger.error(f"Ошибка получения данных {symbol}: {e}")
            return None
    
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
    
    def display_realtime_table(self, instruments_data):
        """Отображает таблицу котировок в реальном времени"""
        self.clear_screen()
        
        print("=" * 100)
        print("⚡ REAL-TIME МОНИТОРИНГ ALOR (Быстрый HTTP)")
        print("=" * 100)
        print(f"{'Инстр':<6} {'Bid':<10} {'Ask':<10} {'Last':<10} {'Спред':<8} {'Изм%':<8} {'Объем':<10} {'Обновлен':<12}")
        print("-" * 100)
        
        current_time = datetime.now()
        
        for symbol, data in instruments_data.items():
            if not data:
                print(f"{symbol:<6} {'ERROR':<10} {'ERROR':<10} {'ERROR':<10} {'ERROR':<8} {'ERROR':<8} {'ERROR':<10} {'ERROR':<12}")
                continue
            
            # Получаем предыдущие данные
            prev_data = self.previous_data.get(symbol, {})
            
            bid = data.get('bid', 0)
            ask = data.get('ask', 0) 
            last = data.get('last_price', 0)
            change_pct = data.get('change_percent', 0)
            volume = data.get('volume', 0)
            orderbook_time = data.get('orderbook_time')
            
            # Индикаторы изменения
            bid_ind = self.format_change_indicator(bid, prev_data.get('bid'))
            ask_ind = self.format_change_indicator(ask, prev_data.get('ask'))
            last_ind = self.format_change_indicator(last, prev_data.get('last_price'))
            
            # Спред
            spread = ask - bid if (bid and ask) else 0
            
            # Форматируем объем
            if volume >= 1000:
                vol_str = f"{volume/1000:.1f}k"
            else:
                vol_str = str(int(volume))
            
            # Время обновления
            if orderbook_time and 'T' in str(orderbook_time):
                time_str = str(orderbook_time).split('T')[1][:8]
                
                # Рассчитываем задержку
                try:
                    ob_time = datetime.fromisoformat(str(orderbook_time).replace('Z', '+00:00'))
                    delay = (current_time - ob_time.replace(tzinfo=None)).total_seconds()
                    if delay > 60:
                        time_str += f" (-{int(delay/60)}м)"
                    elif delay > 5:
                        time_str += f" (-{int(delay)}с)"
                except:
                    pass
            else:
                time_str = "NO_DATA"
            
            # Форматируем строку
            print(f"{symbol:<6} {bid_ind}{bid:<9.4f} {ask_ind}{ask:<9.4f} {last_ind}{last:<9.4f} {spread:<8.4f} {change_pct:<+7.2f}% {vol_str:<10} {time_str:<12}")
        
        print("-" * 100)
        print(f"⏰ Обновлено: {current_time.strftime('%H:%M:%S')} | 🔄 Интервал: {self.update_interval}с | #{self.update_count}")
        print("=" * 100)
    
    def start_monitoring(self):
        """Запускает мониторинг"""
        instruments = self.alor.load_instruments_list()
        
        if not instruments:
            print("❌ Список инструментов пуст")
            return
        
        print(f"⚡ Запуск real-time мониторинга для {len(instruments)} инструментов")
        print(f"🔄 Интервал: {self.update_interval} секунд")
        print("❌ Ctrl+C для остановки")
        time.sleep(2)
        
        self.running = True
        
        try:
            while self.running:
                start_time = time.time()
                
                # Получаем данные по всем инструментам
                instruments_data = {}
                for symbol in instruments:
                    instruments_data[symbol] = self.get_order_book_data(symbol)
                
                request_time = time.time() - start_time
                
                # Отображаем данные
                self.display_realtime_table(instruments_data)
                
                print(f"📊 Время запроса: {request_time:.2f}с")
                
                # Показываем задержку данных
                delays = []
                for symbol, data in instruments_data.items():
                    if data and data.get('orderbook_time'):
                        try:
                            ob_time = datetime.fromisoformat(str(data['orderbook_time']).replace('Z', '+00:00'))
                            delay = (datetime.now() - ob_time.replace(tzinfo=None)).total_seconds()
                            delays.append(delay)
                        except:
                            pass
                
                if delays:
                    avg_delay = sum(delays) / len(delays)
                    print(f"⏱️  Средняя задержка данных: {avg_delay:.0f} секунд")
                
                # Сохраняем данные для сравнения
                self.previous_data = {k: v for k, v in instruments_data.items() if v}
                self.update_count += 1
                
                # Ждем до следующего обновления
                time.sleep(max(0, self.update_interval - request_time))
                
        except KeyboardInterrupt:
            print(f"\n🛑 Мониторинг остановлен. Обновлений: {self.update_count}")
            self.running = False
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.running = False


def main():
    print("⚡ REAL-TIME МОНИТОРИНГ ALOR")
    print("Анализ задержки данных")
    print("=" * 50)
    
    # Выбор интервала
    intervals = {
        "1": 3.0,
        "2": 5.0, 
        "3": 7.0,
        "4": 10.0
    }
    
    print("Интервалы обновления:")
    print("1. 3 секунды")
    print("2. 5 секунд (по умолчанию)")
    print("3. 7 секунд") 
    print("4. 10 секунд")
    
    choice = input("Выберите (1-4): ").strip() or "2"
    interval = intervals.get(choice, 5.0)
    
    print(f"✅ Интервал: {interval} секунд")
    
    monitor = AlorRealTimeMonitor(update_interval=interval)
    monitor.start_monitoring()


if __name__ == "__main__":
    main()
