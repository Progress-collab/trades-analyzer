#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы с cTrader Open API (FxPro)
Получение текущих котировок (bid, ask, last price) по списку криптоинструментов
"""

import os
import requests
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import base64

# Настройка логирования
logger = logging.getLogger(__name__)


class CTraderAPI:
    """Класс для работы с cTrader Open API"""
    
    def __init__(self, client_id: str = None, client_secret: str = None, 
                 api_url: str = "https://api.spotware.com"):
        """
        Инициализация API клиента
        
        Args:
            client_id: Client ID для cTrader Open API
            client_secret: Client Secret для cTrader Open API
            api_url: URL cTrader Open API
        """
        # Загружаем credentials из переменных окружения или .env файла
        if client_id is None:
            client_id = self._load_credential('CTRADER_CLIENT_ID')
        if client_secret is None:
            client_secret = self._load_credential('CTRADER_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            raise ValueError("cTrader credentials не найдены! Создайте файл .env с CTRADER_CLIENT_ID и CTRADER_CLIENT_SECRET")
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = api_url.rstrip('/')
        self.access_token = None
        self.token_expires_at = None
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Python-cTrader-Client/1.0'
        })
        
        logger.info("cTrader API клиент инициализирован")
    
    def _load_credential(self, credential_name: str) -> Optional[str]:
        """
        Загружает credential из переменных окружения или .env файла
        
        Args:
            credential_name: Имя переменной окружения
            
        Returns:
            Значение credential или None
        """
        # Сначала проверяем переменные окружения
        credential = os.environ.get(credential_name)
        if credential:
            return credential
        
        # Затем пробуем загрузить из .env файла
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(f'{credential_name}='):
                            return line.split('=', 1)[1].strip()
            except Exception as e:
                logger.error(f"Ошибка при чтении .env файла: {e}")
        
        return None
    
    def _authenticate(self) -> bool:
        """
        Выполняет аутентификацию и получает access token
        
        Returns:
            True если аутентификация успешна, False иначе
        """
        try:
            # OAuth2 Client Credentials Flow
            auth_url = f"{self.api_url}/connect/token"
            
            # Создаем базовую аутентификацию
            credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            
            headers = {
                'Authorization': f'Basic {credentials}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'client_credentials',
                'scope': 'trading'  # Или другие необходимые scope
            }
            
            logger.info("Выполняется аутентификация в cTrader API...")
            response = self.session.post(auth_url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)  # По умолчанию 1 час
            
            if not self.access_token:
                logger.error("Не удалось получить access token")
                return False
            
            # Обновляем заголовки для будущих запросов
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}'
            })
            
            # Запоминаем время истечения токена
            self.token_expires_at = time.time() + expires_in - 60  # С запасом в 1 минуту
            
            logger.info(f"Аутентификация успешна, токен действует {expires_in} секунд")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при аутентификации: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при аутентификации: {e}")
            return False
    
    def _ensure_authenticated(self) -> bool:
        """
        Проверяет и обновляет аутентификацию при необходимости
        
        Returns:
            True если аутентификация активна, False иначе
        """
        # Проверяем, нужно ли обновить токен
        if (self.access_token is None or 
            self.token_expires_at is None or 
            time.time() >= self.token_expires_at):
            return self._authenticate()
        
        return True
    
    def load_instruments_list(self, filename: str = "crypto_instruments.txt") -> List[str]:
        """
        Загружает список криптоинструментов из файла
        
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
    
    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Получает котировку по криптоинструменту
        
        Args:
            symbol: Символ инструмента (например, BITCOIN, ETHEREUM)
            
        Returns:
            Словарь с данными котировки или None при ошибке
        """
        try:
            # Проверяем аутентификацию
            if not self._ensure_authenticated():
                logger.error("Не удалось выполнить аутентификацию")
                return None
            
            # Попробуем разные варианты endpoint
            # Примечание: точные endpoints нужно уточнить в документации cTrader
            endpoints_to_try = [
                f"{self.api_url}/connect/quotes/{symbol}",
                f"{self.api_url}/v2/symbols/{symbol}/quotes",
                f"{self.api_url}/quotes/{symbol}",
                f"{self.api_url}/symbols/{symbol}/quote"
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
            
            logger.debug(f"Данные для {symbol}: {data}")
            
            # Извлекаем основные поля (структура может отличаться)
            # Адаптируем под реальную структуру ответа cTrader API
            quote_data = {
                'symbol': symbol,
                'bid': data.get('bid') or data.get('bidPrice'),
                'ask': data.get('ask') or data.get('askPrice'), 
                'last_price': data.get('lastPrice') or data.get('last') or data.get('price'),
                'spread': None,
                'timestamp': data.get('timestamp') or data.get('time'),
                'api_request_time': datetime.now().isoformat(),
                'volume': data.get('volume'),
                'high_price': data.get('high') or data.get('highPrice'),
                'low_price': data.get('low') or data.get('lowPrice'),
                'open_price': data.get('open') or data.get('openPrice'),
                'change': data.get('change') or data.get('priceChange'),
                'change_percent': data.get('changePercent') or data.get('priceChangePercent')
            }
            
            # Вычисляем спред если есть bid и ask
            if quote_data['bid'] and quote_data['ask']:
                quote_data['spread'] = quote_data['ask'] - quote_data['bid']
            
            logger.debug(f"Получена котировка {symbol}: bid={quote_data['bid']}, ask={quote_data['ask']}, last={quote_data['last_price']}")
            return quote_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса котировки {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении котировки {symbol}: {e}")
            return None
    
    def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Получает котировки по списку криптоинструментов
        
        Args:
            symbols: Список символов инструментов
            
        Returns:
            Словарь с котировками по всем инструментам
        """
        results = {}
        successful = 0
        failed = 0
        
        logger.info(f"Запрашиваю котировки для {len(symbols)} криптоинструментов...")
        
        for symbol in symbols:
            quote = self.get_quote(symbol)
            if quote:
                results[symbol] = quote
                successful += 1
            else:
                results[symbol] = {"error": "Не удалось получить котировку"}
                failed += 1
            
            # Небольшая пауза между запросами
            time.sleep(0.2)
        
        logger.info(f"Получено котировок: {successful} успешно, {failed} с ошибками")
        return results
    
    def print_quotes(self, quotes_data: Dict[str, Any]):
        """
        Выводит котировки в консоль
        
        Args:
            quotes_data: Данные котировок
        """
        print("\n" + "="*60)
        print("₿ ТЕКУЩИЕ КОТИРОВКИ КРИПТОВАЛЮТ (cTrader FxPro)")
        print("="*60)
        
        for symbol, data in quotes_data.items():
            if 'error' in data:
                print(f"\n❌ {symbol}: {data['error']}")
            else:
                bid = data.get('bid', 'N/A')
                ask = data.get('ask', 'N/A')
                last = data.get('last_price', 'N/A')
                spread = data.get('spread', 'N/A')
                change_pct = data.get('change_percent', 0)
                
                direction = "📈" if change_pct and change_pct > 0 else "📉" if change_pct and change_pct < 0 else "➡️"
                
                # Добавляем эмодзи для криптовалют
                crypto_emoji = {
                    'BITCOIN': '₿',
                    'ETHEREUM': 'Ξ',
                    'XRP': '🌊',
                    'LITECOIN': 'Ł'
                }.get(symbol, '🪙')
                
                print(f"\n{crypto_emoji} {symbol}:")
                print(f"   💰 Bid: {bid}")
                print(f"   💰 Ask: {ask}")
                print(f"   💰 Last: {last}")
                
                if spread != 'N/A' and spread is not None:
                    print(f"   📊 Spread: {spread:.6f}")
                
                change_abs = data.get('change', 0)
                if change_pct:
                    print(f"   📊 Change: {direction} {change_abs:+.6f} ({change_pct:+.2f}%)")
                
                # Дополнительная информация
                high_price = data.get('high_price', 'N/A')
                low_price = data.get('low_price', 'N/A')
                open_price = data.get('open_price', 'N/A')
                volume = data.get('volume', 'N/A')
                
                if any(x != 'N/A' for x in [high_price, low_price, open_price]):
                    print(f"   📈 High: {high_price} | 📉 Low: {low_price} | 🔓 Open: {open_price}")
                
                if volume != 'N/A':
                    print(f"   📦 Volume: {volume}")
                
                # Временная метка
                timestamp = data.get('timestamp', 'N/A')
                if timestamp != 'N/A':
                    print(f"   🕐 Quote Time: {timestamp}")
        
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
        ctrader = CTraderAPI()
        
        # Загружаем список инструментов
        instruments = ctrader.load_instruments_list()
        
        if not instruments:
            print("❌ Список криптоинструментов пуст или не загружен")
            return
        
        print(f"📋 Загружено криптоинструментов: {instruments}")
        
        # Получаем котировки
        quotes = ctrader.get_multiple_quotes(instruments)
        
        # Выводим результаты
        ctrader.print_quotes(quotes)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("💡 Проверьте:")
        print("   1. Создан ли файл .env с CTRADER_CLIENT_ID и CTRADER_CLIENT_SECRET")
        print("   2. Правильные ли credentials для cTrader Open API")
        print("   3. Есть ли интернет соединение")
        print("   4. Доступен ли cTrader Open API")


if __name__ == "__main__":
    main()
