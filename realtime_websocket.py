#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-time мониторинг котировок через WebSocket API Alor
Подписка на обновления bid/ask в реальном времени
"""

import asyncio
import websockets
import json
import os
import logging
from datetime import datetime
from typing import Dict, Any

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlorWebSocketMonitor:
    """Real-time мониторинг через WebSocket API Alor"""
    
    def __init__(self):
        self.token = self._load_token()
        # Попробуем разные возможные WebSocket endpoints
        self.websocket_urls = [
            "wss://api.alor.ru/ws",
            "wss://apiws.alor.ru/ws", 
            "wss://ws.alor.ru",
            "wss://api.alor.ru/md/v2/ws"
        ]
        self.quotes_data = {}
        self.running = False
        
        if not self.token:
            raise ValueError("API токен не найден! Создайте файл .env с ALOR_API_TOKEN")
    
    def _load_token(self) -> str:
        """Загружает токен из .env файла"""
        # Проверяем переменные окружения
        token = os.environ.get('ALOR_API_TOKEN')
        if token:
            return token
        
        # Загружаем из .env файла
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('ALOR_API_TOKEN='):
                            return line.split('=', 1)[1].strip()
            except Exception as e:
                logger.error(f"Ошибка при чтении .env файла: {e}")
        
        return None
    
    def load_instruments_list(self, filename: str = "instruments.txt") -> list:
        """Загружает список инструментов из файла"""
        instruments = []
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        instruments.append(line.upper())
            
            logger.info(f"Загружено {len(instruments)} инструментов: {instruments}")
            return instruments
            
        except FileNotFoundError:
            logger.error(f"Файл {filename} не найден")
            return []
        except Exception as e:
            logger.error(f"Ошибка при загрузке списка инструментов: {e}")
            return []
    
    def clear_screen(self):
        """Очищает экран консоли"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def format_price_change(self, current, previous):
        """Форматирует изменение цены с индикаторами"""
        if previous is None or current is None:
            return f"{current:>8.4f}" if current else "    N/A "
        
        if current > previous:
            return f"📈{current:>7.4f}"  # Рост
        elif current < previous:
            return f"📉{current:>7.4f}"  # Падение
        else:
            return f"➡️{current:>7.4f}"   # Без изменений
    
    def display_quotes(self):
        """Отображает текущие котировки"""
        self.clear_screen()
        print("=" * 100)
        print("🔥 REAL-TIME BID/ASK МОНИТОРИНГ ALOR (WebSocket)")
        print("=" * 100)
        print(f"{'Инструмент':<8} {'Bid':<12} {'Ask':<12} {'Last':<12} {'Spread':<8} {'Время':<20}")
        print("-" * 100)
        
        for symbol, data in self.quotes_data.items():
            bid = data.get('bid', 'N/A')
            ask = data.get('ask', 'N/A')
            last = data.get('last_price', 'N/A')
            timestamp = data.get('timestamp', 'N/A')
            
            # Рассчитываем спред
            if isinstance(bid, (int, float)) and isinstance(ask, (int, float)):
                spread = ask - bid
                spread_str = f"{spread:.4f}"
            else:
                spread_str = "N/A"
            
            # Форматируем время
            if isinstance(timestamp, (int, float)):
                time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S.%f")[:-3]
            else:
                time_str = str(timestamp)[:20]
            
            # Форматируем цены
            bid_str = f"{bid:>8.4f}" if isinstance(bid, (int, float)) else str(bid)[:8]
            ask_str = f"{ask:>8.4f}" if isinstance(ask, (int, float)) else str(ask)[:8]
            last_str = f"{last:>8.4f}" if isinstance(last, (int, float)) else str(last)[:8]
            
            print(f"{symbol:<8} {bid_str:<12} {ask_str:<12} {last_str:<12} {spread_str:<8} {time_str:<20}")
        
        print("-" * 100)
        current_time = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"⏰ Обновлено: {current_time} | 🔄 WebSocket | ❌ Ctrl+C для выхода")
        print("=" * 100)
    
    async def subscribe_to_instrument(self, websocket, symbol: str):
        """Подписывается на котировки инструмента"""
        # Попробуем разные форматы сообщений
        subscribe_formats = [
            # Формат 1: стандартный Alor
            {
                "opcode": "subscribe",
                "token": self.token,
                "exchange": "MOEX",
                "symbol": symbol,
                "format": "Simple"
            },
            # Формат 2: альтернативный
            {
                "method": "subscribe",
                "token": self.token,
                "params": {
                    "exchange": "MOEX",
                    "symbol": symbol,
                    "type": "quotes"
                }
            },
            # Формат 3: упрощенный
            {
                "action": "subscribe",
                "token": self.token,
                "instrument": f"MOEX:{symbol}",
                "stream": "quotes"
            }
        ]
        
        logger.info(f"Подписка на {symbol}")
        
        # Пробуем все форматы по очереди
        for i, subscribe_message in enumerate(subscribe_formats):
            try:
                await websocket.send(json.dumps(subscribe_message))
                logger.info(f"Отправлена подписка на {symbol} (формат {i+1})")
                
                # Ждем ответ на подписку
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    logger.info(f"Ответ на подписку {symbol}: {response[:100]}...")
                    break  # Если получили ответ, прекращаем пробовать другие форматы
                except asyncio.TimeoutError:
                    logger.debug(f"Нет ответа на подписку {symbol} (формат {i+1})")
                    continue
                    
            except Exception as e:
                logger.debug(f"Ошибка подписки {symbol} (формат {i+1}): {e}")
                continue
    
    async def handle_message(self, message: str):
        """Обрабатывает входящее сообщение WebSocket"""
        try:
            data = json.loads(message)
            
            # Извлекаем данные котировки
            symbol = data.get('symbol')
            if not symbol:
                return
            
            # Сохраняем предыдущие данные для сравнения
            previous_data = self.quotes_data.get(symbol, {})
            
            # Обновляем данные
            quote_update = {
                'bid': data.get('bid'),
                'ask': data.get('ask'),
                'last_price': data.get('last_price'),
                'timestamp': data.get('timestamp', datetime.now().timestamp()),
                'previous_bid': previous_data.get('bid'),
                'previous_ask': previous_data.get('ask'),
                'previous_last': previous_data.get('last_price')
            }
            
            self.quotes_data[symbol] = quote_update
            
            # Обновляем отображение
            self.display_quotes()
            
        except json.JSONDecodeError:
            logger.error(f"Ошибка парсинга JSON: {message}")
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
    
    async def try_connect_to_websocket(self):
        """Пробует подключиться к разным WebSocket URL"""
        for url in self.websocket_urls:
            try:
                logger.info(f"Попытка подключения к {url}")
                
                # Пробуем разные способы подключения
                connection_methods = [
                    # Метод 1: с заголовками (новые версии websockets)
                    lambda: websockets.connect(url, extra_headers={"Authorization": f"Bearer {self.token}"}),
                    # Метод 2: без заголовков (авторизация через сообщения)
                    lambda: websockets.connect(url),
                    # Метод 3: с токеном в URL
                    lambda: websockets.connect(f"{url}?token={self.token}")
                ]
                
                for i, method in enumerate(connection_methods):
                    try:
                        logger.debug(f"Пробую метод подключения {i+1}")
                        websocket = await method()
                        logger.info(f"✅ Успешное подключение к {url} (метод {i+1})")
                        return websocket, url
                    except Exception as method_error:
                        logger.debug(f"Метод {i+1} не сработал: {method_error}")
                        continue
                
            except Exception as e:
                logger.warning(f"❌ Не удалось подключиться к {url}: {e}")
                continue
        
        raise Exception("Не удалось подключиться ни к одному WebSocket endpoint")

    async def start_monitoring(self):
        """Запускает WebSocket мониторинг"""
        instruments = self.load_instruments_list()
        
        if not instruments:
            print("❌ Список инструментов пуст")
            return
        
        print(f"🚀 Запуск WebSocket мониторинга для {len(instruments)} инструментов...")
        print("❌ Нажмите Ctrl+C для остановки")
        
        try:
            # Пробуем подключиться к разным URL
            websocket, successful_url = await self.try_connect_to_websocket()
            
            try:
                logger.info(f"WebSocket соединение установлено: {successful_url}")
                
                # Пробуем разные варианты авторизации
                auth_variants = [
                    {"method": "authorize", "token": self.token},
                    {"opcode": "authorize", "token": self.token},  
                    {"action": "auth", "token": self.token},
                    {"type": "auth", "data": {"token": self.token}},
                    {"cmd": "auth", "args": [self.token]}
                ]
                
                auth_success = False
                for i, auth_message in enumerate(auth_variants):
                    try:
                        await websocket.send(json.dumps(auth_message))
                        logger.info(f"Отправлен вариант авторизации {i+1}: {list(auth_message.keys())}")
                        
                        # Ждем ответ на авторизацию
                        auth_response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        logger.info(f"Ответ на авторизацию {i+1}: {auth_response}")
                        
                        # Проверяем, успешна ли авторизация
                        if "401" not in auth_response and "Invalid" not in auth_response:
                            auth_success = True
                            logger.info(f"✅ Авторизация успешна (вариант {i+1})")
                            break
                        
                    except asyncio.TimeoutError:
                        logger.debug(f"Нет ответа на авторизацию {i+1}")
                    except Exception as e:
                        logger.debug(f"Ошибка авторизации {i+1}: {e}")
                
                if not auth_success:
                    logger.warning("❌ Все варианты авторизации не сработали, пробуем продолжить без авторизации")
                
                # Подписываемся на все инструменты
                for symbol in instruments:
                    await self.subscribe_to_instrument(websocket, symbol)
                    await asyncio.sleep(0.2)  # Задержка между подписками
                
                self.running = True
                
                # Слушаем сообщения
                while self.running:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        logger.debug(f"Получено сообщение: {message[:200]}...")  # Первые 200 символов
                        await self.handle_message(message)
                    except asyncio.TimeoutError:
                        # Периодически обновляем дисплей даже без новых данных
                        if self.quotes_data:
                            self.display_quotes()
                        else:
                            print("⏳ Ожидание данных...")
                    except websockets.exceptions.ConnectionClosed:
                        logger.error("WebSocket соединение закрыто")
                        break
                        
            finally:
                await websocket.close()
                        
        except KeyboardInterrupt:
            print("\n\n🛑 Мониторинг остановлен пользователем")
            self.running = False
        except Exception as e:
            logger.error(f"Ошибка WebSocket соединения: {e}")
            print(f"❌ Ошибка соединения: {e}")
            print("💡 Возможные причины:")
            print("   1. Неправильный токен в .env файле")
            print("   2. Токен истек или недействителен") 
            print("   3. WebSocket endpoint изменился")
            print("   4. Проблемы с интернет соединением")


async def main():
    """Основная функция"""
    try:
        monitor = AlorWebSocketMonitor()
        await monitor.start_monitoring()
    except ValueError as e:
        print(f"❌ Ошибка конфигурации: {e}")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())
