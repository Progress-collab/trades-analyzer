#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Измерение задержки WebSocket данных от Alor API в миллисекундах
"""

import sys
import os
import logging
from datetime import datetime
from time import sleep
import json

# Добавляем путь к AlorPy
sys.path.append(os.path.join(os.path.dirname(__file__), 'AlorPy'))

from AlorPy import AlorPy

# Настройка логирования
logging.basicConfig(level=logging.ERROR)


class LatencyMeasurer:
    """Измеритель задержки WebSocket данных"""
    
    def __init__(self):
        # Загружаем токен
        self.refresh_token = self._load_token()
        if not self.refresh_token:
            raise ValueError("Refresh Token не найден!")
        
        self.ap = AlorPy(refresh_token=self.refresh_token)
        self.measurements = []
        
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
        try:
            receive_time = datetime.now()
            data = response.get('data', {})
            
            if data.get('bids') and data.get('asks'):
                # Получаем время от биржи если есть
                exchange_timestamp = data.get('timestamp')  # Время от биржи
                
                if exchange_timestamp:
                    # Конвертируем timestamp биржи в datetime
                    if isinstance(exchange_timestamp, (int, float)):
                        exchange_time = datetime.fromtimestamp(exchange_timestamp)
                    else:
                        exchange_time = datetime.fromisoformat(str(exchange_timestamp).replace('Z', '+00:00'))
                        exchange_time = exchange_time.replace(tzinfo=None)
                    
                    # Рассчитываем задержку в миллисекундах
                    latency_ms = (receive_time - exchange_time).total_seconds() * 1000
                    
                    self.measurements.append({
                        'latency_ms': latency_ms,
                        'exchange_time': exchange_time,
                        'receive_time': receive_time,
                        'bid': data['bids'][0]['price'],
                        'ask': data['asks'][0]['price']
                    })
                    
                    print(f"📊 {receive_time.strftime('%H:%M:%S.%f')[:-3]} | "
                          f"Биржа: {exchange_time.strftime('%H:%M:%S.%f')[:-3]} | "
                          f"Задержка: {latency_ms:+8.1f}мс | "
                          f"Bid: {data['bids'][0]['price']:.4f}")
                else:
                    # Если нет времени от биржи, просто показываем получение данных
                    print(f"📊 {receive_time.strftime('%H:%M:%S.%f')[:-3]} | "
                          f"Bid: {data['bids'][0]['price']:.4f} | "
                          f"Ask: {data['asks'][0]['price']:.4f} | "
                          f"Нет timestamp биржи")
                
                # Показываем статистику каждые 20 измерений
                if len(self.measurements) > 0 and len(self.measurements) % 20 == 0:
                    self.show_latency_stats()
                    
        except Exception as e:
            print(f"❌ Ошибка измерения: {e}")
    
    def show_latency_stats(self):
        """Показывает статистику задержки"""
        if not self.measurements:
            return
        
        latencies = [m['latency_ms'] for m in self.measurements[-20:]]  # Последние 20
        
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        
        print("\n" + "="*60)
        print("📈 СТАТИСТИКА ЗАДЕРЖКИ (последние 20 измерений)")
        print("="*60)
        print(f"📊 Средняя задержка: {avg_latency:6.1f} мс")
        print(f"📊 Минимальная:     {min_latency:6.1f} мс")
        print(f"📊 Максимальная:    {max_latency:6.1f} мс")
        print(f"📊 Всего измерений: {len(self.measurements)}")
        print("="*60 + "\n")
    
    def start_measurement(self):
        """Запускает измерение задержки"""
        print("⏱️  ИЗМЕРЕНИЕ ЗАДЕРЖКИ WEBSOCKET ALOR")
        print("=" * 60)
        print("🎯 Подписываемся на PDU5 для измерения задержки...")
        
        try:
            # Устанавливаем обработчик
            self.ap.on_change_order_book = self.on_orderbook_update
            
            # Подписываемся на один инструмент для чистого измерения
            guid = self.ap.order_book_get_and_subscribe('MOEX', 'PDU5')
            print(f"✅ Подписка создана: {guid}")
            print("⚡ Измеряем задержку... (Ctrl+C для остановки)")
            print("-" * 60)
            
            # Ждем обновления
            while True:
                sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Измерение остановлено")
            
            # Финальная статистика
            if self.measurements:
                self.show_latency_stats()
                
                # Дополнительная статистика
                all_latencies = [m['latency_ms'] for m in self.measurements]
                print("📈 ОБЩАЯ СТАТИСТИКА:")
                print(f"   Измерений: {len(all_latencies)}")
                print(f"   Средняя задержка: {sum(all_latencies)/len(all_latencies):.1f} мс")
                print(f"   Диапазон: {min(all_latencies):.1f} - {max(all_latencies):.1f} мс")
            
            # Отписываемся
            try:
                self.ap.unsubscribe(guid)
                self.ap.close_web_socket()
                print("✅ WebSocket закрыт")
            except:
                pass
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()


def main():
    try:
        measurer = LatencyMeasurer()
        measurer.start_measurement()
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")


if __name__ == "__main__":
    main()
