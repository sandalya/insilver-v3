#!/usr/bin/env python3
"""
Простий діагностичний Telegram бот для виявлення проблем з getUpdates
"""
import requests
import time
import json
from datetime import datetime

TOKEN = "8627781342:AAGRpzlKRGmABft7QkTIyzZjWHk4SFqw4wI"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def log_with_time(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

def test_api():
    """Test basic API connectivity"""
    log_with_time("🧪 Тестую API...")
    
    try:
        response = requests.get(f"{BASE_URL}/getMe", timeout=10)
        if response.status_code == 200:
            bot_info = response.json()['result']
            log_with_time(f"✅ API працює: @{bot_info['username']}")
            return True
        else:
            log_with_time(f"❌ API помилка: {response.status_code}")
            return False
    except Exception as e:
        log_with_time(f"❌ API exception: {e}")
        return False

def check_updates():
    """Check for updates manually"""
    log_with_time("🔍 Перевіряю updates...")
    
    try:
        response = requests.get(f"{BASE_URL}/getUpdates", params={
            'limit': 10,
            'timeout': 5
        }, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            updates = data.get('result', [])
            
            log_with_time(f"📊 Updates знайдено: {len(updates)}")
            
            for update in updates:
                update_id = update.get('update_id')
                message = update.get('message', {})
                text = message.get('text', 'NO_TEXT')
                user_id = message.get('from', {}).get('id', 'NO_USER')
                username = message.get('from', {}).get('username', 'NO_USERNAME')
                
                log_with_time(f"  📨 Update {update_id}: '{text}' from {username} ({user_id})")
            
            return updates
        else:
            log_with_time(f"❌ getUpdates помилка: {response.status_code}")
            return []
            
    except Exception as e:
        log_with_time(f"❌ getUpdates exception: {e}")
        return []

def send_test_message():
    """Send test message to Sashko"""
    log_with_time("📤 Надсилаю тестове повідомлення...")
    
    try:
        response = requests.post(f"{BASE_URL}/sendMessage", json={
            'chat_id': 189793675,
            'text': f'🔬 DEBUG тест {datetime.now().strftime("%H:%M:%S")}'
        }, timeout=10)
        
        if response.status_code == 200:
            message_id = response.json()['result']['message_id']
            log_with_time(f"✅ Повідомлення надіслано: ID {message_id}")
            return True
        else:
            log_with_time(f"❌ sendMessage помилка: {response.status_code}")
            return False
            
    except Exception as e:
        log_with_time(f"❌ sendMessage exception: {e}")
        return False

def main():
    log_with_time("🚀 TELEGRAM DEBUG DIAGNOSTIC")
    log_with_time("=" * 50)
    
    # Test 1: API connectivity
    if not test_api():
        log_with_time("💀 API не працює, виходжу")
        return
    
    # Test 2: Initial getUpdates
    log_with_time("\n--- ПОЧАТКОВА ПЕРЕВІРКА ---")
    initial_updates = check_updates()
    
    # Test 3: Send test message
    log_with_time("\n--- НАДСИЛАЮ ТЕСТ ---")
    if send_test_message():
        log_with_time("⏳ Чекаю 10 секунд для обробки...")
        time.sleep(10)
        
        # Test 4: Check if message appeared in updates
        log_with_time("\n--- ПЕРЕВІРКА ПІСЛЯ ВІДПРАВКИ ---")
        new_updates = check_updates()
        
        if len(new_updates) > len(initial_updates):
            log_with_time("✅ Нові updates з'явились!")
        else:
            log_with_time("❌ Updates не з'явились - проблема з getUpdates!")
    
    log_with_time("\n📱 ТЕПЕР НАПИШИ ЩОСЬ В @insilver_v3_bot")
    log_with_time("⏳ Слухаю 60 секунд...")
    
    # Listen for 60 seconds
    for i in range(12):  # 12 * 5 = 60 seconds
        time.sleep(5)
        updates = check_updates()
        
        if updates:
            log_with_time("🎉 ЗНАЙДЕНО ПОВІДОМЛЕННЯ!")
            break
        else:
            log_with_time(f"⏳ Секунд пройшло: {(i+1)*5}/60")
    
    log_with_time("\n🏁 ДІАГНОСТИКА ЗАВЕРШЕНА")

if __name__ == "__main__":
    main()