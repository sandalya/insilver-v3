#!/usr/bin/env python3
"""
InSilver Bot v3 - Стабільна Telegram інтеграція
Створено для вирішення проблем з getUpdates конфліктами
"""
import logging
import os
import sys
import signal
import traceback
import asyncio
import time
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import Conflict, TimedOut, NetworkError, BadRequest

from core.lock import acquire_lock, release_lock
from core.config import BOT_TOKEN, LOGS_DIR, ADMIN_IDS
from core.health import health_checker

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

# Enhanced logging setup with DEBUG level for troubleshooting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(f"{LOGS_DIR}/bot_stable.log"),
        logging.StreamHandler()
    ]
)

# Enable debug logging for telegram library
logging.getLogger("telegram").setLevel(logging.DEBUG)
logging.getLogger("telegram.ext").setLevel(logging.DEBUG)

log = logging.getLogger("main_stable")

# Global error tracking
error_count = 0
last_error_time = 0


class TelegramStableBot:
    """Стабільна реалізація Telegram бота з обробкою всіх типових проблем"""
    
    def __init__(self, token: str):
        self.token = token
        self.app = None
        self.is_running = False
        self.restart_count = 0
        
    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        log.info(f"🎯 START від {user.id} ({user.username or user.first_name})")
        
        response = f"Вітаю, {user.first_name}!\\n\\nВи звернулись до InSilver v3 - ювелірна майстерня.\\n\\nТест стабільного зв'язку пройшов успішно! 🎉"
        
        await update.message.reply_text(response)
        health_checker.increment_messages()
        
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages"""
        user = update.effective_user
        text = update.message.text
        
        log.info(f"🎯 MSG від {user.id}: '{text[:50]}...'")
        
        # Simple echo response for testing stability
        response = f"✅ Отримав повідомлення: '{text}'\\n\\n🔧 Telegram зв'язок працює стабільно!"
        
        await update.message.reply_text(response)
        health_checker.increment_messages()
        
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors occurred in the dispatcher"""
        global error_count, last_error_time
        
        error_count += 1
        last_error_time = time.time()
        
        log.error(f"💥 Telegram error #{error_count}: {context.error}")
        
        if isinstance(context.error, Conflict):
            log.critical("🚨 КОНФЛІКТ ТОКЕНІВ! Інший процес використовує getUpdates")
            log.critical("Зупиняємо бот щоб уникнути подальших конфліктів")
            
            # Notify admin about conflict
            if update and hasattr(update, 'effective_chat'):
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="⚠️ Виявлено конфлікт токенів. Перезапускаємо бот..."
                    )
                except:
                    pass
            
            # Stop application to avoid further conflicts
            if self.app:
                await self.app.stop()
                return
        
        elif isinstance(context.error, (TimedOut, NetworkError)):
            log.warning(f"⚠️ Мережева помилка (спроба #{error_count}): {context.error}")
            if error_count > 10:
                log.error("Занадто багато мережевих помилок, перезапускаємо...")
                await self.restart_application()
        
        elif isinstance(context.error, BadRequest):
            log.error(f"❌ Невірний запит: {context.error}")
        
        else:
            log.error(f"❓ Невідома помилка: {context.error}")
            log.error(f"Traceback: {traceback.format_exc()}")
    
    async def restart_application(self):
        """Restart the application safely"""
        self.restart_count += 1
        log.info(f"🔄 Перезапуск #{self.restart_count}...")
        
        if self.app:
            await self.app.stop()
            await asyncio.sleep(5)  # Wait before restart
    
    def setup_handlers(self):
        """Setup all handlers"""
        if not self.app:
            return
            
        # Add error handler first
        self.app.add_error_handler(self.error_handler)
        
        # Add command handlers
        self.app.add_handler(CommandHandler("start", self.start_handler))
        
        # Add message handler
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.message_handler
        ))
        
        log.info("✅ Handlers налаштовано")
    
    async def check_token_conflicts(self):
        """Check for token conflicts before starting"""
        log.info("🔍 Перевірка конфліктів токенів...")
        
        try:
            # Try to get bot info
            bot_info = await self.app.bot.get_me()
            log.info(f"✅ Токен валідний: @{bot_info.username}")
            
            # Try a simple getUpdates call to check for conflicts
            updates = await self.app.bot.get_updates(limit=1, timeout=5)
            log.info(f"✅ getUpdates тест пройшов: {len(updates)} updates")
            
            return True
            
        except Conflict as e:
            log.error(f"🚨 КОНФЛІКТ ТОКЕНІВ: {e}")
            return False
        except Exception as e:
            log.error(f"❌ Помилка перевірки токена: {e}")
            return False
    
    async def run_stable(self):
        """Run bot with stability measures"""
        global error_count
        error_count = 0
        
        try:
            # Build application
            self.app = Application.builder().token(self.token).build()
            
            # Setup handlers
            self.setup_handlers()
            
            # Check for token conflicts
            await self.app.initialize()
            
            if not await self.check_token_conflicts():
                log.error("❌ Не вдалося пройти перевірку конфліктів")
                return False
            
            log.info("✅ Перевірки пройшли успішно")
            
            # Set running flag
            self.is_running = True
            
            # Start polling with optimal settings
            log.info("🚀 Запускаємо polling...")
            await self.app.start()
            
            # Manual polling loop for better control
            updater = self.app.updater
            
            log.info("📡 Початок отримання updates...")
            
            # Start the updater
            await updater.start_polling(
                poll_interval=1.0,
                timeout=30,
                bootstrap_retries=-1,  # Infinite retries
                read_timeout=30,
                write_timeout=30,
                connect_timeout=30,
                pool_timeout=30,
                drop_pending_updates=False,  # DON'T drop messages!
            )
            
            # Keep running
            while self.is_running:
                await asyncio.sleep(1)
                
                # Health check
                if time.time() - last_error_time > 300:  # Reset error count after 5 minutes
                    error_count = 0
            
        except KeyboardInterrupt:
            log.info("⏹️ Отримано SIGINT, зупиняємо...")
            self.is_running = False
        except Exception as e:
            log.critical(f"💥 Критична помилка: {e}")
            log.critical(f"Traceback: {traceback.format_exc()}")
            return False
        finally:
            if self.app:
                await self.app.stop()
                await self.app.shutdown()
                
        return True


def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Global uncaught exception handler."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    log.critical("💥 Global critical error:", exc_info=(exc_type, exc_value, exc_traceback))
    release_lock()


async def main():
    """Main entry point with comprehensive error handling."""
    sys.excepthook = global_exception_handler
    
    try:
        # Validate configuration
        if not BOT_TOKEN:
            log.error("❌ TELEGRAM_TOKEN не встановлений в .env")
            sys.exit(1)
        
        # Acquire lock to prevent multiple instances
        acquire_lock()
        log.info("🔐 Lock отримано")
        
        log.info("🚀 InSilver v3 STABLE стартує...")
        log.info(f"📱 Token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-10:]}")
        
        # Initialize health monitoring
        health_checker.mark_activity()
        
        # Create and run stable bot
        bot = TelegramStableBot(BOT_TOKEN)
        
        success = await bot.run_stable()
        
        if success:
            log.info("✅ Бот завершив роботу успішно")
        else:
            log.error("❌ Бот завершив роботу з помилками")
            sys.exit(1)
        
    except Exception as e:
        log.critical(f"💥 Критична помилка в main(): {e}")
        log.critical(f"Traceback:\\n{traceback.format_exc()}")
        health_checker.increment_errors()
        sys.exit(1)
    finally:
        log.info("🔄 Завершуємо роботу...")
        release_lock()


if __name__ == "__main__":
    asyncio.run(main())