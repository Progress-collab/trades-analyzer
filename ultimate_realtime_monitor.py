#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ULTIMATE REAL-TIME МОНИТОРИНГ ВСЕХ ФЬЮЧЕРСОВ
С отображением реальной задержки на основе ms_timestamp
"""

import os
import sys
from datetime import datetime
from time import sleep
import threading

# Добавляем путь к AlorPy
sys.path.append(os.path.join(os.path.dirname(__file__), 'AlorPy'))

from AlorPy import AlorPy


class UltimateRealTimeMonitor:
    """Ultimate real-time мониторинг с анализом задержки"""
    
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
        self.latency_measurements = []
        
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
    
    def calculate_latency(self, computer_time, data):
        """Рассчитывает задержку на основе ms_timestamp"""
        try:
            if 'ms_timestamp' in data:
                ms_ts = data['ms_timestamp']
                if isinstance(ms_ts, (int, float)) and ms_ts > 1e12:
                    exchange_time = datetime.fromtimestamp(ms_ts / 1000)
                    latency_ms = (computer_time - exchange_time).total_seconds() * 1000
                    return latency_ms, exchange_time
        except:
            pass
        return None, None
    
    def on_orderbook_update(self, response):
        """Обработчик обновления стакана"""
        if not self.running:
            return
            
        try:
            computer_time = datetime.now()
            data = response.get('data', {})
            guid = response.get('guid')
            
            # Получаем символ из подписки
            symbol = 'UNKNOWN'
            if guid and guid in self.ap.subscriptions:
                subscription = self.ap.subscriptions[guid]
                symbol = subscription.get('code', 'UNKNOWN')
            
            if data.get('bids') and data.get('asks') and symbol != 'UNKNOWN':
                bid = data['bids'][0]['price']
                ask = data['asks'][0]['price']
                spread = ask - bid
                
                # Рассчитываем задержку
                latency_ms, exchange_time = self.calculate_latency(computer_time, data)
                
                # Сохраняем измерение задержки
                if latency_ms is not None:
                    self.latency_measurements.append(latency_ms)
                    # Храним только последние 50 измерений
                    if len(self.latency_measurements) > 50:
                        self.latency_measurements.pop(0)
                
                # Сохраняем предыдущие данные
                prev_data = self.instruments_data.get(symbol, {})
                
                # Обновляем данные
                self.instruments_data[symbol] = {
                    'bid': bid,
                    'ask': ask,
                    'spread': spread,
                    'prev_bid': prev_data.get('bid'),
                    'prev_ask': prev_data.get('ask'),
                    'last_update': computer_time,
                    'exchange_time': exchange_time,
                    'latency_ms': latency_ms,
                    'update_count': prev_data.get('update_count', 0) + 1
                }
                
                self.update_count += 1
                
                # Обновляем дисплей каждые 3 обновления
                if self.update_count % 3 == 0:
                    self.display_table()
                    
        except Exception as e:
            print(f"❌ Ошибка обработки: {e}")
    
    def get_avg_latency(self):
        """Возвращает среднюю задержку"""
        if self.latency_measurements:
            return sum(self.latency_measurements) / len(self.latency_measurements)
        return 0
    
    def display_table(self):
        """Отображает таблицу котировок с задержкой"""
        if not self.instruments_data:
            return
            
        self.clear_screen()
        
        print("=" * 100)
        print("🚀 ULTIMATE REAL-TIME МОНИТОРИНГ ФЬЮЧЕРСОВ (с анализом задержки)")
        print("=" * 100)
        
        # Время работы и средняя задержка
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
            avg_latency = self.get_avg_latency()
            print(f"⏰ Время работы: {uptime:.0f}с | 📊 Обновлений: {self.update_count} | ⚡ Средняя задержка: {avg_latency:.0f}мс")
        
        print(f"{'Фьючерс':<8} {'Bid':<12} {'Ask':<12} {'Спред':<8} {'Задержка':<10} {'Обновл.':<8} {'Время биржи':<12}")
        print("-" * 100)
        
        # Сортируем по названию инструмента
        sorted_instruments = sorted(self.instruments_data.items())
        
        for symbol, data in sorted_instruments:
            bid = data.get('bid', 0)
            ask = data.get('ask', 0)
            spread = data.get('spread', 0)
            latency_ms = data.get('latency_ms')
            update_count = data.get('update_count', 0)
            exchange_time = data.get('exchange_time')
            
            # Индикаторы изменения
            bid_ind = self.format_change_indicator(bid, data.get('prev_bid'))
            ask_ind = self.format_change_indicator(ask, data.get('prev_ask'))
            
            # Форматируем задержку
            if latency_ms is not None:
                if latency_ms < 100:
                    latency_str = f"✅{latency_ms:>6.0f}мс"
                elif latency_ms < 200:
                    latency_str = f"⚡{latency_ms:>6.0f}мс"
                else:
                    latency_str = f"⚠️{latency_ms:>6.0f}мс"
            else:
                latency_str = "   N/A   "
            
            # Время биржи
            if exchange_time:
                time_str = exchange_time.strftime("%H:%M:%S.%f")[:-3]
            else:
                time_str = "N/A"
            
            # Индикатор активности
            if update_count > 50:
                activity = "🔥"
            elif update_count > 20:
                activity = "⚡"
            elif update_count > 5:
                activity = "📊"
            else:
                activity = "💤"
            
            print(f"{symbol:<8} {bid_ind}{bid:<11.2f} {ask_ind}{ask:<11.2f} {spread:<8.2f} "
                  f"{latency_str:<10} {activity}{update_count:<7d} {time_str:<12}")
        
        print("-" * 100)
        
        # Статистика задержки
        if self.latency_measurements:
            recent_latencies = self.latency_measurements[-10:]  # Последние 10
            avg_recent = sum(recent_latencies) / len(recent_latencies)
            min_recent = min(recent_latencies)
            max_recent = max(recent_latencies)
            
            print(f"📈 Задержка (последние 10): Средняя {avg_recent:.0f}мс | "
                  f"Диапазон {min_recent:.0f}-{max_recent:.0f}мс")
        
        current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"🔄 Обновлено: {current_time} | 🌐 WebSocket Real-time | ❌ Ctrl+C для выхода")
        print("=" * 100)
    
    def start_monitoring(self):
        """Запускает ultimate мониторинг"""
        instruments = self.load_instruments_list()
        
        if not instruments:
            print("❌ Список инструментов пуст")
            return
        
        print("🚀 ULTIMATE REAL-TIME МОНИТОРИНГ")
        print("=" * 60)
        print(f"📊 Инструменты: {', '.join(instruments)}")
        print("⚡ WebSocket подписка с анализом задержки...")
        print("🎯 Ожидаемая задержка: ~120-150мс")
        print("-" * 60)
        
        try:
            # Устанавливаем обработчик
            self.ap.on_change_order_book = self.on_orderbook_update
            
            # Подписываемся на все инструменты
            for i, symbol in enumerate(instruments):
                print(f"📡 {i+1}/{len(instruments)} Подписка на {symbol}...")
                guid = self.ap.order_book_get_and_subscribe('MOEX', symbol)
                self.subscriptions.append((guid, symbol))
                sleep(0.3)  # Пауза между подписками
            
            print(f"✅ Все подписки созданы: {len(self.subscriptions)}")
            print("🔥 Получение real-time данных с анализом задержки...")
            print("-" * 60)
            
            self.start_time = datetime.now()
            self.running = True
            
            # Ждем обновления
            while self.running:
                sleep(0.5)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Остановка мониторинга...")
            self.stop_monitoring()
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Останавливает мониторинг с детальной статистикой"""
        self.running = False
        
        print("📤 Отписка от обновлений...")
        for i, (guid, symbol) in enumerate(self.subscriptions):
            try:
                self.ap.unsubscribe(guid)
                print(f"✅ Отписка {symbol} ({i+1}/{len(self.subscriptions)})")
            except:
                pass
        
        # Детальная финальная статистика
        if self.instruments_data and self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
            total_updates = sum(data.get('update_count', 0) for data in self.instruments_data.values())
            
            print(f"\n📈 ФИНАЛЬНАЯ СТАТИСТИКА:")
            print("="*60)
            print(f"⏰ Время работы:      {uptime:.0f} секунд")
            print(f"📊 Всего обновлений:  {total_updates}")
            print(f"🔄 Общая частота:     {total_updates/uptime:.1f} обновлений/сек")
            
            # Статистика задержки
            if self.latency_measurements:
                avg_latency = sum(self.latency_measurements) / len(self.latency_measurements)
                min_latency = min(self.latency_measurements)
                max_latency = max(self.latency_measurements)
                
                print(f"\n⚡ АНАЛИЗ ЗАДЕРЖКИ:")
                print(f"   📊 Измерений:      {len(self.latency_measurements)}")
                print(f"   📊 Средняя:        {avg_latency:6.1f} мс")
                print(f"   📊 Минимальная:    {min_latency:6.1f} мс")
                print(f"   📊 Максимальная:   {max_latency:6.1f} мс")
                
                if avg_latency < 100:
                    print("   ✅ ОТЛИЧНО: Очень быстрая система!")
                elif avg_latency < 200:
                    print("   ✅ ХОРОШО: Быстрая система")
                else:
                    print("   ⚠️ ПРИЕМЛЕМО: Нормальная скорость")
            
            # Статистика по инструментам
            print(f"\n📊 АКТИВНОСТЬ ПО ИНСТРУМЕНТАМ:")
            for symbol, data in sorted(self.instruments_data.items()):
                updates = data.get('update_count', 0)
                freq = updates / uptime
                last_latency = data.get('latency_ms', 0)
                
                if freq > 2:
                    activity_icon = "🔥"
                elif freq > 1:
                    activity_icon = "⚡"
                elif freq > 0.5:
                    activity_icon = "📊"
                else:
                    activity_icon = "💤"
                
                print(f"   {activity_icon} {symbol}: {updates:3d} обновлений "
                      f"({freq:.1f}/сек) | Задержка: {last_latency:.0f}мс")
            
            print("="*60)
        
        try:
            self.ap.close_web_socket()
            print("✅ WebSocket закрыт")
        except:
            pass
        
        print("🎯 Ultimate мониторинг завершен")
        
        # Принудительное завершение процесса (избегаем зависания)
        print("🔄 Завершение процесса...")
        os._exit(0)
    
    def on_orderbook_update(self, response):
        """Обработчик обновления стакана с анализом задержки"""
        if not self.running:
            return
            
        try:
            computer_time = datetime.now()
            data = response.get('data', {})
            guid = response.get('guid')
            
            # Получаем символ из подписки
            symbol = 'UNKNOWN'
            if guid and guid in self.ap.subscriptions:
                subscription = self.ap.subscriptions[guid]
                symbol = subscription.get('code', 'UNKNOWN')
            
            if data.get('bids') and data.get('asks') and symbol != 'UNKNOWN':
                bid = data['bids'][0]['price']
                ask = data['asks'][0]['price']
                spread = ask - bid
                
                # Рассчитываем задержку
                latency_ms, exchange_time = self.calculate_latency(computer_time, data)
                
                # Сохраняем измерение задержки
                if latency_ms is not None and 0 < latency_ms < 2000:  # Фильтруем аномальные значения
                    self.latency_measurements.append(latency_ms)
                
                # Сохраняем предыдущие данные
                prev_data = self.instruments_data.get(symbol, {})
                
                # Обновляем данные
                self.instruments_data[symbol] = {
                    'bid': bid,
                    'ask': ask,
                    'spread': spread,
                    'prev_bid': prev_data.get('bid'),
                    'prev_ask': prev_data.get('ask'),
                    'last_update': computer_time,
                    'exchange_time': exchange_time,
                    'latency_ms': latency_ms,
                    'update_count': prev_data.get('update_count', 0) + 1
                }
                
                self.update_count += 1
                
                # Обновляем дисплей каждые 5 обновлений
                if self.update_count % 5 == 0:
                    self.display_table()
                    
        except Exception as e:
            print(f"❌ Ошибка обработки: {e}")
    
    def start_monitoring(self):
        """Запускает ultimate мониторинг"""
        instruments = self.load_instruments_list()
        
        if not instruments:
            print("❌ Список инструментов пуст")
            return
        
        print("🚀 ULTIMATE REAL-TIME МОНИТОРИНГ ФЬЮЧЕРСОВ")
        print("=" * 70)
        print(f"📊 Инструменты: {', '.join(instruments)}")
        print("⚡ WebSocket подписка с real-time анализом задержки")
        print("🎯 Целевая задержка: ~120-150мс (по результатам тестов)")
        print("-" * 70)
        
        try:
            # Устанавливаем обработчик
            self.ap.on_change_order_book = self.on_orderbook_update
            
            # Подписываемся на все инструменты
            for i, symbol in enumerate(instruments):
                print(f"📡 {i+1}/{len(instruments)} Подписка на {symbol}...")
                guid = self.ap.order_book_get_and_subscribe('MOEX', symbol)
                self.subscriptions.append((guid, symbol))
                sleep(0.3)
            
            print(f"✅ Все подписки созданы: {len(self.subscriptions)}")
            print("🔥 Получение real-time данных...")
            print("-" * 70)
            
            self.start_time = datetime.now()
            self.running = True
            
            # Ждем обновления
            while self.running:
                sleep(0.5)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Остановка ultimate мониторинга...")
            self.stop_monitoring()
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            self.stop_monitoring()
        
        # Дополнительная защита от зависания
        os._exit(0)


def main():
    print("🚀 ULTIMATE REAL-TIME МОНИТОРИНГ ФЬЮЧЕРСОВ")
    print("=" * 70)
    print("🌐 WebSocket подписка на все фьючерсы")
    print("⚡ Real-time обновления с анализом задержки")
    print("🎯 Основано на тестах: задержка ~120-150мс")
    print("❌ Ctrl+C для остановки")
    print("-" * 70)
    
    try:
        monitor = UltimateRealTimeMonitor()
        monitor.start_monitoring()
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        os._exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Остановлено пользователем")
        os._exit(0)


if __name__ == "__main__":
    main()
