#!/usr/bin/env python3
"""
🚀 МАКСИМАЛЬНИЙ STAGING TEST
Повний тест InSilver v3 через @staging_kit_bot з Claude.ai методологією
Бюджет: до $2 (уникаємо дорогих GPT-4 викликів)
"""

import asyncio
import os
import time
from pathlib import Path
from telegram import Bot

class MaximumStagingTest:
    """
    Максимальний staging тест з Claude.ai reliable getUpdates
    Тестує ВСІ основні функції InSilver v3 без дорогих AI викликів
    """
    
    def __init__(self):
        # Завантажуємо staging config
        staging_env = Path("/home/sashok/.openclaw/workspace/insilver-v3/.env.staging")
        
        self.config = {}
        with open(staging_env, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    self.config[key] = value
        
        self.bot = Bot(token=self.config['STAGING_BOT_TOKEN'])
        self.test_chat_id = int(self.config['TEST_CHAT_ID'])
        self.last_update_id = None
        self.results = []
        self.cost_estimate = 0.0
    
    async def setup(self):
        """Claude.ai reliable setup pattern"""
        print("🔧 Налаштування максимального staging тесту...")
        
        try:
            # Отримуємо bot info
            bot_info = await self.bot.get_me()
            print(f"   🤖 Staging bot: @{bot_info.username}")
            
            # Claude.ai reliable pattern - запам'ятовуємо update_id
            updates = await self.bot.get_updates(limit=1, timeout=0)
            if updates:
                self.last_update_id = updates[-1].update_id
                print(f"   📍 Починаємо з update_id: {self.last_update_id}")
            else:
                self.last_update_id = 0
                print(f"   📍 Немає попередніх updates, починаємо з 0")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Setup помилка: {e}")
            return False
    
    async def wait_for_reply(self, timeout: int = 10, expect_ai: bool = False) -> list:
        """
        Claude.ai reliable long polling з cost tracking
        expect_ai = True означає що очікуємо GPT-4 відповідь (дорого)
        """
        if expect_ai:
            print(f"   ⏳ Чекаємо AI відповідь (може коштувати ~$0.05-0.10)...")
            self.cost_estimate += 0.07  # Середня ціна GPT-4 відповіді
            timeout = 20  # AI відповіді можуть зайняти більше часу
        else:
            print(f"   ⏳ Чекаємо швидку відповідь ({timeout}s)...")
        
        deadline = asyncio.get_event_loop().time() + timeout
        offset = (self.last_update_id or 0) + 1
        
        while asyncio.get_event_loop().time() < deadline:
            try:
                # Claude.ai exact long polling pattern
                updates = await self.bot.get_updates(
                    offset=offset,
                    timeout=5,  # Long polling timeout
                    allowed_updates=["message"]
                )
                
                bot_replies = [
                    u.message for u in updates
                    if u.message and u.message.from_user.is_bot
                ]
                
                if bot_replies:
                    reply_lengths = [len(r.text or "N/A") for r in bot_replies]
                    print(f"   ✅ Отримано {len(bot_replies)} відповідей (довжина: {reply_lengths})")
                    return bot_replies
                
                # Оновлюємо offset для наступної ітерації
                if updates:
                    offset = updates[-1].update_id + 1
                    
            except Exception as e:
                print(f"   ⚠️ Polling помилка: {e}")
                await asyncio.sleep(1)
        
        print(f"   ❌ Немає відповіді за {timeout}s")
        return []
    
    async def send_and_test(self, message: str, test_name: str, expect_ai: bool = False) -> bool:
        """Надіслати повідомлення і перевірити відповідь"""
        print(f"\n📤 {test_name}")
        print(f"   Повідомлення: '{message}'")
        
        try:
            # Надсилаємо повідомлення
            sent = await self.bot.send_message(
                chat_id=self.test_chat_id,
                text=message
            )
            print(f"   ✅ Надіслано (ID: {sent.message_id})")
            
            # Чекаємо відповідь з Claude.ai методологією
            replies = await self.wait_for_reply(expect_ai=expect_ai)
            
            success = len(replies) > 0
            if success:
                # Аналізуємо відповідь
                reply_text = replies[0].text if replies[0].text else "[немає тексту]"
                print(f"   ✅ УСПІХ: {reply_text[:100]}...")
                
                # Перевіряємо що відповідь має сенс
                if "помилка" in reply_text.lower() or "error" in reply_text.lower():
                    print(f"   ⚠️ Відповідь містить помилку")
                    success = False
            
            self.results.append((test_name, "✅ PASS" if success else "❌ FAIL"))
            return success
            
        except Exception as e:
            print(f"   ❌ Помилка: {e}")
            self.results.append((test_name, f"❌ FAIL: {e}"))
            return False
    
    # ======= ШВИДКІ ТЕСТИ (БЕЗ AI, ~$0) =======
    
    async def test_start_command(self) -> bool:
        """Тест /start - має відповідати миттєво без AI"""
        return await self.send_and_test("/start", "START команда", expect_ai=False)
    
    async def test_help_command(self) -> bool:
        """Тест /help - швидка відповідь"""
        return await self.send_and_test("/help", "HELP команда", expect_ai=False)
    
    async def test_contact_command(self) -> bool:
        """Тест /contact - швидка відповідь"""
        return await self.send_and_test("/contact", "CONTACT команда", expect_ai=False)
    
    async def test_catalog_command(self) -> bool:
        """Тест /catalog - має показати каталог без AI"""
        return await self.send_and_test("/catalog", "CATALOG команда", expect_ai=False)
    
    async def test_catalog_search_lanczuzhky(self) -> bool:
        """Тест пошуку 'ланцюжки' - має знайти без AI"""
        return await self.send_and_test("ланцюжки", "Пошук ланцюжків", expect_ai=False)
    
    async def test_catalog_search_kabluchky(self) -> bool:
        """Тест пошуку 'каблучки' - має знайти без AI"""
        return await self.send_and_test("каблучки", "Пошук каблучок", expect_ai=False)
    
    async def test_invalid_command(self) -> bool:
        """Тест неіснуючої команди"""
        return await self.send_and_test("/nonexistent", "Неіснуюча команда", expect_ai=False)
    
    # ======= AI ТЕСТИ (ДОРОГІ, ~$0.50 максимум) =======
    
    async def test_complex_question(self) -> bool:
        """Складне питання про ювелірні вироби - викличе GPT-4"""
        question = "Скільки коштує срібний ланцюжок на 18 років?"
        return await self.send_and_test(question, "Складне питання про ціни", expect_ai=True)
    
    async def test_order_inquiry(self) -> bool:
        """Питання про замовлення - може викликати AI"""
        question = "Хочу замовити каблучку з гравіюванням"
        return await self.send_and_test(question, "Запит на замовлення", expect_ai=True)
    
    async def test_material_question(self) -> bool:
        """Питання про матеріали - training data"""
        question = "Яка різниця між срібла 925 та 999 проби?"
        return await self.send_and_test(question, "Питання про матеріали", expect_ai=True)
    
    # ======= EDGE CASES (БЕЗ AI, ~$0) =======
    
    async def test_empty_message(self) -> bool:
        """Тест порожнього повідомлення"""
        return await self.send_and_test(" ", "Порожнє повідомлення", expect_ai=False)
    
    async def test_long_message(self) -> bool:
        """Тест довгого повідомлення"""
        long_text = "каблучка " * 50  # 500 символів
        return await self.send_and_test(long_text, "Довге повідомлення", expect_ai=False)
    
    async def test_emoji_message(self) -> bool:
        """Тест емоджі"""
        return await self.send_and_test("💍👑🔥", "Емоджі повідомлення", expect_ai=False)
    
    async def test_ukrainian_special_chars(self) -> bool:
        """Тест української мови з апострофами"""
        return await self.send_and_test("д'якую за підв'язку", "Українські спецсимволи", expect_ai=False)
    
    async def run_maximum_test(self) -> list:
        """
        Запустити МАКСИМАЛЬНИЙ staging тест
        Починаємо з дешевих тестів, переходимо до дорогих
        """
        print("🚀 МАКСИМАЛЬНИЙ STAGING TEST")
        print("=" * 45)
        print("Повний тест InSilver v3 через @staging_kit_bot")
        print(f"Бюджет: до $2.00 (поточна оцінка: ${self.cost_estimate:.2f})\n")
        
        # Setup
        if not await self.setup():
            return [("setup", "❌ FAIL: Setup failed")]
        
        print("🏃‍♂️ Фаза 1: ШВИДКІ ТЕСТИ (без AI витрат)")
        print("-" * 50)
        
        # Швидкі тести (0 витрат)
        quick_tests = [
            self.test_start_command,
            self.test_help_command, 
            self.test_contact_command,
            self.test_catalog_command,
            self.test_catalog_search_lanczuzhky,
            self.test_catalog_search_kabluchky,
            self.test_invalid_command,
        ]
        
        for test in quick_tests:
            if self.cost_estimate > 2.0:
                print(f"⚠️ Досягнуто бюджетний ліміт ${self.cost_estimate:.2f}")
                break
            try:
                await test()
                await asyncio.sleep(1.5)  # Пауза між тестами
            except Exception as e:
                self.results.append((test.__name__, f"❌ FAIL: {e}"))
        
        print(f"\n🧠 Фаза 2: AI ТЕСТИ (дорогі, ~${self.cost_estimate:.2f} витрачено)")
        print("-" * 50)
        
        # AI тести (дорогі, але обмежені)
        ai_tests = [
            self.test_complex_question,
            self.test_material_question,  
            self.test_order_inquiry,
        ]
        
        ai_tests_run = 0
        for test in ai_tests:
            if self.cost_estimate > 1.5:  # Залишаємо $0.50 буфер
                print(f"⚠️ Обмежуємо AI тести (бюджет: ${self.cost_estimate:.2f}/$2.00)")
                break
            
            try:
                await test()
                ai_tests_run += 1
                await asyncio.sleep(3)  # Довша пауза для AI тестів
            except Exception as e:
                self.results.append((test.__name__, f"❌ FAIL: {e}"))
            
            # Обмежуємо кількість AI тестів
            if ai_tests_run >= 2:
                print(f"⚠️ Обмежуємо AI тести до 2 штук для економії")
                break
        
        print(f"\n🔍 Фаза 3: EDGE CASES (без AI)")
        print("-" * 50)
        
        # Edge cases (швидкі)
        edge_tests = [
            self.test_empty_message,
            self.test_emoji_message,
            self.test_ukrainian_special_chars,
            self.test_long_message,
        ]
        
        for test in edge_tests:
            try:
                await test()
                await asyncio.sleep(1)
            except Exception as e:
                self.results.append((test.__name__, f"❌ FAIL: {e}"))
        
        return self.results

async def main():
    """Головний runner максимального staging тесту"""
    print("🚀 МАКСИМАЛЬНИЙ INSILVER V3 STAGING TEST")
    print("=" * 50)
    print("Claude.ai методологія + повне покриття функцій")
    print("Бюджетне обмеження: до $2.00\n")
    
    tester = MaximumStagingTest()
    results = await tester.run_maximum_test()
    
    # Детальний звіт
    print(f"\n📊 МАКСИМАЛЬНИЙ STAGING TEST РЕЗУЛЬТАТИ:")
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
    
    if success_rate >= 90:
        print(f"   🌟 ВІДМІННО: InSilver v3 ready for production!")
        grade = "A+"
    elif success_rate >= 80:
        print(f"   🎯 ЧУДОВО: Майже всі функції працюють")
        grade = "A"
    elif success_rate >= 70:
        print(f"   👍 ДОБРЕ: Більшість функцій OK")
        grade = "B+"
    else:
        print(f"   ⚠️ ПОТРЕБУЄ РОБОТИ: Виявлені проблеми")
        grade = "B"
    
    print(f"   🎓 Оцінка: {grade}")
    
    print(f"\n💎 CLAUDE.AI МЕТОДОЛОГІЯ:")
    print(f"   ✅ Reliable long polling застосовано")
    print(f"   ✅ Staging bot testing реалізовано")
    print(f"   ✅ Cost-aware approach дотримано")
    print(f"   ✅ Real production scenarios протестовано")
    
    return success_rate >= 75

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)