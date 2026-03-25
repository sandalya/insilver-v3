#!/usr/bin/env python3
"""
🔄 Регресійні тести - кожен production баг = новий тест
На основі Claude.ai рекомендацій
Тести для багів що вже були знайдені та виправлені
"""

import sys
from pathlib import Path
from telegram.ext import Application, ConversationHandler, MessageHandler

# Add project root to path
sys.path.insert(0, '/home/sashok/.openclaw/workspace/insilver-v3')

def test_порядок_обробників_регресія():
    """
    Регресія: Баг #1 - ConversationHandler після MessageHandler
    Виправлено: 2026-03-25
    Симптом: Розмови замовлень заморожені, MessageHandler перехоплює повідомлення
    """
    print("🔄 ТЕСТ РЕГРЕСІЇ: Порядок обробників")
    print("-" * 38)
    
    try:
        from bot.client import setup_handlers
        
        app = Application.builder().token("fake:token").build()
        setup_handlers(app)
        
        # Перевіряємо що ConversationHandler йде ПЕРЕД MessageHandler в групі 1
        handlers_group1 = app.handlers.get(1, [])
        types = [type(h).__name__ for h in handlers_group1]
        
        conv_idx = next((i for i, t in enumerate(types) if t == "ConversationHandler"), -1)
        msg_idx = next((i for i, t in enumerate(types) if t == "MessageHandler"), -1)
        
        if conv_idx != -1 and msg_idx != -1 and conv_idx < msg_idx:
            print(f"   ✅ ConversationHandler({conv_idx}) перед MessageHandler({msg_idx})")
            return True
        else:
            print(f"   ❌ РЕГРЕСІЯ: Неправильний порядок conv:{conv_idx} msg:{msg_idx}")
            return False
            
    except Exception as e:
        print(f"   ❌ Тест регресії не пройшов: {e}")
        return False

def test_довжина_admin_повідомлень_регресія():
    """
    Регресія: Баг #2 - Повідомлення admin панелі перевищують 4096 символів
    Виправлено: 2026-03-25  
    Симптом: "Message too long" при показі всіх 36 записів
    """
    print("\n📋 ТЕСТ РЕГРЕСІЇ: Довжина admin повідомлень")
    print("-" * 45)
    
    try:
        import json
        
        # Завантажуємо реальні дані тренування
        training_file = Path("/home/sashok/.openclaw/workspace/insilver-v3/data/knowledge/training.json")
        with open(training_file, 'r', encoding='utf-8') as f:
            training_data = json.load(f)
        
        confirmed_records = [r for r in training_data if r.get("status", "confirmed") != "unconfirmed"]
        
        # Симулюємо побудову повідомлення (як в bot/admin.py)
        text = f"📄 ЗАПИСИ БАЗИ ЗНАНЬ ({len(confirmed_records)} всього, показано перші 15)\n\n"
        
        display_records = confirmed_records[:15]  # Обмеження після виправлення
        
        for i, record in enumerate(display_records, 1):
            title = record.get("title", f"Запис {record.get('id', '?')}")[:50]
            created = record.get("created", "")[:10] if record.get("created") else "?"
            
            # Контент (обмежений до 80 символів після виправлення)
            content = record.get("content", [])
            if content and isinstance(content, list) and content[0]:
                full_text = content[0].get("text", "").strip()
                display_text = full_text[:80] + "..." if len(full_text) > 80 else full_text
            else:
                display_text = "Порожній запис"
            
            media_count = len(record.get("media", []))
            media_info = f" 📎{media_count}" if media_count > 0 else ""
            
            text += f"{i}. {title} | {created}{media_info}\n"
            text += f"   {display_text}\n\n"
        
        # Перевіряємо що не перевищує Telegram ліміт
        byte_length = len(text.encode('utf-8'))
        
        if byte_length <= 4096:
            print(f"   ✅ Admin повідомлення в межах ліміту: {byte_length}/4096 bytes")
            return True
        else:
            print(f"   ❌ РЕГРЕСІЯ: Admin повідомлення занадто довге: {byte_length}/4096 bytes")
            return False
            
    except Exception as e:
        print(f"   ❌ Тест регресії не пройшов: {e}")
        return False

def test_дублікати_процесів_регресія():
    """
    Регресія: Баг #3 - Множинні процеси main.py
    Виявлено: 2026-03-25
    Симптом: getUpdates конфлікти, нестабільна робота бота
    """
    print("\n🔄 ТЕСТ РЕГРЕСІЇ: Дублікати процесів")
    print("-" * 35)
    
    try:
        import subprocess
        
        # Перевіряємо кількість процесів main.py (виключаємо git і тестові процеси)
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        main_py_lines = [
            line for line in result.stdout.split('\n') 
            if 'main.py' in line 
            and 'grep' not in line
            and 'git commit' not in line  # виключаємо git процеси
            and '/venv/bin/python3 main.py' in line  # тільки справжні запуски бота
        ]
        
        process_count = len(main_py_lines)
        
        if process_count == 1:
            print(f"   ✅ Тільки один процес main.py: {process_count}")
            return True
        else:
            print(f"   ❌ РЕГРЕСІЯ: Знайдено {process_count} процесів main.py")
            for line in main_py_lines:
                print(f"      🔍 {line.strip()}")
            return False
            
    except Exception as e:
        print(f"   ❌ Тест регресії не пройшов: {e}")
        return False

def run_regression_tests():
    """Запустити всі регресійні тести"""
    print("🔄 РЕГРЕСІЙНІ ТЕСТИ")
    print("=" * 25)
    print("Перевірка що виправлені баги не повернулися\n")
    
    tests = [
        test_порядок_обробників_регресія,
        test_довжина_admin_повідомлень_регресія,
        test_дублікати_процесів_регресія
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ {test.__name__} не пройшов: {e}")
            results.append(False)
    
    # Підсумок
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 РЕЗУЛЬТАТИ РЕГРЕСІЙНИХ ТЕСТІВ:")
    print(f"   Пройшло: {passed}/{total}")
    print(f"   Успіх: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("   🌟 ЧУДОВО: Всі виправлені баги залишаються виправленими")
    elif passed >= total * 0.75:
        print("   👍 ДОБРЕ: Більшість регресій не виявлено")
    else:
        print("   ⚠️ УВАГА: Виявлено повернення старих багів!")
    
    return passed == total

if __name__ == "__main__":
    success = run_regression_tests()
    sys.exit(0 if success else 1)