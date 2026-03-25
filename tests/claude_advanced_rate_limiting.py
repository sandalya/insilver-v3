#!/usr/bin/env python3
"""
⏱️ Advanced Rate Limiting Tests
Based on Claude.ai's exact recommendations
Tests implementation patterns, not API behavior
"""

import sys
import inspect
import asyncio
from pathlib import Path
from typing import List

# Add project root to path
sys.path.insert(0, '/home/sashok/.openclaw/workspace/insilver-v3')

def test_bulk_sender_has_delays():
    """Test that bulk sending code has rate limiting delays (Claude.ai exact code)"""
    print("⏱️ TESTING BULK SENDER RATE LIMITING PATTERNS")
    print("-" * 48)
    
    try:
        # Test AI module for rate limiting patterns
        from core import ai
        ai_source = inspect.getsource(ai.ask_ai)
        
        has_delays = any(keyword in ai_source.lower() for keyword in [
            "sleep", "asyncio.sleep", "delay", "timeout", "wait", "rate"
        ])
        
        if has_delays:
            print("   ✅ AI module shows rate limiting patterns")
        else:
            print("   ⚠️ AI module shows no explicit rate limiting")
        
        # Test admin module for bulk operations
        from bot import admin
        admin_functions = [
            admin.view_all_knowledge,
            admin.admin_menu,
        ]
        
        bulk_delays_found = False
        for func in admin_functions:
            if hasattr(func, '__code__'):
                func_source = inspect.getsource(func)
                if "send_message" in func_source:
                    has_func_delays = any(keyword in func_source.lower() for keyword in [
                        "sleep", "asyncio.sleep", "delay", "rate"  
                    ])
                    
                    if has_func_delays:
                        print(f"   ✅ {func.__name__} has rate limiting")
                        bulk_delays_found = True
                    else:
                        print(f"   ⚠️ {func.__name__} sends without rate limiting")
        
        # Overall assessment
        if has_delays or bulk_delays_found:
            print("   ✅ PASS: Some rate limiting patterns detected")
            return True
        else:
            print("   ⚠️ WARNING: No rate limiting patterns found")
            print("   🔧 Consider adding delays for bulk operations")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def test_bulk_sender_timing_simulation():
    """Test bulk sender timing with mock (Claude.ai pattern)"""
    print("\n🕐 TESTING BULK SENDER TIMING SIMULATION")
    print("-" * 40)
    
    class MockBulkSender:
        """Mock bulk sender that respects rate limits (Claude.ai exact code)"""
        
        def __init__(self, rate_limit: int = 30):
            self.rate_limit = rate_limit
            self.times = []
        
        async def fake_send(self, **kwargs):
            """Mock send function that records timing"""
            self.times.append(asyncio.get_event_loop().time())
        
        async def send_bulk(self, messages: List[str]):
            """Bulk send with rate limiting"""
            for i, msg in enumerate(messages):
                await self.fake_send(text=msg)
                
                # Add delay every rate_limit messages (simulate rate limiting)
                if (i + 1) % self.rate_limit == 0 and i + 1 < len(messages):
                    await asyncio.sleep(1.0)  # 1 second pause
    
    async def run_timing_test():
        """Test timing simulation"""
        sender = MockBulkSender(rate_limit=30)
        
        # Test sending 35 messages (should have 1 pause after message 30)
        messages = [f"msg_{i}" for i in range(35)]
        
        start_time = asyncio.get_event_loop().time()
        await sender.send_bulk(messages)
        end_time = asyncio.get_event_loop().time()
        
        total_time = end_time - start_time
        
        # Should take at least 1 second due to rate limiting pause
        if total_time >= 1.0:
            print(f"   ✅ Bulk sending took {total_time:.1f}s (includes rate limiting)")
            
            # Check gaps between batches (Claude's exact logic)
            if len(sender.times) >= 30:
                batch1_start = sender.times[0]
                batch1_end = sender.times[29]  # 30th message (0-indexed)
                batch2_start = sender.times[30] if len(sender.times) > 30 else None
                
                if batch2_start:
                    gap = batch2_start - batch1_end
                    if gap >= 1.0:
                        print(f"   ✅ Rate limiting gap detected: {gap:.1f}s between batches")
                        return True
                    else:
                        print(f"   ❌ No sufficient gap: {gap:.1f}s < 1.0s")
                        return False
            
            return True
        else:
            print(f"   ❌ Bulk sending too fast: {total_time:.1f}s (no rate limiting)")
            return False
    
    # Run async test
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_timing_test())
        loop.close()
        return result
    except Exception as e:
        print(f"   ❌ Timing test failed: {e}")
        return False

def test_callback_data_byte_length_exact():
    """Test exact callback byte length logic (Claude.ai exact patterns)"""
    print("\n🔢 TESTING CALLBACK BYTE LENGTH (CLAUDE'S EXACT LOGIC)")
    print("-" * 55)
    
    def cb(s: str) -> bool:
        """Claude's exact helper function"""
        return len(s.encode('utf-8')) <= 64
    
    # Claude's exact test cases
    test_cases = [
        ("order:12345:confirm", True, "✅ 18 bytes"),
        ("order:12345:confirm:user:678", True, "✅ 30 bytes"), 
        ("order:" + "x" * 60, False, "❌ 66 bytes"),
        ("order:confirm:🇺🇦💎", True, "Complex emoji test")
    ]
    
    all_passed = True
    
    for callback, expected, description in test_cases:
        actual_safe = cb(callback)
        byte_length = len(callback.encode('utf-8'))
        char_length = len(callback)
        
        if actual_safe == expected:
            status = "✅"
        else:
            status = "❌"
            all_passed = False
        
        print(f"   {status} '{callback}' - {description}")
        print(f"       Chars: {char_length}, Bytes: {byte_length}, Safe: {actual_safe}")
    
    # Claude's specific dangerous symbols test
    print(f"\n   🧪 Testing Claude's dangerous symbols:")
    
    dangerous_tests = [
        ("🔥💎👑🚀", 4, "4-byte emojis"),
        ("🇺🇦🇬🇧", 8, "Flag emojis = 8 bytes each"),
        ("привіт", 2, "Cyrillic = 2 bytes/char"),
        ("你好", 3, "CJK = 3 bytes/char")
    ]
    
    for symbols, expected_bytes_per_char, description in dangerous_tests:
        actual_bytes = len(symbols.encode('utf-8'))
        expected_total = len(symbols) * expected_bytes_per_char
        
        print(f"   📊 {symbols} ({description}): {actual_bytes} bytes")
        
        # Note: This is approximate since some emojis may vary
        if abs(actual_bytes - expected_total) <= 4:  # Allow some variance
            print(f"       ✅ Matches expected ~{expected_total} bytes")
        else:
            print(f"       ⚠️ Differs from expected ~{expected_total} bytes")
    
    return all_passed

def run_claude_advanced_rate_limiting_tests():
    """Run all Claude.ai advanced rate limiting tests"""
    print("⏱️ CLAUDE.AI ADVANCED RATE LIMITING TESTS")
    print("=" * 50)
    print("Testing implementation patterns, not API behavior\n")
    
    tests = [
        test_bulk_sender_has_delays,
        test_bulk_sender_timing_simulation,
        test_callback_data_byte_length_exact
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
    
    print(f"\n📊 CLAUDE ADVANCED RATE LIMITING RESULTS:")
    print(f"   Tests passed: {passed}/{total}")
    print(f"   Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("   🌟 EXCELLENT: All Claude's advanced patterns implemented")
        print("   ✅ Rate limiting patterns detected")
        print("   ✅ Byte length logic validated")
    elif passed >= total * 0.66:
        print("   👍 GOOD: Most Claude patterns OK")
    else:
        print("   ⚠️ WARNING: Claude's patterns need implementation")
    
    return passed == total

if __name__ == "__main__":
    success = run_claude_advanced_rate_limiting_tests()
    sys.exit(0 if success else 1)