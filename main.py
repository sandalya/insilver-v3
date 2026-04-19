#!/usr/bin/env python3
"""InSilver Bot v3 - WORKING VERSION базована на мінімальному боті"""
import logging
import os
import sys
import signal
import traceback
import asyncio
from telegram.ext import Application
from telegram import BotCommand
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

# CRITICAL: Enable bot.client logger
logging.getLogger("bot.client").setLevel(logging.INFO)

# ✅ CLAUDE.AI: Enable telegram debug logging  
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)

log = logging.getLogger("main")

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Global uncaught exception handler."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    log.critical("💥 Критична помилка:", exc_info=(exc_type, exc_value, exc_traceback))
async def simple_error_handler(update: object, context):
    """Simple error handler like minimal bot"""
    error = context.error
    log.error(f"💥 Telegram error: {error}")
    
    # Don't stop on network errors - just log them
    if "Conflict" in str(error):
        log.critical("🚨 КОНФЛІКТ ТОКЕНІВ!")
    
    health_checker.increment_errors()

def main():
    """Main entry point - Claude.AI рекомендований підхід"""
    sys.excepthook = global_exception_handler
    
    # Validate configuration first
    if not BOT_TOKEN:
        log.error("❌ TELEGRAM_TOKEN не встановлений в .env")
        sys.exit(1)
    
    try:
        log.info("🚀 InSilver v3 CLAUDE-FIXED стартує...")
        
        # ✅ Application з правильними timeouts (фікс для Pi5)
        app = (
            Application.builder()
            .token(BOT_TOKEN)
            .connect_timeout(30)
            .read_timeout(30)
            .write_timeout(30)
            .build()
        )
        
        # Add error handler first
        app.add_error_handler(simple_error_handler)
        
        # Setup handlers
        setup_handlers(app)
        log.info(f"✅ Handlers налаштовано: {len(app.handlers[1])} handlers")
        
        # Health monitoring
        health_checker.mark_activity()
        
        # ✅ Критично: очистити webhook і pending updates перед стартом
        async def post_init(application):
            await application.bot.delete_webhook(drop_pending_updates=True)
            log.info("🧹 Webhook очищено, pending updates скинуто")
        
        app.post_init = post_init
        
        log.info("🎯 ЗАПУСК run_polling() з фіксом conflict")
        
        # ✅ run_polling з правильними параметрами
        app.run_polling(
            drop_pending_updates=True,    # 🔑 Критично для фіксу conflict
            poll_interval=1.0,
            timeout=20,                   # Збільшено для Pi5
            allowed_updates=None          # Всі типи updates
        )
        
    except KeyboardInterrupt:
        log.info("⏹️ Отримано SIGINT, завершуємо...")
    except Exception as e:
        log.critical(f"💥 Критична помилка: {e}")
        log.critical(f"Traceback:\\n{traceback.format_exc()}")
        health_checker.increment_errors()
        raise
    finally:
        log.info("🔄 Завершуємо роботу...")
if __name__ == "__main__":
    main()