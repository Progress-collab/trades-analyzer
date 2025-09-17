#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Финальный real-time мониторинг на основе AlorPy
Настоящие real-time данные через WebSocket
"""

import sys
import os
import logging
from datetime import datetime
from time import sleep

# Добавляем путь к AlorPy
sys.path.append(os.path.join(os.path.dirname(__file__), 'AlorPy'))

from AlorPy import AlorPy

# Настройка логирования (только ошибки)
logging.basicConfig(level=logging.ERROR)


class AlorRealTimeFinal:
    """Финальный real-time мониторинг через WebSocket"""
    
    def __init__(self):
        # Загружаем токен из .env
        self.refresh_token = self._load_token()
        if not self.refresh_token:
            raise ValueError("Refresh Token не найден в .env файле!")
        
        self.ap = AlorPy(refresh_token=self.refresh_token)
        self.instruments_data = {}
        self.running = False
        self.update_count = 0
        
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
    
    def format_change(self, current, previous):
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
        try:
            data = response.get('data', {})
            
            # Получаем символ из подписки, а не из response
            guid = response.get('guid')
            symbol = 'UNKNOWN'
            
            if guid and guid in self.ap.subscriptions:
                subscription = self.ap.subscriptions[guid]
                symbol = subscription.get('code', 'UNKNOWN')
            
            if data.get('bids') and data.get('asks'):
                bid = data['bids'][0]['price']
                ask = data['asks'][0]['price']
                
                # Сохраняем предыдущие данные
                prev_data = self.instruments_data.get(symbol, {})
                
                # Обновляем данные
                self.instruments_data[symbol] = {
                    'bid': bid,
                    'ask': ask,
                    'prev_bid': prev_data.get('bid'),
                    'prev_ask': prev_data.get('ask'),
                    'timestamp': datetime.now(),
                    'spread': ask - bid
                }
                
                self.update_count += 1
                
                # Обновляем дисплей только каждые 10 обновлений (чтобы не мигало)
                if self.update_count % 10 == 0:
                    self.display_table()
                
        except Exception as e:
            print(f"❌ Ошибка обработки стакана: {e}")
    
    def display_table(self):
        """Отображает таблицу котировок"""
        self.clear_screen()
        
        print("=" * 80)
        print("🔥 REAL-TIME МОНИТОРИНГ ALOR (WebSocket)")
        print("=" * 80)
        print(f"{'Инстр':<6} {'Bid':<12} {'Ask':<12} {'Спред':<10} {'Время':<15}")
        print("-" * 80)
        
        for symbol, data in self.instruments_data.items():
            bid = data.get('bid', 0)
            ask = data.get('ask', 0)
            spread = data.get('spread', 0)
            timestamp = data.get('timestamp', datetime.now())
            
            # Индикаторы изменения
            bid_ind = self.format_change(bid, data.get('prev_bid'))
            ask_ind = self.format_change(ask, data.get('prev_ask'))
            
            time_str = timestamp.strftime("%H:%M:%S.%f")[:-3]  # С миллисекундами
            
            print(f"{symbol:<6} {bid_ind}{bid:<11.4f} {ask_ind}{ask:<11.4f} {spread:<10.4f} {time_str:<15}")
        
        print("-" * 80)
        print(f"⏰ Обновлений: {self.update_count} | 🔄 Real-time WebSocket | ❌ Ctrl+C выход")
        print("=" * 80)
    
    def start_monitoring(self):
        """Запускает real-time мониторинг"""
        instruments = self.load_instruments_list()
        
        if not instruments:
            print("❌ Список инструментов пуст")
            return
        
        print(f"🚀 Запуск REAL-TIME мониторинга для {len(instruments)} инструментов")
        print("🔔 Подписка на WebSocket обновления стакана...")
        
        try:
            # Устанавливаем обработчик
            self.ap.on_change_order_book = self.on_orderbook_update
            
            # Подписываемся на все инструменты
            subscriptions = []
            for symbol in instruments:
                print(f"📡 Подписка на {symbol}...")
                guid = self.ap.order_book_get_and_subscribe('MOEX', symbol)
                subscriptions.append(guid)
                sleep(0.2)  # Небольшая задержка между подписками
            
            print(f"✅ Подписки созданы: {len(subscriptions)}")
            print("⚡ Получение real-time данных...")
            print("❌ Нажмите Ctrl+C для остановки")
            
            self.running = True
            
            # Ждем real-time обновления
            while self.running:
                sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Остановка мониторинга...")
            
            # Отписываемся от всех подписок
            for guid in subscriptions:
                try:
                    self.ap.unsubscribe(guid)
                except:
                    pass
            
            print(f"📊 Всего обновлений: {self.update_count}")
            self.running = False
            
        except Exception as e:
            print(f"❌ Ошибка мониторинга: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            try:
                self.ap.close_web_socket()
                print("✅ WebSocket закрыт")
            except:
                pass


def main():
    try:
        monitor = AlorRealTimeFinal()
        monitor.start_monitoring()
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")


if __name__ == "__main__":
    main()
