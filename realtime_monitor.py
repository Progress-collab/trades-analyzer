#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-time мониторинг bid/ask котировок через API Alor
Обновляемая консольная таблица с минимальными задержками
"""

import os
import time
import logging
from datetime import datetime
from alor_api import AlorAPI

# Настройка логирования (только ошибки)
logging.basicConfig(level=logging.ERROR)


class RealTimeMonitor:
    """Real-time мониторинг котировок"""
    
    def __init__(self, update_interval=1.0):
        """
        Args:
            update_interval: Интервал обновления в секундах
        """
        self.alor = AlorAPI()
        self.update_interval = update_interval
        self.running = False
        self.previous_data = {}
        
    def clear_screen(self):
        """Очищает экран консоли"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def format_price_change(self, current, previous):
        """
        Форматирует изменение цены с цветовыми индикаторами
        
        Args:
            current: Текущая цена
            previous: Предыдущая цена
            
        Returns:
            Строка с индикатором изменения
        """
        if previous is None or current is None:
            return f"{current:>8.4f}" if current else "    N/A "
        
        if current > previous:
            return f"📈{current:>7.4f}"  # Рост
        elif current < previous:
            return f"📉{current:>7.4f}"  # Падение
        else:
            return f"➡️{current:>7.4f}"   # Без изменений
    
    def print_header(self):
        """Выводит заголовок таблицы"""
        print("=" * 90)
        print("🔥 REAL-TIME BID/ASK МОНИТОРИНГ ALOR")
        print("=" * 90)
        print(f"{'Инструмент':<8} {'Bid':<12} {'Ask':<12} {'Last':<12} {'Change %':<10} {'Время сделки':<19}")
        print("-" * 90)
    
    def print_quote_row(self, symbol, data):
        """
        Выводит строку с котировкой
        
        Args:
            symbol: Символ инструмента
            data: Данные котировки
        """
        if 'error' in data:
            print(f"{symbol:<8} {'ERROR':<12} {'ERROR':<12} {'ERROR':<12} {'ERROR':<10} {'ERROR':<19}")
            return
        
        # Получаем текущие данные
        bid = data.get('bid')
        ask = data.get('ask') 
        last = data.get('last_price')
        change_pct = data.get('change_percent', 0)
        trade_time = data.get('last_trade_time', 'N/A')
        
        # Получаем предыдущие данные для сравнения
        prev_data = self.previous_data.get(symbol, {})
        prev_bid = prev_data.get('bid')
        prev_ask = prev_data.get('ask')
        prev_last = prev_data.get('last_price')
        
        # Форматируем с индикаторами изменения
        bid_str = self.format_price_change(bid, prev_bid)
        ask_str = self.format_price_change(ask, prev_ask)
        last_str = self.format_price_change(last, prev_last)
        
        # Форматируем изменение в процентах
        if change_pct > 0:
            change_str = f"📈{change_pct:+6.2f}%"
        elif change_pct < 0:
            change_str = f"📉{change_pct:+6.2f}%"
        else:
            change_str = f"➡️{change_pct:+6.2f}%"
        
        # Форматируем время (только время без даты)
        if trade_time != 'N/A' and 'T' in trade_time:
            time_only = trade_time.split('T')[1][:8]  # HH:MM:SS
        else:
            time_only = trade_time
        
        print(f"{symbol:<8} {bid_str:<12} {ask_str:<12} {last_str:<12} {change_str:<10} {time_only:<19}")
    
    def print_footer(self):
        """Выводит подвал с информацией об обновлении"""
        print("-" * 90)
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"⏰ Обновлено: {current_time} | 🔄 Интервал: {self.update_interval}с | ❌ Ctrl+C для выхода")
        print("=" * 90)
    
    def update_display(self):
        """Обновляет отображение котировок"""
        try:
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
            
            self.print_footer()
            
            # Сохраняем текущие данные для следующего сравнения
            self.previous_data = {
                symbol: data for symbol, data in quotes.items() 
                if 'error' not in data
            }
            
        except Exception as e:
            print(f"❌ Ошибка при обновлении: {e}")
    
    def start_monitoring(self):
        """Запускает real-time мониторинг"""
        print("🚀 Запуск real-time мониторинга...")
        print("❌ Нажмите Ctrl+C для остановки")
        
        # Проверяем API перед запуском
        try:
            instruments = self.alor.load_instruments_list()
            if not instruments:
                print("❌ Не удалось загрузить список инструментов")
                return
            print(f"✅ Загружено {len(instruments)} инструментов: {', '.join(instruments)}")
        except Exception as e:
            print(f"❌ Ошибка инициализации API: {e}")
            return
        
        time.sleep(2)
        self.running = True
        
        try:
            iteration = 0
            while self.running:
                iteration += 1
                print(f"🔄 Обновление #{iteration}...")
                self.update_display()
                time.sleep(self.update_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Мониторинг остановлен пользователем")
            self.running = False
        except Exception as e:
            print(f"\n\n❌ Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
            self.running = False


def main():
    """Основная функция"""
    print("🔥 REAL-TIME МОНИТОРИНГ BID/ASK")
    print("=" * 50)
    
    # Используем фиксированный интервал без ввода пользователя
    interval = 2.0  # 2 секунды - безопасный интервал
    print(f"⏱️  Интервал обновления: {interval} секунды")
    
    # Создаем и запускаем монитор
    monitor = RealTimeMonitor(update_interval=interval)
    monitor.start_monitoring()


if __name__ == "__main__":
    main()
