#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Получение JWT токена для WebSocket API Alor из Refresh Token
"""

import os
import requests
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class AlorJWTManager:
    """Управление JWT токенами для Alor API"""
    
    def __init__(self, demo=False):
        """
        Args:
            demo: Режим демо торговли
        """
        self.demo = demo
        self.oauth_server = f'https://oauth{"dev" if demo else ""}.alor.ru'
        self.refresh_token = self._load_refresh_token()
        self.jwt_token = None
        self.jwt_token_issued = 0
        self.jwt_token_ttl = 60  # Время жизни JWT токена в секундах
        
        if not self.refresh_token:
            raise ValueError("Refresh Token не найден! Добавьте ALOR_REFRESH_TOKEN в .env файл")
    
    def _load_refresh_token(self) -> Optional[str]:
        """Загружает Refresh Token из .env файла"""
        # Проверяем переменные окружения
        token = os.environ.get('ALOR_REFRESH_TOKEN')
        if token:
            return token
        
        # Если нет ALOR_REFRESH_TOKEN, пробуем ALOR_API_TOKEN (возможно это и есть refresh token)
        token = os.environ.get('ALOR_API_TOKEN')
        if token:
            return token
        
        # Загружаем из .env файла
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Сначала ищем ALOR_REFRESH_TOKEN
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('ALOR_REFRESH_TOKEN='):
                            return line.split('=', 1)[1].strip()
                    
                    # Если не найден, пробуем ALOR_API_TOKEN
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('ALOR_API_TOKEN='):
                            return line.split('=', 1)[1].strip()
                            
            except Exception as e:
                logger.error(f"Ошибка при чтении .env файла: {e}")
        
        return None
    
    def get_jwt_token(self) -> Optional[str]:
        """
        Получает JWT токен из Refresh Token
        
        Returns:
            JWT токен или None при ошибке
        """
        now = int(datetime.timestamp(datetime.now()))
        
        # Проверяем, нужно ли обновить токен
        if self.jwt_token is None or now - self.jwt_token_issued > self.jwt_token_ttl:
            try:
                logger.info("Получаем новый JWT токен...")
                
                response = requests.post(
                    url=f'{self.oauth_server}/refresh',
                    params={'token': self.refresh_token},
                    timeout=10
                )
                
                if response.status_code != 200:
                    logger.error(f"Ошибка получения JWT токена: {response.status_code}")
                    logger.error(f"Ответ сервера: {response.text}")
                    self.jwt_token = None
                    self.jwt_token_issued = 0
                    return None
                
                token_data = response.json()
                self.jwt_token = token_data.get('AccessToken')
                self.jwt_token_issued = now
                
                if self.jwt_token:
                    logger.info("✅ JWT токен успешно получен")
                    logger.debug(f"JWT токен: {self.jwt_token[:50]}...")
                else:
                    logger.error("❌ JWT токен не найден в ответе")
                    logger.error(f"Ответ: {token_data}")
                
            except Exception as e:
                logger.error(f"Ошибка при получении JWT токена: {e}")
                self.jwt_token = None
                self.jwt_token_issued = 0
                return None
        
        return self.jwt_token


def test_jwt():
    """Тестирование получения JWT токена"""
    print("🔑 ТЕСТ ПОЛУЧЕНИЯ JWT ТОКЕНА")
    print("=" * 50)
    
    try:
        jwt_manager = AlorJWTManager()
        
        print(f"📋 Refresh Token загружен: {len(jwt_manager.refresh_token)} символов")
        print(f"🔍 Первые 20 символов: {jwt_manager.refresh_token[:20]}...")
        
        jwt_token = jwt_manager.get_jwt_token()
        
        if jwt_token:
            print(f"✅ JWT токен получен: {len(jwt_token)} символов")
            print(f"🔍 Первые 50 символов: {jwt_token[:50]}...")
            
            # Проверяем, что это действительно JWT
            if jwt_token.count('.') >= 2:
                print("✅ Это действительно JWT токен (содержит точки)")
            else:
                print("❌ Не похож на JWT токен")
        else:
            print("❌ Не удалось получить JWT токен")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("\n💡 Нужно:")
        print("1. Получить Refresh Token на https://alor.dev/login")
        print("2. Добавить ALOR_REFRESH_TOKEN в .env файл")


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    test_jwt()
