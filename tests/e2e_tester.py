#!/usr/bin/env python3
"""
Level 8: E2E User Simulation Tester
Автономна розробка для @gamaiunchik
Budget: $15, Cost tracking: активний
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import aiohttp
import sys
import os
import re
from pathlib import Path

# Add project root to path
sys.path.insert(0, '/home/sashok/.openclaw/workspace/insilver-v3')

# Cost tracking
TOOL_CALLS_COUNT = 0
ESTIMATED_COST = 0.0
BUDGET_LIMIT = 15.0

def track_cost(cost: float, description: str):
    """Track development costs"""
    global TOOL_CALLS_COUNT, ESTIMATED_COST
    TOOL_CALLS_COUNT += 1
    ESTIMATED_COST += cost
    print(f"💰 Tool call #{TOOL_CALLS_COUNT}: {description} - ${cost:.3f} (Total: ${ESTIMATED_COST:.2f}/${BUDGET_LIMIT})")

@dataclass
class UserMessage:
    """Simulate user message"""
    text: str
    message_type: str = "text"  # text, button_click, command
    callback_data: Optional[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class BotResponse:
    """Bot response capture"""
    text: str
    buttons: List[Dict[str, str]]
    message_id: int
    timestamp: float
    
class RealTelegramTester:
    """
    🎭 REAL Telegram Bot Tester
    Підключається до живого InSilver бота через Telegram API
    """
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.api_base = f"https://api.telegram.org/bot{bot_token}"
        self.user_id = 189793675  # Test user (Sashko's ID)
        self.chat_id = self.user_id  # Direct chat
        self.username = "e2e_tester"
        
        # Session state
        self.conversation_log = []
        self.message_offset = 0
        self.session_active = False
        
        # HTTP session
        self.http_session = None
        
        print(f"🎭 REAL Telegram Tester initialized")
        print(f"   Bot API: {self.api_base[:50]}...")
        print(f"   Test Chat ID: {self.chat_id}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.http_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30, connect=10)
        )
        track_cost(0.001, "Initialize HTTP session")
        
        # Test bot connection first
        await self.test_bot_connection()
        return self
    
    async def test_bot_connection(self) -> bool:
        """Test if bot is reachable and token is valid"""
        print(f"🔍 Testing bot connection...")
        
        try:
            async with self.http_session.get(
                f"{self.api_base}/getMe",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    bot_info = result.get("result", {})
                    bot_name = bot_info.get("username", "unknown")
                    bot_id = bot_info.get("id", "unknown")
                    
                    print(f"✅ Bot connection successful!")
                    print(f"   Bot name: @{bot_name}")
                    print(f"   Bot ID: {bot_id}")
                    return True
                else:
                    error = await response.text()
                    print(f"❌ Bot connection failed: {response.status} - {error}")
                    return False
                    
        except Exception as e:
            print(f"❌ Bot connection exception: {e}")
            return False
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.http_session:
            await self.http_session.close()
        track_cost(0.001, "Close HTTP session")
    
    async def send_message_to_bot(self, text: str, delay: float = 2.0) -> Dict:
        """
        Відправляє реальне повідомлення до InSilver бота через Telegram API
        """
        track_cost(0.005, f"Send real message: {text[:30]}")
        
        print(f"👤 SENDING: {text}")
        print(f"🎯 Target chat_id: {self.chat_id}")
        print(f"🤖 Bot API: {self.api_base[:50]}...")
        
        # Prepare message data
        message_data = {
            "chat_id": self.chat_id,
            "text": text
        }
        
        try:
            print(f"📤 Making POST request to sendMessage...")
            
            # Send message via Telegram API
            async with self.http_session.post(
                f"{self.api_base}/sendMessage",
                json=message_data,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                print(f"📬 Response status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    message_id = result.get("result", {}).get("message_id")
                    
                    print(f"✅ Message sent successfully (ID: {message_id})")
                    
                    # Log outgoing message
                    self.conversation_log.append({
                        "type": "outgoing_message",
                        "text": text,
                        "message_id": message_id,
                        "timestamp": time.time()
                    })
                    
                    # Wait for bot response
                    print(f"⏳ Waiting {delay}s for bot response...")
                    await asyncio.sleep(delay)
                    
                    # Get bot response
                    print(f"📥 Getting bot response...")
                    bot_response = await self.get_bot_response()
                    return bot_response
                    
                else:
                    error_text = await response.text()
                    print(f"❌ API Error {response.status}: {error_text}")
                    try:
                        error_json = await response.json()
                        print(f"📋 Error details: {error_json}")
                    except:
                        pass
                    track_cost(0.001, "Message send error")
                    return {"error": f"API Error: {response.status} - {error_text}"}
                    
        except asyncio.TimeoutError:
            print(f"❌ Timeout sending message")
            track_cost(0.001, "Send timeout")
            return {"error": "Timeout"}
        except Exception as e:
            print(f"❌ Exception sending message: {e}")
            print(f"🔍 Exception type: {type(e)}")
            track_cost(0.001, f"Exception: {str(e)[:30]}")
            return {"error": str(e)}
    
    async def get_bot_response(self, timeout: int = 15) -> Dict:
        """
        Отримує відповідь від бота через getUpdates
        """
        track_cost(0.003, "Get bot response")
        
        print(f"📥 Waiting for bot response (timeout: {timeout}s)")
        print(f"🔢 Current message offset: {self.message_offset}")
        
        start_time = time.time()
        attempts = 0
        
        while time.time() - start_time < timeout:
            attempts += 1
            try:
                print(f"📡 Attempt #{attempts}: Getting updates...")
                
                # Get updates from bot
                async with self.http_session.post(
                    f"{self.api_base}/getUpdates",
                    json={
                        "offset": self.message_offset + 1, 
                        "limit": 20, 
                        "timeout": 3
                    },
                    timeout=aiohttp.ClientTimeout(total=8)
                ) as response:
                    
                    print(f"📬 getUpdates status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        updates = result.get("result", [])
                        
                        print(f"📨 Received {len(updates)} updates")
                        
                        if not updates:
                            print(f"📭 No updates, continuing to wait...")
                            await asyncio.sleep(1)
                            continue
                        
                        for update in updates:
                            update_id = update.get("update_id", 0)
                            self.message_offset = max(self.message_offset, update_id)
                            
                            print(f"🔍 Processing update {update_id}")
                            
                            # Check if it's a message to our chat
                            if "message" in update:
                                msg = update["message"]
                                chat_id = msg.get("chat", {}).get("id")
                                from_bot = msg.get("from", {}).get("is_bot", False)
                                
                                print(f"📝 Message from chat {chat_id} (bot: {from_bot})")
                                
                                if chat_id == self.chat_id and from_bot:
                                    
                                    # Parse bot response
                                    bot_text = msg.get("text", "")
                                    reply_markup = msg.get("reply_markup", {})
                                    
                                    print(f"🤖 Found bot message: {bot_text[:100]}...")
                                    
                                    # Extract inline buttons
                                    buttons = []
                                    if "inline_keyboard" in reply_markup:
                                        print(f"🔘 Extracting buttons...")
                                        for row in reply_markup["inline_keyboard"]:
                                            for btn in row:
                                                button_info = {
                                                    "text": btn.get("text", ""),
                                                    "callback_data": btn.get("callback_data"),
                                                    "url": btn.get("url")
                                                }
                                                buttons.append(button_info)
                                                print(f"   Button: {button_info['text']}")
                                    
                                    response_data = {
                                        "text": bot_text,
                                        "buttons": buttons,
                                        "message_id": msg.get("message_id"),
                                        "timestamp": time.time(),
                                        "update_id": update_id
                                    }
                                    
                                    print(f"✅ Bot response captured successfully!")
                                    print(f"📝 Text length: {len(bot_text)} chars")
                                    print(f"🔘 Buttons found: {len(buttons)}")
                                    
                                    # Log bot response
                                    self.conversation_log.append({
                                        "type": "incoming_message",
                                        "content": response_data,
                                        "timestamp": time.time()
                                    })
                                    
                                    return response_data
                                else:
                                    print(f"⏭️ Skipping message (not from our bot or wrong chat)")
                            else:
                                print(f"⏭️ Update is not a message: {list(update.keys())}")
                    else:
                        error_text = await response.text()
                        print(f"❌ getUpdates error {response.status}: {error_text}")
            
            except asyncio.TimeoutError:
                print(f"⏱️ getUpdates timeout (attempt #{attempts})")
            except Exception as e:
                print(f"❌ Error getting updates (attempt #{attempts}): {e}")
                
            await asyncio.sleep(1)
        
        print(f"⚠️ No bot response within {timeout}s after {attempts} attempts")
        return {"error": "No response", "timeout": timeout, "attempts": attempts}
    
    async def click_inline_button(self, callback_data: str, message_id: int) -> Dict:
        """
        Натискає inline кнопку через callback query
        """
        track_cost(0.005, f"Click button: {callback_data}")
        
        print(f"🔘 CLICKING BUTTON: {callback_data}")
        
        callback_query_data = {
            "callback_query_id": f"test_{int(time.time())}",
            "from": {
                "id": self.user_id,
                "username": self.username,
                "first_name": "E2E Tester"
            },
            "message": {
                "message_id": message_id,
                "chat": {"id": self.chat_id}
            },
            "data": callback_data
        }
        
        # This is tricky - we need to simulate callback query
        # For now, we'll send a regular message that triggers the same flow
        
        # Extract order ID from callback data if it's an order button
        if callback_data.startswith("o:"):
            order_id = callback_data[2:]  # Remove "o:" prefix
            # Simulate clicking order button by sending special message
            return await self.send_message_to_bot(f"/order_{order_id}", delay=1.0)
        elif callback_data == "order_full":
            return await self.send_message_to_bot("/order", delay=1.0)
        else:
            return await self.send_message_to_bot(f"/callback_{callback_data}", delay=1.0)
    
    def extract_buttons_from_response(self, response: Dict) -> List[Dict]:
        """Витягнути кнопки з відповіді бота"""
        return response.get("buttons", [])
    
    def find_order_button(self, buttons: List[Dict]) -> Optional[Dict]:
        """Знайти кнопку замовлення"""
        for btn in buttons:
            if "замовити" in btn.get("text", "").lower():
                return btn
        return None
    
    async def save_test_session(self, filename: str = "real_e2e_session.json"):
        """Зберегти реальну тестову сесію"""
        session_data = {
            "test_type": "real_telegram_e2e",
            "bot_token_hash": self.bot_token[-8:] if self.bot_token else "unknown",
            "test_chat_id": self.chat_id,
            "session_start": self.conversation_log[0]['timestamp'] if self.conversation_log else time.time(),
            "total_interactions": len(self.conversation_log),
            "cost_tracking": {
                "tool_calls": TOOL_CALLS_COUNT,
                "estimated_cost": ESTIMATED_COST,
                "budget_used_percent": (ESTIMATED_COST / BUDGET_LIMIT) * 100
            },
            "conversation_log": self.conversation_log
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Real test session saved: {filename}")
    
    async def send_message(self, text: str, delay: float = 1.0) -> Dict:
        """
        Симулює відправку повідомлення користувачем
        """
        track_cost(0.001, f"Simulate user message: {text[:30]}")
        
        message = UserMessage(text=text)
        self.conversation_log.append({
            "type": "user_message",
            "content": text,
            "timestamp": message.timestamp
        })
        
        print(f"👤 USER: {text}")
        
        # Simulate typing delay
        await asyncio.sleep(delay)
        
        # В real implementation тут буде API call до бота
        # Поки що мокаємо
        mock_response = await self._mock_bot_response(text)
        return mock_response
    
    async def click_button(self, button_text: str, callback_data: str) -> Dict:
        """
        Симулює натискання inline кнопки
        """
        track_cost(0.002, f"Simulate button click: {button_text}")
        
        print(f"🔘 BUTTON CLICK: {button_text} ({callback_data})")
        
        click_action = UserMessage(
            text=button_text, 
            message_type="button_click",
            callback_data=callback_data
        )
        
        self.conversation_log.append({
            "type": "button_click",
            "button_text": button_text,
            "callback_data": callback_data,
            "timestamp": click_action.timestamp
        })
        
        # Mock button response
        mock_response = await self._mock_button_response(callback_data)
        return mock_response
    
    async def _mock_bot_response(self, user_text: str) -> Dict:
        """Mock відповіді бота для тестування"""
        
        # Симуляція різних scenarios
        if "/start" in user_text.lower():
            response = {
                "text": "Вітаємо! Ви звернулись до майстерні InSilver",
                "buttons": [
                    {"text": "🌐 Наш сайт", "url": "https://www.insilver.pp.ua/"},
                    {"text": "📱 Зв'язок з майстром", "callback_data": "contact_master"},
                    {"text": "📋 Показати каталог", "callback_data": "show_catalog"}
                ]
            }
        elif "ланцюжки" in user_text.lower() or "плетіння" in user_text.lower():
            response = {
                "text": "*СРІБНИЙ ЛАНЦЮЖОК \"РАМЗЕС\" МАСОЮ ~100 грам*\nКатегорія: Ланцюжки / Рамзес",
                "buttons": [
                    {"text": "🛒 Замовити цей виріб", "callback_data": "o:42"},
                    {"text": "📝 Індивідуальне замовлення", "callback_data": "order_full"}
                ]
            }
        else:
            # AI відповідь
            response = {
                "text": f"Дякую за повідомлення: {user_text}. Можу допомогти з консультацією!",
                "buttons": []
            }
        
        self.last_bot_response = response
        self.conversation_log.append({
            "type": "bot_response",
            "content": response,
            "timestamp": time.time()
        })
        
        print(f"🤖 BOT: {response['text'][:50]}...")
        if response.get('buttons'):
            for btn in response['buttons']:
                print(f"   [{btn['text']}]")
        
        return response
    
    async def _mock_button_response(self, callback_data: str) -> Dict:
        """Mock відповідей на button clicks"""
        
        if callback_data == "contact_master":
            response = {
                "text": "📱 **Контакти майстерні InSilver:**\n🟢 **Telegram майстра:** @gamaiunchik",
                "buttons": []
            }
        elif callback_data == "show_catalog":
            response = {
                "text": "📋 **Основні категорії каталогу:**\n🔗 **Ланцюжки:** Рамзес, Тризуб",
                "buttons": []
            }
        elif callback_data.startswith("o:"):
            # Order process mock
            response = {
                "text": "📝 Розпочинаємо оформлення замовлення. Введіть ваше ім'я:",
                "buttons": [],
                "conversation_state": "ORDER_NAME"
            }
        else:
            response = {
                "text": f"Button clicked: {callback_data}",
                "buttons": []
            }
        
        self.last_bot_response = response
        return response
    
    def extract_buttons(self, response: Dict) -> List[Dict]:
        """Витягнути кнопки з відповіді бота"""
        return response.get('buttons', [])
    
    def find_button_by_text(self, buttons: List[Dict], search_text: str) -> Optional[Dict]:
        """Знайти кнопку за текстом"""
        for button in buttons:
            if search_text.lower() in button['text'].lower():
                return button
        return None
    
    async def get_conversation_log(self) -> List[Dict]:
        """Отримати лог розмови"""
        return self.conversation_log
    
    def save_session_log(self, filename: str):
        """Зберегти лог сесії"""
        log_data = {
            "test_session": {
                "user_id": self.user_id,
                "username": self.username,
                "started": self.conversation_log[0]['timestamp'] if self.conversation_log else time.time(),
                "cost_tracking": {
                    "tool_calls": TOOL_CALLS_COUNT,
                    "estimated_cost": ESTIMATED_COST,
                    "budget_limit": BUDGET_LIMIT
                }
            },
            "conversation": self.conversation_log
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Session log saved: {filename}")

class RealE2EScenarios:
    """
    🧪 REAL E2E Test Scenarios для живого InSilver бота
    """
    
    def __init__(self, telegram_tester: RealTelegramTester):
        self.tester = telegram_tester
        self.test_results = []
        self.orders_file = Path("/home/sashok/.openclaw/workspace/insilver-v3/data/orders/orders.json")
    
    def get_current_orders_count(self) -> int:
        """Отримати поточну кількість замовлень"""
        try:
            if self.orders_file.exists():
                with open(self.orders_file, 'r', encoding='utf-8') as f:
                    orders_data = json.load(f)
                return len(orders_data.get("orders", []))
            return 0
        except:
            return 0
    
    async def scenario_real_order_workflow(self) -> Dict:
        """
        🎯 REAL SCENARIO 1: Complete Order Workflow Test
        Тестує весь process від пошуку до замовлення в живому боті
        """
        print("\n🧪 REAL TEST: Complete Order Workflow")
        track_cost(0.010, "Start real order workflow test")
        
        scenario_results = {
            "name": "real_order_workflow", 
            "status": "running",
            "steps": [],
            "errors": [],
            "orders_before": 0,
            "orders_after": 0,
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            # Pre-check: Count current orders
            scenario_results["orders_before"] = self.get_current_orders_count()
            print(f"📋 Orders before test: {scenario_results['orders_before']}")
            
            # Step 1: Start conversation
            print("👤 Step 1: Starting conversation...")
            response1 = await self.tester.send_message_to_bot("/start")
            
            if "error" not in response1:
                scenario_results["steps"].append({"step": "start_command", "status": "ok", "response_length": len(response1.get("text", ""))})
                print("✅ /start command successful")
            else:
                scenario_results["errors"].append(f"Start command failed: {response1.get('error')}")
                scenario_results["steps"].append({"step": "start_command", "status": "failed"})
            
            # Step 2: Search for products
            print("👤 Step 2: Searching for ланцюжки...")
            await asyncio.sleep(1)
            response2 = await self.tester.send_message_to_bot("ланцюжки")
            
            if "error" not in response2 and response2.get("buttons"):
                scenario_results["steps"].append({
                    "step": "search_products", 
                    "status": "ok", 
                    "buttons_found": len(response2.get("buttons", []))
                })
                print(f"✅ Product search successful, {len(response2.get('buttons', []))} buttons found")
                
                # Step 3: Try to click order button
                buttons = self.tester.extract_buttons_from_response(response2)
                order_button = self.tester.find_order_button(buttons)
                
                if order_button and order_button.get("callback_data"):
                    print(f"👤 Step 3: Clicking order button: {order_button['text']}")
                    
                    # Attempt to trigger order process
                    # Since real callback simulation is complex, we'll test with direct order command
                    await asyncio.sleep(1)
                    response3 = await self.tester.send_message_to_bot("/order")
                    
                    if "error" not in response3:
                        scenario_results["steps"].append({"step": "trigger_order", "status": "ok"})
                        print("✅ Order process triggered")
                        
                        # Step 4: Test order form responses 
                        print("👤 Step 4: Testing order form...")
                        await asyncio.sleep(1)
                        
                        # Send test name
                        name_response = await self.tester.send_message_to_bot("E2E Тестер")
                        if "error" not in name_response:
                            scenario_results["steps"].append({"step": "enter_name", "status": "ok"})
                            
                            await asyncio.sleep(1)
                            # Send test phone 
                            phone_response = await self.tester.send_message_to_bot("+380501234567")
                            if "error" not in phone_response:
                                scenario_results["steps"].append({"step": "enter_phone", "status": "ok"})
                                
                                await asyncio.sleep(1)
                                # Send test city
                                city_response = await self.tester.send_message_to_bot("Київ (E2E тест)")
                                if "error" not in city_response:
                                    scenario_results["steps"].append({"step": "enter_city", "status": "ok"})
                                    print("✅ Order form completed")
                                else:
                                    scenario_results["errors"].append("City input failed")
                            else:
                                scenario_results["errors"].append("Phone input failed")
                        else:
                            scenario_results["errors"].append("Name input failed")
                    else:
                        scenario_results["errors"].append("Order process not triggered")
                        scenario_results["steps"].append({"step": "trigger_order", "status": "failed"})
                else:
                    scenario_results["errors"].append("Order button not found or no callback_data")
                    scenario_results["steps"].append({"step": "find_order_button", "status": "failed"})
            else:
                scenario_results["errors"].append("Product search failed or no buttons returned")
                scenario_results["steps"].append({"step": "search_products", "status": "failed"})
            
            # Post-check: Count orders after test
            await asyncio.sleep(2)  # Wait for potential order saving
            scenario_results["orders_after"] = self.get_current_orders_count()
            print(f"📋 Orders after test: {scenario_results['orders_after']}")
            
            # Determine overall status
            new_orders = scenario_results["orders_after"] - scenario_results["orders_before"]
            if new_orders > 0:
                print(f"🎉 SUCCESS: {new_orders} new order(s) created!")
                scenario_results["new_orders_count"] = new_orders
            
            scenario_results["status"] = "passed" if not scenario_results["errors"] else "failed"
            
        except Exception as e:
            scenario_results["status"] = "error"
            scenario_results["errors"].append(f"Exception: {str(e)}")
            track_cost(0.002, f"Real scenario exception: {str(e)[:30]}")
            print(f"❌ Exception during test: {e}")
        
        scenario_results["duration"] = time.time() - start_time
        self.test_results.append(scenario_results)
        
        print(f"\n📊 REAL SCENARIO COMPLETED:")
        print(f"   Status: {scenario_results['status']}")
        print(f"   Duration: {scenario_results['duration']:.2f}s")
        print(f"   Steps completed: {len([s for s in scenario_results['steps'] if s['status'] == 'ok'])}/{len(scenario_results['steps'])}")
        print(f"   Errors: {len(scenario_results['errors'])}")
        
        return scenario_results
    
    async def scenario_command_testing(self) -> Dict:
        """
        🎯 REAL SCENARIO 2: Command Menu Testing
        Тестує всі команди меню бота
        """
        print("\n🧪 REAL TEST: Command Menu Testing")
        track_cost(0.008, "Start command menu test")
        
        scenario_results = {
            "name": "command_menu_testing",
            "status": "running",
            "steps": [],
            "errors": [],
            "commands_tested": [],
            "duration": 0
        }
        
        start_time = time.time()
        commands_to_test = ["/start", "/catalog", "/contact", "/help"]
        
        try:
            for cmd in commands_to_test:
                print(f"👤 Testing command: {cmd}")
                await asyncio.sleep(1)
                
                response = await self.tester.send_message_to_bot(cmd)
                
                if "error" not in response and response.get("text"):
                    scenario_results["steps"].append({
                        "step": f"command_{cmd.replace('/', '')}",
                        "status": "ok",
                        "response_length": len(response.get("text", ""))
                    })
                    scenario_results["commands_tested"].append(cmd)
                    print(f"✅ {cmd} works - response: {len(response.get('text', ''))} chars")
                else:
                    scenario_results["errors"].append(f"Command {cmd} failed: {response.get('error', 'No response')}")
                    scenario_results["steps"].append({
                        "step": f"command_{cmd.replace('/', '')}",
                        "status": "failed"
                    })
                    print(f"❌ {cmd} failed")
            
            scenario_results["status"] = "passed" if not scenario_results["errors"] else "failed"
            
        except Exception as e:
            scenario_results["status"] = "error"
            scenario_results["errors"].append(f"Exception: {str(e)}")
            print(f"❌ Exception during command testing: {e}")
        
        scenario_results["duration"] = time.time() - start_time
        self.test_results.append(scenario_results)
        
        print(f"📊 Command testing completed: {len(scenario_results['commands_tested'])}/{len(commands_to_test)} commands work")
        return scenario_results
    
    async def scenario_catalog_search_testing(self) -> Dict:
        """
        🎯 REAL SCENARIO 3: Catalog Search Testing  
        Тестує пошук товарів в каталозі
        """
        print("\n🧪 REAL TEST: Catalog Search Testing")
        track_cost(0.006, "Start catalog search test")
        
        scenario_results = {
            "name": "catalog_search_testing",
            "status": "running",
            "steps": [],
            "errors": [],
            "search_queries": [],
            "duration": 0
        }
        
        start_time = time.time()
        search_terms = ["ланцюжки", "браслети", "плетіння", "тризуб", "рамзес", "череп бафомета"]
        
        try:
            for term in search_terms:
                print(f"👤 Searching for: {term}")
                await asyncio.sleep(1)
                
                response = await self.tester.send_message_to_bot(term)
                
                if "error" not in response:
                    response_text = response.get("text", "")
                    buttons = response.get("buttons", [])
                    
                    # Check if search found results
                    if response_text and (buttons or "категор" in response_text.lower() or "*" in response_text):
                        scenario_results["steps"].append({
                            "step": f"search_{term.replace(' ', '_')}",
                            "status": "ok",
                            "buttons_count": len(buttons),
                            "has_product_info": "*" in response_text
                        })
                        scenario_results["search_queries"].append({
                            "term": term,
                            "found_results": True,
                            "buttons_count": len(buttons)
                        })
                        print(f"✅ '{term}' found results - {len(buttons)} buttons")
                    else:
                        scenario_results["steps"].append({
                            "step": f"search_{term.replace(' ', '_')}",
                            "status": "no_results"
                        })
                        scenario_results["search_queries"].append({
                            "term": term,
                            "found_results": False
                        })
                        print(f"⚠️ '{term}' - no specific results")
                else:
                    scenario_results["errors"].append(f"Search for '{term}' failed: {response.get('error')}")
                    print(f"❌ Search for '{term}' failed")
            
            scenario_results["status"] = "passed" if not scenario_results["errors"] else "failed"
            
        except Exception as e:
            scenario_results["status"] = "error"
            scenario_results["errors"].append(f"Exception: {str(e)}")
            print(f"❌ Exception during catalog testing: {e}")
        
        scenario_results["duration"] = time.time() - start_time
        self.test_results.append(scenario_results)
        
        successful_searches = len([q for q in scenario_results["search_queries"] if q.get("found_results")])
        print(f"📊 Catalog search completed: {successful_searches}/{len(search_terms)} searches found results")
        return scenario_results

async def run_real_e2e_tests():
    """
    🚀 REAL E2E Testing Suite для InSilver Bot
    """
    print("🎭 LEVEL 8: REAL TELEGRAM E2E TESTING")
    print("=" * 50)
    print(f"💰 Budget: ${BUDGET_LIMIT}")
    print(f"🎯 Goal: Test live InSilver bot workflows and find real bugs")
    print(f"📱 Mode: Real Telegram API integration\n")
    
    # Load bot token
    from dotenv import load_dotenv
    load_dotenv('/home/sashok/.openclaw/workspace/insilver-v3/.env')
    BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    if not BOT_TOKEN:
        print("❌ TELEGRAM_TOKEN not found in .env")
        return
    
    track_cost(0.005, "Initialize real E2E testing session")
    
    print(f"🤖 InSilver Bot Token: ...{BOT_TOKEN[-8:] if BOT_TOKEN else 'unknown'}")
    print("🎭 Starting real user simulation tests...\n")
    
    # Overall test results
    all_test_results = []
    total_scenarios = 0
    passed_scenarios = 0
    failed_scenarios = 0
    
    try:
        # Initialize real Telegram tester
        async with RealTelegramTester(BOT_TOKEN) as tester:
            scenarios = RealE2EScenarios(tester)
            
            print("🚀 EXECUTING REAL E2E TEST SCENARIOS")
            print("=" * 40)
            
            # Scenario 1: Complete Order Workflow
            try:
                result1 = await scenarios.scenario_real_order_workflow()
                all_test_results.append(result1)
                total_scenarios += 1
                if result1['status'] == 'passed':
                    passed_scenarios += 1
                else:
                    failed_scenarios += 1
            except Exception as e:
                print(f"❌ Order workflow test failed: {e}")
                track_cost(0.002, f"Order workflow exception: {str(e)[:30]}")
                failed_scenarios += 1
            
            await asyncio.sleep(2)  # Pause between major tests
            
            # Scenario 2: Command Menu Testing  
            try:
                result2 = await scenarios.scenario_command_testing()
                all_test_results.append(result2)
                total_scenarios += 1
                if result2['status'] == 'passed':
                    passed_scenarios += 1
                else:
                    failed_scenarios += 1
            except Exception as e:
                print(f"❌ Command testing failed: {e}")
                track_cost(0.002, f"Command test exception: {str(e)[:30]}")
                failed_scenarios += 1
            
            await asyncio.sleep(2)
            
            # Scenario 3: Catalog Search Testing
            try:
                result3 = await scenarios.scenario_catalog_search_testing()
                all_test_results.append(result3)
                total_scenarios += 1
                if result3['status'] == 'passed':
                    passed_scenarios += 1
                else:
                    failed_scenarios += 1
            except Exception as e:
                print(f"❌ Catalog search testing failed: {e}")
                track_cost(0.002, f"Catalog test exception: {str(e)[:30]}")
                failed_scenarios += 1
            
            # Save comprehensive test session
            await tester.save_test_session("comprehensive_e2e_results.json")
        
    except Exception as e:
        print(f"❌ Fatal error in E2E testing: {e}")
        track_cost(0.003, f"Fatal error: {str(e)[:30]}")
        return
    
    # Comprehensive Results Analysis
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE E2E TEST RESULTS")
    print("=" * 60)
    
    print(f"🎭 Total Scenarios: {total_scenarios}")
    print(f"✅ Passed: {passed_scenarios}")
    print(f"❌ Failed: {failed_scenarios}")
    print(f"📈 Success Rate: {(passed_scenarios/total_scenarios)*100:.1f}%" if total_scenarios > 0 else "N/A")
    
    print(f"\n💰 COST ANALYSIS:")
    print(f"   Tool calls executed: {TOOL_CALLS_COUNT}")
    print(f"   Total estimated cost: ${ESTIMATED_COST:.3f}")
    print(f"   Budget utilization: {(ESTIMATED_COST/BUDGET_LIMIT)*100:.1f}%")
    print(f"   Remaining budget: ${BUDGET_LIMIT - ESTIMATED_COST:.3f}")
    
    # Detailed Results Breakdown
    print(f"\n🔍 DETAILED SCENARIO BREAKDOWN:")
    for i, result in enumerate(all_test_results, 1):
        status_emoji = "✅" if result['status'] == 'passed' else "❌"
        print(f"   {status_emoji} Scenario {i}: {result['name']} ({result['duration']:.1f}s)")
        if result.get('errors'):
            for error in result['errors'][:2]:  # Show first 2 errors
                print(f"      ⚠️ {error}")
    
    # Bug Detection Summary
    all_errors = []
    for result in all_test_results:
        all_errors.extend(result.get('errors', []))
    
    if all_errors:
        print(f"\n🐛 BUGS DETECTED ({len(all_errors)} total):")
        unique_errors = list(set(all_errors))[:5]  # Show unique errors, max 5
        for i, error in enumerate(unique_errors, 1):
            print(f"   {i}. {error}")
    else:
        print(f"\n🎉 NO CRITICAL BUGS DETECTED!")
    
    # Performance Insights
    total_duration = sum([r.get('duration', 0) for r in all_test_results])
    print(f"\n⚡ PERFORMANCE INSIGHTS:")
    print(f"   Total test execution: {total_duration:.1f}s")
    print(f"   Average scenario time: {total_duration/len(all_test_results):.1f}s" if all_test_results else "N/A")
    
    # Final Assessment
    print(f"\n🎯 FINAL ASSESSMENT:")
    if passed_scenarios == total_scenarios and not all_errors:
        print("   🌟 EXCELLENT: All tests passed, no bugs detected")
    elif passed_scenarios >= total_scenarios * 0.8:
        print("   👍 GOOD: Most tests passed, minor issues detected") 
    elif passed_scenarios >= total_scenarios * 0.6:
        print("   ⚠️ FAIR: Some critical issues need attention")
    else:
        print("   🔴 POOR: Major issues detected, needs immediate fixes")
    
    print(f"\n💾 Detailed logs saved to: comprehensive_e2e_results.json")
    print("🎭 Level 8 E2E Testing completed!")
    
    track_cost(0.005, "Complete E2E testing session")
    
    return {
        "total_scenarios": total_scenarios,
        "passed": passed_scenarios,
        "failed": failed_scenarios,
        "total_cost": ESTIMATED_COST,
        "bugs_found": len(all_errors),
        "assessment": "excellent" if passed_scenarios == total_scenarios else "needs_work"
    }

if __name__ == "__main__":
    asyncio.run(run_real_e2e_tests())