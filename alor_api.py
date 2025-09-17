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
            symbol: Символ инструмента (например, PLD-9.25)
            exchange: Биржа (по умолчанию MOEX)
            
        Returns:
            Словарь с данными котировки или None при ошибке
        """
        try:
            url = f"{self.api_url}/md/v2/{exchange}/{symbol}/quotes"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Извлекаем нужные данные
            quote_data = {
                'symbol': symbol,
                'exchange': exchange,
                'bid': data.get('bid'),
                'ask': data.get('ask'),
                'last_price': data.get('last_price'),
                'timestamp': datetime.now().isoformat(),
                'volume': data.get('volume'),
                'change': data.get('change'),
                'change_percent': data.get('change_percent')
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
                print(f"   Bid: {bid}")
                print(f"   Ask: {ask}")
                print(f"   Last: {last}")
                if change_pct != 0:
                    print(f"   Change: {direction} {change_pct:+.2f}%")
        
        print("\n⏰ Время обновления:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("="*60)


def main():
    """Основная функция для тестирования модуля"""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
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
