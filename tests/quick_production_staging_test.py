#!/usr/bin/env python3
"""
🎭 Quick Production Staging Test
Uses production bot for CAREFUL testing (Claude.ai methodology)
ONLY safe commands that don't trigger expensive AI calls
"""

import sys
import asyncio
from pathlib import Path
from telegram import Bot

# Add project root to path  
sys.path.insert(0, '/home/sashok/.openclaw/workspace/insilver-v3')

class QuickProductionTest:
    """
    Quick staging test using production bot (Claude.ai pattern)
    ONLY tests safe commands that don't cost money
    """
    
    def __init__(self):
        # Load production token (CAREFULLY!)
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
    
    async def setup(self):
        """Setup with production bot (Claude.ai reliable pattern)"""
        print("🔧 Setting up PRODUCTION bot test (CAREFUL mode)...")
        
        try:
            updates = await self.bot.get_updates(limit=1, timeout=0)
            if updates:
                self.last_update_id = updates[-1].update_id
                print(f"   📍 Starting from update_id: {self.last_update_id}")
            else:
                self.last_update_id = 0
                print("   📍 No previous updates, starting from 0")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Setup failed: {e}")
            return False
    
    async def wait_for_reply(self, timeout: int = 10) -> list:
        """Wait for bot reply using Claude's reliable long polling"""
        print(f"   ⏳ Waiting for reply (timeout: {timeout}s)...")
        
        deadline = asyncio.get_event_loop().time() + timeout
        offset = (self.last_update_id or 0) + 1
        
        while asyncio.get_event_loop().time() < deadline:
            try:
                # Claude's exact long polling pattern
                updates = await self.bot.get_updates(
                    offset=offset,
                    timeout=3,  # Shorter timeout for production safety
                    allowed_updates=["message"]
                )
                
                bot_replies = [
                    u.message for u in updates
                    if u.message and u.message.from_user.is_bot
                ]
                
                if bot_replies:
                    print(f"   ✅ Got {len(bot_replies)} reply(s)")
                    for reply in bot_replies:
                        print(f"      📨 Reply: {reply.text[:80] if reply.text else '[no text]'}...")
                    return bot_replies
                
                if updates:
                    offset = updates[-1].update_id + 1
                    
            except Exception as e:
                print(f"   ⚠️ Polling error: {e}")
                break
        
        print(f"   ❌ No reply within {timeout}s")
        return []
    
    async def send_safe_command(self, command: str, description: str) -> bool:
        """Send safe command that won't trigger expensive AI (Claude.ai pattern)"""
        print(f"\n📤 Testing {description}: '{command}'")
        
        try:
            sent = await self.bot.send_message(
                chat_id=self.test_chat_id,
                text=command
            )
            print(f"   ✅ Sent (ID: {sent.message_id})")
            
            replies = await self.wait_for_reply(10)
            return len(replies) > 0
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False
    
    async def test_start_command(self) -> bool:
        """Test /start - should respond instantly without AI cost"""
        success = await self.send_safe_command("/start", "START command")
        self.results.append(("start_command", "✅ PASS" if success else "❌ FAIL"))
        return success
    
    async def test_help_command(self) -> bool:
        """Test /help - should be instant response"""
        success = await self.send_safe_command("/help", "HELP command") 
        self.results.append(("help_command", "✅ PASS" if success else "❌ FAIL"))
        return success
    
    async def test_contact_command(self) -> bool:
        """Test /contact - should show contact info instantly"""
        success = await self.send_safe_command("/contact", "CONTACT command")
        self.results.append(("contact_command", "✅ PASS" if success else "❌ FAIL"))
        return success
    
    async def test_catalog_command(self) -> bool:
        """Test /catalog - should show catalog without AI"""
        success = await self.send_safe_command("/catalog", "CATALOG command")
        self.results.append(("catalog_command", "✅ PASS" if success else "❌ FAIL"))
        return success
    
    async def run_safe_tests(self) -> list:
        """Run only safe tests that don't cost money (Claude.ai approach)"""
        print("🚀 RUNNING SAFE PRODUCTION TESTS")
        print("=" * 40)
        print("⚠️ ONLY commands that don't trigger GPT-4 calls\n")
        
        if not await self.setup():
            return [("setup", "❌ FAIL")]
        
        # Safe tests only (no AI trigger)
        tests = [
            self.test_start_command,
            self.test_help_command, 
            self.test_contact_command,
            self.test_catalog_command
        ]
        
        for test in tests:
            try:
                await test()
                await asyncio.sleep(1.5)  # Pause between tests
            except Exception as e:
                self.results.append((test.__name__, f"❌ FAIL: {e}"))
        
        return self.results

async def main():
    """Main test runner"""
    print("⚠️ PRODUCTION BOT STAGING TEST")
    print("=" * 35)
    print("Based on Claude.ai methodology - SAFE COMMANDS ONLY")
    print("No GPT-4 calls = No costs\n")
    
    tester = QuickProductionTest()
    results = await tester.run_safe_tests()
    
    print(f"\n📊 PRODUCTION STAGING RESULTS:")
    print("-" * 35)
    
    passed = 0
    for test_name, status in results:
        print(f"{status} {test_name}")
        if "✅ PASS" in status:
            passed += 1
    
    total = len(results)
    print(f"\n🎯 Summary: {passed}/{total} safe tests passed")
    
    if passed == total:
        print("🌟 EXCELLENT: All production handlers responding")
        print("✅ Claude's reliable getUpdates methodology works!")
    elif passed >= total * 0.75:
        print("👍 GOOD: Most handlers working")
    else:
        print("⚠️ WARNING: Production issues detected")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)