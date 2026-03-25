#!/usr/bin/env python3
"""
📋 Contract Tests - Telegram API Constraints
Based on Claude.ai recommendations
Tests that our code respects Telegram API limits
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, '/home/sashok/.openclaw/workspace/insilver-v3')

# Telegram API Limits (from Claude.ai)
TELEGRAM_LIMITS = {
    # Messages
    "message_text": 4096,
    "caption": 1024,
    "poll_question": 300,
    "poll_option": 100,
    
    # Keyboards
    "inline_keyboard_buttons_per_row": 8,
    "inline_keyboard_rows": 100,
    "callback_data": 64,  # BYTES, not chars - critical for Unicode!
    "button_text": 64,
    
    # Media
    "photo_size_mb": 10,
    "document_size_mb": 50,
    
    # Bot API
    "messages_per_second": 30,
    "messages_per_chat_per_second": 1,
    "bulk_messages_per_second": 30,
}

def test_admin_message_lengths():
    """Test admin panel messages don't exceed Telegram limits"""
    print("📋 TESTING ADMIN MESSAGE LENGTHS")
    print("-" * 35)
    
    try:
        # Load real training data
        training_file = Path("/home/sashok/.openclaw/workspace/insilver-v3/data/knowledge/training.json")
        with open(training_file, 'r', encoding='utf-8') as f:
            training_data = json.load(f)
        
        print(f"   Testing with {len(training_data)} real records")
        
        # Test view_all_knowledge message length
        confirmed_records = [r for r in training_data if r.get("status", "confirmed") != "unconfirmed"]
        display_records = confirmed_records[:15]  # Current implementation limit
        
        # Simulate message building (simplified version)
        text = f"📄 ЗАПИСИ БАЗИ ЗНАНЬ ({len(confirmed_records)} всього, показано перші 15)\n\n"
        
        for i, record in enumerate(display_records, 1):
            title = record.get("title", f"Запис {record.get('id', '?')}")[:50]
            created = record.get("created", "")[:10] if record.get("created") else "?"
            
            # Content preview (80 chars limit)
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
        
        if len(confirmed_records) > 15:
            text += f"ℹ️ Показано 15 з {len(confirmed_records)} записів.\n\n"
        
        # Check against Telegram limit
        message_length = len(text.encode('utf-8'))
        limit = TELEGRAM_LIMITS["message_text"]
        
        if message_length <= limit:
            print(f"   ✅ Admin message length OK: {message_length}/{limit} bytes")
            return True
        else:
            print(f"   ❌ Admin message TOO LONG: {message_length}/{limit} bytes")
            print(f"   🔧 Exceeds by: {message_length - limit} bytes")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def test_callback_data_lengths():
    """Test callback data doesn't exceed 64 bytes limit"""
    print("\n🔘 TESTING CALLBACK DATA LENGTHS")
    print("-" * 35)
    
    # Test order callback patterns
    test_callbacks = [
        "o:123",
        "order_full",
        "f:cancel",
        "f:back", 
        "f:length:5",
        "contact_master",
        "show_catalog",
        "admin_view",
        "knowledge_view_12"
    ]
    
    all_passed = True
    limit = TELEGRAM_LIMITS["callback_data"]
    
    for callback in test_callbacks:
        byte_length = len(callback.encode('utf-8'))
        if byte_length <= limit:
            print(f"   ✅ '{callback}': {byte_length}/{limit} bytes")
        else:
            print(f"   ❌ '{callback}': {byte_length}/{limit} bytes - TOO LONG")
            all_passed = False
    
    return all_passed

def test_button_text_lengths():
    """Test inline keyboard button texts don't exceed limits"""
    print("\n🔘 TESTING BUTTON TEXT LENGTHS")  
    print("-" * 35)
    
    # Test typical button texts from our bot
    test_buttons = [
        "🛒 Замовити цей виріб",
        "📝 Індивідуальне замовлення",
        "📱 Зв'язок з майстром", 
        "📋 Показати каталог",
        "⬅️ Назад",
        "❌ Скасувати",
        "✅ Підтвердити",
        "🔙 Назад до меню"
    ]
    
    all_passed = True
    limit = TELEGRAM_LIMITS["button_text"]
    
    for button_text in test_buttons:
        byte_length = len(button_text.encode('utf-8'))
        if byte_length <= limit:
            print(f"   ✅ '{button_text}': {byte_length}/{limit} bytes")
        else:
            print(f"   ❌ '{button_text}': {byte_length}/{limit} bytes - TOO LONG")
            all_passed = False
    
    return all_passed

def test_catalog_item_formatting():
    """Test catalog item formatting respects message limits"""
    print("\n🏪 TESTING CATALOG ITEM FORMATTING")
    print("-" * 35)
    
    try:
        from core.catalog import search_catalog, format_item_text
        
        # Test with real data
        search_result = search_catalog("ланцюжки")
        if isinstance(search_result, tuple):
            items, _ = search_result
        else:
            items = search_result
        
        if not items:
            print("   ⚠️ No items found for testing")
            return True
        
        # Test first item formatting
        first_item = items[0]
        formatted_text = format_item_text(first_item)
        
        byte_length = len(formatted_text.encode('utf-8'))
        limit = TELEGRAM_LIMITS["message_text"]
        
        if byte_length <= limit:
            print(f"   ✅ Item formatting OK: {byte_length}/{limit} bytes")
            print(f"   📝 Sample: {formatted_text[:100]}...")
            return True
        else:
            print(f"   ❌ Item formatting TOO LONG: {byte_length}/{limit} bytes")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def run_contract_tests():
    """Run all contract tests"""
    print("📋 TELEGRAM API CONTRACT TESTS")
    print("=" * 40)
    print("Based on Claude.ai recommendations")
    print("Testing API constraints compliance\n")
    
    tests = [
        test_admin_message_lengths,
        test_callback_data_lengths, 
        test_button_text_lengths,
        test_catalog_item_formatting
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ {test.__name__} failed: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 CONTRACT TEST RESULTS:")
    print(f"   Tests passed: {passed}/{total}")
    print(f"   Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("   🌟 EXCELLENT: All Telegram API constraints respected")
    elif passed >= total * 0.75:
        print("   👍 GOOD: Most constraints OK, minor issues")
    else:
        print("   ⚠️ WARNING: API constraint violations detected")
    
    return passed == total

if __name__ == "__main__":
    success = run_contract_tests()
    sys.exit(0 if success else 1)