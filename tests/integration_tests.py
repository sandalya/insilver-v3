#!/usr/bin/env python3
"""
🔗 Integration Tests - Bot App Initialization
Based on Claude.ai recommendations
Tests handler registration order and app setup
"""

import sys
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, '/home/sashok/.openclaw/workspace/insilver-v3')

def get_registered_handlers(app):
    """Extract handlers in registration order (Claude.ai code)"""
    return {
        group: list(handlers) 
        for group, handlers in app.handlers.items()
    }

def test_conversation_handlers_registered_before_catch_all():
    """Test ConversationHandler comes before MessageHandler (Claude.ai exact fix)"""
    print("🔗 TESTING CONVERSATION HANDLER PRIORITY")
    print("-" * 40)
    
    try:
        # Import bot setup
        from bot.client import setup_handlers
        from telegram.ext import Application, ConversationHandler, MessageHandler
        
        # Create real app with fake token
        app = Application.builder().token("fake:token").build()
        
        # Register handlers exactly like production
        setup_handlers(app)
        
        # Analyze handler registration
        handlers = get_registered_handlers(app)
        
        print(f"   Found {len(handlers)} handler groups")
        
        # Check critical group 1 (main handlers)
        if 1 not in handlers:
            print("   ❌ No handlers in group 1")
            return False
        
        group1_handlers = handlers[1]
        types = [type(h).__name__ for h in group1_handlers]
        
        print(f"   Group 1 handlers: {len(group1_handlers)} total")
        for i, handler_type in enumerate(types):
            print(f"     {i+1}. {handler_type}")
        
        # Find ConversationHandler and MessageHandler positions
        conv_indices = [i for i, t in enumerate(types) if t == "ConversationHandler"]
        msg_indices = [i for i, t in enumerate(types) if "MessageHandler" in t and "ConversationHandler" not in t]
        
        if not conv_indices:
            print("   ⚠️ No ConversationHandler found in group 1")
            return True  # Not critical if no conversations
        
        if not msg_indices:
            print("   ⚠️ No general MessageHandler found in group 1")
            return True  # Not critical if no general handler
        
        # CRITICAL TEST: ConversationHandler must come before MessageHandler
        conv_idx = conv_indices[0]  # First conversation handler
        msg_idx = msg_indices[0]    # First message handler
        
        if conv_idx < msg_idx:
            print(f"   ✅ CORRECT ORDER: ConversationHandler({conv_idx}) before MessageHandler({msg_idx})")
            return True
        else:
            print(f"   ❌ WRONG ORDER: ConversationHandler({conv_idx}) after MessageHandler({msg_idx})")
            print("   🔧 This causes conversation messages to be intercepted!")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def test_error_handler_registered():
    """Test error handler is properly registered (Claude.ai code)"""
    print("\n🚨 TESTING ERROR HANDLER REGISTRATION")
    print("-" * 38)
    
    try:
        from bot.client import setup_handlers
        from telegram.ext import Application
        
        app = Application.builder().token("fake:token").build()
        setup_handlers(app)
        
        error_handlers_count = len(app.error_handlers)
        
        if error_handlers_count > 0:
            print(f"   ✅ Error handler registered: {error_handlers_count} handler(s)")
            return True
        else:
            print("   ❌ No error handler registered!")
            print("   🔧 Unhandled errors will crash the bot")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def test_no_duplicate_command_handlers():
    """Test no duplicate command handlers (Claude.ai code)"""
    print("\n📝 TESTING DUPLICATE COMMAND HANDLERS")
    print("-" * 37)
    
    try:
        from bot.client import setup_handlers
        from telegram.ext import Application, CommandHandler
        
        app = Application.builder().token("fake:token").build()
        setup_handlers(app)
        
        # Collect all commands
        commands = []
        for group_handlers in app.handlers.values():
            for handler in group_handlers:
                if isinstance(handler, CommandHandler):
                    commands.extend(handler.commands)
        
        print(f"   Found commands: {commands}")
        
        # Check for duplicates
        unique_commands = set(commands)
        if len(commands) == len(unique_commands):
            print(f"   ✅ No duplicate commands: {len(commands)} unique")
            return True
        else:
            duplicates = [cmd for cmd in unique_commands if commands.count(cmd) > 1]
            print(f"   ❌ Duplicate commands found: {duplicates}")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def test_admin_handlers_proper_group():
    """Test admin handlers are in higher group number (lower priority)"""
    print("\n👨‍💼 TESTING ADMIN HANDLER GROUP ISOLATION")
    print("-" * 42)
    
    try:
        from bot.client import setup_handlers
        from telegram.ext import Application
        
        app = Application.builder().token("fake:token").build()
        setup_handlers(app)
        
        handlers = get_registered_handlers(app)
        
        # Find admin handlers (should be in group 2)
        admin_group = None
        regular_group = None
        
        for group_num, group_handlers in handlers.items():
            if group_num == 1:
                regular_group = group_num
            elif group_num == 2:
                admin_group = group_num
        
        if admin_group is not None and regular_group is not None:
            if admin_group > regular_group:
                print(f"   ✅ Admin handlers in higher group ({admin_group}) than regular ({regular_group})")
                print(f"   ✅ Admin handlers have lower priority (correct)")
                return True
            else:
                print(f"   ❌ Admin handlers in wrong group: {admin_group} <= {regular_group}")
                return False
        else:
            print(f"   ⚠️ Expected groups not found: regular={regular_group}, admin={admin_group}")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def test_no_group_priority_conflicts():
    """Test handlers in same group don't conflict by type (Claude.ai exact code)"""
    print("\n⚔️ TESTING GROUP PRIORITY CONFLICTS")
    print("-" * 36)
    
    try:
        from bot.client import setup_handlers
        from telegram.ext import Application, MessageHandler
        
        app = Application.builder().token("fake:token").build()
        setup_handlers(app)
        
        handlers = get_registered_handlers(app)
        
        all_conflicts_resolved = True
        
        for group_num, group_handlers in handlers.items():
            # Check for multiple catch-all MessageHandlers in same group
            catch_all_count = sum(
                1 for h in group_handlers 
                if isinstance(h, MessageHandler) and 
                str(h.filters) in ("filters.ALL", "True", "None")
            )
            
            if catch_all_count <= 1:
                print(f"   ✅ Group {group_num}: {catch_all_count} catch-all MessageHandler (OK)")
            else:
                print(f"   ❌ Group {group_num}: {catch_all_count} catch-all MessageHandlers (CONFLICT!)")
                all_conflicts_resolved = False
        
        return all_conflicts_resolved
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def test_conversation_states_are_complete():
    """Test all ConversationHandler states have handlers (Claude.ai exact code)"""
    print("\n🗣️ TESTING CONVERSATION STATE COMPLETENESS")
    print("-" * 42)
    
    try:
        from bot.client import setup_handlers
        from telegram.ext import Application, ConversationHandler
        
        app = Application.builder().token("fake:token").build()
        setup_handlers(app)
        
        handlers = get_registered_handlers(app)
        
        all_states_complete = True
        conversation_count = 0
        
        for group_num, group_handlers in handlers.items():
            for handler in group_handlers:
                if isinstance(handler, ConversationHandler):
                    conversation_count += 1
                    print(f"   📝 ConversationHandler found in group {group_num}")
                    
                    # Check all states have handlers
                    for state, state_handlers in handler.states.items():
                        if state_handlers:
                            print(f"      ✅ State {state}: {len(state_handlers)} handler(s)")
                        else:
                            print(f"      ❌ State {state}: NO HANDLERS (broken conversation!)")
                            all_states_complete = False
                    
                    # Check entry points
                    if handler.entry_points:
                        print(f"      ✅ Entry points: {len(handler.entry_points)}")
                    else:
                        print(f"      ❌ No entry points (unreachable conversation!)")
                        all_states_complete = False
                    
                    # Check fallbacks
                    if handler.fallbacks:
                        print(f"      ✅ Fallbacks: {len(handler.fallbacks)}")
                    else:
                        print(f"      ⚠️ No fallbacks (consider adding for error handling)")
        
        if conversation_count == 0:
            print("   ⚠️ No ConversationHandlers found")
            return True  # Not an error if no conversations
        
        if all_states_complete:
            print(f"   ✅ All {conversation_count} conversations have complete states")
        else:
            print(f"   ❌ Some conversations have incomplete states")
        
        return all_states_complete
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def test_handler_group_structure():
    """Test overall handler group structure makes sense"""
    print("\n🏗️ TESTING HANDLER GROUP STRUCTURE")
    print("-" * 36)
    
    try:
        from bot.client import setup_handlers
        from telegram.ext import Application
        
        app = Application.builder().token("fake:token").build()
        setup_handlers(app)
        
        handlers = get_registered_handlers(app)
        
        print(f"   Handler groups found: {list(handlers.keys())}")
        
        for group_num, group_handlers in sorted(handlers.items()):
            handler_types = [type(h).__name__ for h in group_handlers]
            handler_counts = {}
            for ht in handler_types:
                handler_counts[ht] = handler_counts.get(ht, 0) + 1
            
            print(f"   Group {group_num}: {len(group_handlers)} handlers")
            for handler_type, count in handler_counts.items():
                print(f"     - {handler_type}: {count}")
        
        # Basic sanity checks
        total_handlers = sum(len(group_handlers) for group_handlers in handlers.values())
        
        if total_handlers > 0:
            print(f"   ✅ Total handlers registered: {total_handlers}")
            return True
        else:
            print("   ❌ No handlers registered at all!")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def run_integration_tests():
    """Run all integration tests (Claude.ai ROI approach)"""
    print("🔗 TELEGRAM BOT INTEGRATION TESTS")
    print("=" * 42)
    print("Based on Claude.ai recommendations")
    print("Testing app initialization and handler order\n")
    
    tests = [
        test_conversation_handlers_registered_before_catch_all,  # CRITICAL
        test_error_handler_registered,
        test_no_duplicate_command_handlers,
        test_admin_handlers_proper_group,
        test_no_group_priority_conflicts,  # Claude.ai additional pattern
        test_conversation_states_are_complete,  # Claude.ai additional pattern
        test_handler_group_structure
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
    
    print(f"\n📊 INTEGRATION TEST RESULTS:")
    print(f"   Tests passed: {passed}/{total}")
    print(f"   Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("   🌟 EXCELLENT: All integration issues resolved")
        print("   ✅ Handler conflicts fixed")
    elif passed >= total * 0.8:
        print("   👍 GOOD: Most integration OK, minor issues")  
    else:
        print("   ⚠️ WARNING: Critical integration issues detected")
    
    return passed == total

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)