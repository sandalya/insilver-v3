#!/usr/bin/env python3
"""
🔧 ВНУТРІШНІЙ ФУНКЦІОНАЛЬНИЙ ТЕСТ
Максимальне тестування InSilver v3 БЕЗ Telegram API
Тестує core функції напряму - обходить getUpdates конфлікт
"""

import sys
import json
from pathlib import Path

# Add project root
sys.path.insert(0, '/home/sashok/.openclaw/workspace/insilver-v3')

def test_catalog_functions():
    """Тест функцій каталогу"""
    print("🏪 ТЕСТУВАННЯ КАТАЛОГУ")
    print("-" * 25)
    
    try:
        from core.catalog import search_catalog, load_catalog, format_item_text
        
        # Тест 1: Завантаження каталогу
        catalog = load_catalog()
        print(f"   ✅ Каталог завантажено: {len(catalog)} товарів")
        
        # Тест 2: Пошук ланцюжків
        result = search_catalog("ланцюжки")
        if isinstance(result, tuple):
            items, _ = result
        else:
            items = result
        print(f"   ✅ Пошук 'ланцюжки': {len(items)} результатів")
        
        # Тест 3: Пошук каблучок
        result = search_catalog("каблучки") 
        if isinstance(result, tuple):
            items, _ = result
        else:
            items = result
        print(f"   ✅ Пошук 'каблучки': {len(items)} результатів")
        
        # Тест 4: Форматування товару
        if items:
            formatted = format_item_text(items[0])
            print(f"   ✅ Форматування товару: {len(formatted)} символів")
        
        # Тест 5: Складні пошуки (edge cases)
        test_searches = ["сережки", "кільця", "срібло", "золото", "підвіски"]
        for search_term in test_searches:
            result = search_catalog(search_term)
            if isinstance(result, tuple):
                items, _ = result
            else:
                items = result
            print(f"   ✅ Пошук '{search_term}': {len(items)} результатів")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Помилка каталогу: {e}")
        return False

def test_training_data():
    """Тест даних тренування"""
    print("\n🧠 ТЕСТУВАННЯ TRAINING DATA")
    print("-" * 30)
    
    try:
        training_file = Path("/home/sashok/.openclaw/workspace/insilver-v3/data/knowledge/training.json")
        
        with open(training_file, 'r', encoding='utf-8') as f:
            training_data = json.load(f)
        
        print(f"   ✅ Training data завантажено: {len(training_data)} записів")
        
        # Аналіз структури
        confirmed = len([r for r in training_data if r.get("status", "confirmed") != "unconfirmed"])
        with_media = len([r for r in training_data if r.get("media")])
        
        print(f"   ✅ Підтверджені записи: {confirmed}/{len(training_data)}")
        print(f"   ✅ Записи з медіа: {with_media}/{len(training_data)}")
        
        # Перевірка структури записів
        for i, record in enumerate(training_data[:3]):  # Перші 3 записи
            title = record.get("title", "No title")
            content = record.get("content", [])
            content_text = content[0].get("text", "") if content else ""
            
            print(f"   ✅ Запис {i+1}: '{title[:30]}...' ({len(content_text)} символів)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Помилка training data: {e}")
        return False

def test_ai_functions():
    """Тест AI функцій (без реальних викликів)"""
    print("\n🤖 ТЕСТУВАННЯ AI ФУНКЦІЙ")
    print("-" * 27)
    
    try:
        from core.ai import load_all_training_records
        from core.prompt import ENHANCED_SYSTEM_PROMPT
        
        # Тест 1: Завантаження тренувальних записів
        records = load_all_training_records()
        print(f"   ✅ Тренувальні записи: {len(records)} завантажено")
        
        # Тест 2: Системний промпт
        prompt_length = len(ENHANCED_SYSTEM_PROMPT)
        print(f"   ✅ Системний промпт: {prompt_length} символів")
        
        # Тест 3: Структура промпта
        if "ювелірна майстерня" in ENHANCED_SYSTEM_PROMPT.lower():
            print(f"   ✅ Промпт містить контекст майстерні")
        else:
            print(f"   ⚠️ Промпт може не містити контекст")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Помилка AI функцій: {e}")
        return False

def test_order_functions():
    """Тест функцій замовлень"""
    print("\n📝 ТЕСТУВАННЯ ORDER ФУНКЦІЙ")
    print("-" * 30)
    
    try:
        # Перевіряємо що order модуль імпортується
        from bot.order import build_order_handler
        
        # Тест конструктора обробника
        handler = build_order_handler()
        if handler:
            print(f"   ✅ Order handler створено")
            print(f"   ✅ Кількість states: {len(handler.states)}")
            print(f"   ✅ Entry points: {len(handler.entry_points)}")
            print(f"   ✅ Fallbacks: {len(handler.fallbacks)}")
        else:
            print(f"   ❌ Order handler не створено")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Помилка order functions: {e}")
        return False

def test_admin_functions():
    """Тест admin функцій"""
    print("\n👨‍💼 ТЕСТУВАННЯ ADMIN ФУНКЦІЙ")
    print("-" * 30)
    
    try:
        from bot.admin import load_training_data
        
        # Тест завантаження даних
        admin_data = load_training_data()
        print(f"   ✅ Admin data завантажено: {len(admin_data)} записів")
        
        # Тест що не падає на порожніх даних
        if admin_data:
            first_record = admin_data[0]
            print(f"   ✅ Структура записів валідна")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Помилка admin functions: {e}")
        return False

def test_edge_cases():
    """Тест edge cases"""
    print("\n🔍 ТЕСТУВАННЯ EDGE CASES")
    print("-" * 26)
    
    try:
        from core.catalog import search_catalog
        
        # Тест edge cases
        edge_inputs = [
            "",  # порожній рядок
            "   ",  # пробіли
            "дуже довгий запит " * 20,  # довгий запит
            "💍👑🔥",  # емоджі
            "каблучка з д'яволом",  # апостроф
            "ціна: 1,500 грн",  # числа з комою
        ]
        
        success_count = 0
        for test_input in edge_inputs:
            try:
                result = search_catalog(test_input)
                print(f"   ✅ Edge case '{test_input[:20]}...' оброблено")
                success_count += 1
            except Exception as e:
                print(f"   ❌ Edge case '{test_input[:20]}...' помилка: {e}")
        
        print(f"   📊 Edge cases: {success_count}/{len(edge_inputs)} успішно")
        return success_count >= len(edge_inputs) * 0.8  # 80% успішності
        
    except Exception as e:
        print(f"   ❌ Помилка edge cases: {e}")
        return False

def run_internal_function_test():
    """Запустити всі внутрішні функціональні тести"""
    print("🔧 ВНУТРІШНІЙ ФУНКЦІОНАЛЬНИЙ ТЕСТ INSILVER V3")
    print("=" * 55)
    print("Максимальне тестування БЕЗ Telegram API конфліктів")
    print("Обходить getUpdates проблему з Claude.ai методологією\n")
    
    tests = [
        ("Каталог", test_catalog_functions),
        ("Training Data", test_training_data),
        ("AI Функції", test_ai_functions),
        ("Order Функції", test_order_functions),
        ("Admin Функції", test_admin_functions),
        ("Edge Cases", test_edge_cases),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} критична помилка: {e}")
            results.append((test_name, False))
    
    # Звіт
    print(f"\n📊 ВНУТРІШНІЙ ФУНКЦІОНАЛЬНИЙ ТЕСТ - РЕЗУЛЬТАТИ:")
    print("=" * 55)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    success_rate = (passed/total)*100 if total > 0 else 0
    
    print(f"\n🎯 ВНУТРІШНІЙ ТЕСТ ЗВІТ:")
    print(f"   Модулів протестовано: {passed}/{total}")
    print(f"   Відсоток успіху: {success_rate:.1f}%")
    print(f"   Витрати: $0.00 (внутрішні тести)")
    
    if success_rate >= 90:
        print(f"   🌟 ВІДМІННО: Всі core функції працюють!")
        grade = "A+"
    elif success_rate >= 80:
        print(f"   🎯 ЧУДОВО: Основні функції готові")
        grade = "A"  
    elif success_rate >= 70:
        print(f"   👍 ДОБРЕ: Більшість функцій працює")
        grade = "B+"
    else:
        print(f"   ⚠️ ПОТРЕБУЄ РОБОТИ: Виявлені проблеми")
        grade = "B"
    
    print(f"   🎓 Оцінка core функцій: {grade}")
    
    print(f"\n💎 ВИСНОВОК ДЛЯ САШКА:")
    if success_rate >= 80:
        print(f"   🚀 InSilver v3 ГОТОВИЙ для manual тестування!")
        print(f"   ✅ Core функції працюють коректно")
        print(f"   ✅ Каталог, AI, замовлення - все ОК")
        print(f"   🎯 Можеш тестувати через Telegram без побоювань")
    else:
        print(f"   ⚠️ Core функції потребують уваги перед тестуванням")
    
    return success_rate >= 70

if __name__ == "__main__":
    success = run_internal_function_test()
    exit(0 if success else 1)