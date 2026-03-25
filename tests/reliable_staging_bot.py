#!/usr/bin/env python3
"""
🎭 Reliable Staging Bot Testing
Based on Claude.ai reliable getUpdates pattern
Long polling approach for production-grade testing
"""

import os
import sys
import asyncio
from telegram import Bot
from typing import List, Optional
from pathlib import Path

# Add project root to path
sys.path.insert(0, '/home/sashok/.openclaw/workspace/insilver-v3')

class ReliableSmokeTest:
    """
    Reliable staging bot smoke test (Claude.ai methodology)
    Uses long polling and proper update_id tracking
    """
    
    def __init__(self, staging_token: str, test_chat_id: int):
        self.bot = Bot(token=staging_token)
        self.test_chat_id = test_chat_id
        self.last_update_id: Optional[int] = None
        self.results = []
    
    async def setup(self):
        """Remember current position before test (Claude.ai code)"""
        print("🔧 Setting up staging test environment...")
        
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
    
    async def wait_for_reply(self, timeout: int = 15) -> List:
        """
        Wait for bot replies using reliable long polling (Claude.ai code)
        Much better than offset=-5 naive approach
        """
        print(f"   ⏳ Waiting for bot reply (timeout: {timeout}s)...")
        
        deadline = asyncio.get_event_loop().time() + timeout
        offset = (self.last_update_id or 0) + 1
        
        while asyncio.get_event_loop().time() < deadline:
            try:
                # Long polling - much more efficient than sleep + get_updates
                updates = await self.bot.get_updates(
                    offset=offset,
                    timeout=5,  # Long polling timeout
                    allowed_updates=["message"]
                )
                
                # Look for bot replies
                bot_replies = [
                    u.message for u in updates
                    if u.message and u.message.from_user.is_bot
                ]
                
                if bot_replies:
                    print(f"   ✅ Got {len(bot_replies)} bot reply(s)")
                    for reply in bot_replies:
                        print(f"      📨 Reply: {reply.text[:50]}...")
                    return bot_replies
                
                # Update offset for next iteration
                if updates:
                    offset = updates[-1].update_id + 1
                    
            except Exception as e:
                print(f"   ⚠️ Polling error: {e}")
                await asyncio.sleep(1)
        
        print(f"   ❌ No bot reply within {timeout}s")
        return []
    
    async def send_and_wait(self, text: str, timeout: int = 15) -> bool:
        """Send message and wait for reply (Claude.ai pattern)"""
        print(f"\n📤 Testing: '{text}'")
        
        try:
            # Send message
            sent = await self.bot.send_message(
                chat_id=self.test_chat_id,
                text=text
            )
            print(f"   ✅ Message sent (ID: {sent.message_id})")
            
            # Wait for reply using reliable method
            replies = await self.wait_for_reply(timeout)
            
            return len(replies) > 0
            
        except Exception as e:
            print(f"   ❌ Send failed: {e}")
            return False
    
    async def test_start_command(self) -> bool:
        """Test /start command response"""
        success = await self.send_and_wait("/start")
        
        if success:
            self.results.append(("test_start_command", "✅ PASS"))
        else:
            self.results.append(("test_start_command", "❌ FAIL: No response"))
        
        return success
    
    async def test_catalog_command(self) -> bool:
        """Test /catalog command response"""
        success = await self.send_and_wait("/catalog")
        
        if success:
            self.results.append(("test_catalog_command", "✅ PASS"))
        else:
            self.results.append(("test_catalog_command", "❌ FAIL: No response"))
        
        return success
    
    async def test_product_search(self) -> bool:
        """Test product search (avoid GPT-4 costs)"""
        # Use simple search that should trigger catalog, not AI
        success = await self.send_and_wait("ланцюжки")
        
        if success:
            self.results.append(("test_product_search", "✅ PASS"))
        else:
            self.results.append(("test_product_search", "❌ FAIL: No response"))
        
        return success
    
    async def test_contact_command(self) -> bool:
        """Test /contact command response"""
        success = await self.send_and_wait("/contact")
        
        if success:
            self.results.append(("test_contact_command", "✅ PASS"))
        else:
            self.results.append(("test_contact_command", "❌ FAIL: No response"))
        
        return success
    
    async def run_all_tests(self) -> List[tuple]:
        """
        Run all smoke tests (Claude.ai pattern)
        Returns list of (test_name, status) tuples
        """
        print("🚀 RUNNING STAGING BOT SMOKE TESTS")
        print("=" * 45)
        
        # Setup
        if not await self.setup():
            return [("setup", "❌ FAIL: Setup failed")]
        
        # Run tests (avoid GPT-4 triggering ones to minimize cost)
        tests = [
            self.test_start_command,
            self.test_catalog_command,
            self.test_product_search,
            self.test_contact_command
        ]
        
        for test in tests:
            try:
                await test()
                await asyncio.sleep(2)  # Pause between tests
            except Exception as e:
                self.results.append((test.__name__, f"❌ FAIL: {e}"))
        
        return self.results

def create_staging_config_template():
    """Create staging configuration template"""
    template = """
# STAGING BOT CONFIGURATION
# Copy this to .env.staging and fill in real values

STAGING_BOT_TOKEN=your_staging_bot_token_here
TEST_CHAT_ID=your_telegram_user_id_here

# How to setup staging bot:
# 1. Create new bot via @BotFather  
# 2. Get token and put it in STAGING_BOT_TOKEN
# 3. Send /start to your bot to get chat_id
# 4. Put your chat_id in TEST_CHAT_ID
# 5. Run: python tests/reliable_staging_bot.py
"""
    
    staging_env = Path("/home/sashok/.openclaw/workspace/insilver-v3/.env.staging.template")
    with open(staging_env, 'w') as f:
        f.write(template)
    
    print(f"📝 Staging config template created: {staging_env}")

async def main():
    """Main staging test runner (Claude.ai pattern)"""
    print("🎭 RELIABLE STAGING BOT TESTER")
    print("=" * 40)
    print("Based on Claude.ai reliable getUpdates methodology\n")
    
    # Try to load staging config
    staging_env = Path("/home/sashok/.openclaw/workspace/insilver-v3/.env.staging")
    
    if not staging_env.exists():
        print("❌ Staging config not found!")
        print("🔧 Creating template configuration...")
        create_staging_config_template()
        print("\n📋 Next steps:")
        print("1. Copy .env.staging.template to .env.staging")  
        print("2. Fill in your staging bot token and chat ID")
        print("3. Run this script again")
        return
    
    # Load staging config
    staging_config = {}
    with open(staging_env, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                staging_config[key] = value
    
    staging_token = staging_config.get('STAGING_BOT_TOKEN')
    test_chat_id = staging_config.get('TEST_CHAT_ID')
    
    if not staging_token or not test_chat_id:
        print("❌ Missing STAGING_BOT_TOKEN or TEST_CHAT_ID in .env.staging")
        return
    
    # Run staging tests
    tester = ReliableSmokeTest(staging_token, int(test_chat_id))
    results = await tester.run_all_tests()
    
    # Summary
    print(f"\n📊 STAGING TEST RESULTS:")
    print("-" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, status in results:
        print(f"{status} {test_name}")
        if "✅ PASS" in status:
            passed += 1
    
    print(f"\n🎯 Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🌟 EXCELLENT: All staging tests passed")
        print("✅ InSilver bot ready for production")
    elif passed >= total * 0.75:
        print("👍 GOOD: Most staging tests passed")
    else:
        print("⚠️ WARNING: Staging issues detected")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)