#!/usr/bin/env python3
"""Діагностика Telegram бота за планом Claude"""
import asyncio, httpx, json

TOKEN = "8627781342:AAGRpzlKRGmABft7QkTIyzZjWHk4SFqw4wI"

async def diagnose():
    async with httpx.AsyncClient(timeout=30) as c:
        print("🔍 ДІАГНОСТИКА TELEGRAM БОТА")
        print("="*50)
        
        # 1. Перевірка бота
        try:
            r = await c.get(f"https://api.telegram.org/bot{TOKEN}/getMe")
            print(f"✅ getMe: {r.json()['ok']}")
        except Exception as e:
            print(f"❌ getMe: {e}")
        
        # 2. Webhook info
        try:
            r = await c.get(f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo")
            info = r.json()["result"]
            print(f"📡 Webhook URL: {repr(info['url'])}")
            print(f"📊 Pending updates: {info.get('pending_update_count', 0)}")
            print(f"🎯 Allowed updates: {info.get('allowed_updates', [])}")
        except Exception as e:
            print(f"❌ Webhook info: {e}")
        
        # 3. Спробувати getUpdates
        try:
            r = await c.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset=-1&timeout=5")
            result = r.json()
            if result.get("ok"):
                updates = result.get("result", [])
                print(f"📨 Updates (offset=-1): {len(updates)}")
            else:
                print(f"❌ getUpdates error: {result.get('description', 'Unknown')}")
        except Exception as e:
            print(f"❌ getUpdates: {e}")
        
        # 4. Видалити webhook з drop_pending
        try:
            r = await c.post(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", 
                           data={"drop_pending_updates": "true"})
            print(f"🧹 deleteWebhook: {r.json()['ok']}")
        except Exception as e:
            print(f"❌ deleteWebhook: {e}")

if __name__ == "__main__":
    asyncio.run(diagnose())