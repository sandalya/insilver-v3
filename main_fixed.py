#!/usr/bin/env python3
"""InSilver Bot v3 - WORKING VERSION базована на мінімальному боті"""
import logging
import os
import sys
import signal
import traceback
import asyncio
from telegram.ext import Application
from core.lock import acquire_lock, release_lock
from core.config import BOT_TOKEN, LOGS_DIR
from core.health import health_checker
from bot.client import setup_handlers

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

# Simple logging setup (like minimal bot)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(f"{LOGS_DIR}/bot.log"),
        logging.StreamHandler()
    ]
)

log = logging.getLogger("main")

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Global uncaught exception handler."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    log.critical("💥 Критична помилка:", exc_info=(exc_type, exc_value, exc_traceback))
    release_lock()

async def simple_error_handler(update: object, context):
    """Simple error handler like minimal bot"""
    error = context.error
    log.error(f"💥 Telegram error: {error}")
    
    # Don't stop on network errors - just log them
    if "Conflict" in str(error):
        log.critical("🚨 КОНФЛІКТ ТОКЕНІВ!")
    
    health_checker.increment_errors()

def main():
    """Main entry point - simplified like minimal bot"""
    sys.excepthook = global_exception_handler
    
    async def async_main():
        try:
            # Validate configuration
            if not BOT_TOKEN:
                log.error("❌ TELEGRAM_TOKEN не встановлений в .env")
                sys.exit(1)
            
            acquire_lock()
            log.info("🚀 InSilver v3 FIXED стартує...")

            # Simple application build (like minimal bot)
            app = Application.builder().token(BOT_TOKEN).build()
            
            # Add simple error handler first
            app.add_error_handler(simple_error_handler)
            
            # Setup existing handlers (KNOWN WORKING)
            setup_handlers(app)
            log.info(f"✅ Handlers налаштовано: {len(app.handlers[0])} handlers")
            
            # Health monitoring
            health_checker.mark_activity()
            
            # Initialize and start (MINIMAL BOT METHOD)
            await app.initialize()
            await app.start()
            
            log.info("✅ Application started")
            
            # Start polling with SIMPLE settings (like minimal bot)
            await app.updater.start_polling(
                drop_pending_updates=False,  # ⭐ CRITICAL!
                poll_interval=1.0,
                timeout=10,  # Shorter like minimal bot
                read_timeout=10,
                write_timeout=10,
                connect_timeout=10,
            )
            
            log.info("🎯 POLLING STARTED - BOT READY!")
            
            # Keep running (like minimal bot)
            while True:
                await asyncio.sleep(1)
                health_checker.mark_activity()
        
        except KeyboardInterrupt:
            log.info("⏹️ Отримано SIGINT, завершуємо...")
        except Exception as e:
            log.critical(f"💥 Критична помилка: {e}")
            log.critical(f"Traceback:\\n{traceback.format_exc()}")
            health_checker.increment_errors()
            raise
        finally:
            log.info("🔄 Завершуємо роботу...")
            if 'app' in locals():
                await app.updater.stop()
                await app.stop()
                await app.shutdown()
            release_lock()
    
    # Run async main
    try:
        asyncio.run(async_main())
    except Exception as e:
        log.critical(f"💥 Критична помилка в main(): {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()