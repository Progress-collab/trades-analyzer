#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы с API Alor
Получение текущих котировок (bid, ask, last price) по списку инструментов
"""

import os
import requests
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

# Настройка логирования
logger = logging.getLogger(__name__)


class AlorAPI:
    """Класс для работы с API Alor"""
    
    def __init__(self, token: str = None, api_url: str = "https://api.alor.ru"):
        """
        Инициализация API клиента
        
        Args:
            token: API токен Alor
            api_url: URL API Alor
        """
        # Загружаем токен из переменных окружения или .env файла
        if token is None:
            token = self._load_token()
        
        if not token:
            raise ValueError("API токен не найден! Создайте файл .env с ALOR_API_TOKEN")
        
        self.token = token
        self.api_url = api_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        })
        
        logger.info("Alor API клиент инициализирован")
    
    def _load_token(self) -> Optional[str]:
        """
        Загружает токен из переменных окружения или .env файла
        
        Returns:
            API токен или None
        """
        # Сначала проверяем переменные окружения
        token = os.environ.get('ALOR_API_TOKEN')
        if token:
            return token
        
        # Затем пробуем загрузить из .env файла
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
    
    def load_instruments_list(self, filename: str = "instruments.txt") -> List[str]:
        """
        Загружает список инструментов из файла
        
        Args:
            filename: Имя файла со списком инструментов
            
        Returns:
            Список инструментов
        """
        instruments = []
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Пропускаем комментарии и пустые строки
                    if line and not line.startswith('#'):
                        instruments.append(line.upper())
            
            logger.info(f"Загружено {len(instruments)} инструментов из {filename}")
            return instruments
            
        except FileNotFoundError:
            logger.error(f"Файл {filename} не найден")
            return []
        except Exception as e:
            logger.error(f"Ошибка при загрузке списка инструментов: {e}")
            return []
    
    def get_quote(self, symbol: str, exchange: str = "MOEX") -> Optional[Dict[str, Any]]:
        """
        Получает котировку по инструменту
        
        Args:
            symbol: Символ инструмента (например, SBER)
            exchange: Биржа (по умолчанию MOEX)
            
        Returns:
            Словарь с данными котировки или None при ошибке
        """
        try:
            # Попробуем разные варианты endpoint (рабочий первым)
            endpoints_to_try = [
                f"{self.api_url}/md/v2/securities/{exchange}:{symbol}/quotes",
                f"{self.api_url}/md/v2/{exchange}/{symbol}/quotes",
                f"{self.api_url}/md/v2/{exchange}/{symbol}",
                f"{self.api_url}/md/securities/{exchange}:{symbol}/quotes"
            ]
            
            data = None
            successful_url = None
            
            for url in endpoints_to_try:
                try:
                    logger.debug(f"Пробую endpoint: {url}")
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    successful_url = url
                    logger.debug(f"Успешный endpoint: {url}")
                    break
                except requests.exceptions.RequestException as e:
                    logger.debug(f"Endpoint {url} не работает: {e}")
                    continue
            
            if data is None:
                logger.error(f"Все endpoints не работают для {symbol}")
                return None
            
            # API может возвращать список или словарь
            if isinstance(data, list):
                if len(data) == 0:
                    logger.error(f"Пустой ответ для {symbol}")
                    return None
                data = data[0]  # Берем первый элемент из списка
            
            logger.debug(f"Данные для {symbol}: {data}")
            
            # Извлекаем основные поля
            prev_close = data.get('prev_close_price')
            last_price = data.get('last_price')
            
            # Извлекаем временные метки от биржи (реальное время котировок)
            last_price_timestamp = data.get('last_price_timestamp')  # Unix timestamp последней сделки
            orderbook_timestamp = data.get('ob_ms_timestamp')  # Timestamp стакана (bid/ask) в миллисекундах
            
            # Конвертируем timestamps в читаемый формат
            last_trade_time = None
            orderbook_time = None
            
            if last_price_timestamp:
                last_trade_time = datetime.fromtimestamp(last_price_timestamp).isoformat()
            
            if orderbook_timestamp:
                # ob_ms_timestamp в миллисекундах
                orderbook_time = datetime.fromtimestamp(orderbook_timestamp / 1000).isoformat()
            
            # Извлекаем все полезные данные
            quote_data = {
                'symbol': symbol,
                'exchange': exchange,
                'bid': data.get('bid') or data.get('bestBid') or data.get('b'),
                'ask': data.get('ask') or data.get('bestAsk') or data.get('a'), 
                'last_price': data.get('last_price') or data.get('lastPrice') or data.get('last') or data.get('lp'),
                'prev_close_price': prev_close,
                'change': data.get('change') or data.get('priceChange'),
                'change_percent': data.get('change_percent') or data.get('priceChangePercent') or data.get('changePercent'),
                # Реальные временные метки от биржи
                'last_trade_time': last_trade_time,  # Время последней сделки
                'orderbook_time': orderbook_time,    # Время обновления стакана
                'api_request_time': datetime.now().isoformat(),  # Время запроса к API
                'volume': data.get('volume') or data.get('vol'),
                'high_price': data.get('high_price') or data.get('high'),
                'low_price': data.get('low_price') or data.get('low'),
                'open_price': data.get('open_price') or data.get('open'),
                'open_interest': data.get('open_interest'),
                'description': data.get('description')
            }
            
            logger.debug(f"Получена котировка {symbol}: bid={quote_data['bid']}, ask={quote_data['ask']}, last={quote_data['last_price']}")
            return quote_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса котировки {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении котировки {symbol}: {e}")
            return None
    
    def get_multiple_quotes(self, symbols: List[str], exchange: str = "MOEX") -> Dict[str, Any]:
        """
        Получает котировки по списку инструментов
        
        Args:
            symbols: Список символов инструментов
            exchange: Биржа
            
        Returns:
            Словарь с котировками по всем инструментам
        """
        results = {}
        successful = 0
        failed = 0
        
        logger.info(f"Запрашиваю котировки для {len(symbols)} инструментов...")
        
        for symbol in symbols:
            quote = self.get_quote(symbol, exchange)
            if quote:
                results[symbol] = quote
                successful += 1
            else:
                results[symbol] = {"error": "Не удалось получить котировку"}
                failed += 1
            
            # Небольшая пауза между запросами
            time.sleep(0.1)
        
        logger.info(f"Получено котировок: {successful} успешно, {failed} с ошибками")
        return results
    
    def print_quotes(self, quotes_data: Dict[str, Any]):
        """
        Выводит котировки в консоль
        
        Args:
            quotes_data: Данные котировок
        """
        print("\n" + "="*60)
        print("📈 ТЕКУЩИЕ КОТИРОВКИ ALOR")
        print("="*60)
        
        for symbol, data in quotes_data.items():
            if 'error' in data:
                print(f"\n❌ {symbol}: {data['error']}")
            else:
                bid = data.get('bid', 'N/A')
                ask = data.get('ask', 'N/A')
                last = data.get('last_price', 'N/A')
                change_pct = data.get('change_percent', 0)
                
                direction = "📈" if change_pct > 0 else "📉" if change_pct < 0 else "➡️"
                
                print(f"\n🔸 {symbol}:")
                print(f"   📊 Bid: {bid}")
                print(f"   📊 Ask: {ask}")
                print(f"   📊 Last: {last}")
                
                prev_close = data.get('prev_close_price', 'N/A')
                change_abs = data.get('change', 0)
                
                print(f"   📊 Prev Close: {prev_close}")
                if change_pct != 0:
                    print(f"   📊 Change: {direction} {change_abs:+.4f} ({change_pct:+.2f}%)")
                
                # Дополнительная полезная информация
                high_price = data.get('high_price', 'N/A')
                low_price = data.get('low_price', 'N/A')
                open_price = data.get('open_price', 'N/A')
                volume = data.get('volume', 'N/A')
                open_interest = data.get('open_interest', 'N/A')
                
                print(f"   📈 High: {high_price} | 📉 Low: {low_price} | 🔓 Open: {open_price}")
                print(f"   📦 Volume: {volume} | 🏗️ Open Interest: {open_interest}")
                
                # Показываем реальные временные метки от биржи
                last_trade_time = data.get('last_trade_time', 'N/A')
                orderbook_time = data.get('orderbook_time', 'N/A')
                
                if last_trade_time != 'N/A':
                    print(f"   🕐 Last Trade: {last_trade_time}")
                if orderbook_time != 'N/A':
                    print(f"   🕐 Orderbook: {orderbook_time}")
        
        print("\n⏰ Время обновления:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("="*60)


def main():
    """Основная функция для тестирования модуля"""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,  # Возвращаем обычный уровень
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Создаем клиент API
        alor = AlorAPI()
        
        # Загружаем список инструментов
        instruments = alor.load_instruments_list()
        
        if not instruments:
            print("❌ Список инструментов пуст или не загружен")
            return
        
        print(f"📋 Загружено инструментов: {instruments}")
        
        # Получаем котировки
        quotes = alor.get_multiple_quotes(instruments)
        
        # Выводим результаты
        alor.print_quotes(quotes)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("💡 Проверьте:")
        print("   1. Создан ли файл .env с ALOR_API_TOKEN")
        print("   2. Правильный ли токен")
        print("   3. Есть ли интернет соединение")


if __name__ == "__main__":
    main()
