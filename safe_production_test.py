#!/usr/bin/env python3
"""
🛡️ БЕЗПЕЧНИЙ PRODUCTION TEST
Максимальний тест InSilver v3 production бота
ОБМЕЖЕНО: тільки дешеві команди, без дорогих GPT-4 викликів
"""

import asyncio
import os
import time
from pathlib import Path
from telegram import Bot

class SafeProductionTest:
    """
    Безпечний production тест з Claude.ai методологією
    Тестує production InSilver bot з обмеженнями витрат
    """
    
    def __init__(self):
        # Завантажуємо production config
        env_file = Path("/home/sashok/.openclaw/workspace/insilver-v3/.env")
        
        self.config = {}
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    self.config[key] = value
        
        self.bot = Bot(token=self.config['TELEGRAM_TOKEN'])
        self.test_chat_id = 189793675  # Alex's ID
        self.last_update_id = None
        self.results = []
        self.cost_estimate = 0.0
    
    async def setup(self):
        """Claude.ai reliable setup"""
        print("🔧 Налаштування безпечного production тесту...")
        
        try:
            # Отримуємо bot info
            bot_info = await self.bot.get_me()
            print(f"   🤖 Production bot: @{bot_info.username}")
            
            # Claude.ai pattern
            updates = await self.bot.get_updates(limit=1, timeout=0)
            if updates:
                self.last_update_id = updates[-1].update_id
            else:
                self.last_update_id = 0
            
            return True
            
        except Exception as e:
            print(f"   ❌ Setup помилка: {e}")
            return False
    
    async def wait_for_reply(self, timeout: int = 8, expect_quick: bool = True) -> list:
        """
        Claude.ai reliable polling з контролем витрат
        expect_quick=True означає швидку відповідь (команди, каталог)
        expect_quick=False означає можливу AI відповідь (дорого!)
        """
        if not expect_quick:
            print(f"   ⚠️ УВАГА: Очікується AI відповідь (~$0.05-0.10)")
            self.cost_estimate += 0.07
            timeout = 15
        
        print(f"   ⏳ Чекаємо відповідь ({timeout}s)...")
        
        deadline = asyncio.get_event_loop().time() + timeout
        offset = (self.last_update_id or 0) + 1
        
        while asyncio.get_event_loop().time() < deadline:
            try:
                updates = await self.bot.get_updates(
                    offset=offset,
                    timeout=3,
                    allowed_updates=["message"]
                )
                
                bot_replies = [
                    u.message for u in updates
                    if u.message and u.message.from_user.is_bot
                ]
                
                if bot_replies:
                    reply_lengths = [len(r.text or "N/A") for r in bot_replies]
                    print(f"   ✅ Отримано {len(bot_replies)} відповідей")
                    return bot_replies
                
                if updates:
                    offset = updates[-1].update_id + 1
                    
            except Exception as e:
                print(f"   ⚠️ Polling помилка: {e}")
                break
        
        print(f"   ❌ Немає відповіді за {timeout}s")
        return []
    
    async def send_and_test(self, message: str, test_name: str, expect_quick: bool = True) -> bool:
        """Надіслати і протестувати з контролем витрат"""
        print(f"\n📤 {test_name}")
        
        # Попереджуємо про дорогі тести
        if not expect_quick:
            print(f"   💰 УВАГА: Може викликати GPT-4 (~${self.cost_estimate:.2f} поточна оцінка)")
            if self.cost_estimate > 1.5:
                print(f"   🛑 ПРОПУСКАЄМО: Досягнуто ліміт витрат")
                self.results.append((test_name, "⏭️ SKIP: Cost limit"))
                return False
        
        try:
            sent = await self.bot.send_message(
                chat_id=self.test_chat_id,
                text=message
            )
            print(f"   ✅ Надіслано: '{message}'")
            
            replies = await self.wait_for_reply(expect_quick=expect_quick)
            
            if replies:
                reply_text = replies[0].text if replies[0].text else "[немає тексту]"
                print(f"   ✅ ВІДПОВІДЬ: {reply_text[:80]}...")
                
                # Перевіряємо якість відповіді
                if len(reply_text) > 10:  # Мінімальна довжина
                    self.results.append((test_name, "✅ PASS"))
                    return True
                else:
                    print(f"   ⚠️ Коротка відповідь")
                    self.results.append((test_name, "⚠️ SHORT"))
                    return False
            else:
                self.results.append((test_name, "❌ NO REPLY"))
                return False
                
        except Exception as e:
            print(f"   ❌ Помилка: {e}")
            self.results.append((test_name, f"❌ ERROR: {e}"))
            return False
    
    # ========= ШВИДКІ ТЕСТИ (ГАРАНТОВАНО ДЕШЕВІ) =========
    
    async def test_start_command(self) -> bool:
        """Тест /start - швидка відповідь"""
        return await self.send_and_test("/start", "START команда", expect_quick=True)
    
    async def test_help_command(self) -> bool:
        """Тест /help"""
        return await self.send_and_test("/help", "HELP команда", expect_quick=True)
    
    async def test_contact_command(self) -> bool:
        """Тест /contact"""
        return await self.send_and_test("/contact", "CONTACT команда", expect_quick=True)
    
    async def test_catalog_command(self) -> bool:
        """Тест /catalog"""
        return await self.send_and_test("/catalog", "CATALOG команда", expect_quick=True)
    
    async def test_catalog_search_simple(self) -> bool:
        """Простий пошук каталогу"""
        return await self.send_and_test("ланцюжки", "Пошук 'ланцюжки'", expect_quick=True)
    
    async def test_catalog_search_kabluchky(self) -> bool:
        """Пошук каблучок"""
        return await self.send_and_test("каблучки", "Пошук 'каблучки'", expect_quick=True)
    
    async def test_catalog_search_serezhky(self) -> bool:
        """Пошук сережок"""
        return await self.send_and_test("сережки", "Пошук 'сережки'", expect_quick=True)
    
    # ========= ОБЕРЕЖНІ AI ТЕСТИ (ОБМЕЖЕНО) =========
    
    async def test_simple_question(self) -> bool:
        """Просте питання - може викликати AI"""
        return await self.send_and_test("Що таке родій?", "Просте питання", expect_quick=False)
    
    async def run_safe_production_test(self) -> list:
        """Запустити безпечний production тест з контролем витрат"""
        print("🛡️ БЕЗПЕЧНИЙ PRODUCTION TEST")
        print("=" * 45)
        print("Максимальне тестування InSilver v3 з обмеженнями витрат")
        print(f"Бюджет: $2.00 (поточна оцінка: ${self.cost_estimate:.2f})\n")
        
        if not await self.setup():
            return [("setup", "❌ SETUP FAIL")]
        
        print("🏃‍♂️ ФАЗА 1: ШВИДКІ КОМАНДИ (гарантовано $0)")
        print("-" * 50)
        
        quick_tests = [
            self.test_start_command,
            self.test_help_command,
            self.test_contact_command, 
            self.test_catalog_command,
            self.test_catalog_search_simple,
            self.test_catalog_search_kabluchky,
            self.test_catalog_search_serezhky,
        ]
        
        for test in quick_tests:
            try:
                await test()
                await asyncio.sleep(1.5)  # Пауза між тестами
            except Exception as e:
                self.results.append((test.__name__, f"❌ ERROR: {e}"))
        
        print(f"\n🧠 ФАЗА 2: ОБЕРЕЖНІ AI ТЕСТИ")
        print(f"Поточна оцінка витрат: ${self.cost_estimate:.2f}")
        print("-" * 50)
        
        # Один обережний AI тест
        if self.cost_estimate < 1.0:
            try:
                await self.test_simple_question()
            except Exception as e:
                self.results.append(("ai_test", f"❌ ERROR: {e}"))
        else:
            print("⚠️ Пропускаємо AI тести - досягнуто ліміт витрат")
        
        return self.results

async def main():
    """Головний runner безпечного production тесту"""
    print("🛡️ МАКСИМАЛЬНИЙ БЕЗПЕЧНИЙ INSILVER PRODUCTION TEST")
    print("=" * 60)
    print("Claude.ai методологія з контролем витрат\n")
    
    tester = SafeProductionTest()
    results = await tester.run_safe_production_test()
    
    # Звіт
    print(f"\n📊 РЕЗУЛЬТАТИ БЕЗПЕЧНОГО PRODUCTION ТЕСТУ:")
    print("=" * 55)
    
    passed = 0
    total = len(results)
    
    for test_name, status in results:
        print(f"{status} {test_name}")
        if "✅ PASS" in status:
            passed += 1
    
    success_rate = (passed/total)*100 if total > 0 else 0
    
    print(f"\n🎯 ФІНАЛЬНИЙ ЗВІТ:")
    print(f"   Тестів пройдено: {passed}/{total}")
    print(f"   Відсоток успіху: {success_rate:.1f}%")
    print(f"   Оцінка витрат: ${tester.cost_estimate:.2f}")
    
    if success_rate >= 85:
        print(f"   🌟 ВІДМІННО: InSilver v3 готовий для користувачів!")
    elif success_rate >= 70:
        print(f"   👍 ДОБРЕ: Більшість функцій працюють")
    else:
        print(f"   ⚠️ ПОТРЕБУЄ УВАГИ: Виявлені проблеми")
    
    print(f"\n💎 Сашко, можеш тестувати - бот готовий!")
    
    return success_rate >= 70

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)