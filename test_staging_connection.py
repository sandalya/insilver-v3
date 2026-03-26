#!/usr/bin/env python3
"""
🔌 Тест підключення Staging Bot
Перевірка що @staging_kit_bot працює з Claude.ai методологією
"""

import asyncio
import os
from pathlib import Path
from telegram import Bot

async def test_staging_connection():
    """Тест базового підключення staging bot (Claude.ai approach)"""
    print("🤖 ТЕСТ STAGING BOT ПІДКЛЮЧЕННЯ")
    print("=" * 40)
    
    # Завантажуємо staging config
    staging_env = Path("/home/sashok/.openclaw/workspace/insilver-v3/.env.staging")
    
    staging_config = {}
    with open(staging_env, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                staging_config[key] = value
    
    staging_token = staging_config.get('STAGING_BOT_TOKEN')
    test_chat_id = staging_config.get('TEST_CHAT_ID')
    
    print(f"📋 Staging bot token: {staging_token[:20]}...")
    print(f"📋 Test chat ID: {test_chat_id}")
    
    try:
        # Створюємо bot instance
        bot = Bot(token=staging_token)
        
        # Тест 1: Отримати інформацію про бота
        print("\n🔍 Тест 1: Bot info")
        bot_info = await bot.get_me()
        print(f"   ✅ Bot name: @{bot_info.username}")
        print(f"   ✅ Bot ID: {bot_info.id}")
        print(f"   ✅ Can join groups: {bot_info.can_join_groups}")
        
        # Тест 2: Надіслати тестове повідомлення (Claude.ai pattern)
        print("\n📤 Тест 2: Надсилання тестового повідомлення")
        test_message = "🧪 Staging bot test з Claude.ai методологією"
        
        sent = await bot.send_message(
            chat_id=int(test_chat_id),
            text=test_message
        )
        print(f"   ✅ Повідомлення надіслано (ID: {sent.message_id})")
        
        # Тест 3: Claude's reliable getUpdates approach 
        print("\n📥 Тест 3: Claude.ai reliable getUpdates")
        updates = await bot.get_updates(limit=1, timeout=3)
        if updates:
            print(f"   ✅ Отримано updates: {len(updates)}")
            print(f"   ✅ Останній update ID: {updates[-1].update_id}")
        else:
            print("   ✅ Немає нових updates (нормально)")
        
        print(f"\n🎉 STAGING BOT READY!")
        print(f"✅ @{bot_info.username} працює коректно")
        print(f"✅ Claude.ai методологія готова до застосування")
        return True
        
    except Exception as e:
        print(f"\n❌ Staging bot помилка: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_staging_connection())
    exit(0 if success else 1)