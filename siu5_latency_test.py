#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Точный тест задержки SiU5 - сравнение времени компьютера и времени в котировке
"""

import os
import sys
from datetime import datetime
from time import sleep
import json

# Добавляем путь к AlorPy
sys.path.append(os.path.join(os.path.dirname(__file__), 'AlorPy'))

from AlorPy import AlorPy


class SiU5LatencyTest:
    """Тест задержки для SiU5 с анализом timestamp"""
    
    def __init__(self):
        self.refresh_token = self._load_token()
        if not self.refresh_token:
            raise ValueError("Токен не найден!")
        
        self.ap = AlorPy(refresh_token=self.refresh_token)
        self.measurements = []
        self.running = False
        
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
    
    def on_orderbook_change(self, response):
        """Обработчик изменения стакана SiU5"""
        if not self.running:
            return
            
        try:
            # Время получения на компьютере (синхронизировано с Google)
            computer_time = datetime.now()
            
            data = response.get('data', {})
            
            if data.get('bids') and data.get('asks'):
                bid = data['bids'][0]['price']
                ask = data['asks'][0]['price']
                spread = ask - bid
                
                # Ищем все возможные поля с временем в данных
                print(f"\n📊 ИЗМЕНЕНИЕ СТАКАНА SiU5 #{len(self.measurements)+1}")
                print("-" * 70)
                print(f"🕐 Время компьютера:     {computer_time.strftime('%H:%M:%S.%f')}")
                print(f"📈 Bid: {bid:>10.2f} | Ask: {ask:>10.2f} | Спред: {spread:>6.2f}")
                
                # Анализируем все временные поля в data
                time_fields_found = []
                
                for key, value in data.items():
                    if 'time' in key.lower() or key in ['timestamp', 'ts', 'datetime']:
                        time_fields_found.append((key, value))
                        print(f"🕐 data.{key}: {value}")
                        
                        # Пробуем конвертировать в читаемое время
                        try:
                            if isinstance(value, (int, float)):
                                if value > 1e12:  # Миллисекунды
                                    dt = datetime.fromtimestamp(value / 1000)
                                    latency_ms = (computer_time - dt).total_seconds() * 1000
                                    print(f"   → {dt.strftime('%H:%M:%S.%f')} (миллисекунды)")
                                    print(f"   ⚡ Задержка: {latency_ms:+7.1f} мс")
                                elif value > 1e9:  # Секунды
                                    dt = datetime.fromtimestamp(value)
                                    latency_ms = (computer_time - dt).total_seconds() * 1000
                                    print(f"   → {dt.strftime('%H:%M:%S.%f')} (секунды)")
                                    print(f"   ⚡ Задержка: {latency_ms:+7.1f} мс")
                            elif isinstance(value, str):
                                if 'T' in value:
                                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                    dt = dt.replace(tzinfo=None)
                                    latency_ms = (computer_time - dt).total_seconds() * 1000
                                    print(f"   → {dt.strftime('%H:%M:%S.%f')} (ISO)")
                                    print(f"   ⚡ Задержка: {latency_ms:+7.1f} мс")
                        except Exception as e:
                            print(f"   ❌ Ошибка конвертации: {e}")
                
                # Анализируем временные поля в response
                for key, value in response.items():
                    if 'time' in key.lower() or key in ['timestamp', 'ts', 'datetime']:
                        if (key, value) not in time_fields_found:  # Избегаем дублирования
                            print(f"🕐 response.{key}: {value}")
                
                # Если не нашли временных полей
                if not time_fields_found:
                    print("⚠️  Временные поля в данных не найдены")
                    print("💡 Возможно, время передается в другом формате")
                
                self.measurements.append({
                    'computer_time': computer_time,
                    'bid': bid,
                    'ask': ask,
                    'spread': spread,
                    'raw_data': data,
                    'raw_response': response
                })
                
                # Останавливаем после 25 измерений
                if len(self.measurements) >= 25:
                    self.running = False
                    print(f"\n✅ Собрано {len(self.measurements)} измерений - завершение теста")
                    
        except Exception as e:
            print(f"❌ Ошибка обработки: {e}")
    
    def show_latency_statistics(self):
        """Показывает детальную статистику задержки"""
        if not self.measurements:
            return
        
        print("\n" + "="*70)
        print("📈 ДЕТАЛЬНАЯ СТАТИСТИКА ЗАДЕРЖКИ SiU5")
        print("="*70)
        
        # Собираем все задержки по ms_timestamp (самые точные)
        ms_latencies = []
        sec_latencies = []
        
        for measurement in self.measurements:
            computer_time = measurement['computer_time']
            data = measurement['raw_data']
            
            # Задержка по миллисекундам (точная)
            if 'ms_timestamp' in data:
                ms_ts = data['ms_timestamp']
                if isinstance(ms_ts, (int, float)) and ms_ts > 1e12:
                    exchange_time = datetime.fromtimestamp(ms_ts / 1000)
                    latency = (computer_time - exchange_time).total_seconds() * 1000
                    ms_latencies.append(latency)
            
            # Задержка по секундам (менее точная)
            if 'timestamp' in data:
                sec_ts = data['timestamp']
                if isinstance(sec_ts, (int, float)) and sec_ts > 1e9:
                    exchange_time = datetime.fromtimestamp(sec_ts)
                    latency = (computer_time - exchange_time).total_seconds() * 1000
                    sec_latencies.append(latency)
        
        # Статистика по миллисекундным timestamp (главная)
        if ms_latencies:
            avg_ms = sum(ms_latencies) / len(ms_latencies)
            min_ms = min(ms_latencies)
            max_ms = max(ms_latencies)
            
            print(f"🎯 ТОЧНАЯ ЗАДЕРЖКА (по ms_timestamp):")
            print(f"   📊 Измерений:      {len(ms_latencies)}")
            print(f"   📊 Средняя:        {avg_ms:6.1f} мс")
            print(f"   📊 Минимальная:    {min_ms:6.1f} мс")
            print(f"   📊 Максимальная:   {max_ms:6.1f} мс")
            print(f"   📊 Разброс:        {max_ms - min_ms:6.1f} мс")
            
            # Оценка качества
            if avg_ms < 50:
                print("   ✅ ПРЕВОСХОДНО: < 50мс")
            elif avg_ms < 100:
                print("   ✅ ОТЛИЧНО: < 100мс")
            elif avg_ms < 200:
                print("   ✅ ХОРОШО: < 200мс")
            elif avg_ms < 500:
                print("   ⚠️ ПРИЕМЛЕМО: < 500мс")
            else:
                print("   ❌ МЕДЛЕННО: > 500мс")
        
        # Статистика по секундным timestamp (для сравнения)
        if sec_latencies:
            avg_sec = sum(sec_latencies) / len(sec_latencies)
            print(f"\n📊 Задержка по секундам: {avg_sec:6.1f} мс (менее точно)")
        
        # Общая статистика
        total_time = (self.measurements[-1]['computer_time'] - self.measurements[0]['computer_time']).total_seconds()
        frequency = len(self.measurements) / total_time
        
        print(f"\n🔄 ЧАСТОТА ОБНОВЛЕНИЙ:")
        print(f"   📊 Время теста:    {total_time:6.1f} секунд")
        print(f"   📊 Обновлений:     {len(self.measurements)}")
        print(f"   📊 Частота:        {frequency:6.1f} раз/сек")
        
        print("="*70)
    
    def start_test(self):
        """Запускает тест"""
        print("🎯 ТЕСТ ЗАДЕРЖКИ SiU5 - 25 ИЗМЕРЕНИЙ")
        print("=" * 70)
        print("📡 Подписка на изменения стакана SiU5 (доллар-рубль)...")
        
        try:
            # Устанавливаем обработчик
            self.ap.on_change_order_book = self.on_orderbook_change
            
            # Подписываемся только на SiU5
            guid = self.ap.order_book_get_and_subscribe('MOEX', 'SiU5')
            print(f"✅ Подписка создана: {guid[:8]}...")
            print("⚡ Ожидание изменений стакана...")
            
            self.running = True
            
            # Ждем пока не соберем 10 измерений
            while self.running:
                sleep(0.1)
            
            print("\n🎯 Тест завершен")
            
            # Показываем статистику
            self.show_latency_statistics()
            
            # Быстрый выход без сложного закрытия
            os._exit(0)
            
        except KeyboardInterrupt:
            print("\n🛑 Остановлено пользователем")
            os._exit(0)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            os._exit(1)


def main():
    try:
        test = SiU5LatencyTest()
        test.start_test()
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")


if __name__ == "__main__":
    main()
