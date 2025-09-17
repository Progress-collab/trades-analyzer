#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрый real-time мониторинг через HTTP API с высокой частотой
Интервал 0.5 секунды - достаточно для мониторинга
"""

import os
import time
import asyncio
import logging
from datetime import datetime
from alor_api import AlorAPI

# Настройка логирования (только ошибки)
logging.basicConfig(level=logging.ERROR)


class FastRealTimeMonitor:
    """Быстрый real-time мониторинг через HTTP API"""
    
    def __init__(self, update_interval=0.5):
        """
        Args:
            update_interval: Интервал обновления в секундах (по умолчанию 0.5с)
        """
        self.alor = AlorAPI()
        self.update_interval = update_interval
        self.running = False
        self.previous_data = {}
        self.update_count = 0
        
    def clear_screen(self):
        """Очищает экран консоли"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def format_price_with_change(self, current, previous, precision=4):
        """
        Форматирует цену с индикатором изменения
        
        Args:
            current: Текущая цена
            previous: Предыдущая цена
            precision: Количество знаков после запятой
            
        Returns:
            Строка с индикатором изменения
        """
        if current is None:
            return "     N/A "
        
        if previous is None:
            return f" {current:>{8}.{precision}f}"
        
        if current > previous:
            return f"↑{current:>{8}.{precision}f}"  # Рост - стрелка вверх
        elif current < previous:
            return f"↓{current:>{8}.{precision}f}"  # Падение - стрелка вниз
        else:
            return f"={current:>{8}.{precision}f}"   # Без изменений - равно
    
    def print_header(self):
        """Выводит заголовок таблицы"""
        print("=" * 110)
        print("⚡ БЫСТРЫЙ REAL-TIME МОНИТОРИНГ ALOR (HTTP API)")
        print("=" * 110)
        print(f"{'Инстр.':<6} {'Bid':<12} {'Ask':<12} {'Last':<12} {'Spread':<8} {'Change%':<9} {'Vol.':<8} {'Обновлен':<15}")
        print("-" * 110)
    
    def print_quote_row(self, symbol, data):
        """
        Выводит строку с котировкой
        
        Args:
            symbol: Символ инструмента
            data: Данные котировки
        """
        if 'error' in data:
            print(f"{symbol:<6} {'ERROR':<12} {'ERROR':<12} {'ERROR':<12} {'ERROR':<8} {'ERROR':<9} {'ERROR':<8} {'ERROR':<15}")
            return
        
        # Получаем текущие данные
        bid = data.get('bid')
        ask = data.get('ask') 
        last = data.get('last_price')
        change_pct = data.get('change_percent', 0)
        volume = data.get('volume', 0)
        orderbook_time = data.get('orderbook_time', 'N/A')
        
        
        # Получаем предыдущие данные для сравнения
        prev_data = self.previous_data.get(symbol, {})
        prev_bid = prev_data.get('bid')
        prev_ask = prev_data.get('ask')
        prev_last = prev_data.get('last_price')
        
        # Форматируем с индикаторами изменения
        bid_str = self.format_price_with_change(bid, prev_bid)
        ask_str = self.format_price_with_change(ask, prev_ask)
        last_str = self.format_price_with_change(last, prev_last)
        
        # Рассчитываем спред
        if isinstance(bid, (int, float)) and isinstance(ask, (int, float)):
            spread = ask - bid
            spread_str = f"{spread:.4f}"
        else:
            spread_str = "N/A"
        
        # Форматируем изменение в процентах
        if change_pct > 0:
            change_str = f"↑{change_pct:+5.2f}%"
        elif change_pct < 0:
            change_str = f"↓{change_pct:+5.2f}%"
        else:
            change_str = f"={change_pct:+5.2f}%"
        
        # Форматируем объем
        if isinstance(volume, (int, float)):
            if volume >= 1000:
                vol_str = f"{volume/1000:.1f}k"
            else:
                vol_str = str(int(volume))
        else:
            vol_str = "N/A"
        
        # Форматируем время обновления стакана от биржи
        if orderbook_time and orderbook_time != 'N/A':
            if 'T' in str(orderbook_time):
                # Извлекаем время с миллисекундами и обрезаем до секунд
                time_part = str(orderbook_time).split('T')[1]
                time_only = time_part[:8]  # HH:MM:SS (без миллисекунд)
            else:
                time_only = str(orderbook_time)[:8]
        else:
            # Если нет времени стакана от биржи, показываем что данных нет
            time_only = "NO_DATA"
        
        print(f"{symbol:<6} {bid_str:<12} {ask_str:<12} {last_str:<12} {spread_str:<8} {change_str:<9} {vol_str:<8} {time_only:<15}")
    
    def print_footer(self):
        """Выводит подвал с информацией об обновлении"""
        print("-" * 110)
        current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # С миллисекундами
        print(f"⏰ Обновлено: {current_time} | 🔄 Интервал: {self.update_interval}с | #{self.update_count} | ❌ Ctrl+C для выхода")
        print("=" * 110)
    
    def update_display(self):
        """Обновляет отображение котировок"""
        try:
            start_time = time.time()
            
            # Загружаем список инструментов
            instruments = self.alor.load_instruments_list()
            
            if not instruments:
                print("❌ Список инструментов пуст")
                return
            
            # Получаем котировки
            quotes = self.alor.get_multiple_quotes(instruments)
            
            # Очищаем экран и выводим данные
            self.clear_screen()
            self.print_header()
            
            # Выводим каждый инструмент
            for symbol in instruments:
                data = quotes.get(symbol, {"error": "Нет данных"})
                self.print_quote_row(symbol, data)
            
            # Время выполнения запроса
            request_time = time.time() - start_time
            
            self.print_footer()
            print(f"📊 Время запроса: {request_time:.3f}с | 🚀 Следующее обновление через {self.update_interval}с")
            
            # Сохраняем текущие данные для следующего сравнения
            self.previous_data = {
                symbol: data for symbol, data in quotes.items() 
                if 'error' not in data
            }
            
            self.update_count += 1
            
        except Exception as e:
            print(f"❌ Ошибка при обновлении: {e}")
    
    def start_monitoring(self):
        """Запускает быстрый мониторинг"""
        print("⚡ Запуск быстрого real-time мониторинга...")
        print(f"🔄 Интервал обновления: {self.update_interval} секунд")
        print("❌ Нажмите Ctrl+C для остановки")
        time.sleep(2)
        
        self.running = True
        request_times = []  # Для отслеживания времени запросов
        
        try:
            while self.running:
                start_time = time.time()
                
                # Получаем данные без вывода на экран
                instruments = self.alor.load_instruments_list()
                if not instruments:
                    print("❌ Список инструментов пуст")
                    break
                
                quotes = self.alor.get_multiple_quotes(instruments)
                request_time = time.time() - start_time
                
                # Выводим данные на экран
                self.clear_screen()
                self.print_header()
                
                for symbol in instruments:
                    data = quotes.get(symbol, {"error": "Нет данных"})
                    self.print_quote_row(symbol, data)
                
                self.print_footer()
                print(f"📊 Время запроса: {request_time:.3f}с | 🚀 Следующее обновление через {self.update_interval}с")
                
                # Сохраняем данные для сравнения
                self.previous_data = {
                    symbol: data for symbol, data in quotes.items() 
                    if 'error' not in data
                }
                self.update_count += 1
                
                # Отслеживаем время запросов
                request_times.append(request_time)
                if len(request_times) > 5:
                    request_times.pop(0)  # Храним только последние 5
                
                avg_request_time = sum(request_times) / len(request_times)
                
                # Проверяем, не слишком ли маленький интервал
                if avg_request_time >= self.update_interval * 0.8:
                    recommended_interval = avg_request_time + 1.0
                    print(f"⚠️  ВНИМАНИЕ: Время запроса {avg_request_time:.1f}с близко к интервалу {self.update_interval}с")
                    print(f"💡 Рекомендуется интервал {recommended_interval:.1f}с или больше")
                
                # Рассчитываем фактический интервал ожидания
                actual_wait = max(0, self.update_interval - request_time)
                time.sleep(actual_wait)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Мониторинг остановлен пользователем")
            print(f"📊 Всего обновлений: {self.update_count}")
            self.running = False
        except Exception as e:
            print(f"\n\n❌ Критическая ошибка: {e}")
            self.running = False


def main():
    """Основная функция"""
    print("⚡ БЫСТРЫЙ REAL-TIME МОНИТОРИНГ")
    print("=" * 50)
    
    # Выбираем интервал обновления
    print("📊 Доступные интервалы:")
    print("  1. 3.0 секунды (быстро)")
    print("  2. 5.0 секунд (оптимально, по умолчанию)")  
    print("  3. 7.0 секунд (комфортно)")
    print("  4. 10.0 секунд (экономично)")
    print("  5. Пользовательский интервал")
    
    try:
        choice = input("⚡ Выберите интервал (1-5, по умолчанию 2): ").strip() or "2"
        
        if choice == "5":
            interval = float(input("🔧 Введите интервал в секундах (минимум 3.0): ") or "5.0")
            if interval < 3.0:
                print("⚠️  Минимальный интервал установлен: 3.0 секунды")
                interval = 3.0
        else:
            intervals = {"1": 3.0, "2": 5.0, "3": 7.0, "4": 10.0}
            interval = intervals.get(choice, 5.0)
        
        print(f"✅ Выбран интервал: {interval} секунд")
        
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
        return
    
    # Создаем и запускаем монитор
    monitor = FastRealTimeMonitor(update_interval=interval)
    monitor.start_monitoring()


if __name__ == "__main__":
    main()
