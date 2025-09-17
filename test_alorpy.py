#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестируем AlorPy с вашим Refresh Token
"""

import sys
import os
import logging

# Добавляем путь к AlorPy
sys.path.append(os.path.join(os.path.dirname(__file__), 'AlorPy'))

from AlorPy import AlorPy

def test_alorpy():
    """Тестируем AlorPy"""
    print("🧪 ТЕСТ ALORPY С ВАШИМ ТОКЕНОМ")
    print("=" * 50)
    
    # Загружаем токен из .env
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    refresh_token = None
    
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('ALOR_API_TOKEN='):
                    refresh_token = line.split('=', 1)[1].strip().strip("'\"")
                    break
    
    if not refresh_token:
        print("❌ Токен не найден в .env")
        return
    
    print(f"📋 Токен загружен: {len(refresh_token)} символов")
    print(f"🔍 Токен: {refresh_token[:20]}...{refresh_token[-10:]}")
    
    try:
        # Создаем AlorPy с вашим токеном
        print("\n🔌 Подключаемся к AlorPy...")
        ap = AlorPy(refresh_token=refresh_token)
        
        print("✅ AlorPy инициализирован!")
        print(f"📊 JWT токен получен: {len(ap.jwt_token) if ap.jwt_token else 0} символов")
        
        if ap.jwt_token:
            print(f"🔍 JWT: {ap.jwt_token[:50]}...")
            
            # Тестируем получение стакана
            print("\n📈 Тестируем получение стакана PDU5...")
            order_book = ap.get_order_book('MOEX', 'PDU5')
            
            if order_book and order_book.get('bids') and order_book.get('asks'):
                best_bid = order_book['bids'][0]
                best_ask = order_book['asks'][0]
                print(f"✅ Стакан получен!")
                print(f"   Best Bid: {best_bid['price']} (vol: {best_bid['volume']})")
                print(f"   Best Ask: {best_ask['price']} (vol: {best_ask['volume']})")
                
                # Тестируем подписку на стакан
                print("\n🔔 Тестируем подписку на стакан (5 секунд)...")
                
                def on_orderbook_change(response):
                    data = response.get('data', {})
                    if data.get('bids') and data.get('asks'):
                        bid = data['bids'][0]['price']
                        ask = data['asks'][0]['price']
                        print(f"📊 {datetime.now().strftime('%H:%M:%S.%f')[:-3]} - Bid: {bid}, Ask: {ask}")
                
                ap.on_change_order_book = on_orderbook_change
                
                from time import sleep
                from datetime import datetime
                
                guid = ap.order_book_get_and_subscribe('MOEX', 'PDU5')
                print(f"✅ Подписка создана: {guid}")
                
                sleep(5)  # Ждем 5 секунд real-time данных
                
                ap.unsubscribe(guid)
                print("✅ Подписка отменена")
                
                ap.close_web_socket()
                print("✅ WebSocket закрыт")
                
            else:
                print("❌ Не удалось получить стакан")
        else:
            print("❌ JWT токен не получен")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    test_alorpy()
