#!/usr/bin/env python3
"""
Синхронний тест Telegram API
"""
import requests
import time
import json

TOKEN = "8627781342:AAGRpzlKRGmABft7QkTIyzZjWHk4SFqw4wI"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def test_sync():
    print("🧪 Синхронний тест Telegram API...")
    
    # Test 1: getMe
    print("1. Тест getMe...")
    response = requests.get(f"{BASE_URL}/getMe")
    if response.status_code == 200:
        bot_info = response.json()['result']
        print(f"✅ Бот: @{bot_info['username']}")
    else:
        print(f"❌ getMe failed: {response.status_code}")
        return
    
    # Test 2: Send test message
    print("2. Надсилаю тестове повідомлення...")
    send_response = requests.post(f"{BASE_URL}/sendMessage", json={
        'chat_id': 189793675,
        'text': '🧪 Синхронний тест'
    })
    
    if send_response.status_code == 200:
        msg_data = send_response.json()['result']
        print(f"✅ Повідомлення надіслано: ID {msg_data['message_id']}")
    else:
        print(f"❌ sendMessage failed: {send_response.status_code}")
        return
    
    # Test 3: Check getUpdates
    print("3. Перевіряю getUpdates через 5 секунд...")
    time.sleep(5)
    
    updates_response = requests.get(f"{BASE_URL}/getUpdates")
    if updates_response.status_code == 200:
        data = updates_response.json()
        updates = data.get('result', [])
        print(f"✅ getUpdates працює: {len(updates)} updates")
        
        for update in updates[-3:]:
            message = update.get('message', {})
            text = message.get('text', 'NO_TEXT')
            user_id = message.get('from', {}).get('id', 'NO_USER')
            print(f"  Update {update['update_id']}: '{text}' від {user_id}")
    else:
        print(f"❌ getUpdates failed: {updates_response.status_code}")
    
    print("🏁 Синхронний тест завершено")

if __name__ == "__main__":
    test_sync()