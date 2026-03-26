#!/usr/bin/env python3
"""
⚡ Швидка перевірка staging bot
Діагностика чому максимальний тест завис
"""

import asyncio
from pathlib import Path
from telegram import Bot

async def quick_staging_check():
    """Швидка перевірка що staging bot працює"""
    print("⚡ ШВИДКА ПЕРЕВІРКА STAGING BOT")
    print("=" * 40)
    
    # Завантажуємо config
    staging_env = Path("/home/sashok/.openclaw/workspace/insilver-v3/.env.staging")
    config = {}
    with open(staging_env, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                config[key] = value
    
    try:
        bot = Bot(token=config['STAGING_BOT_TOKEN'])
        test_chat_id = int(config['TEST_CHAT_ID'])
        
        print("1. Тест bot info...")
        bot_info = await bot.get_me()
        print(f"   ✅ @{bot_info.username}")
        
        print("2. Тест надсилання повідомлення...")
        sent = await bot.send_message(test_chat_id, "⚡ Швидкий тест")
        print(f"   ✅ Надіслано ID: {sent.message_id}")
        
        print("3. Тест отримання updates...")
        updates = await bot.get_updates(limit=1, timeout=5)
        print(f"   ✅ Updates: {len(updates)}")
        
        print("\n🎉 STAGING BOT ПРАЦЮЄ!")
        return True
        
    except Exception as e:
        print(f"\n❌ Помилка: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_staging_check())
    print(f"Результат: {'УСПІХ' if success else 'ПОМИЛКА'}")