#!/usr/bin/env python3
"""
🎭 Handler Order & Integration Test
Tests handler registration order and message routing
Level 8.5 - Integration testing improvement
"""

import sys
from pathlib import Path
import inspect

# Add project root to path
sys.path.insert(0, '/home/sashok/.openclaw/workspace/insilver-v3')

def test_handler_registration_order():
    """
    Test that handlers are registered in correct order to avoid conflicts
    """
    print("🔍 HANDLER ORDER INTEGRATION TEST")
    print("=" * 40)
    
    try:
        # Import the setup function
        from bot.client import setup_handlers
        from telegram.ext import Application
        from unittest.mock import MagicMock
        
        # Create mock application
        mock_app = MagicMock()
        mock_app.add_handler = MagicMock()
        mock_app.add_error_handler = MagicMock()
        mock_app.post_init = None
        
        # Get the setup function source to analyze handler order
        source = inspect.getsource(setup_handlers)
        lines = source.split('\n')
        
        # Find handler registration lines
        handler_lines = []
        for i, line in enumerate(lines):
            if 'add_handler' in line and 'group=' in line:
                handler_lines.append((i, line.strip()))
        
        print(f"📋 Handler registration analysis:")
        print(f"   Found {len(handler_lines)} handler registrations")
        
        # Check critical order: ConversationHandler should be before MessageHandler
        conversation_handler_line = None
        message_handler_line = None
        
        for line_num, line in handler_lines:
            if 'build_order_handler' in line:
                conversation_handler_line = line_num
                print(f"   ✅ ConversationHandler at line {line_num}: {line}")
            elif 'MessageHandler(filters.TEXT' in line and 'handle_message' in line:
                message_handler_line = line_num
                print(f"   ⚠️ General MessageHandler at line {line_num}: {line}")
        
        # Verify order
        if conversation_handler_line and message_handler_line:
            if conversation_handler_line < message_handler_line:
                print("   ✅ CORRECT ORDER: ConversationHandler BEFORE MessageHandler")
                return True
            else:
                print("   ❌ WRONG ORDER: MessageHandler BEFORE ConversationHandler")
                print("   🔧 This causes conversation messages to be intercepted!")
                return False
        else:
            print("   ⚠️ Could not detect both handlers in source")
            return False
            
    except Exception as e:
        print(f"❌ Handler order test failed: {e}")
        return False

def test_conversation_handler_priority():
    """
    Test ConversationHandler has proper message filtering
    """
    print(f"\n🎯 CONVERSATION HANDLER PRIORITY TEST")
    print("-" * 40)
    
    try:
        from bot.order import build_order_handler
        from telegram.ext import ConversationHandler, MessageHandler
        
        # Build the order handler
        order_handler = build_order_handler()
        
        if not isinstance(order_handler, ConversationHandler):
            print("❌ Order handler is not ConversationHandler")
            return False
        
        # Check if it has proper entry points
        entry_points = order_handler.entry_points
        callback_entries = [ep for ep in entry_points if hasattr(ep, 'pattern')]
        command_entries = [ep for ep in entry_points if hasattr(ep, 'commands')]
        
        print(f"   Entry points: {len(entry_points)} total")
        print(f"   - Callback handlers: {len(callback_entries)}")
        print(f"   - Command handlers: {len(command_entries)}")
        
        # Check states
        states = order_handler.states
        print(f"   Conversation states: {len(states)}")
        
        # Verify text handling in states
        has_text_handlers = False
        for state_name, handlers in states.items():
            for handler in handlers:
                if isinstance(handler, MessageHandler):
                    has_text_handlers = True
                    print(f"   ✅ State {state_name} handles TEXT messages")
                    break
        
        if has_text_handlers:
            print("   ✅ ConversationHandler properly handles text in conversations")
            return True
        else:
            print("   ❌ ConversationHandler missing text message handling")
            return False
            
    except Exception as e:
        print(f"❌ Conversation handler test failed: {e}")
        return False

def test_message_handler_filters():
    """
    Test that general message handler has proper filters
    """
    print(f"\n🔧 MESSAGE HANDLER FILTERS TEST")
    print("-" * 35)
    
    try:
        from bot.client import handle_message
        
        # Check if handle_message has conversation check
        import inspect
        source = inspect.getsource(handle_message)
        
        has_conversation_check = 'ctx.user_data.get("order")' in source
        
        if has_conversation_check:
            print("   ✅ General handler checks for active conversations")
            print("   ✅ Should not interfere with ConversationHandler")
            return True
        else:
            print("   ❌ General handler missing conversation check")
            print("   ⚠️ May interfere with active conversations")
            return False
            
    except Exception as e:
        print(f"❌ Message handler filter test failed: {e}")
        return False

def test_integration_flow():
    """
    Test complete integration flow scenario
    """
    print(f"\n🎭 INTEGRATION FLOW SIMULATION")
    print("-" * 35)
    
    try:
        print("   📋 Simulating user flow:")
        print("   1. User starts order conversation")
        print("   2. ConversationHandler should catch callbacks")
        print("   3. ConversationHandler should catch text responses")
        print("   4. General handler should NOT interfere")
        
        # Test handler order
        order_test = test_handler_registration_order()
        
        # Test conversation priority  
        conversation_test = test_conversation_handler_priority()
        
        # Test message filters
        filter_test = test_message_handler_filters()
        
        all_passed = order_test and conversation_test and filter_test
        
        if all_passed:
            print("   ✅ Integration flow should work correctly")
        else:
            print("   ❌ Integration flow has potential issues")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Integration flow test failed: {e}")
        return False

def main():
    """Run all handler integration tests"""
    print("🎭 LEVEL 8.5: HANDLER INTEGRATION TESTING")
    print("=" * 50)
    
    # Run tests
    test1 = test_handler_registration_order()
    test2 = test_conversation_handler_priority()
    test3 = test_message_handler_filters()
    test4 = test_integration_flow()
    
    # Summary
    tests = [test1, test2, test3, test4]
    passed = sum(tests)
    total = len(tests)
    
    print(f"\n📊 INTEGRATION TEST RESULTS:")
    print(f"   Tests passed: {passed}/{total}")
    print(f"   Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("   🌟 EXCELLENT: All integration tests passed")
        print("   ✅ Handler conflicts resolved")
    elif passed >= total * 0.75:
        print("   👍 GOOD: Most integration tests passed")
    else:
        print("   ⚠️ WARNING: Integration issues detected")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)